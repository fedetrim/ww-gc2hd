#!/usr/bin/env python3
"""make_gci_pictures.py IN.gci FILE(1-3) COUNT OUT.gci

Writes a GameCube card file in which FILE legitimately holds its first COUNT picture blocks:
item_record.picture_num = COUNT and event register 0x89FF (erased-picture marks) cleared, in both save
copies, with the file checksum and the block checksum recomputed. Picture blocks and all other bytes are
kept as they are. Used for the Lenzo `rewards` run from a state that owns the pictures it shows
(docs/verification/npcs.md, addendum).

Inputs:  a .gci whose FILE is used and valid in both copies
Output:  OUT.gci (write it under research/out/, not into samples/); the old and new values on stdout.
Run:     python3 verify/npcs/make_gci_pictures.py \
             samples/gc/archive-org-memcard-251-us/extracted-gci/01-GZLE-gczelda.gci 1 3 \
             research/out/verify/npcs/lenzo-rewards-legit/input.gci
"""
import os, struct, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from wwsave import gc, layout
src, slot, count, out = sys.argv[1], int(sys.argv[2]) - 1, int(sys.argv[3]), sys.argv[4]
raw = bytearray(open(src, "rb").read())
card = gc.load(bytes(raw))
assert card.source == "gci" and all(ok and s[slot] for ok, s in card.copy_status())
for k in (1, 2):
    base = gc.DENTRY + k * gc.BLOCK
    o = base + 8 + slot * gc.GAMEDATA
    g = layout.Save(bytearray(raw[o:o + gc.SAVE_SIZE]))
    print("copy %d: picture_num %d -> %d, reg 0x89FF %d -> 0" % (k, g.u("item_record.picture_num"), count, g.event_reg(0x89FF)))
    g.set_u("item_record.picture_num", count)
    g.set_event_reg(0x89FF, 0)
    raw[o:o + gc.SAVE_SIZE] = bytes(g.data)
    struct.pack_into(">Q", raw, o + gc.SAVE_SIZE, gc.gamedata_checksum(bytes(g.data)))
    struct.pack_into(">I", raw, base + gc.BLOCK - 4, gc.block_checksum(bytes(raw[base:base + gc.BLOCK])))
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
open(out, "wb").write(raw)
new = gc.load(bytes(raw))
print("copy status:", new.copy_status(), "pictures per file:", [len(p) for p in new.pictures()])
