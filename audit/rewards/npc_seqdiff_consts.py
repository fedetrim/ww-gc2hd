#!/usr/bin/env python3
"""Resolve GameCube source constants (event flag names, item names) to numbers (module used by
npc_msglists.py; not run by itself).

Inputs:  zeldaret/tww clone: include/d/d_save.h, include/d/d_item_data.h
Output:  none.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auditenv  # noqa: E402
ROOT = auditenv.TWW
EV = {}; ITEM = {}
t = open(os.path.join(ROOT, "include/d/d_save.h"), errors="replace").read()
for m in re.finditer(r"\b([A-Z][A-Z0-9_]+)\s*=\s*(0x[0-9A-Fa-f]+)", t): EV.setdefault(m.group(1), int(m.group(2), 16))
t = open(os.path.join(ROOT, "include/d/d_item_data.h"), errors="replace").read()
n = -1
for m in re.finditer(r"^\s*(dItemNo_[A-Za-z0-9_]+)\s*(?:=\s*(0x[0-9A-Fa-f]+|\d+))?\s*,", t, re.M):
    n = int(m.group(2), 0) if m.group(2) else n + 1
    ITEM[m.group(1)] = n
def value(tok):
    tok = tok.strip()
    try: return int(tok, 0)
    except ValueError: pass
    k = tok.split("::")[-1]
    if k.startswith("UNK_"):
        try: return int(k[4:], 16)
        except ValueError: pass
    if k in EV: return EV[k]
    if k in ITEM: return ITEM[k]
    return None
