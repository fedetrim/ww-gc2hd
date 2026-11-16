#!/usr/bin/env python3
"""GameCube side of the machine-code audit: every call in main.dol and in all RELs, with the constant
values of the argument registers.

Loads main.dol and every REL of the disc (loose files and those inside RELS.arc, Yaz0), applies the REL
relocation tables (calls into the dol are resolved through the relocation addend), names every function and
attributes it to a source file through the symbol and split tables of the decompilation, and runs ppc.py
over each function.

Inputs:  GameCube disc image, USA (GZLE01): main.dol, /RELS.arc, every *.rel
         zeldaret/tww clone: config/GZLE01/symbols.txt, splits.txt and rels/*/{symbols,splits}.txt
         (locations: audit/auditenv.py; setup: docs/SETUP-RESEARCH.md)
Output:  gc_calls.json (about 30 MB) in research/out/machine-code/, or the path given as argument:
         {"game_info": address of g_dComIfG_gameInfo, "calls": [...], "funcs": [...], "names": {address: symbol}}
Run:     python3 -I audit/machine-code/gc_extract.py [OUT.json]        (about 15 s)

Also imported by other scripts for load() (relocated memory image) and the symbol/split parsers.
"""
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import ppc  # noqa: E402
import auditenv  # noqa: E402

CFG = os.path.join(auditenv.TWW, "config", "GZLE01")

TARGET_RE = re.compile(r"dSv_|^dComIfGs_|^fopAcM_(is|on|off|rev)Switch|^dComIfGp_.*(Switch|Tbox)|Event(Bit|Reg)|"
                       r"^checkItemGet|^isHeart|^getSelectItem|^dStage_.*Tbox|^check_?[A-Za-z]*Get")


def yaz0(d):
    if d[:4] != b"Yaz0":
        return d
    size = struct.unpack(">I", d[4:8])[0]
    out = bytearray()
    i = 16
    while len(out) < size:
        code = d[i]
        i += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if code & 0x80 >> bit:
                out.append(d[i])
                i += 1
            else:
                b1, b2 = d[i], d[i + 1]
                i += 2
                dist = ((b1 & 0xF) << 8 | b2) + 1
                n = b1 >> 4
                if n == 0:
                    n = d[i] + 0x12
                    i += 1
                else:
                    n += 2
                for _ in range(n):
                    out.append(out[-dist])
    return bytes(out)


def rarc_files(d):
    assert d[:4] == b"RARC", d[:4]
    hdr = 0x20
    data_off = struct.unpack(">I", d[0x0C:0x10])[0] + hdr
    nfiles, files_off, _, str_off = struct.unpack(">IIII", d[hdr + 8:hdr + 0x18])
    files_off += hdr
    str_off += hdr
    out = {}
    for i in range(nfiles):
        e = d[files_off + i * 0x14:files_off + (i + 1) * 0x14]
        if e[4] & 0x02:
            continue
        name_off = struct.unpack(">H", e[6:8])[0]
        off, size = struct.unpack(">II", e[8:16])
        name = d[str_off + name_off:d.index(b"\0", str_off + name_off)].decode("latin-1")
        out[name] = d[data_off + off:data_off + off + size]
    return out


def parse_symbols(path):
    """[(name, section, addr, size, type)]"""
    out = []
    for line in open(path):
        m = re.match(r"(\S+) = (\S+):0x([0-9A-Fa-f]+); // (.*)", line)
        if not m:
            continue
        attrs = dict(kv.split(":", 1) for kv in m.group(4).split() if ":" in kv)
        out.append((m.group(1), m.group(2), int(m.group(3), 16), int(attrs.get("size", "0"), 16), attrs.get("type", "")))
    return out


