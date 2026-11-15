#!/usr/bin/env python3
"""HD side of the machine-code audit: every call (bl) in cking.rpx with the constant values of the argument
registers.

Decompresses the sections of cking.rpx, maps code to source files through the `/* 0XXXXXXX */` function
address markers of the HD decompilation (a function with no marker is attributed to the marked function
before it) and runs ppc.py over each function.

Inputs:  extracted Wind Waker HD, USA v0: code/cking.rpx
         ZeldaWWHDDecomp/wwhd clone: wwhd_src/ (all .cpp/.c/.inc/.h, for the address markers)
         (locations: audit/auditenv.py; setup: docs/SETUP-RESEARCH.md)
Output:  hd_calls.json (about 30 MB) in research/out/machine-code/, or the path given as argument:
         {"calls": [...], "markers": {address: [file, function, line]}, "sections": [...]}
Run:     python3 -I audit/machine-code/hd_extract.py [OUT.json]        (about 5 s)

Also imported by other scripts for load_rpx() and markers().
"""
import json
import os
import re
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import ppc  # noqa: E402
import auditenv  # noqa: E402

RPX = os.path.join(auditenv.HD_GAME, "code", "cking.rpx")
SRC = os.path.join(auditenv.WWHD, "wwhd_src")


def load_rpx():
    d = open(RPX, "rb").read()
    shoff, = struct.unpack_from(">I", d, 0x20)
    shentsize, shnum, shstrndx = struct.unpack_from(">HHH", d, 0x2E)
    secs = []
    for i in range(shnum):
        name, typ, flags, addr, off, size, link, info, align, entsize = struct.unpack_from(">10I", d, shoff + i * shentsize)
        data = b""
        if typ != 8 and off:
            data = d[off:off + size]
            if flags & 0x08000000:
                data = zlib.decompress(data[4:])
        secs.append(dict(name=name, type=typ, flags=flags, addr=addr, data=data, link=link, info=info, size=size))
    strtab = secs[shstrndx]["data"]
    for s in secs:
        s["name"] = strtab[s["name"]:strtab.index(b"\0", s["name"])].decode()
    return secs


def markers():
    """{addr: (relative file, name)} from /* 0XXXXXXX */ markers in the HD source"""
    out = {}
    pat = re.compile(r"^/\* ([0-9A-F]{8}) \*/\s*$")
    for root, _, files in os.walk(SRC):
        for fn in files:
            if not fn.endswith((".cpp", ".c", ".inc", ".h")):
                continue
            p = os.path.join(root, fn)
            lines = open(p, errors="replace").read().split("\n")
            for i, line in enumerate(lines):
                m = pat.match(line)
                if not m:
                    continue
                sig = " ".join(lines[i + 1:i + 4])
                head = sig.split("(")[0]
                nm = re.findall(r"[A-Za-z_~][A-Za-z_0-9:~<>]*", head)
                out[int(m.group(1), 16)] = (os.path.relpath(p, SRC), nm[-1] if nm else "?", i + 2)
    return out


def main(out_path):
    secs = load_rpx()
    text = next(s for s in secs if s["name"] == ".text")
    base, data = text["addr"], text["data"]
    mk = markers()
    starts = sorted(a for a in mk if base <= a < base + len(data))

    def r32(a):
        return struct.unpack_from(">I", data, a - base)[0]

    calls = []
    init = {r: frozenset([("a%d" % r, 0)]) for r in range(3, 11)}
    for i, st in enumerate(starts):
        en = starts[i + 1] if i + 1 < len(starts) else base + len(data)
        fn, name, line = mk[st]

        def on_call(pc, target, regs, fn=fn, name=name, st=st):
            if target is None:
                return
            rec = {"file": fn, "func": name, "fs": st, "pc": "%08X" % pc, "t": target}
            for r in range(3, 8):
                if r in regs:
                    rec["r%d" % r] = sorted(regs[r], key=str)
            calls.append(rec)
        ppc.scan_function(r32, st, en, on_call, init)
    json.dump({"calls": calls, "markers": {"%08X" % a: v for a, v in mk.items()},
               "sections": [(s["name"], s["addr"], s["size"]) for s in secs]}, open(out_path, "w"))
    print(len(starts), "functions,", len(calls), "calls")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else auditenv.out_file("machine-code", "hd_calls.json"))
