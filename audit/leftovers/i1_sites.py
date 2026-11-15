#!/usr/bin/env python3
"""Item 1 (flags reached from differently named functions), step 1: for each (unit, accessor, flag) line of the
machine-code audit's funcdiff.txt, list all call sites of both games.

Inputs:  research/out/machine-code/funcdiff.txt (audit/machine-code/funcdiff.py), gc_calls.json and
         hd_calls.json in the same folder
Output:  text on stdout; i1_auto.py and i1_ctx.py read research/out/leftovers/i1_sites.txt.
Run:     python3 -I audit/leftovers/i1_sites.py > research/out/leftovers/i1_sites.txt
"""
import sys, os, re, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auditenv  # noqa: E402
sys.path.insert(0, auditenv.MACHINE_CODE)
import compare  # noqa: E402
G, H, bases, gw, hw = compare.load()
for line in open(auditenv.out_file("machine-code", "funcdiff.txt")):
    p = line.split()
    if len(p) < 3: continue
    u, acc, fl = p[0], p[1], p[2]
    k = (acc, fl)
    print("##", u, acc, fl)
    print("  GC:", " ; ".join(sorted(G[u][k])))
    print("  HD:", " ; ".join(sorted(H[u][k])))
