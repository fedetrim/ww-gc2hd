#!/usr/bin/env python3
"""Item 8, helper: find the HD functions that only return the save pointer (the word at 0x101F84DC, plus a
constant), most called first. A call to one of them hides a direct access from i8_direct.py.

Inputs:  cking.rpx and wwhd_src (through audit/machine-code/hd_extract.py),
         research/out/machine-code/hd_calls.json
Output:  text on stdout: address, number of calls, name, the first instructions.
Run:     python3 -I audit/leftovers/i8_getters.py
Needs the Python package `capstone`.
"""
import sys, os, struct, json, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auditenv  # noqa: E402
SA = auditenv.MACHINE_CODE
sys.path.insert(0, SA)
import hd_extract as h, capstone
secs = h.load_rpx(); t = next(s for s in secs if s['name'] == '.text')
base, data = t['addr'], t['data']
calls = json.load(open(auditenv.out_file("machine-code", "hd_calls.json")))["calls"]
tg = collections.Counter(c["t"] for c in calls)
md = capstone.Cs(capstone.CS_ARCH_PPC, capstone.CS_MODE_32 | capstone.CS_MODE_BIG_ENDIAN)
mk = h.markers()
for a, n in tg.most_common():
    if not (base <= a < base + len(data)): continue
    ins = [struct.unpack_from(">I", data, a - base + 4 * i)[0] for i in range(6)]
    # look for blr within 6 and a lwz with disp 0x84DC (-0x7b24)
    txt = []
    for i, w in enumerate(ins):
        d = list(md.disasm(struct.pack(">I", w), a + 4 * i))
        txt.append("%s %s" % (d[0].mnemonic, d[0].op_str) if d else "?")
        if w == 0x4E800020: break
    else: continue
    if any("-0x7b24" in x for x in txt):
        print("%08X calls=%d %s | %s" % (a, n, mk.get(a, ("", "?"))[1], " ; ".join(txt)))
