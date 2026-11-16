#!/usr/bin/env python3
"""Decode the random drop table of both games (item_table.bin: 16-byte header, then rows of 16 item ids) and
print the rows that differ and the set of item ids that occur.

Inputs:  GameCube disc image: /res/ItemTable/item_table.bin
         extracted Wind Waker HD: content/Common/Misc/Misc.szs (the table is found inside Misc.bfres by
         its first 10 bytes)
Output:  text on stdout.
Run:     python3 -I audit/rewards/item_table.py

Drops are not stored in a save; this shows that the differing rows hold consumables only.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
sys.path.insert(0, auditenv.SCRIPTS)
import gc_stage_dump as G, hd_stage_dump as H
fst = auditenv.gc_fst()
f = open(auditenv.gc_iso(), "rb"); off, size = fst["/res/ItemTable/item_table.bin"]; f.seek(off); g = f.read(size)
m = H.sarc_files(G.yaz0(open(os.path.join(auditenv.HD_GAME, "content/Common/Misc/Misc.szs"), "rb").read()))["Misc.bfres"]
q = m.find(g[:10]); h = m[q:q + len(g)]
print("header", g[:16], h[:16])
rows = (len(g) - 16) // 16
for i in range(rows):
    a, b = g[16 + i * 16:32 + i * 16], h[16 + i * 16:32 + i * 16]
    if a != b:
        print("row %2d (drop id 0x%02X)  GC %s  HD %s" % (i, 0x20 + i, a.hex(" "), b.hex(" ")))
print("item ids in GC table:", sorted("%02X" % x for x in set(g[16:])))
print("item ids in HD table:", sorted("%02X" % x for x in set(h[16:])))
