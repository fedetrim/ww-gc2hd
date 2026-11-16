#!/usr/bin/env python3
"""Readers for the message data of both games (module, not run by itself): the GameCube BMG (zel_00.bmg in
/res/Msg/bmgres.arc: id, price, next message, attributes, text) and the HD MSBT sets inside
content/Common/Pack/permanent_2d_UsEnglish.pack (label = message id, ATR1 attributes, TXT2 text).

Inputs:  GameCube disc image; extracted Wind Waker HD
Output:  none.

HD attribute layout used by i67_cmp.py (found by correlation with the GameCube fields, not from a format
description): price = s16 at +4, next message = u16 at +6.
"""
import glob, json, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
sys.path.insert(0, auditenv.SCRIPTS)
import gc_stage_dump as G, hd_stage_dump as H  # noqa: E402
HD = auditenv.HD_GAME
def gc_file(p):
    fst = auditenv.gc_fst()
    f = open(auditenv.gc_iso(), "rb"); off, size = fst[p]; f.seek(off); return G.yaz0(f.read(size))
def bmg_sections(d):
    assert d[:8] == b"MESGbmg1", d[:8]
    n = struct.unpack(">I", d[12:16])[0]; o = 0x20; out = {}
    for _ in range(n):
        tag, size = struct.unpack(">4sI", d[o:o + 8]); out[tag.decode()] = d[o:o + size]; o += size
    return out
def gc_msgs(d):
    s = bmg_sections(d); inf, dat = s["INF1"], s["DAT1"][8:]
    cnt, esz = struct.unpack(">HH", inf[8:12]); out = {}
    for i in range(cnt):
        e = inf[16 + i * esz:16 + (i + 1) * esz]
        off, mid, price, nxt, unk = struct.unpack(">IHhHH", e[:12])
        # text ends at first 0 that is not inside a 0x1A escape
        p = off; 
        while dat[p] != 0:
            p += dat[p + 1] if dat[p] == 0x1A else 1
        out.setdefault(mid, []).append({"idx": i, "price": price, "next": nxt, "unk": unk, "attr": e[12:], "text": dat[off:p]})
    return out
def hd_packs(lang="UsEnglish"):
    out = {}
    def walk(name, d, depth=0):
        d = G.yaz0(d)
        if d[:8] == b"MsgStdBn": out[name.split("@")[-1]] = d
        if d[:4] == b"SARC" and depth < 4:
            for n, x in H.sarc_files(d).items(): walk(name + "@" + n, x, depth + 1)
    p = os.path.join(HD, "content/Common/Pack/permanent_2d_%s.pack" % lang)
    walk(os.path.basename(p), open(p, "rb").read())
    return out
def msbt(d):
    assert d[:8] == b"MsgStdBn"; be = d[8:10] == b"\xFE\xFF"; E = ">" if be else "<"
    nsec = struct.unpack(E + "H", d[14:16])[0]; o = 0x20; sec = {}
    for _ in range(nsec):
        tag, size = struct.unpack(E + "4sI", d[o:o + 8]); sec[tag.decode()] = d[o + 16:o + 16 + size]; o += 16 + size; o = (o + 15) & ~15
    lbl = sec["LBL1"]; ng = struct.unpack(E + "I", lbl[:4])[0]; labels = {}
    for g in range(ng):
        c, off = struct.unpack(E + "II", lbl[4 + g * 8:12 + g * 8])
        for _ in range(c):
            ln = lbl[off]; name = lbl[off + 1:off + 1 + ln].decode(); idx = struct.unpack(E + "I", lbl[off + 1 + ln:off + 5 + ln])[0]
            labels[idx] = name; off += 5 + ln
    atr = sec.get("ATR1", b""); attrs = {}
    if atr:
        c, esz = struct.unpack(E + "II", atr[:8])
        for i in range(c): attrs[i] = atr[8 + i * esz:8 + (i + 1) * esz]
    txt = sec["TXT2"]; c = struct.unpack(E + "I", txt[:4])[0]; texts = {}
    offs = struct.unpack(E + "%dI" % c, txt[4:4 + 4 * c])
    for i in range(c):
        end = offs[i + 1] if i + 1 < c else len(txt)
        texts[i] = txt[offs[i]:end]
    return {i: {"label": labels.get(i), "attr": attrs.get(i), "text": texts[i]} for i in range(c)}