def parse_splits(path):
    """section order, [(file, section, start, end)]"""
    sections, out, cur, in_sections = [], [], None, False
    for line in open(path):
        if line.startswith("Sections:"):
            in_sections = True
            continue
        if not line.strip():
            in_sections = False
            continue
        if in_sections:
            sections.append(line.split()[0])
            continue
        if not line.startswith("\t"):
            cur = line.strip().rstrip(":")
            continue
        m = re.match(r"\s+(\S+)\s+start:0x([0-9A-Fa-f]+) end:0x([0-9A-Fa-f]+)", line)
        if m:
            out.append((cur, m.group(1), int(m.group(2), 16), int(m.group(3), 16)))
    return sections, out


class Mem:
    def __init__(self):
        self.segs = []   # (addr, bytes)

    def add(self, addr, data):
        self.segs.append((addr, bytearray(data)))

    def find(self, addr):
        for a, d in self.segs:
            if a <= addr < a + len(d):
                return a, d
        return None, None

    def r32(self, addr):
        a, d = self.find(addr)
        return struct.unpack_from(">I", d, addr - a)[0] if d is not None else 0

    def r16(self, addr):
        a, d = self.find(addr)
        return struct.unpack_from(">H", d, addr - a)[0] if d is not None else 0

    def r8(self, addr):
        a, d = self.find(addr)
        return d[addr - a] if d is not None else 0

    def w(self, addr, fmt, v):
        a, d = self.find(addr)
        struct.pack_into(fmt, d, addr - a, v)


def load():
    fst = auditenv.gc_fst()
    f = open(auditenv.gc_iso(), "rb")
    hdr = f.read(0x440)
    dol_off = struct.unpack(">I", hdr[0x420:0x424])[0]
    f.seek(dol_off)
    dh = f.read(0x100)
    offs = struct.unpack(">18I", dh[0:0x48])
    addrs = struct.unpack(">18I", dh[0x48:0x90])
    sizes = struct.unpack(">18I", dh[0x90:0xD8])
    mem = Mem()
    for o, a, s in zip(offs, addrs, sizes):
        if s:
            f.seek(dol_off + o)
            mem.add(a, f.read(s))
    rels = {}
    for p, (off, size) in fst.items():
        if p.endswith(".rel"):
            f.seek(off)
            rels[os.path.basename(p)[:-4]] = yaz0(f.read(size))
    off, size = fst["/RELS.arc"]
    f.seek(off)
    for name, data in rarc_files(yaz0(f.read(size))).items():
        if name.endswith(".rel"):
            rels[name[:-4]] = yaz0(data)
    return mem, rels


