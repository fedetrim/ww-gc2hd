#!/usr/bin/env python3
"""Dump every actor-format entry of every stage and room file of both games: all layers, all entity chunk types
(ACT*, SCO*, TRE*, TGOB, TGSC, TGDR, DOOR, PLYR), with chunk index and file offset, plus the stage's save
record number and the totals per chunk tag. Uses the container readers of scripts/gc_stage_dump.py and
scripts/hd_stage_dump.py.

Inputs:  GameCube disc image: /res/Stage/*/{Stage,Room*}.arc
         extracted Wind Waker HD: content/Common/Stage/*.szs and content/Common/Pack/*.pack
         (locations: audit/auditenv.py; setup: docs/SETUP-RESEARCH.md)
Output:  stage_all.json (about 8 MB) in research/out/rewards/, or the path given as argument:
         {"gc": {stage: {"save_table": n, "ents": [...]}}, "hd": {...}}; a summary on stdout.
Run:     python3 -I audit/rewards/stage_all.py [OUT.json]        (about 2 minutes: the HD archives are decompressed in Python)

First step of this audit: stage_cmp.py, stage_types.py, totals.py, rando_match.py, rando_final.py, reach*.py
and gc_only_stages.py read stage_all.json. Also imported by audit/undo/hd_all.py for hd().
"""
import glob, json, os, struct, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
sys.path.insert(0, auditenv.SCRIPTS)
import gc_stage_dump as G  # noqa: E402
import hd_stage_dump as H  # noqa: E402

E20 = ("ACT", "TRE", "PLY", "TGO")
E24 = ("SCO", "TGS", "TGD", "DOO")

def parse(data, arc, fname, out, tags):
    n = struct.unpack(">I", data[:4])[0]
    for i in range(n):
        tag, count, coff = struct.unpack(">4sII", data[4 + i * 12:16 + i * 12])
        tag = tag.decode("latin-1")
        tags[tag] += count
        if tag == "STAG":
            out["save_table"] = data[coff + 9] >> 1 & 0x7F
        p = tag[:3]
        if p in E20 or p in E24:
            es = 0x24 if p in E24 else 0x20
            for k in range(count):
                o = coff + k * es
                e = data[o:o + es]
                if len(e) < es:
                    break
                name = e[:8].split(b"\0")[0].decode("latin-1")
                params = struct.unpack(">I", e[8:12])[0]
                pos = [round(v, 1) for v in struct.unpack(">fff", e[12:24])]
                aux = struct.unpack(">HHHH", e[24:32])
                out["ents"].append({"arc": arc, "file": fname, "layer": tag, "idx": k, "off": o, "name": name,
                                    "params": "%08X" % params, "pos": pos, "aux": ["%04X" % v for v in aux],
                                    "extra": e[32:].hex()})

def gc(iso):
    f = open(iso, "rb")
    h = f.read(0x440)
    fst_off, fst_size = struct.unpack(">II", h[0x424:0x42C])
    f.seek(fst_off); fst = f.read(fst_size)
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
    stages, tags, skipped = {}, collections.Counter(), []
    for p, (off, size) in sorted(paths.items()):
        parts = p.split("/")
        if len(parts) != 5 or parts[1] != "res" or parts[2] != "Stage" or not parts[4].endswith(".arc"):
            continue
        stage, arc = parts[3], parts[4][:-4]
        f.seek(off)
        try:
            files = G.rarc_files(G.yaz0(f.read(size)))
        except Exception as e:
            skipped.append(p); continue
        for fname, data in files.items():
            if fname.endswith((".dzs", ".dzr")):
                st = stages.setdefault(stage, {"save_table": None, "ents": []})
                parse(data, arc, fname, st, tags)
    return stages, tags, skipped

def hd(game):
    stages, tags, skipped = {}, collections.Counter(), []
    blobs = {}
    for p in glob.glob(os.path.join(game, "content/Common/Stage/*.szs")):
        blobs[os.path.basename(p)] = open(p, "rb").read()
    for p in glob.glob(os.path.join(game, "content/Common/Pack/*.pack")):
        try:
            for name, d in H.sarc_files(open(p, "rb").read()).items():
                if name.endswith(".szs"):
                    blobs.setdefault(os.path.basename(name), d)
        except AssertionError:
            skipped.append(p)
    for fname, raw in sorted(blobs.items()):
        base = fname[:-4]
        if "_" not in base:
            continue
        stage, arc = base.rsplit("_", 1)
        try:
            files = H.sarc_files(G.yaz0(raw))
        except Exception:
            skipped.append(fname); continue
        for name, d in files.items():
            if not name.endswith(".bfres"):
                continue
            for s in H.find_dzx(d):
                st = stages.setdefault(stage, {"save_table": None, "ents": []})
                parse(d[s:], arc, name, st, tags)
    return stages, tags, skipped

if __name__ == "__main__":
    gs, gt, gk = gc(auditenv.gc_iso())
    hs, ht, hk = hd(auditenv.HD_GAME)
    json.dump({"gc": gs, "hd": hs}, open(sys.argv[1] if len(sys.argv) > 1 else auditenv.out_file("rewards", "stage_all.json"), "w"))
    for n, s, t, k in (("GC", gs, gt, gk), ("HD", hs, ht, hk)):
        print(n, "stages", len(s), "entries", sum(len(x["ents"]) for x in s.values()))
        print("  chunk tags (total entry counts):", dict(sorted(t.items())))
        print("  skipped containers:", k)
        arcs = collections.Counter(e["arc"].rstrip("0123456789") for x in s.values() for e in x["ents"])
        print("  archive kinds:", dict(arcs))
