#!/usr/bin/env python3
"""Validation of the extractor: for the GameCube actors whose source is decompiled, compare the event
bit/register constants written in the source text with those found in the machine code.

Inputs:  gc_calls.json, hd_calls.json, stubs.json in research/out/machine-code/
         zeldaret/tww clone: include/d/d_save_event_flag.inc, src/d/actor/*.cpp
Output:  text on stdout: one line per actor that differs, then the totals. The audit kept it as
         validate.txt (738 of 744 source constants found; the 6 misses are in VERSION_DEMO blocks).
Run:     python3 -I audit/machine-code/validate.py

Limit: the source side is a text search (no preprocessor), so code in `#if` blocks of other versions
counts as source-only. Only the GameCube side is validated this way.
"""
import os, re, sys, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import compare
TWW = compare.auditenv.TWW
enum = {}
for m in re.finditer(r"(\w+)\s*=\s*0x([0-9A-Fa-f]{4})", open(os.path.join(TWW, "include/d/d_save_event_flag.inc")).read()):
    enum[m.group(1)] = int(m.group(2), 16)
G, H, bases, gw, hw = compare.load()
stubs = {os.path.basename(k)[:-4] for k in json.load(open(compare.auditenv.out_file("machine-code", "stubs.json")))}
call = re.compile(r"dComIfGs_(is|on|off)EventBit\(\s*([^()]+?)\s*\)|dComIfGs_(get)EventReg\(\s*([^()]+?)\s*\)|dComIfGs_(set)EventReg\(\s*([^(),]+?)\s*,")
def src_set(path):
    s = open(path, errors="replace").read()
    s = re.sub(r"//.*", "", s); s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    out, unres = set(), 0
    for m in call.finditer(s):
        kind = m.group(1) or m.group(3) or m.group(5); arg = m.group(2) or m.group(4) or m.group(6)
        name = {"is": "isEventBit", "on": "onEventBit", "off": "offEventBit", "get": "getEventReg", "set": "setEventReg"}[kind]
        v = None
        if re.fullmatch(r"0x[0-9A-Fa-f]+", arg): v = int(arg, 16)
        elif arg.split("::")[-1] in enum: v = enum[arg.split("::")[-1]]
        if v is None: unres += 1
        else: out.add((name, "%X" % v))
    return out, unres
ok = bad = 0; tot_s = tot_match = 0
for fn in sorted(os.listdir(os.path.join(TWW, "src/d/actor"))):
    u = fn[:-4]
    if not fn.endswith(".cpp") or u in stubs: continue
    S, unres = src_set(os.path.join(TWW, "src/d/actor", fn))
    B = set(); bq = 0
    for k in G.get(u, {}):
        if k[0].startswith("event:") or k[0].startswith("?:"):
            if "?" in k[1]: bq += 1
            else: B.add((k[0].split(":")[1], k[1]))
    tot_s += len(S); tot_match += len(S & B)
    if S - B or (B - S and not unres):
        bad += 1
        print("%-22s src-only %s  bin-only %s  (src unresolved args %d, bin non-constant %d)" % (u, sorted(S - B), sorted(B - S), unres, bq))
    else: ok += 1
print("GC decompiled actors: %d identical, %d with differences; %d/%d source constants found in machine code" % (ok, bad, tot_match, tot_s))
