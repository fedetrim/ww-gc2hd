#!/usr/bin/env python3
"""Item numbers written to the event controller's "get item" byte (dComIfGp_event_setGtItm), per unit, both
games. GameCube: stb to g_dComIfG_gameInfo+0x52AC; HD: stb with displacement 0x52A4 (play+0x52A4).
Prints the constant values, or `?` when the stored register is not a constant.

Inputs:  GameCube disc image and zeldaret/tww config (through gc_extract.py), cking.rpx and wwhd_src
         (through hd_extract.py), gc_calls.json in research/out/machine-code/
Output:  text on stdout (one line per unit, `!` marks a difference).
Run:     python3 -I audit/machine-code/gtitm.py        (about 20 s: both binaries are scanned again)

Limit: on the HD side every `stb` with displacement 0x52A4 is taken, whatever its base register.
"""
import collections, json, os, re, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ppc as P
orig_scan = P.scan_function
import compare, gc_extract, hd_extract

def collect_gc():
    out = collections.defaultdict(lambda: collections.defaultdict(set))
    gc = json.load(open(compare.auditenv.out_file("machine-code", "gc_calls.json")))
    gi = gc["game_info"]
    memref = {}
    ol = gc_extract.load
    def load():
        m, r = ol(); memref["m"] = m; return m, r
    gc_extract.load = load
    P.scan_function = lambda *a, **k: None
    jd = json.dump; json.dump = lambda *a, **k: None
    gc_extract.main(os.devnull); json.dump = jd
    mem = memref["m"]
    for f, n, m, s, e in gc["funcs"]:
        def on_ins(pc, ins, state, f=f, n=n):
            if ins >> 26 == 38 and (ins & 0xFFFF) == 0x52AC:
                base = state.get(ins >> 16 & 31)
                if base and all(t is None and x == gi for t, x in base):
                    v = state.get(ins >> 21 & 31)
                    vals = sorted("%X" % (x & 0xFF) if t is None else "?" for t, x in v) if v else ["?"]
                    out[compare.unit_of(f)][n.split("__")[0]].update(vals)
        orig_scan(mem.r32, s, e, lambda *a: None, None, on_ins)
    return out, {compare.unit_of(f[0]) for f in gc["funcs"]}

def collect_hd(bases):
    out = collections.defaultdict(lambda: collections.defaultdict(set))
    secs = hd_extract.load_rpx(); text = next(s for s in secs if s["name"] == ".text")
    base, data = text["addr"], text["data"]
    r32 = lambda a: struct.unpack_from(">I", data, a - base)[0]
    mk = hd_extract.markers(); starts = sorted(a for a in mk if base <= a < base + len(data))
    for i, st in enumerate(starts):
        en = starts[i + 1] if i + 1 < len(starts) else base + len(data)
        f, n, _ = mk[st]
        def on_ins(pc, ins, state, f=f, n=n):
            if ins >> 26 == 38 and (ins & 0xFFFF) == 0x52A4:
                v = state.get(ins >> 21 & 31)
                vals = sorted("%X" % (x & 0xFF) if t is None else "?" for t, x in v) if v else ["?"]
                out[compare.unit_of(f, bases)][n.split("::")[-1]].update(vals)
        orig_scan(r32, st, en, lambda *a: None, None, on_ins)
    return out

G, bases = collect_gc()
H = collect_hd(bases)
for u in sorted(set(G) | set(H)):
    g = sorted(set().union(*G[u].values())) if u in G else []
    h = sorted(set().union(*H[u].values())) if u in H else []
    print("%s %-22s GC %-28s HD %-28s | GC funcs: %s | HD funcs: %s" % (" " if g == h else "!", u, ",".join(g) or "-", ",".join(h) or "-",
          ",".join(sorted(G.get(u, {}))), ",".join(sorted(H.get(u, {})))))
