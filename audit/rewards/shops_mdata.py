#!/usr/bin/env python3
"""Shops, part 3: daShopItem_c::mData (display data of the 255 shop item models), entry by entry; prints the
entries that differ.

Inputs:  GameCube disc image, zeldaret/tww config, cking.rpx
Output:  text on stdout (nothing when all entries are equal).
Run:     python3 -I audit/rewards/shops_mdata.py

Limit: every address in this script is a constant of the two builds compared (GameCube USA GZLE01 and HD
USA v0); nothing is looked up by name on the HD side. Another build needs the addresses found again.
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shops_lib import *
mem, names, funcs, rel24 = load_gc(); hd = HD()
rn = {n: a for a, n in names.items()}
g = rn["mData__12daShopItem_c"]
for i in range(255):
    a, b = gb(mem, g + i * 0x20, 0x20), hd.b(0x1003A930 + i * 0x20, 0x20)
    if a != b:
        fa = struct.unpack(">6f3h2x", a); fb = struct.unpack(">6f3h2x", b)
        print("item %02X  GC %s (%s)\n         HD %s (%s)" % (i, a.hex(), fa, b.hex(), fb))
