#!/usr/bin/env python3
"""Final table of the randomizer comparison. Stage-based locations are paired through the stage entity
(rando_pairs.json) and the item id is read from the stage data of each game, not from the randomizer label.
The remaining locations (given by code or events) are paired by name: a fixed alias list (ALIAS), then the
closest normalised name (ratio >= 0.8), printed for review.

Inputs:  rando_tables.json, rando_pairs.json, stage_all.json in research/out/rewards/
Output:  text on stdout; the audit kept it as rando_final.txt (243 pairs through the stage entity, 75 by
         name).
Run:     python3 -I audit/rewards/rando_final.py > research/out/rewards/rando_final.txt

Limit: the name pairing is a heuristic and the ALIAS list is tied to the location names at the commits
used; read the "name pairs" and the two "no partner" lists, do not trust the DIFF/same column alone.
"""
import json, os, re, sys, difflib, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
T = json.load(open(auditenv.out_file("rewards", "rando_tables.json")))
P = json.load(open(auditenv.out_file("rewards", "rando_pairs.json")))["pairs"]
gp = set(a for a, b, k in P); hp = set(b for a, b, k in P)
S = json.load(open(auditenv.out_file("rewards", "stage_all.json")))
def item_of(e):
    if e["layer"][:3] == "TRE":
        return int(e["aux"][2], 16) >> 8
    if e["name"] == "Salvage":
        return int(e["params"], 16) >> 4 & 0xFF
    return int(e["params"], 16) & 0xFF
def data_items(side, keys):
    out = set()
    for st, arc, lay, name, pos in keys:
        for e in S[side][st]["ents"]:
            if e["arc"] == arc and e["layer"][:3] == lay and e["name"] == name and e["pos"] == pos:
                out.add("%s:%02X" % (e["layer"], item_of(e)))
    return ",".join(sorted(out))
ALIAS = {"Dragon Roost Island - Baito Mail Game": "Dragon Roost Island - Rito Aerie - Mail Sorting",
 "Outset Island - Orca Hit 500 Times": "Outset Island - Orca - Hit 500 Times",
 "Spectacle Island - Barrel Shooting Second Prize": "Spectacle Island - Barrel Shooting - Second Prize",
 "Tingle Island - Ankle All Statues Reward": "Tingle Island - Ankle - Reward for All Tingle Statues",
 "Windfall Island - Battle Squid Second Prize": "Windfall Island - Battlesquid - Second Prize",
 "Windfall Island - Dampa Pig Minigame": "Windfall Island - Dampa's Piggy Sitting Minigame",
 "Windfall Island - Mrs. Marie 21 Joy Pendant": "Windfall Island - Mrs. Marie - Give 21 Joy Pendants",
 "Windfall Island - Mrs. Marie 40 Joy Pendant": "Windfall Island - Mrs. Marie - Give 40 Joy Pendants",
 "Windfall Island - Mrs. Marie 1 Joy Pendant": "Windfall Island - Mrs. Marie - Give 1 Joy Pendant",
 "Windfall Island - Auction 40 Rupee": "Windfall Island - 40 Rupee Auction", "Windfall Island - Auction 5 Rupee": "Windfall Island - 5 Rupee Auction",
 "Windfall Island - Auction 60 Rupee": "Windfall Island - 60 Rupee Auction", "Windfall Island - Auction 80 Rupee": "Windfall Island - 80 Rupee Auction",
 "Windfall Island - Cafe Postman Delivery": "Windfall Island - Cafe Bar - Postman",
 "Windfall Island - Kane Decorate Shop Guru": "Windfall Island - Kane - Place Shop Guru Statue on Gate",
 "Windfall Island - Mila Catch Thief": "Windfall Island - Mila - Follow the Thief",
 "Windfall Island - Potion Shop 15 Blue Chu": "Windfall Island - Chu Jelly Juice Shop - Give 15 Blue Chu Jelly",
 "Windfall Island - Potion Shop 15 Green Chu": "Windfall Island - Chu Jelly Juice Shop - Give 15 Green Chu Jelly",
 "Windfall Island - Sam Decorate Island": "Windfall Island - Sam - Decorate the Town"}

