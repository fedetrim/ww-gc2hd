#!/usr/bin/env python3
"""Shops, part 2: who calls the shop functions (fopAcM_createShopItem, dShop_BoughtErrorStatus,
ShopItems_c::createItem, setItemSetDataList, SoldOutItem, getSelectItemNo, getItemNo,
dShop_now_triggercheck) in each game, with call counts per function.

Inputs:  GameCube disc image, zeldaret/tww config, cking.rpx, wwhd_src (address markers)
Output:  text on stdout.
Run:     python3 -I audit/rewards/shops_callers.py        (about 15 s)

Limit: every address in this script is a constant of the two builds compared (GameCube USA GZLE01 and HD
USA v0); nothing is looked up by name on the HD side. Another build needs the addresses found again.
"""
import sys, os, struct, bisect, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shops_lib import *
mem, names, funcs, rel24 = load_gc(); hd = HD()
mk = h.markers(); addrs = sorted(mk)
t = next(s for s in hd.secs if s["name"] == ".text")
targets = {0x025D87E4: "fopAcM_createShopItem", 0x025BBA1C: "dShop_BoughtErrorStatus", 0x025BC810: "ShopItems_c::createItem", 0x025BCF84: "setItemSetDataList()", 0x025BCFA0: "setItemSetDataList(list)", 0x025BCECC: "SoldOutItem", 0x025BD22C: "getSelectItemNo", 0x025BD248: "getItemNo", 0x025BB698: "dShop_now_triggercheck"}
res = collections.defaultdict(collections.Counter)
d = t["data"]
for off in range(0, len(d) - 3, 4):
    w = struct.unpack_from(">I", d, off)[0]
    if w >> 26 == 18 and w & 1 and not w & 2:
        disp = w & 0x03FFFFFC
        if disp & 0x02000000: disp -= 0x04000000
        tg = t["addr"] + off + disp
        if tg in targets:
            pc = t["addr"] + off
            i = bisect.bisect_right(addrs, pc) - 1
            res[targets[tg]]["%s %s" % (mk[addrs[i]][0], mk[addrs[i]][1])] += 1
print("== HD callers")
for k in sorted(res):
    for u, c in sorted(res[k].items()): print("  %-28s %d  %s" % (k, c, u))
print("== GC callers")
gt = ("fopAcM_createShopItem__", "dShop_BoughtErrorStatus__", "createItem__11ShopItems_c", "setItemSetDataList__11ShopItems_c", "SoldOutItem__11ShopItems_c", "getSelectItemNo__11ShopItems_c", "getItemNo__11ShopItems_c", "dShop_now_triggercheck")
tn = {a: n for a, n in names.items() if n.startswith(gt)}
res = collections.defaultdict(collections.Counter)
for f, n, m, s, e in funcs:
    for pc in range(s, e, 4):
        w = mem.r32(pc)
        if w >> 26 == 18 and w & 1:
            if pc in rel24: tg = rel24[pc]
            else:
                disp = w & 0x03FFFFFC
                if disp & 0x02000000: disp -= 0x04000000
                tg = pc + disp
            if tg in tn: res[tn[tg]]["%s %s" % (m if m != "dol" else f, n)] += 1
for k in sorted(res):
    for u, c in sorted(res[k].items()): print("  %-50s %d  %s" % (k, c, u))
