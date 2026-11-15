#!/usr/bin/env python3
"""Compare the save-accessor calls of the two games per source unit.

For every unit (source file name; HD split files such as `_exec`, `_msg` are folded into the GameCube unit)
builds the set of (accessor, constant arguments). Event and temporary bits are told apart by the `this`
pointer (GameCube g_dComIfG_gameInfo+0x624 / +0x1158; HD *(0x101F84DC)+0x644 / +0x1178). A call made
through a wrapper whose flag argument is the wrapper's own parameter is expanded to the wrapper's call
sites (4 levels). Prints the keys present on one side only.

Inputs:  gc_calls.json and hd_calls.json in research/out/machine-code/ (gc_extract.py, hd_extract.py)
Output:  text on stdout. The audit kept `compare.py > diff_all.txt` and `compare.py --global > global_diff.txt`.
Run:     python3 -I audit/machine-code/compare.py [--all] [--unit NAME] [--wrappers]
         python3 -I audit/machine-code/compare.py --global      one-sided (accessor, constant) over all units
         (a few seconds)

The HD addresses above are those of the USA v0 cking.rpx. Imported by most other scripts of this folder
for load(), unit_of() and the wrapper expansion.
"""
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import auditenv  # noqa: E402

# number of key arguments (after `this` for members; from r3 for free functions)
FREE = {
    "dComIfGs_isStageTbox": (None, 2), "dComIfGs_onStageTbox": (None, 2), "dComIfGs_isStageBossEnemy": (None, 1),
    "dComIfGs_onStageLife": (None, 1), "dComIfGs_isStageLife": (None, 1), "dComIfGs_checkGetItem": (None, 1),
    "dComIfGs_checkGetItemNum": (None, 1), "dComIfGs_isStageMap": (None, 1), "dComIfGs_isStageCompass": (None, 1),
    "dComIfGs_isStageBossKey": (None, 1), "dComIfGs_checkSeaLandingEvent": (None, 0),
}
SKIP_METHOD = re.compile(r"::(init|reinit|__ct|__dt|set|getSave|putSave|initZone|createZone|card_to_memory|memory_to_card|"
                         r"initdata_to_card|setRoom|setRestartOption|clearRoomSwitch|getTimer|decTimer|resetTimer|"
                         r"checkVibration|getTriforceNum|getCollectMapNum|checkEmptyBottle|checkBaitItemEmpty|"
                         r"checkReserveItemEmpty|setEmptyBottle)$")
# second argument is a room number / value, not part of the flag identity
ONE_ARG = re.compile(r"dSv_(info|memBit|danBit|zoneBit|zoneActor)_c::|dSv_event_c::|Tact|Triforce|Symbol|Beast|Bait|Reserve|"
                     r"BottleItem|Bottle$|Map$|Grid|GridForAgb|BottleItemIn|BottleItemEmpty|BaitItem")
SKIP_UNITS = {"d_save", "d_com_inf_game"}


def gc_canon(t):
    if ":" in t:        # REL-local symbol
        return None
    m = re.match(r"(\w+?)__(\d+)(\w+)", t)
    if m and not t.startswith("__"):
        n = int(m.group(2))
        cls = m.group(3)[:n]
        if cls.startswith("dSv_"):
            return cls + "::" + m.group(1), True
    m = re.match(r"(\w+?)__F", t)
    if m and m.group(1) in FREE:
        return m.group(1), False
    return None


def hd_canon(n):
    n = n.replace("d_save_cpp::", "")
    if n.startswith("dSv_"):
        n = n.replace("item_record2_c", "item_record_c").replace("item_max2_c", "item_max_c")
        return n, True
    if n.startswith("hdGameInfo_") and n[11:] in FREE:
        return n[11:], False
    return None


def unit_of(path, bases=None):
    b = os.path.basename(path)
    b = re.sub(r"\.(cpp|c|inc|h)$", "", b)
    if bases is None or b in bases:
        return b
    best = None
    for g in bases:
        if b.startswith(g + "_") and (best is None or len(g) > len(best)):
            best = g
    return best or b


