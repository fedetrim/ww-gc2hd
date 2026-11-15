#!/usr/bin/env python3
"""Compare the event scripts (event_list.dat) of every stage between the GameCube disc and the extracted
HD game, byte for byte.  usage: event_diff.py GC.iso GC_FST.json HD_GAME_DIR"""
import glob
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gc_stage_dump import rarc_files, yaz0  # noqa: E402
from hd_stage_dump import sarc_files  # noqa: E402

SIZES = [0xB0, 0x50, 0x50, 0x40, 4, 4, 1]     # event, actor, action, property, float, int, string byte


def total_size(d):
    h = struct.unpack(">14I", d[:0x38])
    return max(h[2 * i] + h[2 * i + 1] * SIZES[i] for i in range(7))


def main(iso, fst_path, game):
    fst = json.load(open(fst_path))
    f = open(iso, "rb")
    hd = {}
    for p in glob.glob(os.path.join(game, "content/Common/Stage/*_Stage.szs")):
        hd[os.path.basename(p)[:-10]] = open(p, "rb").read()
    for p in glob.glob(os.path.join(game, "content/Common/Pack/*.pack")):
        try:
            for name, d in sarc_files(open(p, "rb").read()).items():
                if name.endswith("_Stage.szs"):
                    hd.setdefault(os.path.basename(name)[:-10], d)
        except AssertionError:
            pass
    same, different, missing = [], [], []
    for path, (off, size) in sorted(fst.items()):
        parts = path.split("/")
        if not (len(parts) == 5 and parts[2] == "Stage" and parts[4] == "Stage.arc") or parts[3] not in hd:
            continue
        f.seek(off)
        files = rarc_files(yaz0(f.read(size)))
        g = files.get("event_list.dat")
        if not g or struct.unpack(">I", g[4:8])[0] == 0:
            continue
        n = total_size(g)
        first = g[0x40:0x60].split(b"\0")[0] + b"\0"
        found = None
        for name, d in sarc_files(yaz0(hd[parts[3]])).items():
            p = 0
            while name.endswith(".bfres") and found is None:
                p = d.find(first, p)
                if p < 0:
                    break
                if p >= 0x40 and d[p - 0x40:p - 0x3C] == b"\0\0\0\x40":
                    found = d[p - 0x40:p - 0x40 + n]
                p += 1
        (missing if found is None else same if found == g[:n] else different).append(parts[3])
    print("event scripts: %d stages byte-identical, different: %s, not found in HD: %s" % (
        len(same), different, missing))


if __name__ == "__main__":
    main(*sys.argv[1:4])
