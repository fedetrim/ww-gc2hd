#!/usr/bin/env python3
"""Statistical check: after reaching the same milestone, do converted GameCube saves and real HD saves
differ systematically in any bit of the save block?  Prints bits that (almost) all saves of one side
have and no save of the other side has.  usage: compare_with_hd.py [--raw] (raw = unconverted GameCube)"""
import glob
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from wwsave import convert as conv, gc, hd, layout  # noqa: E402

RAW = "--raw" in sys.argv
ANCHORS = {
    "sword": lambda s: s.raw("collect.collect")[0] & 1,
    "Wind Waker": lambda s: s.u("item.slot02") == 0x22,
    "sail": lambda s: s.u("item.slot01") in (0x78, 0x77),
    "DRC boss": lambda s: s.u("memory03.dungeon_item") & 8,
    "FW boss": lambda s: s.u("memory04.dungeon_item") & 8,
    "TotG boss": lambda s: s.u("memory05.dungeon_item") & 8,
    "Master Sword": lambda s: s.raw("collect.collect")[0] & 2,
    "ET boss": lambda s: s.u("memory06.dungeon_item") & 8,
    "WT boss": lambda s: s.u("memory07.dungeon_item") & 8,
    "8 shards": lambda s: s.u("collect.triforce") == 0xFF,
}
# fields that legitimately vary per player or are covered by other checks
SKIP = ("status_b", "status_c", "info.", "priest", "return_place", "status_a", "get_bag_item._unk",
        "item_record", "bag_item", "item_max", "config.ruby", "config.att", "config.vib", "item.slot",
        "map.fmap", "map.arrive", "ocean")


def field_at(off):
    for name, (o, size) in layout.FIELDS.items():
        if o <= off < o + size:
            return name, off - o


def load():
    seen, H, G = set(), [], []
    for f in sorted(glob.glob(os.path.join(ROOT, "samples/hd/**/cking.sav"), recursive=True)):
        raw = open(f, "rb").read()
        if len(raw) != hd.FILE_SIZE or "/rejected/" in f:
            continue
        for s in hd.HdFile.parse(raw, strict=False).slots:
            k = hashlib.md5(bytes(s)).hexdigest()
            if k not in seen and s.u("info.save_count"):
                seen.add(k)
                H.append(s)
    for f in sorted(glob.glob(os.path.join(ROOT, "samples/gc/**/*.gci"), recursive=True)):
        if "Hacked_File" in f or "/rejected/" in f:
            continue
        # every region on purpose: the save block is the same and the statistics need the numbers
        card = gc.load(open(f, "rb").read())
        slots = card.slots() if RAW else conv.convert(card, conv.Options.all("steps"))[0].slots
        for g, s in zip(card.slots(), slots):
            if g is None or g.is_new():
                continue
            k = hashlib.md5(bytes(s)).hexdigest()
            if k not in seen:
                seen.add(k)
                G.append(s)
    return H, G


def one_sided(A, B, label):
    found = {}
    for anchor, fn in ANCHORS.items():
        a = [s for s in A if fn(s)]
        b = [s for s in B if fn(s)]
        if len(a) < 4 or len(b) < 5:
            continue
        for off in range(layout.SAVE_SIZE):
            name, rel = field_at(off)
            if name.startswith(SKIP):
                continue
            for bit in range(8):
                na = sum(s.data[off] >> bit & 1 for s in a)
                if na >= 0.9 * len(a) and not any(s.data[off] >> bit & 1 for s in b):
                    found.setdefault((name, rel, 1 << bit), "%s: %d/%d vs 0/%d" % (anchor, na, len(a), len(b)))
    print("%s (%d):" % (label, len(found)))
    for (name, rel, mask), why in sorted(found.items()):
        print("  %-24s +%02x mask %02x   after %s" % (name, rel, mask, why))


H, G = load()
print("%d real HD saves, %d %s GameCube saves" % (len(H), len(G), "raw" if RAW else "converted"))
one_sided(H, G, "set in (nearly) all HD saves, in no GameCube save")
one_sided(G, H, "set in (nearly) all GameCube saves, in no HD save")
