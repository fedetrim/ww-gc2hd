#!/usr/bin/env python3
"""Compare the stage event tables (EVNT chunk of every stage.dzs) of the GameCube disc and the HD game.

Each entry names an event of the stage and holds the switch that is set when the event is started by a
player spawn point (dEvent_exception_c::setStartDemo). usage: evnt_diff.py GAME.iso HD_GAME_DIR
"""
import glob
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gc_stage_dump as G  # noqa: E402
import hd_stage_dump as H  # noqa: E402


def events(dz):
    out = []
    n = struct.unpack(">I", dz[:4])[0]
    for i in range(n):
        tag, count, off = struct.unpack(">4sII", dz[4 + i * 12:16 + i * 12])
        if tag == b"EVNT":
            for k in range(count):
                e = dz[off + k * 0x18:off + (k + 1) * 0x18]
                out.append((e[1:16].split(b"\0")[0].decode("latin-1"), e[0x13], e[:1].hex() + e[0x10:0x13].hex() + e[0x14:].hex()))
    return out


def gc_tables(iso):
    f = open(iso, "rb")
    out = {}
    for p, (a, b) in G.disc_files(f).items():
        if p.startswith("/res/Stage/") and p.endswith("/Stage.arc"):
            f.seek(a)
            for fname, data in G.rarc_files(G.yaz0(f.read(b))).items():
                if fname.endswith(".dzs"):
                    out[p.split("/")[3]] = events(data)
    return out


def hd_tables(game):
    blobs = {}
    for p in glob.glob(os.path.join(game, "content/Common/Stage/*_Stage.szs")):
        blobs[os.path.basename(p)] = open(p, "rb").read()
    for p in glob.glob(os.path.join(game, "content/Common/Pack/*.pack")):
        try:
            for name, d in H.sarc_files(open(p, "rb").read()).items():
                if name.endswith("_Stage.szs"):
                    blobs.setdefault(os.path.basename(name), d)
        except AssertionError:
            pass
    out = {}
    for fname, raw in blobs.items():
        for name, d in H.sarc_files(H.yaz0(raw)).items():
            if name.endswith(".bfres"):
                for s in H.find_dzx(d):
                    ev = events(d[s:])
                    if ev:
                        out[fname[:-len("_Stage.szs")]] = ev
    return out


def main():
    g, h = gc_tables(sys.argv[1]), hd_tables(sys.argv[2])
    same = 0
    for stage in sorted(set(g) | set(h)):
        a, b = g.get(stage), h.get(stage)
        if a == b:
            same += bool(a)
            continue
        if a is None or b is None:
            print("%-8s only in %s (%d events)" % (stage, "GC" if b is None else "HD", len(a or b or [])))
            continue
        for k in range(max(len(a), len(b))):
            x = a[k] if k < len(a) else None
            y = b[k] if k < len(b) else None
            if x != y:
                print("%-8s event %2d  GC %s  HD %s" % (stage, k, x, y))
    print("%d stages with identical event tables" % same)


if __name__ == "__main__":
    main()
