#!/usr/bin/env python3
"""Items 6-7 (data files), ActorDat.bin: decode the table (ACFN column names, ACNA row names, ACDS byte matrix)
of both games and list the cells that differ.

Inputs:  GameCube disc image: /res/ActorDat/ActorDat.bin
         extracted Wind Waker HD: content/Common/Misc/Misc.szs (the table is found inside Misc.bfres by
         its first 8 bytes)
Output:  text on stdout. The differing cells are printed under both possible row/column orders; the
         "full rows" at the end use the name-major one.
Run:     python3 -I audit/leftovers/i67_actordat.py
"""
import json, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
sys.path.insert(0, auditenv.SCRIPTS)
import gc_stage_dump as G, hd_stage_dump as H
fst = auditenv.gc_fst()
f = open(auditenv.gc_iso(), "rb"); off, size = fst["/res/ActorDat/ActorDat.bin"]; f.seek(off); gc = f.read(size)
m = G.yaz0(open(os.path.join(auditenv.HD_GAME, "content/Common/Misc/Misc.szs"), "rb").read())
bf = H.sarc_files(m)["Misc.bfres"] if m[:4] == b"SARC" else m
q = bf.find(gc[:8]); hd = bf[q:q + len(gc)]
def dec(d):
    n = struct.unpack(">I", d[:4])[0]; blk = {}
    for i in range(n):
        t, a, b = struct.unpack(">4sII", d[4 + i * 12:16 + i * 12]); blk[t.decode()] = (a, b)
    def strs(t):
        cnt, o = blk[t]
        return [d[p:d.index(b"\0", p)].decode("latin-1") for p in struct.unpack(">%dI" % cnt, d[o:o + 4 * cnt])]
    return blk, strs("ACFN"), strs("ACNA"), blk["ACDS"]
bg, fg, ng, (sg, og) = dec(gc); bh, fh, nh, (sh, oh) = dec(hd)
print("blocks GC", bg, "HD", bh); print("formats equal", fg == fh, "names equal", ng == nh)
print("formats", fg); print("rows", len(ng))
# which is row/col: dat_size == row_num(ACFN) * colum_num(ACNA); cDT::GetInf(fmt, name)
nf, nn = len(fg), len(ng)
diffs = [i for i in range(len(gc)) if gc[i] != hd[i]]
print("differing bytes", len(diffs), "outside ACDS:", [hex(i) for i in diffs if not og <= i < og + sg])
for layout in ("name-major", "fmt-major"):
    print("--", layout)
    for i in diffs:
        k = i - og
        r, c = (k // nf, k % nf) if layout == "name-major" else (k % nn, k // nn)
        print("  0x%03X %-10s %-8s GC %02X HD %02X" % (i, ng[r], fg[c], gc[i], hd[i]))
print("-- full rows that differ (name-major)")
for r in sorted({(i - og) // nf for i in diffs}):
    arg = fg.index("ARG")
    print(ng[r], "ARG", gc[og + r * nf + arg]); 
    print("   GC", " ".join("%s=%02X" % (fg[c], gc[og + r * nf + c]) for c in range(nf)))
    print("   HD", " ".join("%s=%02X" % (fg[c], hd[og + r * nf + c]) for c in range(nf)))
