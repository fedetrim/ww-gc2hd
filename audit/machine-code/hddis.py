#!/usr/bin/env python3
"""Disassemble a range of HD code (helper for reading a difference by hand).

Inputs:  cking.rpx and wwhd_src (through hd_extract.py)
Output:  disassembly on stdout, with function markers and the names of call targets.
Run:     python3 -I audit/machine-code/hddis.py START_HEX END_HEX
Needs the Python package `capstone`.
"""
import sys, os, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hd_extract as h, capstone
secs = h.load_rpx(); t = next(s for s in secs if s['name'] == '.text')
mk = h.markers()
md = capstone.Cs(capstone.CS_ARCH_PPC, capstone.CS_MODE_32 | capstone.CS_MODE_BIG_ENDIAN)
a, b = int(sys.argv[1], 16), int(sys.argv[2], 16)
for pc in range(a, b, 4):
    if pc in mk: print("==", mk[pc][1], mk[pc][0])
    ii = list(md.disasm(t['data'][pc - t['addr']:pc - t['addr'] + 4], pc))
    if not ii: print(" %08X ?" % pc); continue
    i = ii[0]; extra = ""
    if i.mnemonic in ("bl", "b"):
        try:
            tg = int(i.op_str, 16)
            if tg in mk: extra = "  -> " + mk[tg][1]
        except ValueError: pass
    print(" %08X %-7s %s%s" % (pc, i.mnemonic, i.op_str, extra))
