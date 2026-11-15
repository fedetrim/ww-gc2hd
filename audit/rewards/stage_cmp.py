#!/usr/bin/env python3
"""Full diff of stage_all.json: every entity of every layer and chunk type in the stages both games have,
matched by (archive, chunk, actor name, position) and compared on parameters, aux words and extra bytes.
Lists one-sided stages and archives, every changed or one-sided entity, and totals per actor name.

Inputs:  stage_all.json in research/out/rewards/ (stage_all.py), or the path given as argument
Output:  text on stdout; the audit kept it as stage_cmp.txt (18,904 GameCube and 18,824 HD entries,
         18,785 identical).
Run:     python3 -I audit/rewards/stage_cmp.py [stage_all.json] > research/out/rewards/stage_cmp.txt
"""
import json, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auditenv  # noqa: E402
D = json.load(open(sys.argv[1] if len(sys.argv) > 1 else auditenv.out_file("rewards", "stage_all.json")))
G, H = D["gc"], D["hd"]
print("GC-only stages:", sorted(set(G) - set(H)))
print("HD-only stages:", sorted(set(H) - set(G)))
tot = collections.Counter()
names = collections.Counter()
for st in sorted(set(G) & set(H)):
    if G[st]["save_table"] != H[st]["save_table"]:
        print("save_table differs", st, G[st]["save_table"], H[st]["save_table"])
    ga = set((e["arc"], e["file"]) for e in G[st]["ents"]); ha = set((e["arc"], e["file"]) for e in H[st]["ents"])
    if set(a for a, _ in ga) != set(a for a, _ in ha):
        print("archives differ", st, "GC-only", sorted(set(a for a, _ in ga) - set(a for a, _ in ha)), "HD-only", sorted(set(a for a, _ in ha) - set(a for a, _ in ga)))
    g = collections.defaultdict(list); h = collections.defaultdict(list)
    for e in G[st]["ents"]:
        g[(e["arc"], e["layer"], e["name"], tuple(e["pos"]))].append((e["params"], tuple(e["aux"]), e["extra"]))
    for e in H[st]["ents"]:
        h[(e["arc"], e["layer"], e["name"], tuple(e["pos"]))].append((e["params"], tuple(e["aux"]), e["extra"]))
    for k in sorted(set(g) | set(h)):
        a, b = sorted(g.get(k, [])), sorted(h.get(k, []))
        tot["keys"] += 1; tot["gc_inst"] += len(a); tot["hd_inst"] += len(b)
        if a == b:
            tot["identical_inst"] += len(a)
            continue
        kind = "changed" if a and b else ("GC only" if a else "HD only")
        names[(kind, k[1][:3], k[2])] += max(len(a), len(b))
        print("  %-7s %-8s %-7s %-5s %-8s pos %s  GC %s  HD %s" % (kind, st, k[0], k[1], k[2], list(k[3]),
              [p + " " + "/".join(x) + " " + z for p, x, z in a], [p + " " + "/".join(x) + " " + z for p, x, z in b]))
print("totals (common stages):", dict(tot))
for (kind, lay, name), n in sorted(names.items()):
    print("  %-8s %-4s %-10s %d" % (kind, lay, name, n))
