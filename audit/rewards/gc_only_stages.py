#!/usr/bin/env python3
"""Are the GameCube-only stages and rooms reachable? Lists every exit (SCLS entry) of the GameCube disc that
leads to a stage HD does not have, or to PShip rooms 0/1 or TF_03 rooms 1-6, and searches main.dol and all
RELs for those stage names.

Inputs:  GameCube disc image, zeldaret/tww config (through audit/machine-code/gc_extract.py),
         stage_all.json in research/out/rewards/
Output:  text on stdout.
Run:     python3 -I audit/rewards/gc_only_stages.py
"""
import os, struct, sys, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
sys.path.insert(0, auditenv.SCRIPTS); sys.path.insert(0, auditenv.MACHINE_CODE)
import gc_stage_dump as G
import gc_extract as GX
fst = auditenv.gc_fst()
D = json.load(open(auditenv.out_file("rewards", "stage_all.json")))
only = sorted(set(D["gc"]) - set(D["hd"]))
f = open(auditenv.gc_iso(), "rb")
hits = collections.defaultdict(list); n = 0
for p, (off, size) in sorted(fst.items()):
    parts = p.split("/")
    if len(parts) != 5 or parts[2] != "Stage" or not parts[4].endswith(".arc"):
        continue
    f.seek(off)
    try:
        files = G.rarc_files(G.yaz0(f.read(size)))
    except Exception:
        continue
    for fn, d in files.items():
        if not fn.endswith((".dzs", ".dzr")):
            continue
        for tag, lst in G.chunks(d).items():
            if tag != "SCLS":
                continue
            for count, coff in lst:
                for k in range(count):
                    e = d[coff + k * 12:coff + k * 12 + 12]
                    dest = e[:8].split(b"\0")[0].decode("latin-1"); n += 1
                    room = e[9]
                    if dest in only or (dest == "PShip" and room in (0, 1)) or (dest == "TF_03" and room in range(1, 7)):
                        hits[(dest, room)].append("%s/%s" % (parts[3], parts[4]))
print("SCLS exits scanned:", n)
for k, v in sorted(hits.items()):
    print("  exit to %s room %d from: %s" % (k[0], k[1], sorted(set(v))))
mem, rels = GX.load()
blobs = {"main.dol": b"".join(bytes(d) for a, d in mem.segs)}
blobs.update(rels)
for s in only + ["PShip"]:
    w = [n for n, b in blobs.items() if s.encode() + b"\0" in b]
    print("  string %-8s in code/data of: %s" % (s, w))
