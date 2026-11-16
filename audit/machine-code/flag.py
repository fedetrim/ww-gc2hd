#!/usr/bin/env python3
"""All uses of one flag value on both sides (helper).

Inputs:  gc_calls.json, hd_calls.json in research/out/machine-code/
Output:  text on stdout.
Run:     python3 -I audit/machine-code/flag.py HEX [ACCESSOR_SUBSTRING]      e.g. 3940, or 2A isSwitch
         (the accessor substring defaults to `Event`)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare
G, H, bases, gw, hw = compare.load()
v = sys.argv[1].upper(); sub = sys.argv[2] if len(sys.argv) > 2 else "Event"
for nm, S in (("GC", G), ("HD", H)):
    for u, d in sorted(S.items()):
        for k, lst in sorted(d.items()):
            if k[1] == v and sub in k[0]:
                print(nm, u, k[0], k[1], len(lst), sorted(set(w.split("@")[0] for w in lst))[:5])
