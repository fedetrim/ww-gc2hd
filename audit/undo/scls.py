#!/usr/bin/env python3
"""List the exits (SCLS entries) of every HD stage and room that lead to the given destination stages: how a
player gets back to the place of a reopened chest.

Inputs:  extracted Wind Waker HD: content/Common/Stage/*.szs and content/Common/Pack/*.pack
Output:  text on stdout: stage, archive, exit number, destination, start point, room, fade.
Run:     python3 -I audit/undo/scls.py DEST [DEST...]      e.g. TF_01 TF_02 TF_04 Cave09 PShip
         (about 2 minutes: every HD stage archive is decompressed)
"""
import glob, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
sys.path.insert(0, auditenv.SCRIPTS)
import gc_stage_dump as G  # noqa: E402
import hd_stage_dump as H  # noqa: E402
game, dests = auditenv.HD_GAME, set(sys.argv[1:])
blobs = {}
for p in glob.glob(os.path.join(game, "content/Common/Stage/*.szs")):
    blobs[os.path.basename(p)] = open(p, "rb").read()
for p in glob.glob(os.path.join(game, "content/Common/Pack/*.pack")):
    try:
        for name, d in H.sarc_files(open(p, "rb").read()).items():
            if name.endswith(".szs"):
                blobs.setdefault(os.path.basename(name), d)
    except AssertionError:
        pass
for fname, raw in sorted(blobs.items()):
    base = fname[:-4]
    if "_" not in base:
        continue
    stage, arc = base.rsplit("_", 1)
    try:
        files = H.sarc_files(G.yaz0(raw))
    except Exception:
        continue
    for name, d in files.items():
        if not name.endswith(".bfres"):
            continue
        for s in H.find_dzx(d):
            data = d[s:]
            n = struct.unpack(">I", data[:4])[0]
            for i in range(n):
                tag, count, coff = struct.unpack(">4sII", data[4 + i * 12:16 + i * 12])
                if tag == b"SCLS":
                    for k in range(count):
                        e = data[coff + k * 12:coff + k * 12 + 12]
                        dst = e[:8].split(b"\0")[0].decode("latin-1")
                        if dst in dests:
                            print(stage, arc, "exit", k, "->", dst, "start", e[8], "room", e[9], "fade", e[10], e[11])
