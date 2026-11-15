#!/usr/bin/env python3
"""Compare, for all 256 item ids, the get function (item_func_ptr) and the get-check function of the GameCube
dol with those of the HD rpx, by function name. Prints the rows where the function name or the item's enum
name differs.

Inputs:  GameCube disc image (main.dol); zeldaret/tww clone: config/GZLE01/symbols.txt,
         include/d/d_item_data.h; cking.rpx; wwhd clone: wwhd_src (address markers),
         wwhd_src/include/d/d_item_data.h
Output:  text on stdout.
Run:     python3 -I audit/rewards/item_tables.py

Limit: the table addresses are constants of these two builds (GameCube USA 0x803888C8 / 0x80388CC8, HD USA
v0 0x101E3A98 / 0x101E3E98).
"""
import os, re, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
sys.path.insert(0, auditenv.MACHINE_CODE)
import gc_extract as GX
import hd_extract as HX

def enum_names(path):
    out = {}
    for line in open(path, errors="replace"):
        m = re.match(r"\s*/\* 0x([0-9A-F]{2}) \*/ (dItemNo_\w+?)_e", line)
        if m:
            out.setdefault(int(m.group(1), 16), m.group(2)[8:])
    return out

mem, rels = GX.load()
syms = {a: n for n, sec, a, sz, t in GX.parse_symbols(os.path.join(GX.CFG, "symbols.txt")) if sec == ".text"}
secs = HX.load_rpx()
mk = HX.markers()
def hr32(addr):
    for s in secs:
        if s["addr"] <= addr < s["addr"] + len(s["data"]) and s["data"]:
            return struct.unpack_from(">I", s["data"], addr - s["addr"])[0]
    raise KeyError(hex(addr))
gn = enum_names(os.path.join(auditenv.TWW, "include/d/d_item_data.h"))
hn = enum_names(os.path.join(auditenv.WWHD, "wwhd_src/include/d/d_item_data.h"))
def norm(n):
    return re.sub(r"__F.*$", "", n)
rows = []
for tab, ga, ha in (("func", 0x803888C8, 0x101E3A98), ("getcheck", 0x80388CC8, 0x101E3E98)):
    for i in range(256):
        g = norm(syms.get(mem.r32(ga + 4 * i), "%08X" % mem.r32(ga + 4 * i)))
        a = hr32(ha + 4 * i)
        h = mk.get(a, (None, "%08X" % a, 0))
        rows.append((tab, i, g, h[1], h[0], h[2]))
print("item id | GC enum | HD enum | table | GC function | HD function (file:line)   -- only rows where function name or enum name differs")
for tab, i, g, h, f, l in rows:
    if g != h or (tab == "func" and gn.get(i) != hn.get(i)):
        print("0x%02X | %s | %s | %s | %s | %s (%s:%s)" % (i, gn.get(i), hn.get(i), tab, g, h, f, l))
print("rows compared:", len(rows), "identical names:", sum(1 for r in rows if r[2] == r[3]))
