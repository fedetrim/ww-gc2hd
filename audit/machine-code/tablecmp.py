#!/usr/bin/env python3
"""Find one GameCube data object, by symbol name, byte for byte in HD's .rodata/.data.

Inputs:  GameCube disc image, zeldaret/tww config (symbols and splits), cking.rpx
Output:  text on stdout: where the bytes were found in HD, or the GameCube bytes when they were not.
Run:     python3 -I audit/machine-code/tablecmp.py MODULE SYMBOL_SUBSTRING [...] [-v]
         MODULE is a REL name (d_a_obj_toripost) or `dol`.
"""
import json, os, re, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gc_extract as g, hd_extract as h, ppc

def main():
    mod, pats = sys.argv[1], sys.argv[2:]
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
    hd = [(s["name"], s["addr"], s["data"]) for s in secs if s["name"] in (".rodata", ".data")]
    if mod == "dol":
        syms = [(n, a, sz) for n, sec, a, sz, t in g.parse_symbols(os.path.join(g.CFG, "symbols.txt")) if t == "object"]
    else:
        d, base, sec_addr, mid, _, _ = memref["r"][mod]
        secn, _ = g.parse_splits(os.path.join(g.CFG, "rels", mod, "splits.txt"))
        smap = dict(zip(secn, [a for a in sec_addr if a is not None]))
        syms = [(n, smap[sec] + a, sz) for n, sec, a, sz, t in g.parse_symbols(os.path.join(g.CFG, "rels", mod, "symbols.txt")) if t == "object" and sec in smap]
    for n, a, sz in syms:
        if not any(p in n for p in pats) or not sz: continue
        b, dd = mem.find(a)
        if dd is None: print(n, "bss"); continue
        raw = bytes(dd[a - b:a - b + sz])
        hits = []
        for name, addr, data in hd:
            i = data.find(raw)
            while i >= 0 and len(hits) < 4:
                hits.append("%s:%08X" % (name, addr + i)); i = data.find(raw, i + 1)
        print("%s size 0x%X: %s" % (n, sz, "FOUND in HD at " + ", ".join(hits) if hits else "NOT found in HD"))
        if not hits or "-v" in sys.argv:
            print("   GC bytes:", raw.hex())
main()