def fmt(tag, x):
    if tag is not None:
        return "?"
    return "%X" % (x & 0xFFFF if x < 0x10000 or x >= 0xFFFF0000 else x)


def vals(regs, reg):
    v = regs.get(reg)
    if not v:
        return ["?"]
    return sorted(set(fmt(t, x) for t, x in v))


def keys(canon, member, regs, this_tag):
    kr = ["r4", "r5"] if member else ["r3", "r4"]
    name = canon
    nargs = 2
    if not member:
        nargs = FREE[canon][1]
    elif ONE_ARG.search(canon):
        nargs = 1
    if name.startswith("dSv_event_c::"):
        name = (this_tag or "?") + ":" + name.split("::")[1]
    if nargs == 0:
        return [(name, "")]
    args = [vals(regs, r) for r in kr[:nargs]]
    if nargs == 2:
        return [(name, a + "," + b) for a in args[0] for b in args[1]]
    return [(name, a) for a in args[0]]


def subst(inner, outer):
    """registers of a call inside a wrapper, with the wrapper's incoming arguments replaced by the caller's values"""
    out = {}
    for r, vs in inner.items():
        res = []
        ok = True
        for tag, x in vs:
            if isinstance(tag, str):          # incoming argument rN (+x)
                src = outer.get("r" + tag[1:])
                if not src:
                    ok = False
                    break
                res.extend((t2, (x2 + x) & 0xFFFFFFFF) for t2, x2 in src)
            else:
                res.append((tag, x))
        if ok and len(res) <= 16:
            out[r] = res
    return out


def has_arg(regs, names):
    return any(isinstance(t, str) for r in names for t, x in regs.get(r, []))


def side(calls, canon_of, this_of, unit_fn, inside):
    """-> {unit: {key: [where]}}, wrappers info"""
    direct = []          # (call, canon, member, regs)
    for c in calls:
        cn = canon_of(c["t"])
        if cn and not SKIP_METHOD.search(cn[0]) and not inside(c["fs"]):
            regs = {r: [tuple(v) for v in c[r]] for r in ("r3", "r4", "r5", "r6", "r7") if r in c}
            direct.append((c, cn[0], cn[1], regs))
    by_target = collections.defaultdict(list)
    for c in calls:
        by_target[c["t"]].append(c)
    out = collections.defaultdict(lambda: collections.defaultdict(list))
    wrappers = collections.defaultdict(list)   # function start -> [(canon, member, regs)]
    winfo = {}
    work = direct
    for depth in range(4):
        nxt = []
        for c, canon, member, regs in work:
            kr = (["r4", "r5"] if member else ["r3", "r4"])
            if member and canon.startswith("dSv_event_c::"):
                kr = ["r3"] + kr[:1]
            elif member and ONE_ARG.search(canon):
                kr = kr[:1]
            if has_arg(regs, kr) and by_target.get(c["fs"]):
                wrappers[c["fs"]].append((canon, member, regs))
                winfo[c["fs"]] = (c["func"], c["file"], len(by_target[c["fs"]]))
                for caller in by_target[c["fs"]]:
                    oregs = {r: [tuple(v) for v in caller[r]] for r in ("r3", "r4", "r5", "r6", "r7") if r in caller}
                    nxt.append((caller, canon, member, subst(regs, oregs)))
                continue
            for k in keys(canon, member, regs, this_of(regs.get("r3")) if member else None):
                out[unit_fn(c["file"])][k].append(c["func"] + "@" + c["pc"] + " " + c["file"])
        work = nxt
    return out, winfo


