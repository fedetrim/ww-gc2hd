#!/usr/bin/env python3
"""Hex-dump data symbols of a GameCube REL after relocation (helper for reading an NPC's tables).

Inputs:  GameCube disc image, zeldaret/tww config/GZLE01/rels/MODULE/{symbols,splits}.txt
Output:  text on stdout: symbol, section, size, address, bytes.
Run:     python3 -I audit/rewards/npc_gcsym.py MODULE SYMBOL_SUBSTRING [...]      e.g. d_a_npc_ho l_
"""
import json, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
sys.path.insert(0, auditenv.MACHINE_CODE)
import gc_extract as g, ppc
memref = {}
ol = g.load
def load():
    m, r = ol(); memref["m"] = m; memref["r"] = r; return m, r
g.load = load
ppc.scan_function = lambda *a, **k: None
jd = json.dump; json.dump = lambda *a, **k: None
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    g.main(os.devnull)
mem = memref["m"]; mod = sys.argv[1]
d, base, sec_addr, mid, _, _ = memref["r"][mod]
secn, _ = g.parse_splits(os.path.join(g.CFG, "rels", mod, "splits.txt"))
smap = dict(zip(secn, [a for a in sec_addr if a is not None]))
for n, sec, a, sz, t in g.parse_symbols(os.path.join(g.CFG, "rels", mod, "symbols.txt")):
    if t != "object" or sec not in smap: continue
    if any(p in n for p in sys.argv[2:]):
        ad = smap[sec] + a
        b, dd = mem.find(ad)
        if dd is None: print(n, sec, "no data"); continue
        raw = bytes(dd[ad - b:ad - b + sz])
        print("%s %s 0x%X @%08X: %s" % (n, sec, sz, ad, raw.hex()))
