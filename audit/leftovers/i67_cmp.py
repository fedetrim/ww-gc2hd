#!/usr/bin/env python3
"""Items 6-7, messages: compare every message both games have (same id): price, next message, the control tags
that carry meaning (choices, item/number insertions; pure timing tags are dropped) and the numbers written in
the text. Then lists the ids only one game has and every priced message with both prices.

Inputs:  GameCube disc image: /res/Msg/bmgres.arc (zel_00.bmg)
         extracted Wind Waker HD: content/Common/Pack/permanent_2d_UsEnglish.pack
Output:  text on stdout; the audit kept it as i67_cmp.txt (this is where the 25 changed prices come from).
Run:     python3 -I audit/leftovers/i67_cmp.py > research/out/leftovers/i67_cmp.txt

Limit: the GameCube -> HD tag mapping (gmap/hmap) covers the tag groups seen in the common messages; a tag
outside it is ignored on both sides. English text only.
"""
import os, sys, struct, collections, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import i67_msglib as L
from i67_tags import gc_tok, hd_tok, load
g, h = load()
def gmap(x):
    grp, i = x[1], x[2]
    if grp == 0:
        if i == 0: return (2, 0)
        if 3 <= i <= 6: return (1, i - 1)      # waits etc (with arg)
        if i in (8, 9): return (1, i - 1)      # choices
        if 32 <= i <= 38: return (2, i - 31)
        if i in (40, 41): return (2, i - 32)
        if 43 <= i <= 56: return (2, i - 33)
        if 59 <= i <= 74: return (2, i - 35)
        return None
    return None
def hmap(x):
    if x[0] != "H": return None
    if x[1] == 2: return (2, x[2])
    if x[1] == 1 and x[2] in (2, 3, 4, 5, 7, 8): return (1, x[2])
    return None
def nums(toks):
    s = " ".join(t[1] for t in toks if t[0] == "T")
    return re.findall(r"\d+", s.replace(",", ""))
def plain(toks): return re.sub(r"\s+", " ", "".join(t[1] for t in toks if t[0] == "T")).strip()
ids = sorted(set(g) & set(h))
print("== common ids:", len(ids), " GC-only:", len(set(g) - set(h)), " HD-only:", len(set(h) - set(g)))
np = nn = nt = nnum = 0
for mid in ids:
    for k, (a, b) in enumerate(zip(g[mid], h[mid])):
        at = b["attr"]; hp, hn = struct.unpack(">hH", at[4:8])
        ta, tb = gc_tok(a["text"]), hd_tok(b["text"])
        sa = collections.Counter(filter(None, (gmap(x) for x in ta if x[0] == "G")))
        sb = collections.Counter(filter(None, (hmap(x) for x in tb)))
        # waits (1,2..5) are timing only: drop from semantic compare
        for c in (sa, sb):
            for key in [k2 for k2 in c if k2[0] == 1 and k2[1] in (2, 3, 4, 5)]: del c[key]
        d = []
        if a["price"] != hp: d.append("PRICE GC %d HD %d" % (a["price"], hp)); np += 1
        if a["next"] != hn: d.append("NEXT GC %d HD %d" % (a["next"], hn)); nn += 1
        if sa != sb: d.append("TAGS GC %s HD %s" % (sorted(sa.items()), sorted(sb.items()))); nt += 1
        if nums(ta) != nums(tb): d.append("NUMS GC %s HD %s" % (nums(ta), nums(tb))); nnum += 1
        if d:
            print("%5d (0x%04X) %s" % (mid, mid, " | ".join(d)))
            print("       GC: %s\n       HD: %s" % (plain(ta)[:230], plain(tb)[:230]))
    if len(g[mid]) != len(h[mid]): print("%5d duplicate count GC %d HD %d" % (mid, len(g[mid]), len(h[mid])))
print("== totals price %d next %d tags %d nums %d" % (np, nn, nt, nnum))
print("== GC-only ids")
for mid in sorted(set(g) - set(h)):
    a = g[mid][0]; print("%5d price %d next %d  %s" % (mid, a["price"], a["next"], plain(gc_tok(a["text"]))[:150]))
print("== HD-only ids")
for mid in sorted(set(h) - set(g)):
    b = h[mid][0]; hp, hn = struct.unpack(">hH", b["attr"][4:8]); t = hd_tok(b["text"])
    print("%5d price %d next %d tags %s  %s" % (mid, hp, hn, sorted({x[1:3] for x in t if x[0] == "H" and x[1] in (1, 2)}), plain(t)[:150]))
print("== all priced messages (GC price / HD price)")
for mid in sorted(set(g) | set(h)):
    gp = g[mid][0]["price"] if mid in g else None
    hp = struct.unpack(">h", h[mid][0]["attr"][4:6])[0] if mid in h else None
    if gp or hp: print("%5d GC %s HD %s%s" % (mid, gp, hp, "" if gp == hp else "   <<< DIFF"))
