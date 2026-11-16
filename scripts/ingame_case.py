#!/usr/bin/env python3
"""Build a test save for one case: convert a GameCube file with chosen answers, put it in Quest Log 1 and
start it at a given place.

usage: ingame_case.py SAVE.gci FILE(1-3) OUT/cking.sav STAGE ROOM POINT [all=steps|rewards] [CASE=steps|rewards ...]
CASE is an Options field: floor50, marie, lenzo, pawprint_chest, horseshoe_chest, star_belt_chest,
triforce_chart_2/4/6/7/8. `all` (default steps) answers the cases not named.
OUT is a folder for test saves: its cking.sav is replaced and its cking_pic*.sav files are removed without a
backup. Do not point it at a save you want to keep."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wwsave import convert as conv, gc
src, slot, out, stage, room, point = sys.argv[1:7]
slot = int(slot) - 1
kw = dict(a.split("=", 1) for a in sys.argv[7:] if "=" in a)
mode = kw.pop("all", "steps")
bad = [a for a in sys.argv[7:] if "=" not in a] + [
    "%s=%s" % (k, v) for k, v in kw.items() if k not in conv.Options.CASES or v not in conv.MODES]
if bad or mode not in conv.MODES:
    sys.exit("not a case answer: %s\ncases: %s; answers: steps, rewards" % (
        ", ".join(bad) or "all=" + mode, ", ".join(conv.Options.CASES)))
print("cases not named are answered by %s" % mode)
card = gc.load(open(src, "rb").read())
f, reports = conv.convert(card, conv.Options.all(mode, **kw))
if reports[slot].unhealthy or not reports[slot].used:
    sys.exit("file %d of %s is not converted (%s): there is nothing to test" % (
        slot + 1, src, "; ".join(reports[slot].unhealthy) or "unused or unreadable"))
for c in reports[slot].changes: print("changed:", c)
if slot:
    f.move_to_quest_log_1(slot)
s = f.slots[0]
s.set_raw("return_place.stage", stage.encode().ljust(8, b"\0"))
s.set_u("return_place.room", int(room)); s.set_u("return_place.point", int(point))
folder = os.path.dirname(os.path.abspath(out))
os.makedirs(folder, exist_ok=True)
with open(out, "wb") as fh:
    fh.write(f.serialize())
# The rig copies the album files next to the save into the game: leave there only the album of the file
# under test, named for Quest Log 1, where the file now is.
old = [name for name in os.listdir(folder) if name.startswith("cking_pic") and name.endswith(".sav")]
for name in old:
    os.remove(os.path.join(folder, name))
if old:
    print("removed %d album file(s) of an earlier save from %s" % (len(old), folder))
for name, data in conv.convert_pictures(card).items():
    prefix = "cking_pic_order%d" % slot if name.startswith("cking_pic_order") else "cking_pic%d_" % slot
    if name.startswith(prefix):
        with open(os.path.join(folder, name.replace(prefix, prefix[:-2] + "0_" if prefix.endswith("_") else
                                                    "cking_pic_order0", 1)), "wb") as fh:
            fh.write(data)
