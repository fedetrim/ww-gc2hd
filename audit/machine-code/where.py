#!/usr/bin/env python3
"""List the save-accessor call sites of one unit on both sides (helper).

Inputs:  gc_calls.json, hd_calls.json in research/out/machine-code/
Output:  text on stdout.
Run:     python3 -I audit/machine-code/where.py UNIT          e.g. d_a_npc_de1
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare
G, H, bases, gw, hw = compare.load()
u = sys.argv[1]
for nm, S in (("GC", G), ("HD", H)):
    for k, lst in sorted(S.get(u, {}).items()):
        for w in lst:
            print(nm, k[0], k[1], w)