def load():
    gc = json.load(open(auditenv.out_file("machine-code", "gc_calls.json")))
    hd = json.load(open(auditenv.out_file("machine-code", "hd_calls.json")))
    gi = gc["game_info"]
    bases = {unit_of(f[0]) for f in gc["funcs"]}
    names = gc["names"]
    gcache = {}

    def gc_canon_of(t):
        if t not in gcache:
            n = names.get(str(t))
            gcache[t] = gc_canon(n) if n else None
        return gcache[t]

    def gc_this(r3):
        if r3 and len(r3) == 1 and r3[0][0] is None:
            return {0x624: "event", 0x1158: "tmp"}.get(r3[0][1] - gi)

    mk = hd["markers"]
    hcache = {}

    def hd_canon_of(t):
        if t not in hcache:
            m = mk.get("%08X" % t)
            hcache[t] = hd_canon(m[1]) if m else None
        return hcache[t]

    def hd_this(r3):
        if r3 and len(r3) == 1 and r3[0][0] == 0x101F84DC:
            return {0x644: "event", 0x1178: "tmp"}.get(r3[0][1])

    def gc_inside(fs):
        n = names.get(str(fs), "")
        return bool(re.search(r"__\d+dSv_", n)) or gc_canon_of(fs) is not None

    def hd_inside(fs):
        m = mk.get("%08X" % fs)
        return bool(m and ("dSv_" in m[1] or hd_canon_of(fs) is not None))

    G, gw = side(gc["calls"], gc_canon_of, gc_this, unit_of, gc_inside)
    H, hw = side(hd["calls"], hd_canon_of, hd_this, lambda f: unit_of(f, bases), hd_inside)
    return G, H, bases, gw, hw


def main():
    G, H, bases, gw, hw = load()
    if "--wrappers" in sys.argv:
        for nm, w in (("GC", gw), ("HD", hw)):
            for fs, (fn, fl, n) in sorted(w.items()):
                print(nm, "%08X" % fs, fn, fl, n, "call sites")
        return
    args = sys.argv[1:]
    only = args[args.index("--unit") + 1] if "--unit" in args else None
    show_all = "--all" in args
    ndiff = 0
    for u in sorted(set(G) | set(H)):
        if u in SKIP_UNITS or (only and u != only):
            continue
        g, h = G.get(u, {}), H.get(u, {})
        rows = []
        # an unknown `this` ("?:") on one side pairs with event:/tmp: of the same method and flag on the other
        for a_, b_ in ((g, h), (h, g)):
            for k in [k for k in a_ if k[0].startswith("?:")]:
                for tag in ("event", "tmp"):
                    k2 = (tag + k[0][1:], k[1])
                    if k2 in b_ and k not in b_:
                        a_.setdefault(k2, []).extend(a_.pop(k))
                        break
        for k in sorted(set(g) | set(h)):
            if show_all or (k in g) != (k in h):
                rows.append((k, len(g.get(k, [])), len(h.get(k, [])), g.get(k, []), h.get(k, [])))
        if rows:
            print("== %s%s" % (u, "" if u in bases else "  (no GC unit)"))
            for k, ng, nh, lg, lh in rows:
                mark = " " if ng and nh else "!"
                ndiff += mark == "!"
                print(" %s %-34s %-12s GC %2d  HD %2d   %s" % (mark, k[0], k[1], ng, nh,
                      "; ".join(sorted(set(x.split("@")[0] + " " + x.split(" ")[-1].split("/")[-1] for x in (lh if not ng else lg if not nh else [])))[:4])))
    print(ndiff, "one-sided keys")




def global_diff():
    G, H, bases, gw, hw = load()
    def flat(S):
        out = collections.defaultdict(set)
        for u, d in S.items():
            for k in d:
                name = k[0].replace("?:", "event:")
                out[(name, k[1])].add(u)
        return out
    g, h = flat(G), flat(H)
    for k in sorted(set(g) | set(h)):
        if (k in g) != (k in h) and "?" not in k[1]:
            print("%s %-40s %-10s %s" % ("GC-only" if k in g else "HD-only", k[0], k[1], ",".join(sorted(g.get(k) or h.get(k)))))


if __name__ == "__main__":
    global_diff() if "--global" in sys.argv else main()
