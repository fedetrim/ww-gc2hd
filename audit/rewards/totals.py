#!/usr/bin/env python3
"""Totals per item: count, per game, the stage-data sources of each item id (chests, chart salvage, other
salvage, free-standing items, pig dig spots, race items, boss items, drops with a fixed item id) in the
stages both games have. Prints the ids whose source sets differ and the counts for the unique collectibles
(Pieces of Heart, Heart Containers, charts, Triforce shards, bottles, Tingle statues, Hero's Charm).
Duplicates are folded: a chest is (stage, save flag, item), a chart salvage is (chart number, item) - the
four random positions of one point count once -, a free item is (stage, room, item, pickup flag).

Inputs:  stage_all.json in research/out/rewards/
         zeldaret/tww clone: include/d/d_item_data.h (item names)
         LagoLunatic/wwrando clone: data/actor_info.txt (actor name -> class)
Output:  text on stdout; the audit kept it as totals.txt.
Run:     python3 -I audit/rewards/totals.py > research/out/rewards/totals.txt

Limit: stage data only. Items given by code (NPCs, minigames, shops) are not counted here.
"""
import json, os, re, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
D = json.load(open(auditenv.out_file("rewards", "stage_all.json")))
names = {}
for line in open(os.path.join(auditenv.TWW, "include/d/d_item_data.h"), errors="replace"):
    m = re.match(r"\s*/\* 0x([0-9A-F]{2}) \*/ dItemNo_(\w+?)_e", line)
    if m: names.setdefault(int(m.group(1), 16), m.group(2))
cls = {}; cur = None
for line in open(os.path.join(auditenv.WWRANDO, "data/actor_info.txt")):
    m = re.match(r"^(\S+):\s*$", line)
    if m: cur = m.group(1)
    m = re.match(r"^\s+Class Name: (\S+)", line)
    if m and cur: cls[cur] = m.group(1)
DROP = {"d_a_tsubo": ("p", 0x3F), "d_a_stone": ("p", 0x3F), "d_a_stone2": ("p", 0x3F), "d_a_obj_movebox": ("p", 0x3F),
        "d_a_obj_barrel2": ("p", 0x3F), "d_a_acorn_leaf": ("p", 0x3F), "d_a_obj_homen": ("p", 0x3F000),
        "d_a_switem": ("p", 0x3F00), "d_a_obj_bemos": ("z", 0x3F)}
def field(v, mask):
    s = (mask & -mask).bit_length() - 1
    return (v & mask) >> s
common = sorted(set(D["gc"]) & set(D["hd"]))
def collect(side):
    src = collections.defaultdict(set)   # item id -> set of source descriptors
    for st in common:
        rec = D[side][st]["save_table"]
        for e in D[side][st]["ents"]:
            p = int(e["params"], 16); z = int(e["aux"][2], 16); c = cls.get(e["name"])
            if e["layer"][:3] == "TRE":
                t = p & 0x7F
                src[z >> 8].add(("chest", st, "rec%d" % (1 if t in (7, 8) else rec), "tboxbit%d" % (p >> 7 & 0x1F)))
            elif c == "d_a_salvage":
                kind, sv, room, item = p >> 28, p >> 20 & 0xFF, p >> 12 & 0xFF, p >> 4 & 0xFF
                if kind == 0:
                    src[item].add(("chart salvage", "collect map %d" % sv, "sea " + e["arc"]))
                else:
                    src[item].add(("salvage kind %d" % kind, st, e["arc"], "save no %d" % sv, "sw%02X" % (z & 0xFF)))
            elif c == "d_a_item":
                src[p & 0xFF].add(("free item", st, e["arc"], "itembit %02X" % (p >> 8 & 0xFF), tuple(e["pos"])))
            elif c == "d_a_tag_kb_item":
                src[p & 0xFF].add(("pig dig spot", st, e["arc"], "itembit %02X" % (p >> 8 & 0xFF)))
            elif c == "d_a_race_item":
                src[p & 0xFF].add(("race item", st, e["arc"], tuple(e["pos"])))
            elif c == "d_a_boss_item":
                src[8].add(("boss item", st, e["arc"], "stage id %d" % (p & 0xFF)))
            elif c in DROP:
                w, mask = DROP[c]
                v = field(p if w == "p" else z, mask)
                if v < 0x20:
                    src[v].add(("fixed drop " + c, st, e["arc"], e["layer"], e["params"], tuple(e["pos"])))
    return src
g, h = collect("gc"), collect("hd")
print("item id | name | GC sources | HD sources   (stage data only; ids whose source sets differ)")
for i in sorted(set(g) | set(h)):
    if g.get(i, set()) != h.get(i, set()):
        print("0x%02X %-18s GC %3d  HD %3d" % (i, names.get(i, "?"), len(g.get(i, ())), len(h.get(i, ()))))
        for s in sorted(g.get(i, set()) - h.get(i, set())): print("      GC only:", s)
        for s in sorted(h.get(i, set()) - g.get(i, set())): print("      HD only:", s)
print()
print("counts of stage-data sources for unique collectibles (GC / HD):")
def cnt(ids):
    return sum(len(g.get(i, ())) for i in ids), sum(len(h.get(i, ())) for i in ids)
print("  Piece of Heart (0x07): %d / %d" % cnt([7]))
print("  Heart Container (0x08): %d / %d" % cnt([8]))
print("  collect maps 1..8 (0xFE..0xF7): %d / %d" % cnt(range(0xF7, 0xFF)))
print("  collect maps 9..49 (0xF6..0xCE): %d / %d" % cnt(range(0xCE, 0xF7)))
print("  collect maps 50..61 (0xCD..0xC2): %d / %d" % cnt(range(0xC2, 0xCE)))
print("  Triforce shards (0x61..0x68): %d / %d" % cnt(range(0x61, 0x69)))
print("  Empty Bottle (0x50): %d / %d" % cnt([0x50]))
print("  Tingle statues (0xA3..0xA7): %d / %d" % cnt(range(0xA3, 0xA8)))
print("  Hero's Charm (0x43): %d / %d" % cnt([0x43]))
for side, s in (("GC", g), ("HD", h)):
    print(side, "collect-map items in stage data, by map number: ", end="")
    out = []
    for n in range(1, 62):
        i = 0xFF - n
        if i in s:
            out.append("%d:%s" % (n, "+".join(sorted(set(x[0][:5] for x in s[i])))))
    print(" ".join(out))
    cs = collections.defaultdict(set)
    for i, v in s.items():
        for x in v:
            if x[0] == "chart salvage": cs[int(x[1].split()[-1])].add(i)
    print(side, "chart salvage points (collect map number -> item id): ", " ".join("%d:%s" % (n, "/".join("%02X" % i for i in sorted(v))) for n, v in sorted(cs.items())))
    print(side, "PoH sources:", collections.Counter(x[0] for x in s[7]))
    oth = collections.Counter((x[0], "%02X" % i) for i, v in s.items() for x in v if x[0].startswith("salvage"))
    print(side, "other salvage (kind, item): ", dict(sorted(oth.items())))
    fd = collections.Counter("%02X" % i for i, v in s.items() for x in v if x[0].startswith("fixed drop"))
    print(side, "fixed drops by item id:", dict(sorted(fd.items())))
