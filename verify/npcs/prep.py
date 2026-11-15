#!/usr/bin/env python3
"""prep.py SAVE.gci FILE(1-3) OUT/cking.sav STAGE ROOM POINT [opt=val ...] [flags]

Converts like scripts/ingame_case.py (all=steps|rewards plus per-case options, e.g. marie=rewards), puts the
file in Quest Log 1 at STAGE/ROOM/POINT, then applies test-only edits to the HD file:
  --pendant-button   put the Joy Pendant bag slot on item button X (adds nothing)
  --add-pendant      add one Joy Pendant when the file has none (so there is something to show)
  --camera-button    put the Picto Box slot on item button X
  --album            also write the converter's own album files for this file as Quest Log 1
                     (cking_pic0_*.sav, cking_pic_order0.sav next to OUT/cking.sav)
  --time HOURS       set the time of day
Prints the converter's changes and the relevant state of the converted file and of the GameCube file.

Inputs:  a GameCube save (the samples used are named in verify/README.md)
Outputs: OUT/cking.sav (and the album files with --album); text on stdout.
Run:     python3 verify/npcs/prep.py SAVE.gci 1 research/out/verify/npcs/NAME/cking.sav Nitiyou 0 0 \
             all=rewards --pendant-button --time 12
         (run_marie.sh and run_lenzo.sh call it)
"""
import os, struct, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from wwsave import convert as conv, gc, hd, layout

args = sys.argv[1:]
flags = {}
pos = []
i = 0
while i < len(args):
    if args[i] == "--pendant-button": flags["pendant"] = True
    elif args[i] == "--time": flags["time"] = float(args[i + 1]); i += 1
    elif args[i] == "--camera-button": flags["camera"] = True
    elif args[i] == "--add-pendant": flags["add"] = True
    elif args[i] == "--album": flags["album"] = True
    else: pos.append(args[i])
    i += 1
src, slot, out, stage, room, point = pos[:6]
slot = int(slot) - 1
kw = dict(a.split("=") for a in pos[6:])
mode = kw.pop("all", "steps")
card = gc.load(open(src, "rb").read())
gslot = slot
f, reports = conv.convert(card, conv.Options.all(mode, **kw))
for c in reports[slot].changes: print("changed:", c)
if slot:
    f.move_to_quest_log_1(slot)
s = f.slots[0]
s.set_raw("return_place.stage", stage.encode().ljust(8, b"\0"))
s.set_u("return_place.room", int(room)); s.set_u("return_place.point", int(point))
if flags.get("add") and 0x1F not in s.raw("bag_item.beast"):     # test-only: one Joy Pendant to show
    bag = bytearray(s.raw("bag_item.beast")); n = bytearray(s.raw("bag_item_record.beast_num"))
    bag[bag.index(0xFF)] = 0x1F; n[7] = 1
    s.set_raw("bag_item.beast", bytes(bag)); s.set_raw("bag_item_record.beast_num", bytes(n))
    s.set_u("get_bag_item.beast_flags", s.u("get_bag_item.beast_flags") | 0x80)
    print("test edit: one Joy Pendant added")
if flags.get("pendant"):
    bag = s.raw("bag_item.beast")
    assert 0x1F in bag, "no Joy Pendant in the Spoils Bag"
    sel = bytearray(s.raw("status_a.select_item"))
    sel[0] = 24 + bag.index(0x1F)
    s.set_raw("status_a.select_item", bytes(sel))
if flags.get("camera"):
    sel = bytearray(s.raw("status_a.select_item"))
    sel[0] = layout.SLOT_CAMERA
    s.set_raw("status_a.select_item", bytes(sel))
if "time" in flags:
    s.set_raw("status_b.time", struct.pack(">f", flags["time"] * 15.0))
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "wb").write(f.serialize())
if flags.get("album"):      # the converter's own album files for this file, as Quest Log 1
    import re
    for name, data in conv.convert_pictures(card).items():
        m = re.match(r"cking_pic(_order)?(\d)(.*)", name)
        if int(m.group(2)) == gslot:
            open(os.path.join(os.path.dirname(out), "cking_pic%s0%s" % (m.group(1) or "", m.group(3))), "wb").write(data)
    from wwsave import picture
    recs, order, count = picture.parse_order(open(os.path.join(os.path.dirname(out), "cking_pic_order0.sav"), "rb").read())
    print("album: count %d order %s subjects %s" % (count, order[:count], [r[4] for r in recs[:count]]))
def state(tag, x):
    print("%s: pendants %d bag %s sel %s 1C04 %d 1C08 %d 1E04 %d C0FF %d chart45 %d C407 %d slot8 %02X get8 %02X charm %s time %s rupee %d" % (
        tag, x.raw("bag_item_record.beast_num")[7], x.raw("bag_item.beast").hex(), x.raw("status_a.select_item").hex(),
        x.event_bit(0x1C04), x.event_bit(0x1C08), x.event_bit(0x1E04), x.event_reg(0xC0FF),
        conv._map_bit(x, "map.get_map", 7), x.event_reg(0xC407), x.raw("item.slot08")[0], x.raw("get_item.slot08")[0],
        x.raw("collect.collect").hex(), struct.unpack(">f", x.raw("status_b.time"))[0], x.u("status_a.rupee")) + " picture_num %d ev1701 %d ev1601 %d" % (x.raw("item_record.picture_num")[0], x.event_bit(0x1701), x.event_bit(0x1601)))
state("hd", s)
try:
    gs = card.slots()[gslot]
    gs = gs if hasattr(gs, "raw") else layout.Save(gs)
    state("gc", gs)
except Exception as e: print("gc state:", e)
