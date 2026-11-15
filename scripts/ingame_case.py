#!/usr/bin/env python3
"""Build a test save for one case: convert a GameCube file with chosen answers, put it in Quest Log 1 and
start it at a given place.

usage: ingame_case.py SAVE.gci FILE(1-3) OUT/cking.sav STAGE ROOM POINT [all=steps|rewards] [CASE=steps|rewards ...]
CASE is an Options field: floor50, marie, lenzo, pawprint_chest, horseshoe_chest, star_belt_chest,
triforce_chart_2/4/6/7/8. `all` (default steps) answers the cases not named."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wwsave import convert as conv, gc, hd
src, slot, out, stage, room, point = sys.argv[1:7]
slot = int(slot) - 1
kw = dict(a.split("=") for a in sys.argv[7:])
mode = kw.pop("all", "steps")
card = gc.load(open(src, "rb").read())
f, reports = conv.convert(card, conv.Options.all(mode, **kw))
for c in reports[slot].changes: print("changed:", c)
if slot:
    f.slots[0], f.slots[slot] = f.slots[slot], f.slots[0]
    f.extras[0], f.extras[slot] = f.extras[slot], f.extras[0]
s = f.slots[0]
s.set_raw("return_place.stage", stage.encode().ljust(8, b"\0"))
s.set_u("return_place.room", int(room)); s.set_u("return_place.point", int(point))
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "wb").write(f.serialize())
