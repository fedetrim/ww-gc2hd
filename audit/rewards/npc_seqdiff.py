#!/usr/bin/env python3
"""Per function, the ordered sequence of save-accessor and item-giving calls in a GameCube source file against
the same functions of one or more HD source files, diffed. Finds a flag or item call that moved, appeared
or disappeared inside an NPC whose source exists on both sides.

Inputs:  the two source paths given as arguments (GameCube: a file of the zeldaret/tww clone; HD: one or
         more files of wwhd_src, comma-separated); zeldaret/tww clone: include/d/d_save.h,
         include/d/d_item_data.h (to turn names into numbers)
Output:  text on stdout: DIFF blocks per function (SAME lines with -v).
Run:     python3 -I audit/rewards/npc_seqdiff.py research/tww/src/d/actor/d_a_npc_ho.cpp \
             research/wwhd/wwhd_src/d/actor/d_a_npc_ho.cpp [-v]

Limit: a text comparison with regular expressions, no preprocessor; functions are matched by name; an
argument that is not a literal or a known constant shows as `?`. It is a reading aid, not a proof.
"""
import re, sys, os, difflib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auditenv  # noqa: E402
ROOT = auditenv.TWW
hdr = open(os.path.join(ROOT, "include/d/d_save.h"), errors="replace").read()
EV = {}
for m in re.finditer(r"\b([A-Z][A-Z0-9_]+)\s*=\s*(0x[0-9A-Fa-f]+)", hdr):
    EV.setdefault(m.group(1), int(m.group(2), 16))
ITEM = {}
for p in ("include/d/d_item_data.h",):
    t = open(os.path.join(ROOT, p), errors="replace").read()
    for m in re.finditer(r"\b(dItemNo_[A-Za-z0-9_]+)\s*=\s*(0x[0-9A-Fa-f]+)", t):
        ITEM[m.group(1)] = int(m.group(2), 16)
    # sequential enum fallback
    n = -1
    for m in re.finditer(r"^\s*(dItemNo_[A-Za-z0-9_]+)\s*(?:=\s*(0x[0-9A-Fa-f]+|\d+))?\s*,", t, re.M):
        n = int(m.group(2), 0) if m.group(2) else n + 1
        ITEM.setdefault(m.group(1), n)
CALL = re.compile(r"\b(dComIfGs_(?:on|off|is)EventBit|dComIfGs_(?:get|set)EventReg|dComIfGs_(?:on|off|is)TmpBit|dComIfGs_(?:get|set)TmpReg|dComIfGs_checkGetItem(?:Num)?|dComIfGs_isSymbol|dComIfGs_isGetItem\w*|dComIfGs_onGetItem\w*|dComIfGs_isCollect\w*|dComIfGs_\w*Reserve\w*|dComIfGs_\w*Beast\w*|dComIfGs_\w*Bait\w*|dComIfGs_\w*Bottle\w*|dComIfGs_set\w+|dComIfGs_on\w+|dComIfGp_setItem\w+|fopAcM_createItem\w*|\w*[cC]reateItem\w*|execItemGet|dComIfGp_event_setGtItm|isSwitch|onSwitch|offSwitch)\s*\(([^;{]*)")
def norm(arg):
    arg = arg.strip()
    arg = re.sub(r"/\*.*?\*/", "", arg)
    def r(m):
        k = m.group(0).split("::")[-1]
        if k.startswith("UNK_"): return "0x%04X" % int(k[4:], 16)
        if k in EV: return "0x%04X" % EV[k]
        if k in ITEM: return "0x%02X" % ITEM[k]
        return k
    arg = re.sub(r"(?:dSv_event_(?:tmp_)?flag_c::)?[A-Za-z_][A-Za-z0-9_:]*", r, arg)
    arg = re.sub(r"0x0*([0-9A-Fa-f]+)", lambda m: "0x%X" % int(m.group(1), 16), arg)
    m = re.match(r"\(?\s*(0x[0-9A-F]+|\d+)", arg)
    first = arg.split(",")[0].rstrip(") ")
    m = re.match(r"^(0x[0-9A-F]+|\d+)$", first)
    return ("0x%X" % int(first, 0)) if m else "?"
FN = re.compile(r"^[A-Za-z_].*?\b(\w+::\w+|\w+)\s*\([^;]*\)\s*(?:const\s*)?\{\s*$")
def parse(path):
    out = {}; cur = None
    for ln, line in enumerate(open(path, errors="replace"), 1):
        m = FN.match(line)
        if m and not line.startswith((" ", "\t", "}")):
            cur = m.group(1).split("::")[-1]; out.setdefault(cur, [])
        if cur is None: continue
        for c in CALL.finditer(line):
            nm = c.group(1).replace("people", "fopAcM_") if c.group(1).startswith("people") else c.group(1)
            out[cur].append(("%s(%s)" % (nm, norm(c.group(2))), ln))
        m2 = re.search(r"\b(mGetItemNo|m75C|mItemNo|m_item_no|mItem)\s*=\s*([^;]+);", line)
        if m2: out[cur].append(("ITEMVAR=%s" % norm(m2.group(2)), ln))
    return out
gc = parse(sys.argv[1]); hd = {}
for p in sys.argv[2].split(","):
    for k, v in parse(p).items(): hd.setdefault(k, []).extend(v)
verbose = "-v" in sys.argv
for fn in sorted(set(gc) | set(hd)):
    a = gc.get(fn, []); b = hd.get(fn, [])
    if not a and not b: continue
    sa = [x[0] for x in a]; sb = [x[0] for x in b]
    if sa == sb:
        if verbose: print("SAME %-28s %d tokens" % (fn, len(sa)))
        continue
    print("DIFF %s (GC %d, HD %d)%s" % (fn, len(sa), len(sb), "" if fn in gc and fn in hd else "  [one side only]"))
    sm = difflib.SequenceMatcher(None, sa, sb, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal": continue
        for x in a[i1:i2]: print("   - GC:%d %s" % (x[1], x[0]))
        for x in b[j1:j2]: print("   + HD:%d %s" % (x[1], x[0]))
