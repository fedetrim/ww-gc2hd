#!/usr/bin/env python3
"""Bookkeeping for the stage comparison: classify every stage entity by actor class (wwrando
data/actor_info.txt) and by the kind of save-relevant parameter the class has (wwrando
data/actor_parameters.txt: fields naming an item id, an item pickup flag, a chest flag, a switch, ...). For
the stages both games have, counts the instances and how many are not byte-identical (parameters, aux words,
position, scale) in the other game.

Inputs:  stage_all.json in research/out/rewards/
         LagoLunatic/wwrando clone: data/actor_info.txt, data/actor_parameters.txt
Output:  text on stdout; the audit kept it as stage_types.txt.
Run:     python3 -I audit/rewards/stage_types.py > research/out/rewards/stage_types.txt

Limit: the class and parameter names are the GameCube randomizer's; they are applied to HD entities by actor
name. Classes wwrando does not describe are listed at the end and are compared byte-wise all the same.
"""
import json, os, re, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
D = json.load(open(auditenv.out_file("rewards", "stage_all.json")))
cls = {}
cur = None
for line in open(os.path.join(auditenv.WWRANDO, "data/actor_info.txt")):
    m = re.match(r"^(\S+):\s*$", line)
    if m:
        cur = m.group(1)
    m = re.match(r"^\s+Class Name: (\S+)", line)
    if m and cur:
        cls[cur] = m.group(1)
fields = collections.defaultdict(list)
cur = None
for line in open(os.path.join(auditenv.WWRANDO, "data/actor_parameters.txt")):
    m = re.match(r"^(d_a_\w+):", line)
    if m:
        cur = m.group(1); continue
    m = re.match(r"^  (\w+):\s*$", line)
    if m and cur:
        fields[cur].append(m.group(1))
def kind(c):
    fs = fields.get(c, [])
    k = set()
    for f in fs:
        if "item_id" in f or f.startswith("item") and "flag" not in f or "dropped_item" in f or "item_drop" in f: k.add("item")
        if "pickup_flag" in f or "item_flag" in f: k.add("itemflag")
        if "chest" in f or "open_flag" in f: k.add("chestflag")
        if "switch" in f: k.add("switch")
        if "event" in f and ("bit" in f or "flag" in f or "reg" in f): k.add("eventbit")
        if "salvage" in f or "chart" in f: k.add("salvage")
    return k
common = sorted(set(D["gc"]) & set(D["hd"]))
def ms(side):
    c = collections.Counter()
    for st in common:
        for e in D[side][st]["ents"]:
            c[(st, e["arc"], e["layer"], e["name"], e["params"], tuple(e["aux"]), tuple(e["pos"]), e["extra"])] += 1
    return c
g, h = ms("gc"), ms("hd")
stat = collections.defaultdict(lambda: [0, 0, 0, 0])   # gc, hd, gc-not-in-hd, hd-not-in-gc
for k, n in g.items():
    c = "TRES chest (d_a_tbox)" if k[2][:3] == "TRE" else cls.get(k[3], "?" + k[3])
    stat[c][0] += n; stat[c][2] += max(0, n - h.get(k, 0))
for k, n in h.items():
    c = "TRES chest (d_a_tbox)" if k[2][:3] == "TRE" else cls.get(k[3], "?" + k[3])
    stat[c][1] += n; stat[c][3] += max(0, n - g.get(k, 0))
tot = [sum(v[i] for v in stat.values()) for i in range(4)]
print("all entities in the %d common stages: GC %d, HD %d; GC instances without identical HD instance %d; HD without GC %d" % (len(common), *tot))
print("classes: %d" % len(stat))
groups = collections.defaultdict(lambda: [0, 0, 0, 0, 0])
print("%-28s %-34s %6s %6s %8s %8s" % ("class", "save-relevant parameter kinds", "GC", "HD", "GC-only", "HD-only"))
for c in sorted(stat):
    k = kind(c) if not c.startswith("TRES") else {"item", "chestflag", "switch"}
    v = stat[c]
    for x in (k or {"none"}):
        gr = groups[x]; gr[4] += 1
        for i in range(4): gr[i] += v[i]
    if k & {"item", "itemflag", "chestflag", "salvage", "eventbit"} or v[2] or v[3]:
        print("%-28s %-34s %6d %6d %8d %8d" % (c, ",".join(sorted(k)) or "-", *v))
print("totals by parameter kind (a class can be in several):")
for x, v in sorted(groups.items()):
    print("  %-10s classes %3d  GC %6d  HD %6d  GC-only %4d  HD-only %4d" % (x, v[4], *v[:4]))
print("classes with no parameter description in wwrando (compared byte-wise anyway):", sorted(c for c in stat if c.startswith("?"))[:80])
