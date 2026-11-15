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
sys.path.insert(0, os.path.join(verifyenv.ROOT, "scripts"))
from ingame_test import MEM  # noqa: E402  (the one table of block offsets in the game's memory)
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
