#!/usr/bin/env python3
"""Compare the item numbers passed to item-giving calls per source unit, GameCube machine code against HD
machine code.

Covered calls: fopAcM_createItem*, fopAcM_fastCreateItem*, fopAcM_createItemFor*Demo, fopAcM_createShopItem,
fopAcM_createRaceItem*, fopAcM_createDemoItem, fopAcM_createStealItem, fopAcM_createIball,
fopAcM_createItemFromEnemyTable, execItemGet. Wrappers are expanded as in compare.py.

Inputs:  gc_calls.json, hd_calls.json in research/out/machine-code/
Output:  text on stdout; the audit kept `rewards.py --all > rewards_all.txt`.
Run:     python3 -I audit/machine-code/rewards.py [--all] [--unit NAME] [--wrappers]

Limit: an item number that is not a constant at the call site (a shop selection, an actor member) shows as
`?`; for those units only the number of call sites is compared.
"""
import collections, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import compare

# function -> register holding the item number
FUNCS = {n: "r4" for n in """fopAcM_createItemForPresentDemo fopAcM_createItemForTrBoxDemo fopAcM_createItemFromTable
fopAcM_createRaceItemFromTable fopAcM_createShopItem fopAcM_createRaceItem fopAcM_createDemoItem fopAcM_createItem
fopAcM_fastCreateItem2 fopAcM_createItemForKP2 fopAcM_createItemForSimpleDemo fopAcM_fastCreateItem
fopAcM_createItemFromTableRegister""".split()}
FUNCS.update({"execItemGet": "r3", "fopAcM_createStealItem": "r4", "fopAcM_createIball": "r4",
              "fopAcM_createItemFromEnemyTable": "r3"})
ALIAS = {"fopAcM_createItemFromTableRegister": "fopAcM_createItemFromTable"}


def load():
    gc = json.load(open(compare.auditenv.out_file("machine-code", "gc_calls.json")))
    hd = json.load(open(compare.auditenv.out_file("machine-code", "hd_calls.json")))
    bases = {compare.unit_of(f[0]) for f in gc["funcs"]}
    names = gc["names"]
    mk = hd["markers"]

    def gcn(t):
        n = names.get(str(t), "")
        m = re.match(r"(\w+?)__F", n)
        return m.group(1) if m and m.group(1) in FUNCS else None

    def hdn(t):
        m = mk.get("%08X" % t)
        return m[1] if m and m[1] in FUNCS else None

    def side(calls, canon, unit_fn):
        by_target = collections.defaultdict(list)
        for c in calls:
            by_target[c["t"]].append(c)
        out = collections.defaultdict(lambda: collections.defaultdict(list))
        winfo = {}
        work = []
        for c in calls:
            n = canon(c["t"])
            if n and not canon(c["fs"]):
                work.append((c, n, {r: [tuple(v) for v in c[r]] for r in ("r3", "r4", "r5", "r6", "r7") if r in c}))
        for depth in range(4):
            nxt = []
            for c, n, regs in work:
                reg = FUNCS[n]
                if compare.has_arg(regs, [reg]) and by_target.get(c["fs"]):
                    winfo[c["fs"]] = (c["func"], c["file"], len(by_target[c["fs"]]))
                    for caller in by_target[c["fs"]]:
                        oregs = {r: [tuple(v) for v in caller[r]] for r in ("r3", "r4", "r5", "r6", "r7") if r in caller}
                        nxt.append((caller, n, compare.subst(regs, oregs)))
                    continue
                for v in compare.vals(regs, reg):
                    out[unit_fn(c["file"])][(ALIAS.get(n, n), v)].append(c["func"] + "@" + c["pc"] + " " + c["file"])
            work = nxt
        return out, winfo
    G, gw = side(gc["calls"], gcn, compare.unit_of)
    H, hw = side(hd["calls"], hdn, lambda f: compare.unit_of(f, bases))
    return G, H, bases, gw, hw


def main():
    G, H, bases, gw, hw = load()
    args = sys.argv[1:]
    only = args[args.index("--unit") + 1] if "--unit" in args else None
    if "--wrappers" in args:
        for nm, w in (("GC", gw), ("HD", hw)):
            for fs, v in sorted(w.items()):
                print(nm, "%08X" % fs, *v)
        return
    n = 0
    for u in sorted(set(G) | set(H)):
        if only and u != only:
            continue
        g, h = G.get(u, {}), H.get(u, {})
        rows = [k for k in sorted(set(g) | set(h)) if "--all" in args or (k in g) != (k in h)]
        if rows:
            print("== %s%s" % (u, "" if u in bases else "  (no GC unit)"))
            for k in rows:
                one = (k in g) != (k in h)
                n += one
                print(" %s %-34s item %-4s GC %2d  HD %2d  %s" % ("!" if one else " ", k[0], k[1], len(g.get(k, [])), len(h.get(k, [])),
                      "; ".join(sorted(set(x.split("@")[0] for x in g.get(k, []) + h.get(k, [])))[:4])))
    tot = lambda S: sum(len(l) for d in S.values() for l in d.values())
    print(n, "one-sided keys; call sites GC %d HD %d; units GC %d HD %d" % (tot(G), tot(H), len(G), len(H)))


if __name__ == "__main__":
    main()
