#!/usr/bin/env python3
"""Resolve the randomizer locations of both games to stage entities and pair them by (stage, archive, chunk
type, actor name, position). Prints every pair whose vanilla item label differs and every entry left
unpaired (stage-based and not).

Inputs:  rando_tables.json (rando_tables.py) and stage_all.json (stage_all.py) in research/out/rewards/
Output:  rando_pairs.json in research/out/rewards/; text on stdout (the audit kept it as rando_match.txt).
Run:     python3 -I audit/rewards/rando_match.py > research/out/rewards/rando_match.txt
"""
import json, os, re, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
T = json.load(open(auditenv.out_file("rewards", "rando_tables.json")))
S = json.load(open(auditenv.out_file("rewards", "stage_all.json")))

def ent_key(st, e):
    return (st, e["arc"], e["layer"][:3], e["name"], tuple(e["pos"]))

gidx = {}
for st, v in S["gc"].items():
    for e in v["ents"]:
        gidx[(st, e["arc"], e["layer"], e["idx"])] = e
hents = collections.defaultdict(list)
for st, v in S["hd"].items():
    for e in v["ents"]:
        hents[(st, e["arc"])].append(e)

def gc_resolve(p):
    m = re.match(r"^(\w+)/(\w+)\.arc/(?:Layer(\w)/)?(Chest|ScalableObject|Actor)([0-9A-F]{3})$", p)
    if not m:
        return None
    st, arc, lay, kind, idx = m.groups()
    base = {"Chest": "TRE", "ScalableObject": "SCO", "Actor": "ACT"}[kind]
    tag = base + (lay.lower() if lay and lay in "AB" else lay) if lay else base + {"TRE": "S", "SCO": "B", "ACT": "R"}[base]
    e = gidx.get((st, arc, tag, int(idx, 16)))
    return (st, e) if e else ("?" + p, None)

def hd_resolve(v):
    out = []
    raw = v["raw"]
    cur = None
    for line in raw:
        s = line.strip()
        m = re.search(r"([A-Za-z0-9_]+)_(Room\d+|Stage)\.szs@.*(room\.dzr|stage\.dzs)", s)
        if s.startswith("Path:") or (m and s.endswith(":")):
            cur = (m.group(1), m.group(2)) if m else None
            continue
        if s.startswith("code/") or s.startswith("Offsets:") and False:
            cur = None
        m2 = re.match(r"^- (0x[0-9A-Fa-f]+)$", s)
        if m2 and cur:
            off = int(m2.group(1), 16)
            hit = [e for e in hents[cur] if e["off"] <= off < e["off"] + (0x24 if e["layer"][:3] in ("SCO", "TGS", "TGD", "DOO") else 0x20)]
            out.append((cur[0], hit[0]) if hit else ("?%s@%X" % (cur, off), None))
    return out

gmap = collections.defaultdict(set)   # entity key -> GC location names
for n, v in T["gc"].items():
    for p in v["paths"]:
        r = gc_resolve(p)
        if r and r[1]:
            gmap[ent_key(*r)].add(n)
        elif r:
            print("GC unresolved path", n, p)
hmap = collections.defaultdict(set)
for n, v in T["hd"].items():
    for r in hd_resolve(v):
        if r[1]:
            hmap[ent_key(*r)].add(n)
        else:
            print("HD unresolved offset", n, r[0])

pairs = collections.defaultdict(set)
for k in set(gmap) & set(hmap):
    for a in gmap[k]:
        for b in hmap[k]:
            pairs[(a, b)].add(k)
gp = set(a for a, b in pairs); hp = set(b for a, b in pairs)
def base(s):
    return re.sub(r"\s+\d+$", "", s)
print("== paired by stage entity: %d pairs (%d GC names, %d HD names)" % (len(pairs), len(gp), len(hp)))
print("== paired, vanilla item differs")
for (a, b), ks in sorted(pairs.items()):
    ga, hb = T["gc"][a]["item"], T["hd"][b]["item"]
    if base(ga) != base(hb):
        k = sorted(ks)[0]
        print("  GC %-55s %-22s | HD %-55s %-22s | %s %s %s" % (a, ga, b, hb, k[0], k[1], k[3]))
print("== GC entries with stage paths but no HD partner")
for n, v in sorted(T["gc"].items()):
    if n not in gp and any(gc_resolve(p) for p in v["paths"]):
        print("  %s%s -> %s %s" % ("#" if v["commented"] else "", n, v["item"], v["paths"]))
print("== HD stage-type entries with no GC partner")
for n, v in sorted(T["hd"].items()):
    if n not in hp and v["type"] in ("Chest", "SCOB", "Actor", "Boss"):
        print("  %s -> %s [%s]" % (n, v["item"], v["type"]))
json.dump({"pairs": sorted([a, b, sorted(map(list, ks))] for (a, b), ks in pairs.items())}, open(auditenv.out_file("rewards", "rando_pairs.json"), "w"))
print("== not stage-based: GC")
for n, v in sorted(T["gc"].items()):
    if n not in gp and not any(gc_resolve(p) for p in v["paths"]):
        print("  %s%s -> %s %s" % ("#" if v["commented"] else "", n, v["item"], v["paths"]))
print("== not stage-based: HD")
for n, v in sorted(T["hd"].items()):
    if n not in hp and v["type"] not in ("Chest", "SCOB", "Actor", "Boss"):
        print("  %s -> %s [%s]" % (n, v["item"], v["type"]))
