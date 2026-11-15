#!/usr/bin/env python3
"""Read bytes of the HD rpx by address (helper; also a module: hd(addr, n)).

Inputs:  cking.rpx (through audit/machine-code/hd_extract.py)
Output:  hex on stdout.
Run:     python3 -I audit/rewards/npc_mem.py ADDR_HEX LEN [b|h|w]     bytes, 16-bit or 32-bit words
"""
import os, sys, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
sys.path.insert(0, auditenv.MACHINE_CODE)
import hd_extract

_secs = None
def hd(addr, n):
    global _secs
    if _secs is None:
        _secs = hd_extract.load_rpx()
    for s in _secs:
        if s["addr"] and s["addr"] <= addr < s["addr"] + len(s["data"]):
            o = addr - s["addr"]
            return s["data"][o:o + n]
    raise KeyError(hex(addr))

if __name__ == "__main__":
    a = int(sys.argv[1], 16); n = int(sys.argv[2], 0)
    fmt = sys.argv[3] if len(sys.argv) > 3 else "b"
    d = hd(a, n)
    if fmt == "w":
        print(" ".join("%08X" % x for x in struct.unpack(">%dI" % (n // 4), d)))
    elif fmt == "h":
        print(" ".join("%04X" % x for x in struct.unpack(">%dH" % (n // 2), d)))
    else:
        print(d.hex(" "))