def base(s):
    s = re.sub(r"\s+\d+$", "", s) if re.match(r"^(Piece of Heart|Heart Container|Small Key|Empty Bottle)", s) else s
    s = s.lower().replace("'", "").replace("-", " ").replace("(pickup)", "")
    s = re.sub(r"\s+", " ", s).strip()
    al = {"heros bow": "progressive bow", "picto box": "progressive picto box", "deluxe picto box": "progressive picto box",
          "heros sword": "progressive sword", "heros shield": "progressive shield", "mirror shield": "progressive shield",
          "60 bomb bomb bag": "progressive bomb bag", "99 bomb bomb bag": "progressive bomb bag",
          "60 arrow quiver": "progressive quiver", "99 arrow quiver": "progressive quiver",
          "1000 rupee wallet": "progressive wallet", "5000 rupee wallet": "progressive wallet",
          "magic meter upgrade": "progressive magic meter", "master sword (powerless)": "master sword powerless",
          "fire and ice arrows": "fire ice arrows", "light arrow": "light arrows", "fill up coupon": "fill up coupon",
          "500 rupees, reward for finding all tingle statues": "rainbow rupee", "bombs": "bombs",
          "wind waker": "wind waker", "tingle tuner": "TINGLE TUNER (GC)", "tingle bottle": "TINGLE BOTTLE (HD)"}
    return al.get(s, s)

def norm(n):
    n = n.lower().replace("&", "and").replace("'", "").replace(".", "")
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    drop = {"the", "chest", "a", "to", "of", "on", "in", "at", "give", "reward", "for", "item", "prize", "island", "isle", "isles",
            "ship", "shop", "special", "beedles", "beedle", "jail", "lenzos", "house", "windfall", "place", "decorate", "rito", "aerie"}
    return " ".join(w for w in n.split() if w not in drop)

g = {n: v for n, v in T["gc"].items() if n not in gp}
h = {n: v for n, v in T["hd"].items() if n not in hp}
hn = {norm(n): n for n in h}
pairs2, used, gused = [], set(), set()
for b, a in ALIAS.items():
    assert a in g and b in h, (a, b)
    pairs2.append((a, b)); used.add(b); gused.add(a)
cand = []
for n in g:
    if g[n]["commented"]:
        continue
    for x in hn:
        cand.append((difflib.SequenceMatcher(None, norm(n), x).ratio(), n, hn[x]))
for r, a, b in sorted(cand, reverse=True):
    if r >= 0.8 and a not in gused and b not in used:
        pairs2.append((a, b)); used.add(b); gused.add(a)
pairs2.sort()
print("== stage-entity pairs: %d ; randomizer labels differ (after normalising progressive/duplicate names):" % len(P))
nd = 0
for a, b, k in P:
    gi, hi = data_items("gc", k), data_items("hd", k)
    lab = base(T["gc"][a]["item"]) != base(T["hd"][b]["item"])
    if gi != hi:
        nd += 1
    if lab or gi != hi:
        print("  %s GC %-56s %-18s data %-16s | HD %-56s %-18s data %s" % ("DATA-DIFF " if gi != hi else "label-only", a, T["gc"][a]["item"], gi, b, T["hd"][b]["item"], hi))
print("  pairs whose stage data item id differs: %d" % nd)
print("== name pairs (code/event locations): %d" % len(pairs2))
for a, b in pairs2:
    x, y = g[a]["item"], h[b]["item"]
    print("  %s GC %s%-66s %-22s | HD %-55s %s" % ("DIFF" if base(x) != base(y) else "same", "#" if g[a]["commented"] else " ", a, x, b, y))
print("== GC entries with no HD partner")
for n in sorted(g):
    if n not in [a for a, b in pairs2]:
        print("  %s%s -> %s %s" % ("#" if g[n]["commented"] else "", n, g[n]["item"], g[n]["paths"][:3]))
print("== HD entries with no GC partner")
for n in sorted(h):
    if n not in used:
        print("  %s -> %s [%s]" % (n, h[n]["item"], h[n]["type"]))
