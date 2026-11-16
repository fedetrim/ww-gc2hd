#!/usr/bin/env python3
"""Stage reachability on the GameCube disc. The exits (SCLS chunks) of all stages form a graph; stage names
that occur as strings in main.dol or a REL are extra entry points. Prints the stages that no exit of
another stage and no code string leads to, with the chests they contain.

Inputs:  GameCube disc image (stage archives, main.dol, RELs), zeldaret/tww config (through
         audit/machine-code/gc_extract.py), stage_all.json in research/out/rewards/
Output:  text on stdout; the audit kept it as reach.txt.
Run:     python3 -I audit/rewards/reach.py > research/out/rewards/reach.txt
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
f = open(auditenv.gc_iso(), "rb")
edges = collections.defaultdict(set); stages = set()
for p, (off, size) in sorted(fst.items()):
    parts = p.split("/")
    if len(parts) != 5 or parts[2] != "Stage" or not parts[4].endswith(".arc"):
        continue
    stages.add(parts[3])
    f.seek(off)
    try:
        files = G.rarc_files(G.yaz0(f.read(size)))
    except Exception:
        continue
    for fn, d in files.items():
        if fn.endswith((".dzs", ".dzr")):
            for tag, lst in G.chunks(d).items():
                if tag == "SCLS":
                    for count, coff in lst:
                        for k in range(count):
                            e = d[coff + k * 12:coff + k * 12 + 12]
                            edges[parts[3]].add(e[:8].split(b"\0")[0].decode("latin-1"))
mem, rels = GX.load()
blobs = [b"".join(bytes(d) for a, d in mem.segs)] + list(rels.values())
incode = set(s for s in stages if any(b"\0" + s.encode() + b"\0" in b for b in blobs))
seen = set(); todo = ["sea"] + sorted(incode)
while todo:
    s = todo.pop()
    if s in seen or s not in stages: continue
    seen.add(s); todo.extend(edges[s])
print("stages on disc %d; named in code %d; reachable from 'sea' + code-named stages through exits: %d" % (len(stages), len(incode), len(seen)))
for s in sorted(stages - seen):
    into = sorted(a for a in stages if s in edges[a] and a != s)
    ch = [(e["arc"], e["aux"][2][:2]) for e in D["gc"].get(s, {"ents": []})["ents"] if e["layer"][:3] == "TRE"]
    print("  unreachable %-8s in HD: %-5s exits into it from: %s  chests (arc, item): %s" % (s, s in D["hd"], into, ch))
print("code-named stages:", sorted(incode))
