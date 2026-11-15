#!/usr/bin/env python3
"""Item 1, step 2: for each funcdiff pair, compare the GameCube machine-code functions that use the flag with
the HD *source* functions that contain the constant (by number or by its name in d_save_event_flag.inc).
SAMEFUNCS means the HD source uses the flag in functions of the same names, i.e. the difference in the HD
machine code is inlining or renaming; CHECK means the pair has to be read (i1_ctx.py).

Inputs:  research/out/leftovers/i1_sites.txt (i1_sites.py)
         zeldaret/tww clone: include/d/d_save_event_flag.inc; wwhd clone: wwhd_src (the files named in
         the HD call sites)
Output:  text on stdout; the audit kept it as i1_auto.txt.
Run:     python3 -I audit/leftovers/i1_auto.py > research/out/leftovers/i1_auto.txt

Limit: only event bit/register accessors are classified automatically; every other accessor is CHECK.
"""
import sys, os, re, glob, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auditenv  # noqa: E402
NAMES = {}
for m in re.finditer(r"(\w+) = 0x([0-9A-Fa-f]{4})", open(auditenv.TWW + "/include/d/d_save_event_flag.inc").read()):
    NAMES.setdefault(m.group(2).upper(), []).append(m.group(1))
def gname(w):
    n = w.split("@")[0]
    n = re.sub(r"__(Q\d)?\d+.*$", "", n); n = re.sub(r"__F.*$", "", n)
    return n.lower().lstrip("_")
def srcfuncs(path, rx):
    L = open(path, errors="replace").read().split("\n"); out = collections.Counter()
    for h, l in enumerate(L):
        if not rx.search(l) or l.startswith("ext ") or l.lstrip().startswith("//"): continue
        fn = "?"
        for j in range(h, -1, -1):
            if L[j] and not L[j][0] in " \t}/#" and "(" in L[j]:
                fn = re.sub(r"^.*?([\w:~]+)\s*\(.*$", r"\1", L[j].strip()).split("::")[-1].lower().lstrip("_"); break
        out[fn] += 1
    return out
lines = open(auditenv.out_file("leftovers", "i1_sites.txt")).read().split("\n")
i = 0
while i < len(lines):
    if not lines[i].startswith("##"): i += 1; continue
    _, u, acc, fl = lines[i].split(); gc, hd = lines[i + 1], lines[i + 2]; i += 3
    a = acc.split(":")[-1]; v = fl.split(",")[0]
    if "Event" in a:
        rx = re.compile(r"(0x0*%s\b|_%s\b|%s)" % (v, v.zfill(4), "|".join(r"\b" + n + r"\b" for n in NAMES.get(v.zfill(4).upper(), ["@@@"]))), re.I)
    else:
        rx = None
    g = collections.Counter(gname(w) for w in gc[6:].split(" ; ") if w)
    hm = collections.Counter(w.split("@")[0].split("::")[-1].lower().lstrip("_") for w in hd[6:].split(" ; ") if w)
    hs = collections.Counter()
    if rx:
        for f in sorted(set(re.findall(r"@\w+ (\S+)", hd))): hs += srcfuncs(auditenv.WWHD + "/wwhd_src/" + f, rx)
    same = rx and set(g) == set(hs)
    print("%-16s %-14s %-5s %s\n      GC %s\n      HDm %s\n      HDs %s" % (u, acc.split("::")[-1], fl, "SAMEFUNCS" if same else "CHECK", dict(g), dict(hm), dict(hs)))
