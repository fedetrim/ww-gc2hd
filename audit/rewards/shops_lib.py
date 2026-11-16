#!/usr/bin/env python3
"""Shared loaders for the shop scripts (module, not run by itself): the relocated GameCube memory image (dol
and all RELs) with symbol names, and reads from the HD rpx by address.

Inputs:  GameCube disc image and zeldaret/tww config (through audit/machine-code/gc_extract.py),
         cking.rpx (through hd_extract.py)
Output:  none.
"""
import sys, os, struct, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
sys.path.insert(0, auditenv.MACHINE_CODE)
import gc_extract as g, hd_extract as h
def load_gc():
    cap = {}; memref = {}
    od = json.dump; json.dump = lambda obj, f: cap.update(obj)
    import ppc
    sc = ppc.scan_function; ppc.scan_function = lambda *a, **k: None
    ol = g.load
    def load():
        m, r = ol(); memref['m'] = m; return m, r
    g.load = load
    g.main(os.devnull)
    json.dump = od; ppc.scan_function = sc; g.load = ol
    names = {int(a): n for a, n in cap['names'].items()}
    return memref['m'], names, cap['funcs'], g.LAST_REL24
class HD:
    def __init__(self):
        self.secs = [s for s in h.load_rpx() if s["addr"] and s["data"]]
    def b(self, a, n):
        for s in self.secs:
            if s["addr"] <= a < s["addr"] + len(s["data"]):
                return s["data"][a - s["addr"]:a - s["addr"] + n]
        return None
    def r32(self, a): return struct.unpack(">I", self.b(a, 4))[0]
    def r16(self, a): return struct.unpack(">H", self.b(a, 2))[0]
    def r8(self, a): return self.b(a, 1)[0]
def gb(mem, a, n):
    b, d = mem.find(a); return bytes(d[a - b:a - b + n])
def set_entry(r32, p):
    it = r32(p)
    return "item=%02X notown=%X own=%X cond=%02X show=%04X buy=%04X m0C=%X cnt=%d" % (r32(it), r32(it + 4), r32(it + 8), r32(it + 12) >> 24, r32(p + 4), r32(p + 8), r32(p + 12), struct.unpack(">i", struct.pack(">I", r32(p + 16)))[0])
