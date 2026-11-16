#!/usr/bin/env python3
"""Items 6-7, messages: tokenizers for the control tags of GameCube (0x1A escapes) and HD (0x0E / 0x0F tags)
message text, and load() returning both message sets by id. Run by itself it prints the tag inventory of
both games and how the tags pair up in messages with the same number of tags (this is how the tag mapping in
i67_cmp.py was derived).

Inputs:  GameCube disc image, extracted Wind Waker HD (through i67_msglib.py)
Output:  text on stdout.
Run:     python3 -I audit/leftovers/i67_tags.py
"""
import os, sys, struct, collections, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import i67_msglib as L
def gc_tok(t):
    out, s, p = [], bytearray(), 0
    while p < len(t):
        if t[p] == 0x1A:
            n = t[p + 1]; b = t[p + 2:p + n]
            if s: out.append(("T", s.decode("cp1252", "replace"))); s = bytearray()
            out.append(("G", b[0], b[1] << 8 | b[2], bytes(b[3:]).hex())); p += n
        else:
            s.append(t[p]); p += 1
    if s: out.append(("T", s.decode("cp1252", "replace")))
    return out
def hd_tok(t):
    out, s, p = [], [], 0
    n = len(t) // 2; u = struct.unpack(">%dH" % n, t[:n * 2])
    while p < n:
        c = u[p]
        if c == 0x0E:
            g, ty, sz = u[p + 1], u[p + 2], u[p + 3]
            if s: out.append(("T", "".join(map(chr, s)))); s = []
            out.append(("H", g, ty, t[(p + 4) * 2:(p + 4) * 2 + sz].hex())); p += 4 + sz // 2
        elif c == 0x0F:
            if s: out.append(("T", "".join(map(chr, s)))); s = []
            out.append(("HE", u[p + 1], u[p + 2], "")); p += 3
        elif c == 0: break
        else: s.append(c); p += 1
    if s: out.append(("T", "".join(map(chr, s))))
    return out
def load():
    g = L.gc_msgs(L.G.rarc_files(L.gc_file("/res/Msg/bmgres.arc"))["zel_00.bmg"]); h = {}
    for n, d in L.hd_packs().items():
        if n.startswith("message"):
            for i, m in L.msbt(d).items(): h.setdefault(int(m["label"]), []).append(dict(m, set=n))
    return g, h
if __name__ == "__main__":
    g, h = load()
    cg, ch, pair = collections.Counter(), collections.Counter(), collections.Counter()
    exg, exh = {}, {}
    for mid in sorted(set(g) & set(h)):
        a = [x for x in gc_tok(g[mid][0]["text"]) if x[0] != "T"]; b = [x for x in hd_tok(h[mid][0]["text"]) if x[0] != "T"]
        for x in a: cg[x[1:3]] += 1; exg.setdefault(x[1:3], (mid, x[3]))
        for x in b: ch[x[:3]] += 1; exh.setdefault(x[:3], (mid, x[3]))
        if len(a) == len(b):
            for x, y in zip(a, b): pair[(x[1:3], y[:3])] += 1
    print("GC tags"); [print("  ", k, v, exg[k]) for k, v in sorted(cg.items())]
    print("HD tags"); [print("  ", k, v, exh[k]) for k, v in sorted(ch.items())]
    print("pairs"); [print("  ", k, v) for k, v in sorted(pair.items())]
