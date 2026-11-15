#!/usr/bin/env python3
"""Compare the non-stage data tables of the GameCube disc (/res/ItemTable/item_table.bin,
/res/ActorDat/ActorDat.bin, /res/FmapDat/*) with the same data in HD (content/Common/Misc/* and the packs):
byte-identical, contained in a larger HD file, or differing (with the number and first positions of the
differing bytes).

Inputs:  GameCube disc image; extracted Wind Waker HD: content/Common/Misc/*, content/Common/Pack/*.pack
Output:  text on stdout; the audit kept it as misc_tables.txt.
Run:     python3 -I audit/rewards/misc_tables.py > research/out/rewards/misc_tables.txt     (about 30 s)

The differing cells of ActorDat.bin are decoded by audit/leftovers/i67_actordat.py.
"""
import glob, json, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
sys.path.insert(0, auditenv.SCRIPTS)
import gc_stage_dump as G
import hd_stage_dump as H
fst = auditenv.gc_fst()
f = open(auditenv.gc_iso(), "rb")
def gcfile(p):
    off, size = fst[p]; f.seek(off); return G.yaz0(f.read(size))
hd = {}
def walk(name, d, depth=0):
    d = G.yaz0(d)
    hd[name] = d
    if d[:4] == b"SARC" and depth < 4:
        for n, x in H.sarc_files(d).items():
            walk(name + "@" + n, x, depth + 1)
for p in glob.glob(os.path.join(auditenv.HD_GAME, "content/Common/Misc/*")) + glob.glob(os.path.join(auditenv.HD_GAME, "content/Common/Pack/*.pack")):
    walk(os.path.basename(p), open(p, "rb").read())
print("HD Misc.szs members:", sorted(n.split("@", 1)[1] for n in hd if n.startswith("Misc.szs@")))
gc = {}
for p in fst:
    if p.startswith(("/res/ItemTable/", "/res/ActorDat/", "/res/FmapDat/")):
        d = gcfile(p)
        if d[:4] == b"RARC":
            for n, x in G.rarc_files(d).items():
                gc[p + "@" + n] = x
        else:
            gc[p] = d
for p, d in sorted(gc.items()):
    base = p.split("@")[-1].split("/")[-1]
    same = [n for n, x in hd.items() if x == d]
    cont = [n for n, x in hd.items() if len(d) >= 16 and d in x and x != d][:2]
    if not same and not cont:      # locate by header and report differing bytes
        for n, x in hd.items():
            q = x.find(d[:8])
            if q >= 0 and "@" in n and not x[:4] == b"SARC":
                y = x[q:q + len(d)]
                diffs = [i for i in range(len(y)) if y[i] != d[i]]
                print("     header found in %s at 0x%X: %d of %d bytes differ, at %s" % (n, q, len(diffs), len(d), ["0x%X" % i for i in diffs[:40]]))
    byname = [(n, len(x)) for n, x in hd.items() if n.split("@")[-1].split("/")[-1].lower() == base.lower()]
    print("%-45s %7d bytes | identical HD file: %s | contained in: %s | same name in HD: %s" % (p, len(d), same[:2], cont, byname[:2]))
    for n, ln in byname[:1]:
        x = hd[n]
        if x != d:
            diffs = [i for i in range(min(len(x), len(d))) if x[i] != d[i]]
            print("     differs: GC %d bytes, HD %d bytes, %d differing byte positions, first at %s" % (len(d), len(x), len(diffs), ["0x%X" % i for i in diffs[:12]]))
