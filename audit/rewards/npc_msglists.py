#!/usr/bin/env python3
"""Compare every numeric table `static u32/u16/int NAME[] = {...}` of a GameCube actor source (USA build,
`#if VERSION` blocks evaluated) with the bytes of the HD binary at the address the HD source assigns to the
same name (`data NAME ADDR` lines and WWHD_OFFSET struct members).

Inputs:  the GameCube source path given as argument (a file of the zeldaret/tww clone); wwhd clone:
         wwhd_src/d/actor/PREFIX*.cpp and wwhd_src/include/d/actor/PREFIX*.h; cking.rpx; zeldaret/tww
         include/d/d_save.h and d_item_data.h
Output:  text on stdout: DIFF blocks, then the totals and the names with no HD address.
Run:     python3 -I audit/rewards/npc_msglists.py research/tww/src/d/actor/d_a_npc_people.cpp d_a_npc_people

Limit: only tables whose every element resolves to a number are compared, and only those the HD source
names; the rest is listed as "no address".
"""
import glob, os, re, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
ROOT = auditenv.WWHD
import npc_mem
import npc_seqdiff_consts as C
VER = {"VERSION_DEMO": 0, "VERSION_JPN": 1, "VERSION_USA": 2, "VERSION_PAL": 3, "VERSION": 2}
def preprocess(text):
    out = []; stack = []
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("#if "):
            e = s[4:]
            for k in sorted(VER, key=len, reverse=True): e = re.sub(r"\b%s\b" % k, str(VER[k]), e)
            try: v = bool(eval(e.replace("||", " or ").replace("&&", " and ").replace("!", " not ").replace(" not =", "!=")))
            except Exception: v = True
            stack.append([v, v]); continue
        if s.startswith("#ifdef") or s.startswith("#ifndef"): stack.append([True, True]); continue
        if s.startswith("#elif"):
            e = s[5:]
            for k in sorted(VER, key=len, reverse=True): e = re.sub(r"\b%s\b" % k, str(VER[k]), e)
            v = bool(eval(e.replace("||", " or ").replace("&&", " and "))) and not stack[-1][1]
            stack[-1][0] = v; stack[-1][1] = stack[-1][1] or v; continue
        if s.startswith("#else"): stack[-1][0] = not stack[-1][1]; continue
        if s.startswith("#endif"): stack.pop(); continue
        if all(x[0] for x in stack): out.append(line)
    return "\n".join(out)
gc = preprocess(open(sys.argv[1], errors="replace").read())
tables = {}
for m in re.finditer(r"static\s+(?:const\s+)?(u32|u16|s16|int|s32|u8|s8)\s+(\w+)\[\w*\]\s*=\s*\{([^}]*)\}", gc):
    typ, name, body = m.groups()
    vals = []
    ok = True
    for tok in body.split(","):
        tok = re.sub(r"/\*.*?\*/|//.*", "", tok).strip()
        if not tok: continue
        v = C.value(tok)
        if v is None: ok = False; break
        vals.append(v)
    if ok: tables[name] = (typ, vals)
# HD addresses
addr = {}
pref = sys.argv[2]
for p in glob.glob(os.path.join(ROOT, "wwhd_src/d/actor/%s*.cpp" % pref)) + glob.glob(os.path.join(ROOT, "wwhd_src/include/d/actor/%s*.h" % pref)):
    t = open(p, errors="replace").read()
    for m in re.finditer(r"^data (\w+) ([0-9A-F]{8})", t, re.M): addr.setdefault(m.group(1), int(m.group(2), 16))
    bases = dict((m.group(1), int(m.group(2), 16)) for m in re.finditer(r"object_at<(\w+)>\((0x[0-9A-Fa-f]+)\)", t))
    for m in re.finditer(r"WWHD_OFFSET\((\w+),\s*(\w+),\s*(0x[0-9A-Fa-f]+)\)", t):
        if m.group(1) in bases: addr.setdefault(m.group(2), bases[m.group(1)] + int(m.group(3), 16))
SZ = {"u32": 4, "int": 4, "s32": 4, "u16": 2, "s16": 2, "u8": 1, "s8": 1}
same = diff = noaddr = 0
missing = []
for name, (typ, vals) in tables.items():
    if name not in addr: noaddr += 1; missing.append(name); continue
    sz = SZ[typ]
    raw = npc_mem.hd(addr[name], sz * len(vals))
    hv = [int.from_bytes(raw[i * sz:(i + 1) * sz], "big") for i in range(len(vals))]
    gv = [v & ((1 << (8 * sz)) - 1) for v in vals]
    if hv == gv: same += 1
    else:
        diff += 1
        print("DIFF %s @%08X\n   GC %s\n   HD %s" % (name, addr[name], " ".join("%X" % v for v in gv), " ".join("%X" % v for v in hv)))
print("tables parsed %d: identical at HD address %d, different %d, no HD address known %d" % (len(tables), same, diff, noaddr))
print("no address:", " ".join(missing))
