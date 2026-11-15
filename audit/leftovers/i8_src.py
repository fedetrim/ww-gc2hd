#!/usr/bin/env python3
"""Item 8, source side: in the HD source of the units that are stubs on the GameCube, the lines that touch a
save structure by member name or address without an accessor call.

Inputs:  research/out/machine-code/stubs.json; wwhd clone: wwhd_src/**/UNIT.cpp and UNIT_*.cpp
Output:  text on stdout; the audit kept it as i8_src.txt.
Run:     python3 -I audit/leftovers/i8_src.py > research/out/leftovers/i8_src.txt

Limit: a text search with two fixed patterns (member names seen in wwhd_src at commit a13ed11).
"""
import sys, os, re, json, glob
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
SRC = os.path.join(auditenv.WWHD, "wwhd_src")
stubs = sorted({os.path.basename(k)[:-4] for k in json.load(open(auditenv.out_file("machine-code", "stubs.json")))})
pat = re.compile(r"mSavedata|mPlayerStatus|mSave\b|mSave\.|l_save|saveInfo|SaveInfo|dComIfGs_ea|mMemory|mTmp\b|mDan\b|mZone|mRestart|mEvent\b|0x101F84DC|101F84DC|mItemMax|mItemRecord|mBagItem|mCollect\b|mPlayer\.")
acc = re.compile(r"(isEventBit|onEventBit|offEventBit|getEventReg|setEventReg|isSwitch|onSwitch|offSwitch|revSwitch|isTbox|onTbox|isItem|onItem|isActor|onActor|DungeonItem|isSymbol|isTact|isCollect|onCollect|checkGetItem|isReserve|checkReserveItem|setReserveItemEmpty|checkBottle|isBeast|isVisitedRoom|onVisitedRoom|isStageBoss|onStageBoss|isStageTbox|isTriforce|TmpBit|isGetBottleItem|isGetItem|setBottleItem|setEmptyBottle|checkEmptyBottle|StageLife|getClearCount)\w*\s*\(")
for u in stubs:
    fs = glob.glob(SRC + "/**/" + u + ".cpp", recursive=True) + glob.glob(SRC + "/**/" + u + "_*.cpp", recursive=True)
    hits = []
    for f in fs:
        for i, l in enumerate(open(f, errors="replace").read().split("\n")):
            s = l.strip()
            if not pat.search(s) or s.startswith(("ext ", "//", "extern", "data ", "*", "/*", "static inline", "inline", "#")): continue
            if acc.search(s): continue
            hits.append("%s:%d: %s" % (os.path.relpath(f, SRC), i + 1, s[:170]))
    if hits:
        print("== %s (%d)" % (u, len(hits)))
        for h in hits: print("   " + h)
