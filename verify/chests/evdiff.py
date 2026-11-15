#!/usr/bin/env python3
"""evdiff.py CASE...: every byte of the save block (0x768 bytes as saved) that differs between the save a case
loaded (CASE/cking.sav, Quest Log 1) and the game's memory at the end of the run (CASE/run/si.bin). The
clock/date block (status_b) and the return place are not compared.

Inputs:  research/out/verify/chests/CASE/ of cases already run with vc.py
Output:  text on stdout, one line per case: block+offset old->new for every differing byte.
Run:     python3 verify/chests/evdiff.py f30_rewards f30_steps ...
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.dirname(HERE))
from wwsave import hd, layout
import verifyenv
HERE = verifyenv.out_dir("chests")          # the case folders
MEM = {"status_a": 0x000, "status_b": 0x018, "return_place": 0x030, "item": 0x03C, "get_item": 0x051, "item_record": 0x066, "item_max": 0x06E, "bag_item": 0x076, "get_bag_item": 0x090, "bag_item_record": 0x09C, "collect": 0x0B4, "map": 0x0C4, "info": 0x148, "config": 0x1A4, "priest": 0x1AC, "ocean": 0x5C0, "event": 0x624, "reserve": 0x724}
MEM.update({"status_c%d" % i: 0x1BC + 0x70 * i for i in range(4)}); MEM.update({"memory%02d" % i: 0x380 + 0x24 * i for i in range(16)})
SKIP = ("status_b", "return_place")
for case in sys.argv[1:]:
    s = hd.HdFile.parse(open(os.path.join(HERE, case, "cking.sav"), "rb").read()).slots[0]
    m = open(os.path.join(HERE, case, "run", "si.bin"), "rb").read()[0x20:]
    out = []
    for block, (off, size) in layout.BLOCKS.items():
        if block in SKIP: continue
        for i in range(size):
            a, b = s.data[off + i], m[MEM[block] + i]
            if a != b: out.append("%s+0x%02X %02X->%02X" % (block, i, a, b))
    print("%-26s %s" % (case, ", ".join(out) or "no byte differs (status_b clock/date and return_place not compared)"))
