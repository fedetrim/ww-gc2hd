#!/usr/bin/env python3
"""Disassemble GameCube functions by symbol name (helper for reading a difference by hand).

Inputs:  GameCube disc image, zeldaret/tww config (through gc_extract.py)
Output:  disassembly on stdout, with the resolved targets of calls that go through a REL relocation.
Run:     python3 -I audit/machine-code/gcdis.py MODULE SYMBOL_SUBSTRING [...]
         MODULE is a REL name (d_a_npc_tc) or `dol`.
Needs the Python package `capstone`.
"""
import json, os, re, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import capstone
import gc_extract as g

def main():
    mod, pats = sys.argv[1], sys.argv[2:]
    names = {}
    orig_dump = json.dump
    cap = {}
    json.dump = lambda obj, f: cap.update(obj)
    # reuse main() loading by monkeypatching scan
    import ppc
    scan = ppc.scan_function
    ppc.scan_function = lambda *a, **k: None
    memref = {}
    oload = g.load
    def load():
        m, r = oload(); memref['m'] = m; return m, r
    g.load = load
    relsink = {}
    g.main(os.devnull)
    mem = memref['m']
    names = {int(a): n for a, n in cap['names'].items()}
    md = capstone.Cs(capstone.CS_ARCH_PPC, capstone.CS_MODE_32 | capstone.CS_MODE_BIG_ENDIAN)
    rel24 = g.LAST_REL24
    for f, n, m, s, e in cap['funcs']:
        if m == mod and any(p in n for p in pats):
            print("==", n, hex(s))
            b, d = mem.find(s)
            for pc in range(s, e, 4):
                ii = list(md.disasm(bytes(d[pc - b:pc - b + 4]), pc))
                if not ii:
                    print(" %08X .long   %08X" % (pc, mem.r32(pc))); continue
                i = ii[0]
                extra = ""
                if i.address in rel24:
                    extra = "  -> " + names.get(rel24[i.address], hex(rel24[i.address]))
                elif i.mnemonic == "bl":
                    t = int(i.op_str, 16); extra = "  -> " + names.get(t, "")
                print(" %08X %-7s %s%s" % (i.address, i.mnemonic, i.op_str, extra))
main()
