#!/usr/bin/env python3
"""Items 3-5, helper: print the entities of one stage in both games from the rewards audit's stage_all.json,
optionally only those whose actor name contains a substring.

Inputs:  research/out/rewards/stage_all.json (audit/rewards/stage_all.py)
Output:  text on stdout.
Run:     python3 -I audit/leftovers/i345_stage.py STAGE [NAME_SUBSTRING]      e.g. sea Search
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auditenv  # noqa: E402
d = json.load(open(auditenv.out_file("rewards", "stage_all.json")))
st = sys.argv[1]; sub = sys.argv[2] if len(sys.argv) > 2 else ""
for side in ("gc", "hd"):
    v = d[side].get(st)
    if v is None: print(side, "no stage"); continue
    if not sub and len(sys.argv) < 3:
        print(side, type(v), (list(v)[:20] if isinstance(v, dict) else v[:3]))
        for k, x in (v.items() if isinstance(v, dict) else []):
            print("  ", k, str(x)[:300])
        continue
    def walk(x, path):
        if isinstance(x, dict):
            if "name" in x and sub.lower() in str(x["name"]).lower(): print(side, path, x)
            for k, y in x.items(): walk(y, path + "/" + str(k))
        elif isinstance(x, list):
            for i, y in enumerate(x): walk(y, path)
    walk(v, st)
