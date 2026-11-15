#!/usr/bin/env python3
"""Function-level comparison: (unit, accessor, flag) keys that exist in both games but are reached from
differently named functions, i.e. a setter or reader that may have moved to another step.

Inputs:  gc_calls.json, hd_calls.json (through compare.py)
Output:  one line per key on stdout, then the count. The audit kept it as funcdiff.txt (99 keys);
         audit/leftovers/i1_sites.py reads research/out/machine-code/funcdiff.txt.
Run:     python3 -I audit/machine-code/funcdiff.py > research/out/machine-code/funcdiff.txt

Limit: functions are compared by name only (GameCube mangled name vs HD marker name), so a renamed or
inlined function is listed too; each line has to be read against the sources (audit/leftovers/i1_*.py).
"""
import sys, os, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare
G, H, bases, gw, hw = compare.load()

def gname(w):
    n = w.split("@")[0]
    n = re.sub(r"__(Q\d)?\d+.*$", "", n)
    n = re.sub(r"__F.*$", "", n)
    return n.lower().lstrip("_")

def hname(w):
    return w.split("@")[0].split("::")[-1].lower().lstrip("_")

n = 0
for u in sorted(set(G) & set(H)):
    if u in compare.SKIP_UNITS: continue
    for k in sorted(set(G[u]) & set(H[u])):
        if "?" in k[1]: continue
        gf = collections.Counter(gname(w) for w in G[u][k]); hf = collections.Counter(hname(w) for w in H[u][k])
        if set(gf) != set(hf):
            go = sorted(set(gf) - set(hf)); ho = sorted(set(hf) - set(gf))
            print("%-22s %-28s %-8s GC-only-in: %s | HD-only-in: %s" % (u, k[0], k[1], ",".join(go), ",".join(ho)))
            n += 1
print(n)
