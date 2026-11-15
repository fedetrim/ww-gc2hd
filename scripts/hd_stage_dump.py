#!/usr/bin/env python3
"""Dump stage data from an extracted Wind Waker HD game folder (your own copy), in the same JSON shape as
gc_stage_dump.py.  usage: hd_stage_dump.py GAME_DIR OUT.json"""
import glob
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gc_stage_dump import yaz0  # noqa: E402

TAGS = {b"STAG", b"ACTR", b"SCOB", b"PLYR", b"TRES", b"RTBL", b"EVNT", b"FILI", b"MULT", b"RPAT", b"RPPN",
        b"PATH", b"PPNT", b"SOND", b"CAMR", b"RCAM", b"AROB", b"RARO", b"TGOB", b"TGSC", b"TGDR", b"DOOR",
        b"SHIP", b"LGHT", b"LGTV", b"ENVR", b"Colo", b"Pale", b"Virt", b"2DMA", b"2Dma", b"DMAP", b"FLOR",
        b"MEMA", b"MECO", b"LBNK", b"RPPN", b"SCLS", b"TRES", b"LGTV", b"MPAT", b"DOOR", b"FILI"}


def sarc_files(d):
    assert d[:4] == b"SARC", d[:4]
    be = d[6:8] == b"\xfe\xff"
    e = ">" if be else "<"
    data_off = struct.unpack(e + "I", d[0x0C:0x10])[0]
    assert d[0x14:0x18] == b"SFAT"
    n = struct.unpack(e + "H", d[0x1A:0x1C])[0]
    nodes = 0x20
    names = nodes + n * 16 + 8
    out = {}
    for i in range(n):
        h, attr, a, b = struct.unpack(e + "IIII", d[nodes + i * 16:nodes + (i + 1) * 16])
        name = "%08x" % h
        if attr & 0x01000000:
            o = names + (attr & 0xFFFF) * 4
            name = d[o:d.index(b"\0", o)].decode("latin-1")
        out[name] = d[data_off + a:data_off + b]
    return out


def find_dzx(d):
    """the embedded stage.dzs / room.dzr inside a BFRES: locate a consistent chunk table"""
    found = []
    p = 0
    while True:
        p = min((q for q in (d.find(t, p) for t in (b"ACTR", b"STAG", b"PLYR", b"RTBL", b"FILI", b"SCOB")) if q >= 0),
                default=-1)
        if p < 0:
            break
        for k in range(64):
            s = p - 4 - 12 * k
            if s < 0:
                break
            n = struct.unpack(">I", d[s:s + 4])[0]
            if not 1 <= n <= 96 or k >= n:
                continue
            ok = True
            for i in range(n):
                tag, count, off = struct.unpack(">4sII", d[s + 4 + i * 12:s + 16 + i * 12])
                if not all(48 <= c <= 57 or 65 <= c <= 90 or 97 <= c <= 122 for c in tag) \
                        or s + off > len(d) or count > 20000:
                    ok = False
                    break
            if ok:
                found.append(s)
                break
        p += 4
    return sorted(set(found))


def parse(data, arc, st):
    n = struct.unpack(">I", data[:4])[0]
    for i in range(n):
        tag, count, coff = struct.unpack(">4sII", data[4 + i * 12:16 + i * 12])
        tag = tag.decode("latin-1")
        if tag == "STAG":
            st["save_table"] = data[coff + 9] >> 1 & 0x7F
        elif tag.startswith(("TRE", "ACT", "SCO")) or tag == "PLYR":
            esize = 0x24 if tag.startswith("SCO") else 0x20
            for k in range(count):
                e = data[coff + k * esize:coff + (k + 1) * esize]
                if len(e) < 0x20:
                    break
                name = e[:8].split(b"\0")[0].decode("latin-1")
                params = struct.unpack(">I", e[8:12])[0]
                pos = [round(v, 1) for v in struct.unpack(">fff", e[12:24])]
                aux = struct.unpack(">HHHH", e[24:32])
                rec = {"arc": arc, "layer": tag, "name": name, "params": "%08X" % params, "pos": pos,
                       "aux": ["%04X" % v for v in aux]}
                if tag.startswith("TRE"):
                    rec.update(type=params & 0x7F, open_flag=params >> 7 & 0x1F,
                               appear_switch=params >> 12 & 0xFF, item=aux[2] >> 8)
                    st["chests"].append(rec)
                elif tag == "PLYR":
                    rec.update(room=aux[0] & 0x3F, start_code=aux[2] & 0xFF)
                    st["spawns"].append(rec)
                else:
                    st["actors"].append(rec)


def main(game, out_path):
    stages = {}
    blobs = {}
    for p in glob.glob(os.path.join(game, "content/Common/Stage/*.szs")):
        blobs[os.path.basename(p)] = open(p, "rb").read()
    for p in glob.glob(os.path.join(game, "content/Common/Pack/*.pack")):
        try:
            for name, d in sarc_files(open(p, "rb").read()).items():
                if name.endswith(".szs") and ("_Room" in name or "_Stage" in name):
                    blobs.setdefault(os.path.basename(name), d)
        except AssertionError:
            pass
    for fname, raw in sorted(blobs.items()):
        base = fname[:-4]
        if "_" not in base:
            continue
        stage, arc = base.rsplit("_", 1)
        if not (arc == "Stage" or arc.startswith("Room")):
            continue
        try:
            files = sarc_files(yaz0(raw))
        except Exception as e:
            print("skip", fname, e, file=sys.stderr)
            continue
        st = stages.setdefault(stage, {"save_table": None, "chests": [], "actors": [], "spawns": []})
        for name, d in files.items():
            if not name.endswith(".bfres"):
                continue
            for s in find_dzx(d):
                parse(d[s:], arc, st)
    json.dump(stages, open(out_path, "w"))
    print("%d stages, %d chests, %d actors" % (len(stages), sum(len(s["chests"]) for s in stages.values()),
                                               sum(len(s["actors"]) for s in stages.values())))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
