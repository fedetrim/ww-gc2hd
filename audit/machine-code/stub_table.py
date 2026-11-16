#!/usr/bin/env python3
"""Per-actor table for the GameCube stub actors: every save-accessor constant with its GameCube and HD call
counts (section 6 of docs/research/machine-code-audit.md).

Inputs:  gc_calls.json, hd_calls.json, stubs.json in research/out/machine-code/
Output:  a Markdown table on stdout.
Run:     python3 -I audit/machine-code/stub_table.py > research/out/machine-code/stub_table.md
"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare
G, H, bases, gw, hw = compare.load()
stubs = json.load(open(compare.auditenv.out_file("machine-code", "stubs.json")))
tot = lambda S: sum(len(l) for u, d in S.items() if u not in compare.SKIP_UNITS for l in d.values())
print("Totals (all units, excluding d_save/d_com_inf_game internals): GC %d accessor call sites in %d units, HD %d in %d units.\n" % (tot(G), len(G), tot(H), len(H)))
print("| actor | stub fns | accessor constants: `kind flag` GC count/HD count (bold = one side only) |")
print("|---|---|---|")
for path, (n, t) in sorted(stubs.items()):
    u = os.path.basename(path).rsplit(".", 1)[0]
    g, h = G.get(u, {}), H.get(u, {})
    for a_, b_ in ((g, h), (h, g)):
        for k in [k for k in a_ if k[0].startswith("?:")]:
            for tag in ("event", "tmp"):
                k2 = (tag + k[0][1:], k[1])
                if k2 in b_ and k not in b_:
                    a_.setdefault(k2, []).extend(a_.pop(k)); break
    cells = []
    for k in sorted(set(g) | set(h)):
        nm = k[0].replace("dSv_", "").replace("_c::", ".").replace("dComIfGs_", "").replace("event:", "ev.").replace("tmp:", "tmp.").replace("player_", "")
        s = "%s %s %d/%d" % (nm, k[1] or "-", len(g.get(k, [])), len(h.get(k, [])))
        cells.append("**" + s + "**" if (k in g) != (k in h) else s)
    print("| %s | %d/%d | %s |" % (u, n, t, "; ".join(cells) or "no save accessor calls on either side"))
