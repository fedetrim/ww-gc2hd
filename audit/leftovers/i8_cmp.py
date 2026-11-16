#!/usr/bin/env python3
"""Item 8: compare the direct save accesses per unit (kind load/store and offset inside the save structure),
with the name of the save region each offset falls in. Without argument: the GameCube stub units, all keys.
With `all`: every unit, one-sided keys only.

Inputs:  research/out/leftovers/i8_direct.json (i8_direct.py), research/out/machine-code/stubs.json
Output:  text on stdout; the audit kept `i8_cmp.py all` as i8_all.txt.
Run:     python3 -I audit/leftovers/i8_cmp.py [all] > research/out/leftovers/i8_all.txt
"""
import sys, os, json, collections, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
SA = auditenv.MACHINE_CODE
sys.path.insert(0, SA)
import compare
d = json.load(open(auditenv.out_file("leftovers", "i8_direct.json")))
stubs = {os.path.basename(k)[:-4] for k in json.load(open(auditenv.out_file("machine-code", "stubs.json")))}
gb = {os.path.basename(f).rsplit(".", 1)[0] for f, *_ in d["GC"]}
def region(off):
    R = [(0x000, "player.status_a"), (0x018, "player.status_b"), (0x030, "return_place"), (0x03C, "item"), (0x051, "get_item"),
         (0x066, "item_record"), (0x06E, "item_max"), (0x076, "bag_item"), (0x08E, "get_bag_item"), (0x09A, "bag_item_record"),
         (0x0B2, "collect"), (0x0BF, "map"), (0x143, "info"), (0x19B, "config"), (0x1A0, "priest"), (0x1B0, "status_c"),
         (0x380, "memory[16]"), (0x5C0, "ocean"), (0x624, "event"), (0x724, "reserve"), (0x778, "mMemory(cur)"), (0x79C, "mDan"),
         (0x7C8, "mZone"), (0x1128, "mRestart"), (0x1158, "mTmp"), (0x1258, "turnRestart"), (0x12A0, "end")]
    n = R[0][1]
    for a, b in R:
        if off >= a: n = b
    return n
U = {"GC": collections.defaultdict(lambda: collections.defaultdict(list)), "HD": collections.defaultdict(lambda: collections.defaultdict(list))}
for side in ("GC", "HD"):
    for f, fn, pc, k, off, m in d[side]:
        u = os.path.basename(f).rsplit(".", 1)[0] if side == "GC" else compare.unit_of(f, gb)
        U[side][u][(k, off)].append("%s@%s(%s)" % (fn.split("__")[0], pc, m))
allu = len(sys.argv) > 1
for u in sorted(set(U["GC"]) | set(U["HD"])):
    if not allu and u not in stubs: continue
    g, h = U["GC"].get(u, {}), U["HD"].get(u, {})
    keys = sorted(set(g) | set(h), key=lambda k: (k[1], k[0]))
    one = [k for k in keys if (k in g) != (k in h)]
    if not keys: continue
    print("== %s%s  GC %d keys, HD %d keys, one-sided %d" % (u, " [stub]" if u in stubs else "", len(g), len(h), len(one)))
    for k in (one if allu else keys):
        print("   %s %s +0x%03X %-16s GC:%s | HD:%s" % ("!" if k in one else " ", k[0], k[1], region(k[1]), ",".join(g.get(k, []))[:90], ",".join(h.get(k, []))[:110]))
