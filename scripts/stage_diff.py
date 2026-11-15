#!/usr/bin/env python3
"""Compare the stage data of the two games (outputs of gc_stage_dump.py and hd_stage_dump.py):
chests whose flag or content changed, actors added, removed or with changed parameters, and player spawn
points that differ.
usage: stage_diff.py GC.json HD.json"""
import collections
import json
import sys

G = json.load(open(sys.argv[1]))
H = json.load(open(sys.argv[2]))


def key(a):
    return (a["arc"], a["layer"], a["name"], tuple(a["pos"]))


print("== stages and save records")
for st in sorted(set(G) ^ set(H)):
    print("  %-8s only on the %s disc" % (st, "GameCube" if st in G else "HD"))
moved = [st for st in sorted(set(G) & set(H)) if G[st]["save_table"] != H[st]["save_table"]]
for st in moved:
    print("  %-8s save record %s on the GameCube, %s in HD" % (st, G[st]["save_table"], H[st]["save_table"]))
print("  %d stages on both discs; save record differs in %d" % (len(set(G) & set(H)), len(moved)))

print("== chests")
for st in sorted(set(G) & set(H)):
    g = collections.defaultdict(list)
    h = collections.defaultdict(list)
    for c in G[st]["chests"]:
        g[(c["arc"], tuple(c["pos"]))].append(c)
    for c in H[st]["chests"]:
        h[(c["arc"], tuple(c["pos"]))].append(c)
    for k in sorted(set(g) | set(h)):
        a = sorted((c["type"], c["open_flag"], c["appear_switch"], c["item"]) for c in g.get(k, []))
        b = sorted((c["type"], c["open_flag"], c["appear_switch"], c["item"]) for c in h.get(k, []))
        if a != b:
            print("  %-8s %-7s rec %-2s pos %s\n      GC (type, flag, switch, item) %s\n      HD %s" % (
                st, k[0], G[st]["save_table"], list(k[1]),
                [(t, f, s, "%02X" % i) for t, f, s, i in a], [(t, f, s, "%02X" % i) for t, f, s, i in b]))

print("== actors")
names = collections.Counter()
for st in sorted(set(G) & set(H)):
    g = collections.defaultdict(list)
    h = collections.defaultdict(list)
    for a in G[st]["actors"]:
        g[key(a)].append((a["params"], tuple(a["aux"])))
    for a in H[st]["actors"]:
        h[key(a)].append((a["params"], tuple(a["aux"])))
    for k in sorted(set(g) | set(h)):
        a, b = sorted(g.get(k, [])), sorted(h.get(k, []))
        if a == b:
            continue
        kind = "changed" if a and b else ("GC only" if a else "HD only")
        names[(kind, k[2])] += 1
        print("  %-7s %-8s %-7s %-5s %-8s pos %s  GC %s  HD %s" % (
            kind, st, k[0], k[1], k[2], list(k[3]),
            [p + " " + "/".join(x) for p, x in a], [p + " " + "/".join(x) for p, x in b]))
print("== player spawn points")
for st in sorted(set(G) & set(H)):
    g = collections.defaultdict(list)
    h = collections.defaultdict(list)
    for a in G[st]["spawns"]:
        g[(a["arc"], a["start_code"])].append((a["params"], tuple(a["aux"]), tuple(a["pos"])))
    for a in H[st]["spawns"]:
        h[(a["arc"], a["start_code"])].append((a["params"], tuple(a["aux"]), tuple(a["pos"])))
    for k in sorted(set(g) | set(h)):
        if sorted(g.get(k, [])) != sorted(h.get(k, [])):
            print("  %-8s %-7s spawn %-3d GC %s  HD %s" % (st, k[0], k[1], [x[0] for x in g.get(k, [])] or "-",
                                                        [x[0] for x in h.get(k, [])] or "-"))
print("== summary by actor name")
for (kind, name), n in sorted(names.items()):
    print("  %-8s %-10s %d" % (kind, name, n))
