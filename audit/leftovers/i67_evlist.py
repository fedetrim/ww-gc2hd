#!/usr/bin/env python3
"""Items 6-7, event scripts: parse the event_list.dat of every GameCube stage and list the values of the
EventFlag property (which stages use each), every property name by frequency with an example, and the
ItemNo / SwOn / ItemType values per stage.

Inputs:  GameCube disc image: /res/Stage/*/Stage.arc (event_list.dat)
Output:  text on stdout.
Run:     python3 -I audit/leftovers/i67_evlist.py

GameCube only: scripts/event_diff.py shows that HD's event scripts are byte-identical.
"""
import os, sys, struct, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import i67_msglib as L
fst = L.auditenv.gc_fst(); f = open(L.auditenv.gc_iso(), "rb")
flags = collections.defaultdict(set); props = collections.Counter(); ex = {}
nst = 0
for path, (off, size) in sorted(fst.items()):
    parts = path.split("/")
    if not (len(parts) == 5 and parts[2] == "Stage" and parts[4] == "Stage.arc"): continue
    f.seek(off)
    try: files = L.G.rarc_files(L.G.yaz0(f.read(size)))
    except Exception: continue
    d = files.get("event_list.dat")
    if not d: continue
    h = struct.unpack(">14I", d[:0x38])
    (eo, en, so, sn, co, cn, po, pn, fo, fn, io, inn, sto, stn) = h
    if en == 0: continue
    nst += 1
    cs = lambda b: b.split(b"\0")[0].decode("latin-1")
    staff = [(cs(d[so + i * 0x50:so + i * 0x50 + 0x20]), struct.unpack(">I", d[so + i * 0x50 + 0x28:so + i * 0x50 + 0x2C])[0]) for i in range(sn)]
    cuts = []
    for i in range(cn):
        c = d[co + i * 0x50:co + (i + 1) * 0x50]
        cuts.append((cs(c[:0x20]), struct.unpack(">I", c[0x3C:0x40])[0]))  # name, first property index
    def prop(i):
        p = d[po + i * 0x40:po + (i + 1) * 0x40]
        name = cs(p[:0x20]); idx, typ, di, cnt, nxt = struct.unpack(">IIIIi", p[0x20:0x34])
        if typ == 3: val = struct.unpack(">%di" % cnt, d[io + di * 4:io + (di + cnt) * 4])
        elif typ == 4: val = cs(d[sto + di:sto + di + cnt])
        else: val = struct.unpack(">%df" % (cnt * (3 if typ == 1 else 1)), d[fo + di * 4:fo + (di + cnt * (3 if typ == 1 else 1)) * 4])
        return name, typ, val, nxt
    for i in range(pn):
        name, typ, val, nxt = prop(i)
        props[name] += 1; ex.setdefault(name, (parts[3], val))
        if name == "EventFlag": flags[val].add(parts[3])
print("stages with events:", nst)
print("EventFlag values:"); [print("   %s  %s" % (["0x%04X" % (v & 0xFFFF) for v in k], sorted(s))) for k, s in sorted(flags.items())]
print("property names:"); [print("   %-16s %5d  e.g. %s" % (k, v, ex[k])) for k, v in sorted(props.items())]
# second pass: ItemNo / SwOn / ItemType values per stage
f.seek(0); vals = collections.defaultdict(lambda: collections.defaultdict(set))
for path, (off, size) in sorted(fst.items()):
    parts = path.split("/")
    if not (len(parts) == 5 and parts[2] == "Stage" and parts[4] == "Stage.arc"): continue
    f.seek(off)
    try: files = L.G.rarc_files(L.G.yaz0(f.read(size)))
    except Exception: continue
    d = files.get("event_list.dat")
    if not d: continue
    h = struct.unpack(">14I", d[:0x38]); po, pn, io = h[6], h[7], h[10]
    for i in range(pn):
        p = d[po + i * 0x40:po + (i + 1) * 0x40]; name = p[:0x20].split(b"\0")[0].decode()
        idx, typ, di, cnt = struct.unpack(">IIII", p[0x20:0x30])
        if name in ("ItemNo", "SwOn", "ItemType") and typ == 3:
            vals[name][struct.unpack(">%di" % cnt, d[io + di * 4:io + (di + cnt) * 4])].add(parts[3])
for n, v in vals.items():
    print(n); [print("   ", ["0x%X" % x for x in k], sorted(s)) for k, s in sorted(v.items())]
