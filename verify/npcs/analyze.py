#!/usr/bin/env python3
"""analyze.py CASE_DIR [SI_FILE]

Compares CASE_DIR/cking.sav (Quest Log 1) with the game's save block dumped at the end of the run
(CASE_DIR/run/si.bin) and prints the fields the Mrs. Marie and Lenzo rules are about, every other field
that differs (event flags byte by byte) and whether the log shows a halt.

Inputs:  a case folder produced by scripts/ingame_test.py (run_marie.sh, run_lenzo.sh)
Output:  text on stdout.
Run:     python3 verify/npcs/analyze.py research/out/verify/npcs/marie-rewards-A
"""
import os, struct, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
from wwsave import hd, layout, convert as conv
import ingame_test as it
case = sys.argv[1]
src = hd.HdFile.parse(open(os.path.join(case, "cking.sav"), "rb").read()).slots[0]
si = sys.argv[2] if len(sys.argv) > 2 else os.path.join(case, "run", "si.bin")
mem = open(si, "rb").read()
game = layout.Save(bytearray(src.data))
for name, (off, size) in layout.FIELDS.items():
    block = name.split(".")[0]
    boff, _ = layout.BLOCKS[block]
    a = 0x20 + it.MEM[block] + off - boff
    game.data[off:off + size] = mem[a:a + size]
def state(x):
    return dict(joy_pendants=x.raw("bag_item_record.beast_num")[7], ev_1C04=int(x.event_bit(0x1C04)),
                reg_C0FF=x.event_reg(0xC0FF), chart45=int(conv._map_bit(x, "map.get_map", 7)),
                reg_C407=x.event_reg(0xC407), slot8="%02X" % x.raw("item.slot08")[0],
                get8="%02X" % x.raw("get_item.slot08")[0], collect=x.raw("collect.collect").hex(),
                rupees=x.u("status_a.rupee"), max_life=x.u("status_a.max_life"), buttons=x.raw("status_a.select_item").hex())
a, b = state(src), state(game)
for k in a: print("  %-13s file %-18s game %-18s %s" % (k, a[k], b[k], "" if a[k] == b[k] else "<-- changed"))
print("  other fields that differ:")
for name, (off, size) in layout.FIELDS.items():
    x, y = src.data[off:off + size], game.data[off:off + size]
    if x == y or name in it.VOLATILE: continue
    if name == "event.flags":
        for i in range(size):
            if x[i] != y[i]: print("     event byte 0x%02X: %02X -> %02X" % (i, x[i], y[i]))
    else:
        print("     %-28s %s -> %s" % (name, bytes(x).hex(), bytes(y).hex()))
log = open(os.path.join(case, "run", "log"), errors="replace").read()
bad = [l for l in log.splitlines() if any(k in l.lower() for k in ("halt", "crash", "assert", "fatal"))]
print("  reached the end of the scenario:", os.path.exists(os.path.join(case, "run", "test_done")), "| halt/crash/assert lines in log:", len(bad))
for l in bad[:5]: print("     ", l[:200])
