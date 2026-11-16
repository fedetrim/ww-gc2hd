#!/usr/bin/env python3
"""HD side of reach.py: the exits (SCLS) of every HD stage and room file plus the stage names found as strings
in cking.rpx. Prints the HD stages nothing leads to, and compares the exit lists of the two games file by
file.

Inputs:  GameCube disc image (stage archives), extracted Wind Waker HD (content/Common/Stage, Pack,
         code/cking.rpx), stage_all.json in research/out/rewards/
Output:  text on stdout; the audit kept it as reach_hd.txt.
Run:     python3 -I audit/rewards/reach_hd.py > research/out/rewards/reach_hd.txt      (about 2 minutes)
"""
import glob, os, struct, sys, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
sys.path.insert(0, auditenv.SCRIPTS); sys.path.insert(0, auditenv.MACHINE_CODE)
import gc_stage_dump as G, hd_stage_dump as H, hd_extract as HX
def scls(d):
    out = []
    n = struct.unpack(">I", d[:4])[0]
    for i in range(n):
        tag, count, coff = struct.unpack(">4sII", d[4 + i * 12:16 + i * 12])
        if tag == b"SCLS":
            for k in range(count):
                e = d[coff + k * 12:coff + k * 12 + 12]
                out.append((e[:8].split(b"\0")[0].decode("latin-1"), e[8], e[9]))
    return out
hd = collections.defaultdict(list)
blobs = {}
for p in glob.glob(os.path.join(auditenv.HD_GAME, "content/Common/Stage/*.szs")):
    blobs[os.path.basename(p)] = open(p, "rb").read()
for p in glob.glob(os.path.join(auditenv.HD_GAME, "content/Common/Pack/*.pack")):
    try:
        for name, d in H.sarc_files(open(p, "rb").read()).items():
            if name.endswith(".szs"): blobs.setdefault(os.path.basename(name), d)
    except AssertionError:
        pass
for fname, raw in sorted(blobs.items()):
    base = fname[:-4]
    if "_" not in base: continue
    stage, arc = base.rsplit("_", 1)
    try: files = H.sarc_files(G.yaz0(raw))
    except Exception: continue
    for name, d in files.items():
        if name.endswith(".bfres"):
            for s in H.find_dzx(d):
                hd[(stage, arc)] += scls(d[s:])
fst = auditenv.gc_fst()
f = open(auditenv.gc_iso(), "rb"); gc = collections.defaultdict(list)
for p, (off, size) in sorted(fst.items()):
    parts = p.split("/")
    if len(parts) != 5 or parts[2] != "Stage" or not parts[4].endswith(".arc"): continue
    f.seek(off)
    try: files = G.rarc_files(G.yaz0(f.read(size)))
    except Exception: continue
    for fn, d in files.items():
        if fn.endswith((".dzs", ".dzr")):
            gc[(parts[3], parts[4][:-4])] += scls(d)
hstages = set(s for s, a in hd)
diff = 0
for k in sorted(set(gc) | set(hd)):
    if k[0] in hstages and sorted(gc.get(k, [])) != sorted(hd.get(k, [])):
        diff += 1
        print("exit list differs", k, "GC-only", sorted(set(gc.get(k, [])) - set(hd.get(k, []))), "HD-only", sorted(set(hd.get(k, [])) - set(gc.get(k, []))))
print("stage/room files with exits compared: %d, differing: %d" % (len([k for k in set(gc) | set(hd) if k[0] in hstages]), diff))
rpx = b"".join(s["data"] for s in HX.load_rpx() if s["data"])
allst = set(json.load(open(auditenv.out_file("rewards", "stage_all.json")))["hd"])
incode = set(s for s in allst if b"\0" + s.encode() + b"\0" in rpx)
edges = collections.defaultdict(set)
for (s, a), l in hd.items():
    for d, _, _ in l: edges[s].add(d)
seen = set(); todo = ["sea"] + sorted(incode)
while todo:
    s = todo.pop()
    if s in seen or s not in allst: continue
    seen.add(s); todo.extend(edges[s])
print("HD stages %d, named in rpx %d, reachable %d; unreachable: %s" % (len(allst), len(incode), len(seen), sorted(allst - seen)))
