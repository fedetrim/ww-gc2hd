#!/usr/bin/env python3
"""Item 8 (direct access to the save block): every load or store whose address lies inside the save structure
without going through an accessor function, per function, both games. GameCube: an absolute address in
[g_dComIfG_gameInfo, +0x12A0). HD: base register = the word at 0x101F84DC, offset 0x20..0x12C0 (0x20 is
where dSv_info_c starts).

Inputs:  GameCube disc image and zeldaret/tww config (through audit/machine-code/gc_extract.py), cking.rpx
         and wwhd_src (through hd_extract.py)
Output:  i8_direct.json in research/out/leftovers/, or the path given as argument:
         {"GC": [[file, function, pc, "L"|"S", offset, mnemonic], ...], "HD": [...]}
Run:     python3 -I audit/leftovers/i8_direct.py [OUT.json]        (about 20 s)

Limits: the address of g_dComIfG_gameInfo is the constant of the USA disc (0x803C4C08), written in the
script. Only accesses whose base the constant tracker can follow are seen: a pointer to the save block that
was stored in a member or passed through an untracked call is not.
"""
import sys, os, json, struct, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402
SA = auditenv.MACHINE_CODE
sys.path.insert(0, SA)
import ppc, compare
LOAD = {32: "lwz", 33: "lwzu", 34: "lbz", 35: "lbzu", 40: "lhz", 41: "lhzu", 42: "lha", 43: "lhau", 48: "lfs", 50: "lfd"}
STORE = {36: "stw", 37: "stwu", 38: "stb", 39: "stbu", 44: "sth", 45: "sthu", 52: "stfs", 54: "stfd"}
SIZE = 0x12A0
orig = ppc.scan_function
cur = {}
out = {"GC": [], "HD": []}

def make_on_ins(side, start):
    def on_ins(pc, ins, state):
        op = ins >> 26
        if op not in LOAD and op not in STORE: return
        rA = ins >> 16 & 31
        if not rA or rA not in state: return
        d = ppc.sx16(ins & 0xFFFF)
        for t, x in state[rA]:
            if side == "GC":
                if t is None and GI <= ((x + d) & 0xFFFFFFFF) < GI + SIZE:
                    out[side].append((start, pc, "S" if op in STORE else "L", (x + d - GI) & 0xFFFFFFFF, LOAD.get(op) or STORE.get(op)))
            else:
                if t == 0x101F84DC:
                    off = (x + d) & 0xFFFFFFFF
                    if 0x20 <= off < 0x20 + SIZE:
                        out[side].append((start, pc, "S" if op in STORE else "L", off - 0x20, LOAD.get(op) or STORE.get(op)))
    return on_ins

def wrap(side):
    def f(read32, start, end, on_call, init=None, on_ins=None):
        return orig(read32, start, end, on_call, init, make_on_ins(side, start))
    return f

# GC
import gc_extract as g
cap = {}
json_dump = json.dump
json.dump = lambda obj, f: cap.update(obj)
# need GI before scanning: read from existing json
GI = 2151435272      # 0x803C4C08, g_dComIfG_gameInfo on the USA disc (gc_calls.json "game_info")
ppc.scan_function = wrap("GC")
g.main(os.devnull)
gfun = {s: (f, n) for f, n, m, s, e in cap["funcs"]}
# HD
import hd_extract as h
cap2 = {}
json.dump = lambda obj, f: cap2.update(obj)
ppc.scan_function = wrap("HD")
h.main(os.devnull)
mk = {int(a, 16): v for a, v in cap2["markers"].items()}
json.dump = json_dump
res = {"GC": [(gfun[s][0], gfun[s][1], "%08X" % pc, k, off, m) for s, pc, k, off, m in out["GC"]],
       "HD": [(mk[s][0], mk[s][1], "%08X" % pc, k, off, m) for s, pc, k, off, m in out["HD"]]}
json.dump(res, open(sys.argv[1] if len(sys.argv) > 1 else auditenv.out_file("leftovers", "i8_direct.json"), "w"))
print(len(res["GC"]), len(res["HD"]))
