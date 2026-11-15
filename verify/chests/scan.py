#!/usr/bin/env python3
"""scan.py: which GameCube saves are in each chest case (state before conversion). Used to pick the sample a
case is run on.

Inputs:  every file under samples/gc/, plus any GameCube save (.gci, .gcs, .sav, raw memory card image)
         given as argument
Output:  text on stdout, one line per file of a card that is in at least one case: the cases, maximum
         life, the items on the buttons and the stage the file returns to.
Run:     python3 verify/chests/scan.py [SAVE ...]
"""
import sys, os, glob
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from wwsave import convert as conv, gc
paths = sorted(p for p in glob.glob(os.path.join(ROOT, "samples/gc/**/*"), recursive=True) if os.path.isfile(p))
paths += [os.path.abspath(os.path.expanduser(p)) for p in sys.argv[1:]]
for p in paths:
    try:
        cards = gc.load_all(open(p, "rb").read())
    except Exception:
        continue
    for ci, card in enumerate(cards):
        for i, g in enumerate(card.slots()):
            if g is None: continue
            tags = []
            for k in conv.REUSED_CHARTS:
                if conv._map_bit(g, "map.get_map", k) and conv._stuck_chart(g, k): tags.append("chart%d" % k)
            rec, bits = conv.TRIFORCE_CHESTS[4]
            gs = [b for b in bits if conv._collected(g, ("tbox", rec, b))]
            if gs: tags.append("ghost%s/reg%d" % (gs, g.event_reg(0x8803) if hasattr(g, "event_reg") else -1))
            if conv._collected(g, ("tbox", 1, 26)): tags.append("horseshoe")
            if conv._collected(g, ("tbox", 1, 11)): tags.append("starbelt")
            if conv._collected(g, conv.PAWPRINT_CHEST): tags.append("pawprint")
            if conv._collected(g, conv.SAVAGE_FLOOR_50): tags.append("floor50")
            if g.event_bit(conv.MARIE_EVENT): tags.append("marie")
            if tags:
                sel = list(g.raw("status_a.select_item")[:3])
                print("%s #%d file %d: %s life %d sel %s stage %s" % (os.path.relpath(p, ROOT), ci, i + 1, " ".join(tags), g.u("status_a.max_life"), sel, g.raw("return_place.stage").split(b"\0")[0]))
