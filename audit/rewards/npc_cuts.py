#!/usr/bin/env python3
"""List every cut of the GameCube event scripts (event_list.dat of each stage) that belongs to a staff
(actor) whose name starts with one of the given prefixes, with its integer and string properties.

Inputs:  GameCube disc image: /res/Stage/*/Stage.arc (event_list.dat)
Output:  text on stdout: stage, event, staff, cut number, cut name, properties.
Run:     python3 -I audit/rewards/npc_cuts.py STAFF_PREFIX[,PREFIX...] [STAGE ...]     e.g. Ub1 sea

GameCube only: HD's event scripts are byte-identical (scripts/event_diff.py).
"""
import json, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
sys.path.insert(0, auditenv.SCRIPTS)
from gc_stage_dump import rarc_files, yaz0  # noqa: E402
ISO = auditenv.gc_iso()
fst = auditenv.gc_fst()
staffs = sys.argv[1].split(",")
only = sys.argv[2:]
f = open(ISO, "rb")
def s(b): return b.split(b"\0")[0].decode("latin-1")
for path, (off, size) in sorted(fst.items()):
    parts = path.split("/")
    if not (len(parts) == 5 and parts[2] == "Stage" and parts[4] == "Stage.arc"): continue
    if only and parts[3] not in only: continue
    f.seek(off)
    g = rarc_files(yaz0(f.read(size))).get("event_list.dat")
    if not g or struct.unpack(">I", g[4:8])[0] == 0: continue
    h = struct.unpack(">14I", g[:0x38])
    evo, evn, aco, acn, cuo, cun, pro, prn, flo, fln, ino, inn, sto, stn = h
    for e in range(evn):
        E = g[evo + e * 0xB0: evo + (e + 1) * 0xB0]
        ename = s(E[:32])
        actors = struct.unpack(">20i", E[0x2C:0x7C]); na = struct.unpack(">i", E[0x7C:0x80])[0]
        for ai in actors[:na]:
            A = g[aco + ai * 0x50: aco + (ai + 1) * 0x50]
            aname = s(A[:32]); ci = struct.unpack(">i", A[0x30:0x34])[0]
            step = 0
            while ci >= 0 and step < 500:
                C = g[cuo + ci * 0x50: cuo + (ci + 1) * 0x50]
                pl = []; cname = s(C[:32]); pi, nxt = struct.unpack(">ii", C[0x38:0x40])
                while pi >= 0:
                    P = g[pro + pi * 0x40: pro + (pi + 1) * 0x40]
                    pname = s(P[:32]); typ, di, dn, pn = struct.unpack(">IIIi", P[0x24:0x34])
                    if typ == 3:
                        pl.append("%s=%s" % (pname, list(struct.unpack(">%di" % dn, g[ino + di * 4: ino + (di + dn) * 4]))))
                    elif typ == 4:
                        pl.append("%s=%r" % (pname, s(g[sto + di: sto + di + dn])))
                    else:
                        pl.append(pname)
                    pi = pn
                if any(aname.startswith(x) for x in staffs):
                    print("%-8s %-26s %-10s cut#%d %-16s %s" % (parts[3], ename, aname, step, cname, " ".join(pl)))
                ci = nxt; step += 1