def main(out_path):
    mem, rels = load()
    dol_syms = parse_symbols(os.path.join(CFG, "symbols.txt"))
    addr_name = {}
    for name, sec, addr, size, typ in dol_syms:
        addr_name.setdefault(addr, name)
    funcs = []   # (file, func name, start, end, module)
    _, dol_splits = parse_splits(os.path.join(CFG, "splits.txt"))
    text_splits = sorted((s, e, fn) for fn, sec, s, e in dol_splits if sec in (".text", ".init"))

    def dol_file(addr):
        for s, e, fn in text_splits:
            if s <= addr < e:
                return fn
        return "?"
    for name, sec, addr, size, typ in dol_syms:
        if typ == "function" and size:
            funcs.append((dol_file(addr), name, addr, addr + size, "dol"))

    base = 0x90000000
    rel24 = {}
    global LAST_REL24
    LAST_REL24 = rel24
    rel_info = {}
    for rname in sorted(rels):
        d = rels[rname]
        sp = os.path.join(CFG, "rels", rname, "splits.txt")
        if not os.path.exists(sp):
            print("no config for rel", rname, file=sys.stderr)
            continue
        mod_id, = struct.unpack_from(">I", d, 0)
        nsec, sec_off = struct.unpack_from(">II", d, 0x0C)
        bss_size, rel_off, imp_off, imp_size = struct.unpack_from(">IIII", d, 0x20)
        sec_addr, bss_addr = [], base + ((len(d) + 0x1F) & ~0x1F)
        for i in range(nsec):
            o, s = struct.unpack_from(">II", d, sec_off + i * 8)
            if o & ~1:
                sec_addr.append(base + (o & ~1))
            elif s:
                sec_addr.append(bss_addr)
            else:
                sec_addr.append(None)
        mem.add(base, d)
        mem.add(bss_addr, bytes(bss_size))
        rel_info[mod_id] = (rname, sec_addr)
        rels[rname] = (d, base, sec_addr, mod_id, imp_off, imp_size)
        base += (len(d) + bss_size + 0x1000 + 0xFFF) & ~0xFFF

    for rname, v in rels.items():
        if not isinstance(v, tuple):
            continue
        d, rbase, sec_addr, mod_id, imp_off, imp_size = v
        for i in range(imp_size // 8):
            imp_mod, roff = struct.unpack_from(">II", d, imp_off + i * 8)
            cur = None
            p = roff
            while True:
                off, typ, sec, addend = struct.unpack_from(">HBBI", d, p)
                p += 8
                if typ == 203:
                    break
                if typ == 202:
                    cur = sec_addr[sec]
                    continue
                cur += off
                if typ == 201:
                    continue
                if imp_mod == 0:
                    val = addend
                else:
                    tsec = rel_info[imp_mod][1][sec] if imp_mod in rel_info else None
                    if tsec is None:
                        continue
                    val = tsec + addend
                if typ == 1:
                    mem.w(cur, ">I", val & 0xFFFFFFFF)
                elif typ in (3, 4):
                    mem.w(cur, ">H", val & 0xFFFF)
                elif typ == 5:
                    mem.w(cur, ">H", val >> 16 & 0xFFFF)
                elif typ == 6:
                    mem.w(cur, ">H", (val + 0x8000) >> 16 & 0xFFFF)
                elif typ == 10:
                    rel24[cur] = val & 0xFFFFFFFF
                elif typ == 11:
                    ins = mem.r32(cur)
                    mem.w(cur, ">I", (ins & 0xFFFF0003) | ((val - cur) & 0xFFFC))
                elif typ == 2:
                    ins = mem.r32(cur)
                    mem.w(cur, ">I", (ins & 0xFC000003) | (val & 0x03FFFFFC))
                else:
                    print("unhandled reloc", typ, rname, file=sys.stderr)
        secs, splits = parse_splits(os.path.join(CFG, "rels", rname, "splits.txt"))
        real = [a for a in sec_addr if a is not None]
        sec_map = dict(zip(secs, real))
        tsplits = sorted((s, e, fn) for fn, sec, s, e in splits if sec == ".text")
        for name, sec, addr, size, typ in parse_symbols(os.path.join(CFG, "rels", rname, "symbols.txt")):
            if sec not in sec_map:
                continue
            a = sec_map[sec] + addr
            addr_name.setdefault(a, rname + ":" + name)
            if typ == "function" and size:
                fn = next((f for s, e, f in tsplits if s <= addr < e), "?")
                funcs.append((fn, name, a, a + size, rname))

    game_info = next(a for a, n in addr_name.items() if n == "g_dComIfG_gameInfo")
    calls = []
    init = {r: frozenset([("a%d" % r, 0)]) for r in range(3, 11)}
    for fn, name, start, end, module in funcs:
        def on_call(pc, target, regs, fn=fn, name=name, start=start):
            target = rel24.get(pc, target)
            if target is None:
                return
            if addr_name.get(target, "").startswith(("_savegpr_", "_restgpr_", "_savefpr_", "_restfpr_")):
                return "keep"
            rec = {"file": fn, "func": name, "fs": start, "pc": "%08X" % pc, "t": target}
            for r in range(3, 8):
                if r in regs:
                    rec["r%d" % r] = sorted(regs[r], key=str)
            calls.append(rec)
        ppc.scan_function(mem.r32, start, end, on_call, init)
    json.dump({"game_info": game_info, "calls": calls, "funcs": [(f, n, m, s, e) for f, n, s, e, m in funcs],
               "names": {str(a): n for a, n in addr_name.items()}},
              open(out_path, "w"))
    print(len(funcs), "functions,", len(calls), "calls")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else auditenv.out_file("machine-code", "gc_calls.json"))
