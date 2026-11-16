#!/usr/bin/env python3
"""Shops, part 4: the item sets that are not in d_shop's table: Item_setData_rshop (13 entries), the three
Beedle special-shop entries (Bomb30Bs2, arrow30Bs2, red_bottleBs2) and the static sets of d_a_npc_bs1
(Item_set_data3/4/5/Bs2), entry by entry.

Inputs:  GameCube disc image, zeldaret/tww config, cking.rpx
Output:  text on stdout (SAME / DIFF per entry).
Run:     python3 -I audit/rewards/shops_tables2.py

Limit: every address in this script is a constant of the two builds compared (GameCube USA GZLE01 and HD
USA v0); nothing is looked up by name on the HD side. Another build needs the addresses found again.
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shops_lib import *
mem, names, funcs, rel24 = load_gc(); hd = HD()
rn = {n: a for a, n in names.items()}
def cmp_list(title, ga, ha, n):
    print("==", title, "GC %08X HD %08X" % (ga, ha))
    for i in range(n):
        gp, hp = mem.r32(ga + 4 * i), hd.r32(ha + 4 * i)
        if gp == 0 or hp == 0:
            print("  [%d] GC ptr %08X HD ptr %08X %s" % (i, gp, hp, "SAME(null)" if gp == hp else "DIFF")); continue
        a, b = set_entry(mem.r32, gp), set_entry(hd.r32, hp)
        print("  [%d] %s GC@%08X %s | HD@%08X\n       GC %s\n       HD %s" % (i, "SAME" if a == b else "DIFF", gp, names.get(gp), hp, a, b))
cmp_list("Item_setData_rshop", 0x80376264, 0x101EB940, 13)
# Bs2 entries
for nm, ha in (("shopItems_setData_Bomb30Bs2", 0x101EB8C8), ("shopItems_setData_arrow30Bs2", 0x101EB8DC), ("shopItems_setData_red_bottleBs2", 0x101EB8F0)):
    a, b = set_entry(mem.r32, rn[nm]), set_entry(hd.r32, ha)
    print(nm, "SAME" if a == b else "DIFF", "\n   GC", a, "\n   HD", b)
# bs1 REL statics
for k, v in sorted(rn.items()):
    if k.startswith("d_a_npc_bs1:") and ("Item_set" in k):
        print(k, hex(v))
for nm, ha, n in (("Item_set_data3", 0x101BD548, 6), ("Item_set_data4", 0x101BD560, 3), ("Item_set_data5", 0x101BD56C, 3), ("Item_set_dataBs2", 0x101BD578, 3)):
    c = [v for k, v in rn.items() if k.startswith("d_a_npc_bs1:") and k.split(":")[1].startswith(nm + "$")]
    cmp_list("bs1 " + nm, c[0], ha, n)
# all GC set data and item data in dol vs HD by walking both regions in order
