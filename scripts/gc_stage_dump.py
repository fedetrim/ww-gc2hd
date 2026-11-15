#!/usr/bin/env python3
"""Dump stage data from a GameCube Wind Waker disc image (your own copy): every treasure chest with the
save record and open flag it uses, plus all actors.  usage: gc_stage_dump.py DISC.iso OUT.json"""
import json
import struct
import sys


def yaz0(d):
    if d[:4] != b"Yaz0":
        return d
    size = struct.unpack(">I", d[4:8])[0]
    out = bytearray()
    i = 16
    while len(out) < size:
        code = d[i]
        i += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if code & 0x80 >> bit:
                out.append(d[i])
                i += 1
            else:
                b1, b2 = d[i], d[i + 1]
                i += 2
                dist = ((b1 & 0xF) << 8 | b2) + 1
                n = b1 >> 4
                if n == 0:
                    n = d[i] + 0x12
                    i += 1
                else:
                    n += 2
                for _ in range(n):
                    out.append(out[-dist])
    return bytes(out)


def rarc_files(d):
    """{name: bytes} of a RARC archive"""
    assert d[:4] == b"RARC", d[:4]
    hdr = 0x20
    data_off = struct.unpack(">I", d[0x0C:0x10])[0] + hdr
    nfiles, files_off, _, str_off = struct.unpack(">IIII", d[hdr + 8:hdr + 0x18])
    files_off += hdr
    str_off += hdr
    out = {}
    for i in range(nfiles):
        e = d[files_off + i * 0x14:files_off + (i + 1) * 0x14]
        flags = e[4]
        name_off = struct.unpack(">H", e[6:8])[0]
        off, size = struct.unpack(">II", e[8:16])
        if flags & 0x02:            # directory
            continue
        name = d[str_off + name_off:d.index(b"\0", str_off + name_off)].decode("latin-1")
        out[name] = d[data_off + off:data_off + off + size]
    return out


def chunks(dz):
    n = struct.unpack(">I", dz[:4])[0]
    out = {}
    for i in range(n):
        tag, count, off = struct.unpack(">4sII", dz[4 + i * 12:16 + i * 12])
        out.setdefault(tag.decode("latin-1"), []).append((count, off))
    return out


def main(iso, out_path):
    f = open(iso, "rb")
    h = f.read(0x440)
    fst_off, fst_size = struct.unpack(">II", h[0x424:0x42C])
    f.seek(fst_off)
    fst = f.read(fst_size)
    n = struct.unpack(">I", fst[8:12])[0]
    strs = n * 12
    dirs, paths, i = [(n, "")], {}, 1
    while i < n:
        while i >= dirs[-1][0]:
            dirs.pop()
        is_dir = fst[i * 12]
        name_off = int.from_bytes(fst[i * 12 + 1:i * 12 + 4], "big")
        a, b = struct.unpack(">II", fst[i * 12 + 4:i * 12 + 12])
        name = fst[strs + name_off:fst.index(b"\0", strs + name_off)].decode("latin-1")
        p = dirs[-1][1] + "/" + name
        if is_dir:
            dirs.append((b, p))
        else:
            paths[p] = (a, b)
        i += 1

    stages = {}
    for p, (off, size) in sorted(paths.items()):
        parts = p.split("/")
        if len(parts) != 5 or parts[1] != "res" or parts[2] != "Stage" or not parts[4].endswith(".arc"):
            continue
        stage, arc = parts[3], parts[4][:-4]
        if not (arc == "Stage" or arc.startswith("Room")):
            continue
        f.seek(off)
        try:
            files = rarc_files(yaz0(f.read(size)))
        except Exception as e:           # not an archive we understand
            print("skip", p, e, file=sys.stderr)
            continue
        st = stages.setdefault(stage, {"save_table": None, "chests": [], "actors": [], "spawns": []})
        for fname, data in files.items():
            if not fname.endswith((".dzs", ".dzr")):
                continue
            for tag, lst in chunks(data).items():
                for count, coff in lst:
                    if tag == "STAG":
                        st["save_table"] = data[coff + 9] >> 1 & 0x7F
                    elif tag.startswith("TRE") or tag.startswith("ACT") or tag.startswith("SCO") or tag == "PLYR":
                        esize = 0x24 if tag.startswith("SCO") else 0x20
                        for k in range(count):
                            e = data[coff + k * esize:coff + (k + 1) * esize]
                            name = e[:8].split(b"\0")[0].decode("latin-1")
                            params = struct.unpack(">I", e[8:12])[0]
                            pos = [round(v, 1) for v in struct.unpack(">fff", e[12:24])]
                            aux = struct.unpack(">HHHH", e[24:32])
                            rec = {"arc": arc, "layer": tag, "name": name, "params": "%08X" % params,
                                   "pos": pos, "aux": ["%04X" % v for v in aux]}
                            if tag.startswith("TRE"):
                                rec.update(type=params & 0x7F, open_flag=params >> 7 & 0x1F,
                                           appear_switch=params >> 12 & 0xFF, item=aux[2] >> 8)
                                st["chests"].append(rec)
                            elif tag == "PLYR":
                                rec.update(room=aux[0] & 0x3F, start_code=aux[2] & 0xFF)   # dStage: angle.z low byte
                                st["spawns"].append(rec)
                            else:
                                st["actors"].append(rec)
    json.dump(stages, open(out_path, "w"))
    print("%d stages, %d chests, %d actors" % (len(stages), sum(len(s["chests"]) for s in stages.values()),
                                               sum(len(s["actors"]) for s in stages.values())))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
