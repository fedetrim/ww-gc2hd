#!/usr/bin/env python3
"""Shops, part 1: the nine item sets of d_shop (Item_set_data_tbl) of both games, slot by slot (item, the
"not owned"/"owned" check functions, condition byte, message numbers, count), and default_select_msg.
Ends with ALL SAME or DIFFS.

Inputs:  GameCube disc image, zeldaret/tww config/GZLE01/symbols.txt, cking.rpx
Output:  text on stdout.
Run:     python3 -I audit/rewards/shops_dump.py

Limit: every address in this script is a constant of the two builds compared (GameCube USA GZLE01 and HD
USA v0); nothing is looked up by name on the HD side. Another build needs the addresses found again.
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auditenv  # noqa: E402
sys.path.insert(0, auditenv.MACHINE_CODE)
import gc_extract, hd_extract
mem, rels = gc_extract.load()
syms = gc_extract.parse_symbols(os.path.join(gc_extract.CFG, "symbols.txt"))
byaddr = {a: n for n, s, a, sz, t in syms}
secs = hd_extract.load_rpx()
def h32(a):
    for s in secs:
        if s["addr"] and s["addr"] <= a < s["addr"] + len(s["data"]):
            return struct.unpack_from(">I", s["data"], a - s["addr"])[0]
    return None
def hbytes(a, n):
    for s in secs:
        if s["addr"] and s["addr"] <= a < s["addr"] + len(s["data"]):
            return s["data"][a - s["addr"]:a - s["addr"] + n]
def gbytes(a, n):
    b, d = mem.find(a); return bytes(d[a - b:a - b + n])
def set_entry(r32, p):
    it = r32(p)
    return dict(item=[r32(it), r32(it + 4), r32(it + 8), r32(it + 12) >> 24], show=r32(p + 4), buy=r32(p + 8), m0c=r32(p + 12), cnt=r32(p + 16))
def lst(r32, p, n=None):
    out = []
    i = 0
    while True:
        e = r32(p + 4 * i)
        if e == 0 or (n and i >= n): break
        out.append((e, set_entry(r32, e)))
        i += 1
    return out
def fmt(e):
    return "item=%02X notown=%X own=%X cond=%02X show=%04X buy=%04X m0C=%X cnt=%d" % (e["item"][0], e["item"][1], e["item"][2], e["item"][3], e["show"], e["buy"], e["m0c"], struct.unpack(">i", struct.pack(">I", e["cnt"]))[0])
if __name__ == "__main__":
    G = 0x80376308; H = 0x101EB674
    ok = True
    for i in range(9):
        g = mem.r32(G + 4 * i); h = h32(H + 4 * i)
        print("== Item_set_data_tbl[%d] GC %08X (%s) HD %08X" % (i, g, byaddr.get(g), h or 0))
        if not g: continue
        gl = lst(mem.r32, g); hl = lst(h32, h)
        for k in range(max(len(gl), len(hl))):
            a = fmt(gl[k][1]) if k < len(gl) else None; b = fmt(hl[k][1]) if k < len(hl) else None
            print("  slot %d %s GC@%08X(%s) HD@%08X\n     GC %s\n     HD %s" % (k, "SAME" if a == b else "DIFF", gl[k][0], byaddr.get(gl[k][0]), hl[k][0], a, b))
            ok &= a == b
    # default_select_msg
    print("default_select_msg GC", gbytes(0x80375DF8, 0x24).hex(), "\n                   HD", hbytes(0x101EB4AC, 0x24).hex())
    print("ALL SAME" if ok else "DIFFS")
