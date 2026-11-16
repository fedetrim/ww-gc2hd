#!/usr/bin/env python3
"""Shops, part 5: byte comparison of daShopItem_c::mData and mModelType, the street vendor tables of
d_a_npc_roten (l_save_dat, l_item_dat, l_get_item_no), and a search of both binaries for the item array of
the rat shop (d_a_npc_nz itemArr1) and its message table.

Inputs:  GameCube disc image, zeldaret/tww config, cking.rpx
Output:  text on stdout (IDENTICAL / DIFFERENT per table).
Run:     python3 -I audit/rewards/shops_tables3.py

Limit: every address in this script is a constant of the two builds compared (GameCube USA GZLE01 and HD
USA v0); nothing is looked up by name on the HD side. Another build needs the addresses found again.
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shops_lib import *
mem, names, funcs, rel24 = load_gc(); hd = HD()
rn = {n: a for a, n in names.items()}
def cmp(title, ga, ha, n):
    a, b = gb(mem, ga, n), hd.b(ha, n)
    print("%-40s GC %08X HD %08X size 0x%X %s" % (title, ga, ha, n, "IDENTICAL" if a == b else "DIFFERENT"))
    if a != b:
        for i in range(0, n):
            if a[i] != b[i]: print("    first diff at +0x%X: GC %s HD %s" % (i, a[i:i+16].hex(), b[i:i+16].hex())); break
    return a, b
cmp("daShopItem_c::mData", rn["mData__12daShopItem_c"], 0x1003A930, 0x1FE0)
cmp("daShopItem_c::mModelType", rn["mModelType__12daShopItem_c"], 0x1003C910, 0xFF)
for k in sorted(rn):
    if k.startswith("d_a_npc_roten:") and any(x in k for x in ("l_save_dat", "l_item_dat", "l_get_item_no")): print(k, hex(rn[k]))
a, b = cmp("roten l_save_dat", rn["d_a_npc_roten:l_save_dat"], 0x100212C0, 0x18); print("   ", a.hex())
a, b = cmp("roten l_item_dat", rn["d_a_npc_roten:l_item_dat"], 0x10021308, 36); print("   ", a.hex())
a, b = cmp("roten l_get_item_no", rn["d_a_npc_roten:l_get_item_no"], 0x101C546C, 4); print("   ", a.hex(), b.hex())
# nz itemArr1: search both binaries
pat = bytes([0x82, 0x83, 0x51, 0x53, 0x0C, 0x0E, 0x10, 0x12])
for a0, d in mem.segs:
    i = bytes(d).find(pat)
    while i >= 0:
        print("GC nz itemArr1 pattern at %08X (%s)" % (a0 + i, min(((a0 + i - x, n) for x, n in names.items() if 0 <= a0 + i - x < 0x400), default=(0, "?"))[1]))
        i = bytes(d).find(pat, i + 1)
for s in hd.secs:
    i = s["data"].find(pat)
    while i >= 0:
        print("HD nz itemArr1 pattern at %08X (%s)" % (s["addr"] + i, s["name"])); i = s["data"].find(pat, i + 1)
print("HD shop_next_msg_tbl", hd.b(0x1001EFB0, 32).hex())
for k in sorted(rn):
    if k.startswith("d_a_npc_nz:") and ("shop_next" in k or "itemArr" in k or k.split(":")[1].startswith("@")): 
        if "shop_next" in k: print(k, gb(mem, rn[k], 32).hex())
