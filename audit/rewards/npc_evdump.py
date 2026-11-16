#!/usr/bin/env python3
"""Dump all staffs, cuts and properties of the GameCube events of one stage whose name matches a regular
expression.

Inputs:  GameCube disc image: /res/Stage/STAGE/Stage.arc (event_list.dat)
Output:  text on stdout.
Run:     python3 -I audit/rewards/npc_evdump.py STAGE REGEX          e.g. Ocmera 'PHOTO'
"""
import json, os, re, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
sys.path.insert(0, auditenv.SCRIPTS)
from gc_stage_dump import rarc_files, yaz0  # noqa: E402
ISO = auditenv.gc_iso()
fst = auditenv.gc_fst()
def s(b): return b.split(b"\0")[0].decode("latin-1")
off, size = fst["/res/Stage/%s/Stage.arc" % sys.argv[1]] if "/res/Stage/%s/Stage.arc" % sys.argv[1] in fst else [v for k, v in fst.items() if k.endswith("/Stage/%s/Stage.arc" % sys.argv[1])][0]
f = open(ISO, "rb"); f.seek(off)
g = rarc_files(yaz0(f.read(size)))["event_list.dat"]
evo, evn, aco, acn, cuo, cun, pro, prn, flo, fln, ino, inn, sto, stn = struct.unpack(">14I", g[:0x38])
for e in range(evn):
    E = g[evo + e * 0xB0: evo + (e + 1) * 0xB0]
    ename = s(E[:32])
    if not re.search(sys.argv[2], ename): continue
    print("EVENT", ename)
    actors = struct.unpack(">20i", E[0x2C:0x7C]); na = struct.unpack(">i", E[0x7C:0x80])[0]
    for ai in actors[:na]:
        A = g[aco + ai * 0x50: aco + (ai + 1) * 0x50]
        print("  STAFF", s(A[:32])); ci = struct.unpack(">i", A[0x30:0x34])[0]
        n = 0
        while ci >= 0 and n < 300:
            C = g[cuo + ci * 0x50: cuo + (ci + 1) * 0x50]
            pi, nxt = struct.unpack(">ii", C[0x38:0x40]); ps = []
            while pi >= 0:
                P = g[pro + pi * 0x40: pro + (pi + 1) * 0x40]
                typ, di, dn, pn = struct.unpack(">IIIi", P[0x24:0x34])
                if typ == 3: v = list(struct.unpack(">%di" % dn, g[ino + di * 4: ino + (di + dn) * 4]))
                elif typ == 4: v = s(g[sto + di: sto + di + dn])
                else: v = [round(x, 2) for x in struct.unpack(">%df" % dn, g[flo + di * 4: flo + (di + dn) * 4])] if typ in (0, 1) else "?"
                ps.append("%s=%s" % (s(P[:32]), v)); pi = pn
            print("    %-18s %s" % (s(C[:32]), " ".join(ps)))
            ci = nxt; n += 1
