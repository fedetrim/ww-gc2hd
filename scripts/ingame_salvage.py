#!/usr/bin/env python3
"""Salvage the HD-only Treasure Charts 43-46 of a converted save in the game itself.

Converts one file of a GameCube save by steps, then for each HD chart the conversion
added: marks the chart as opened (what the player does on the chart screen), places the file in the
chart's sea sector, boots the native port, moves the boat onto the sunken treasure, lowers the Grappling
Hook crane and reads the game's save block: the rupees must grow and the chart must become "completed".
The converse (a chart the conversion marks as salvaged brings up nothing) is in verify/chests
(cases salv46_f50rewards and salv45_kept): there the evidence is the screenshot of the empty crane next to a
control run that brings the treasure up, because unchanged rupees alone would not show that the crane went
down.

Needs the port built with scripts/port-ship-warp.patch (adds WWHD_SHIP_WARP).

usage: ingame_salvage.py EXE GAME_DIR SAVE.gci FILE(1-3) OUT_DIR [CHART ...]

SALVAGE_HOOK_AT (seconds, default 8) moves the moment the crane is brought out, for a run where an enemy
interrupts it. SALVAGE_PRE_PRESS adds presses before it (e.g. 3-3.2:8000 to end the boat's warning when the
sector's start point lies at the edge of the sea).
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from wwsave import convert as conv, gc, hd, layout  # noqa: E402

# collect map id -> (sea room, treasure position for each value of info.random_salvage); HD stage data
POINTS = {
    4: (44, [(-191300, 314500), (-196700, 324700), (-197200, 313400), (-208100, 328500)]),
    6: (32, [(3000, 95000), (-4000, 104500), (-1900, 96100), (4000, 106100)]),
    7: (6, [(215400, -316900), (218100, -325800), (223300, -319700), (227100, -312700)]),
    8: (46, [(-3200, 280800), (1800, 283600), (2300, 276800), (8300, 285300)]),
}
BUTTON = {0: "2000", 1: "1000", 2: "0010"}      # item buttons X, Y, R


def _bit(words, n):
    """Chart n (1-based) in a 128-bit chart flag set."""
    w = 4 * ((n - 1) >> 5)
    return bool(int.from_bytes(words[w:w + 4], "big") >> ((n - 1) & 31) & 1)


def main():
    exe, game, src, out = sys.argv[1], sys.argv[2], sys.argv[3], os.path.abspath(sys.argv[5])
    slot = int(sys.argv[4]) - 1
    card = gc.load(open(src, "rb").read())
    hd_file, reports = conv.convert(card, conv.Options.all("steps"))
    given = [k for k in POINTS if _bit(hd_file.slots[slot].raw("map.get_map"), k)]
    if sys.argv[6:]:
        given = [k for k in given if str(conv.REUSED_CHARTS[k]) in sys.argv[6:]]
    if not given:
        sys.exit("the conversion adds no HD chart to this file")
    if slot:                                    # the runner loads Quest Log 1
        hd_file.move_to_quest_log_1(slot)
    base = hd_file.slots[0]
    sel = list(base.raw("status_a.select_item")[:3])
    if layout.SLOT_GRAPPLING not in sel:
        sys.exit("the Grappling Hook is not on an item button in this file")
    hook = BUTTON[sel.index(layout.SLOT_GRAPPLING)]
    failed = 0
    for k in given:
        room, points = POINTS[k]
        x, z = points[base.u("info.random_salvage")]
        f = hd.HdFile.parse(hd_file.serialize())
        s = f.slots[0]
        assert _bit(s.raw("map.get_map"), k) and not _bit(s.raw("map.complete_map"), k)
        conv._set_map_bit(s, "map.open_map", k, True)
        s.set_raw("return_place.stage", b"sea".ljust(8, b"\0"))
        s.set_u("return_place.room", room)
        s.set_u("return_place.point", 0)
        work = os.path.join(out, "chart%d" % conv.REUSED_CHARTS[k])
        os.makedirs(work, exist_ok=True)
        sav = os.path.join(work, "cking.sav")
        open(sav, "wb").write(f.serialize())
        t0 = float(os.environ.get("SALVAGE_HOOK_AT", "8"))
        press = "%.1f-%.1f:%s,%.1f-%.1f:8000,%s" % (t0, t0 + 0.3, hook, t0 + 3, t0 + 13, ",".join("%d-%d.2:8000" % (t, t) for t in range(32, 48, 3)))
        if os.environ.get("SALVAGE_PRE_PRESS"):
            press = os.environ["SALVAGE_PRE_PRESS"] + "," + press
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts/ingame_test.py"), exe, game, sav,
                            os.path.join(work, "run"), "50", "WWHD_SHIP_WARP=150:%d:%d,%d:%d:%d" % (x, z, int((t0 + 2.5) * 30), x, z),   # again once stopped
                            "WWHD_TEST_PRESS=" + press, "WWHD_TEST_SCREENSHOT=4250,4340",
                            "WWHD_SCREENSHOT_DIR=" + os.path.join(work, "shots")],
                           capture_output=True, text=True)
        si = os.path.join(work, "run", "si.bin")
        ok = False
        if os.path.exists(si):
            mem = open(si, "rb").read()[0x20:]
            rup_off = layout.FIELDS["status_a.rupee"][0] - layout.BLOCKS["status_a"][0]
            rupees = int.from_bytes(mem[rup_off:rup_off + 2], "big")
            moff = 0x0C4 + layout.FIELDS["map.complete_map"][0] - layout.BLOCKS["map"][0]
            done = _bit(mem[moff:moff + 16], k)
            ok = done and rupees >= s.u("status_a.rupee")     # a full wallet cannot grow
            print("Treasure Chart %d (sea room %d): rupees %d -> %d, chart completed: %s -> %s" % (
                conv.REUSED_CHARTS[k], room, s.u("status_a.rupee"), rupees, done, "OK" if ok else "FAIL"))
        else:
            print("Treasure Chart %d: the game did not finish the scenario\n%s" % (conv.REUSED_CHARTS[k], r.stdout[-600:]))
        failed += not ok
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
