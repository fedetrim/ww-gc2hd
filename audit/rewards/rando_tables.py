#!/usr/bin/env python3
"""Location -> vanilla item tables of the two randomizers, and their diff by location name.

Inputs:  LagoLunatic/wwrando clone: logic/item_locations.txt (GameCube)
         SuperDude88/TWWHD-Randomizer clone: logic/data/location_data.yaml (HD)
Output:  rando_tables.json in research/out/rewards/ ({"gc": {...}, "hd": {...}}); on stdout the names only
         one list has and the same-name locations whose original item differs.
Run:     python3 -I audit/rewards/rando_tables.py        (under a second)

Limit: both files are parsed with regular expressions written for their format at the commits the audit
used (wwrando 99281a3, TWWHD-Randomizer a66347a); a format change needs a look at gc_table()/hd_table().
"""
import re, sys, json, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auditenv  # noqa: E402

def gc_table():
    out = {}
    cur = None
    for raw in open(os.path.join(auditenv.WWRANDO, "logic/item_locations.txt"), encoding="utf-8"):
        line = raw.rstrip("\n")
        commented = line.startswith("#")
        body = line[1:] if commented else line
        if not body.strip():
            continue
        m = re.match(r"^([^\s#-][^:]*( - [^:]+)?):\s*(#.*)?$", body)
        if m and not body.startswith(" "):
            cur = {"name": m.group(1).strip(), "commented": commented, "item": None, "paths": [], "types": ""}
            out[cur["name"]] = cur
            continue
        if cur is None:
            continue
        b = body.strip()
        if b.startswith("Original item:"):
            cur["item"] = b.split(":", 1)[1].split("#")[0].strip()
        elif b.startswith("Types:"):
            cur["types"] = b.split(":", 1)[1].split("#")[0].strip()
        elif b.startswith("- "):
            cur["paths"].append(b[2:].strip())
    return out

def hd_table():
    out = {}
    cur = None
    sect = None
    for raw in open(os.path.join(auditenv.TWWHD_RANDO, "logic/data/location_data.yaml"), encoding="utf-8"):
        line = raw.rstrip("\n")
        if line.startswith("- Names:"):
            cur = {"name": None, "item": None, "type": None, "raw": []}
            sect = "names"
            continue
        if cur is None:
            continue
        cur["raw"].append(line)
        s = line.strip()
        if sect == "names" and s.startswith("English:"):
            cur["name"] = s.split(":", 1)[1].strip()
            out[cur["name"]] = cur
        if line.startswith("  ") and not line.startswith("    "):
            sect = s.split(":")[0]
            if s.startswith("Original Item:"):
                cur["item"] = s.split(":", 1)[1].split("#")[0].strip()
            if s.startswith("Type:"):
                cur["type"] = s.split(":", 1)[1].strip()
    return out

def norm_item(s):
    s = re.sub(r"\s+\d+$", "", s) if re.match(r"^(Piece of Heart|Heart Container|.* Rupee|Small Key|Joy Pendant|Skull Necklace|Boko Baba Seed|Golden Feather|Knight's Crest|Green Chu Jelly|Red Chu Jelly|Blue Chu Jelly|Empty Bottle|Progressive .*)( \d+)?$", s) else s
    s = s.replace("Wind Waker", "Wind Waker").replace("Hero's Sword", "Progressive Sword")
    return s

if __name__ == "__main__":
    g, h = gc_table(), hd_table()
    json.dump({"gc": g, "hd": h}, open(auditenv.out_file("rewards", "rando_tables.json"), "w"), indent=1)
    print("GC entries %d (commented-out %d), HD entries %d" % (len(g), sum(1 for v in g.values() if v["commented"]), len(h)))
    print("== names only in GC list")
    for n in sorted(set(g) - set(h)):
        print("  %s%s -> %s  %s" % ("#" if g[n]["commented"] else "", n, g[n]["item"], g[n]["paths"][:2]))
    print("== names only in HD list")
    for n in sorted(set(h) - set(g)):
        print("  %s -> %s [%s]" % (n, h[n]["item"], h[n]["type"]))
    print("== same name, different original item (after normalising numbered duplicates)")
    for n in sorted(set(g) & set(h)):
        a, b = g[n]["item"], h[n]["item"]
        if norm_item(a) != norm_item(b):
            print("  %s%s: GC %s | HD %s  %s" % ("#" if g[n]["commented"] else "", n, a, b, g[n]["paths"][:2]))
