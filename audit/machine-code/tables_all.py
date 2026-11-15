#!/usr/bin/env python3
"""For every data object (symbol) of every GameCube REL: is it present byte for byte in HD's .rodata/.data?

Objects that hold pointers (relocated words), all-zero objects, strings, vtables and compiler-generated
symbols are skipped. Prints the objects not found, per REL, and the totals.

Inputs:  GameCube disc image, zeldaret/tww config/GZLE01/rels/*/{symbols,splits}.txt, cking.rpx,
         stubs.json in research/out/machine-code/ (stubs.py --json)
Output:  text on stdout; the audit kept it as tables_all.txt (2,331 compared, 2,155 identical).
Run:     python3 -I audit/machine-code/tables_all.py [--stubs-only]       (a few seconds)

Limit: the dol's own data objects are not walked (only RELs); use tablecmp.py dol SYMBOL for those.
"""
import json, os, re, struct, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gc_extract as g, hd_extract as h, ppc

def main():
    memref = {}
    ol = g.load
    def load():
        m, r = ol(); memref["m"] = m; memref["r"] = r; return m, r
    g.load = load
    ppc.scan_function = lambda *a, **k: None
    jd = json.dump; json.dump = lambda *a, **k: None
    g.main(os.devnull); json.dump = jd
    mem = memref["m"]
    secs = h.load_rpx()
    hd = b"\0\0\0\0".join(s["data"] for s in secs if s["name"] in (".rodata", ".data"))
    stubs = {os.path.basename(k).rsplit(".", 1)[0] for k in json.load(open(g.auditenv.out_file("machine-code", "stubs.json")))}
    tot = found = skipped = 0
    res = collections.defaultdict(list)
    for mod, v in sorted(memref["r"].items()):
        if not isinstance(v, tuple): continue
        if "--stubs-only" in sys.argv and mod not in stubs: continue
        d, base, sec_addr, mid, _, _ = v
        secn, _ = g.parse_splits(os.path.join(g.CFG, "rels", mod, "splits.txt"))
        smap = dict(zip(secn, [a for a in sec_addr if a is not None]))
        for n, sec, a, sz, t in g.parse_symbols(os.path.join(g.CFG, "rels", mod, "symbols.txt")):
            if t != "object" or sec not in (".rodata", ".data") or sz < 4 or sz > 0x1000: continue
            if n.startswith(("__vt", "@", "lbl_", "...")) or "stringBase" in n or "$" in n and "init$" in n: continue
            ad = smap[sec] + a
            b, dd = mem.find(ad)
            raw = bytes(dd[ad - b:ad - b + sz])
            words = [struct.unpack_from(">I", raw, i)[0] for i in range(0, sz - 3, 4)]
            if any(0x80003000 <= w < 0x81800000 or 0x90000000 <= w < 0x98000000 for w in words): skipped += 1; continue
            if not any(raw): skipped += 1; continue
            tot += 1
            if hd.find(raw) >= 0: found += 1
            else: res[mod].append((n, sz, raw))
    for mod in sorted(res):
        print("== %s%s" % (mod, " *stub" if mod in stubs else ""))
        for n, sz, raw in res[mod]:
            print("   %-50s 0x%-4X %s" % (n[:50], sz, raw[:48].hex()))
    print("objects compared %d, found identical in HD %d, not found %d, skipped (pointers/zero) %d" % (tot, found, tot - found, skipped))
main()
