#!/usr/bin/env python3
"""Item 1, step 3: source context of each funcdiff pair, both games: the lines of the GameCube source and of
the HD source that use the flag, with W lines around each and the enclosing function. This is what was read
to classify the 99 pairs (renamed/inlined, code change with the same meaning, known difference).

Inputs:  research/out/leftovers/i1_sites.txt
         zeldaret/tww clone: include/d/d_save_event_flag.inc, src/**/UNIT.{cpp,inc}; wwhd clone: wwhd_src
Output:  text on stdout; the audit kept it as i1_ctx.txt (about 200 KB).
Run:     python3 -I audit/leftovers/i1_ctx.py [UNIT_SUBSTRING] [W]        (W defaults to 4)
         python3 -I audit/leftovers/i1_ctx.py "" 3 > research/out/leftovers/i1_ctx.txt     (all units; what the audit kept)

Limit: a unit that is a stub on the GameCube has no source to show ("GC no source match"); for those the
GameCube side was read as disassembly (audit/machine-code/gcdis.py).
"""
import sys, os, re, glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auditenv  # noqa: E402
R = auditenv.RES
flt = sys.argv[1] if len(sys.argv) > 1 else ""
W = int(sys.argv[2]) if len(sys.argv) > 2 else 4
def files_gc(u):
    return glob.glob(auditenv.TWW + "/src/**/" + u + ".cpp", recursive=True) + glob.glob(auditenv.TWW + "/src/**/" + u + ".inc", recursive=True)
def show(path, rx, label):
    L = open(path, errors="replace").read().split("\n")
    hits = [i for i, l in enumerate(L) if rx.search(l)]
    if not hits: return 0
    # find enclosing function header (last non-indented line w/ '(' before)
    done = -1
    for h in hits:
        fn = ""
        for j in range(h, -1, -1):
            if L[j] and not L[j][0] in " \t}/#" and "(" in L[j]: fn = L[j].strip(); break
        print("   --%s %s:%d  in [%s]" % (label, os.path.relpath(path, R), h + 1, fn[:90]))
        for j in range(max(done + 1, h - W), min(len(L), h + W + 1)):
            print("     %5d%s %s" % (j + 1, ">" if j == h else " ", L[j][:170]))
        done = h + W
    return len(hits)
NAMES = {}
for m in re.finditer(r"(\w+) = 0x([0-9A-Fa-f]{4})", open(auditenv.TWW + "/include/d/d_save_event_flag.inc").read()):
    NAMES.setdefault(m.group(2).upper(), []).append(m.group(1))
cur = None
lines = open(auditenv.out_file("leftovers", "i1_sites.txt")).read().split("\n")
i = 0
while i < len(lines):
    if lines[i].startswith("##"):
        _, u, acc, fl = lines[i].split()
        gc, hd = lines[i + 1], lines[i + 2]
        i += 3
        if flt not in u: continue
        print("=" * 100); print(u, acc, fl); print(gc[:400]); print(hd[:400])
        a = acc.split(":")[-1]
        v = fl.split(",")[0]
        if "Event" in a:
            rx = re.compile(r"(0x0*%s\b|_%s\b|%s)" % (v, v.zfill(4), "|".join(r"\b" + n + r"\b" for n in NAMES.get(v.zfill(4).upper(), ["@@@"]))), re.I)
        elif a in ("checkGetItem", "checkBottle", "isSymbol", "isItem", "onCollect", "checkReserveItem", "isReserve", "isStageBossEnemy", "onStageBossEnemy", "isDungeonItem", "onDungeonItem", "isStageTbox"):
            alt = {"onDungeonItem": "onDungeonItem|onStageBossEnemy|onStageLife", "isDungeonItem": "isDungeonItem|isStageBossEnemy|isStageLife|isStageMap|isStageCompass|isStageBossKey", "isItem":"isItem|isGetItem|checkGetItem"}.get(a, a)
            rx = re.compile(r"(%s)" % alt)
        else:
            rx = re.compile(r"%s\w*\(\s*(0x0*%s\b|%d\b)" % (a, v, int(v, 16)), re.I)
        n = 0
        for f in files_gc(u): n += show(f, rx, "GC")
        if not n: print("   --GC no source match")
        hf = sorted(set(re.findall(r"@\w+ (\S+)", hd)))
        n = 0
        for f in hf: n += show(auditenv.WWHD + "/wwhd_src/" + f, rx, "HD")
        if not n: print("   --HD no source match")
    else: i += 1
