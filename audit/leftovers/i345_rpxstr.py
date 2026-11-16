#!/usr/bin/env python3
"""Items 3-5 (one-sided keys of the machine-code audit), helper: find byte strings in the decompressed
sections of cking.rpx; prints section, address and the surrounding bytes.

Inputs:  cking.rpx (through audit/machine-code/hd_extract.py)
Output:  text on stdout.
Run:     python3 -I audit/leftovers/i345_rpxstr.py STRING [...]
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
sys.path.insert(0, auditenv.MACHINE_CODE)
import hd_extract
secs = hd_extract.load_rpx()
for s in sys.argv[1:]:
    b = s.encode()
    hit = False
    for sec in secs:
        d = sec["data"]; i = d.find(b)
        while i >= 0:
            hit = True
            print(s, sec["name"], hex(sec["addr"] + i), bytes(d[max(0, i - 16):i + 32]))
            i = d.find(b, i + 1)
    if not hit: print(s, "NOT FOUND")
