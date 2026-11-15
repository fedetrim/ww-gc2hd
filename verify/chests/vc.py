#!/usr/bin/env python3
"""vc.py: one in-game chest verification run.

usage: vc.py CASE SRC FILE STAGE ROOM POINT END_SECONDS [--opt k=v ...] [--gc PYEXPR ...] [--hd PYEXPR ...]
             [--shots t1,t2,...] [--cache N] [NAME=value ...]

Converts file FILE (1-3) of the GameCube save SRC with the given case options (--opt all=steps|rewards,
--opt floor50=rewards ...), puts it in Quest Log 1 at STAGE/ROOM/POINT and runs scripts/ingame_test.py for
END_SECONDS with the NAME=value test aids (environment variables of the port, see docs/SETUP-RESEARCH.md).
In a NAME=value argument the text {work} is replaced by the case's output folder.

--gc EXPR   Python statement run on the GameCube file `g` BEFORE the conversion (builds a GameCube state no
            sample is in; helpers: conv, layout, tbox(g, record, bit, on), mapbit(g, field, n, on)).
--hd EXPR   Python statement run on the converted HD Quest Log `s` AFTER the conversion: test positioning only
            (time of day, date, chart opened on the chart screen, item on a button).
--shots     screenshot times in scenario seconds (frame = 3400 + 30 t).
--cache N   use the shader cache shadercacheN.bin of the output folder (q.sh gives every parallel run its own).

Inputs:  SRC: a GameCube save (a path relative to the repository root is accepted, e.g. samples/gc/...)
         the native port built with both test-aid patches, the extracted game, research/hd-game/stages.json
         (locations and variables: verify/verifyenv.py)
Outputs: research/out/verify/chests/CASE/: cking.sav (the save loaded), result.txt (everything printed),
         run/ (log, si.bin = the game's save block at the end), shots/ and sheet.png with --shots (the
         contact sheet needs the Python package Pillow).
Prints the conversion's change list, the rig's field differences and a before/after table of the fields the
chest rules are about, including the stage record the game holds for the current stage (live memory).

Run:     python3 verify/chests/vc.py f30_rewards 'samples/gc/pack1/Wind Waker/5th save.gci' 1 Cave09 20 0 30 \
             --opt all=rewards WWHD_LINK_WARP=150:0:-70:-4320:-32768 WWHD_TEST_PRESS=8-8.2:8000,14-14.2:8000
         (a 30 s scenario takes about 2.5 minutes, most of it the boot to the title screen and into the
         Quest Log; the cases of cases.txt are run with q.sh)
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(HERE))
from wwsave import convert as conv, gc, hd, layout  # noqa: E402
import verifyenv  # noqa: E402

EXE = verifyenv.EXE
GAME = verifyenv.GAME
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "scripts"))
from ingame_test import MEM  # noqa: E402  (the one table of block offsets in the game's memory)
LIVE = 0x778            # dSv_info_c.mMemory (the current stage's record) inside the save-info block
BASE = 0x20


def tbox(save, record, bit, on):
    conv._set_tbox(save, record, bit, on)


def mapbit(save, field, n, on):
    conv._set_map_bit(save, field, n, on)


class View:
    """Reads the fields of interest from a Save (file) or from the game's save-info dump."""

    def __init__(self, data, mem):
        self.d, self.mem = bytes(data), mem

    def raw(self, name):
        off, size = layout.FIELDS[name]
        if self.mem:
            block = name.split(".")[0]
            boff = layout.BLOCKS[block][0]
            moff = MEM[block]
            off = BASE + moff + off - boff
        return self.d[off:off + size]

    def u(self, name):
        return int.from_bytes(self.raw(name), "big")

    def mapbit(self, field, n):
        w = self.raw(field)
        i = 4 * ((n - 1) >> 5)
        return int.from_bytes(w[i:i + 4], "big") >> ((n - 1) & 31) & 1

    def reg(self, r):
        off = layout.FIELDS["event.flags"][0]
        if self.mem:
            off = BASE + MEM["event"] + off - layout.BLOCKS["event"][0]
        return self.d[off + (r >> 8)] & (r & 0xFF)

    def summary(self, record):
        out = {
            "rupees": self.u("status_a.rupee"), "max_life": self.u("status_a.max_life"),
            "triforce": "%02X" % self.u("collect.triforce"), "collect": self.raw("collect.collect").hex(),
            "reg8803": self.reg(0x8803), "ev1C04": int(bool(self.reg(0x1C04))),
            "tbox[%X]" % record: "%08X" % self.u("memory%02d.tbox" % record),
            "tbox[1]": "%08X" % self.u("memory01.tbox"), "tbox[D]": "%08X" % self.u("memory13.tbox"),
        }
        for n in (4, 6, 7, 8):
            out["chart%d get/open/done" % conv.REUSED_CHARTS[n]] = "%d%d%d" % tuple(
                self.mapbit(f, n) for f in ("map.get_map", "map.open_map", "map.complete_map"))
        if self.mem:
            live = self.d[BASE + LIVE:BASE + LIVE + 0x24]
            out["live stage record tbox"] = live[0:4].hex().upper()
            out["live stage record rest"] = live[4:].hex()
        return out


def main():
    a = sys.argv[1:]
    case, src, slot, stage, room, point, end = a[:7]
    slot = int(slot) - 1
    opts, gcs, hds, shots, envs, cache = {}, [], [], "", [], ""
    i = 7
    while i < len(a):
        if a[i] == "--opt":
            k, v = a[i + 1].split("="); opts[k] = v; i += 2
        elif a[i] == "--gc":
            # the card is rebuilt from its three files only: its picture blocks are not carried over
            print("note: --gc rebuilds the card file without its Picto Box pictures")
            gcs.append(a[i + 1]); i += 2
        elif a[i] == "--hd":
            hds.append(a[i + 1]); i += 2
        elif a[i] == "--shots":
            shots = a[i + 1]; i += 2
        elif a[i] == "--cache":
            cache = a[i + 1]; i += 2
        else:
            envs.append(a[i]); i += 1
    out_root = verifyenv.out_dir("chests")
    work = os.path.join(out_root, case)
    os.makedirs(work, exist_ok=True)
    envs = [e.replace("{work}", work) for e in envs]
    out = open(os.path.join(work, "result.txt"), "w")

    def say(*t):
        line = " ".join(str(x) for x in t)
        print(line, flush=True)
        out.write(line + "\n")
        out.flush()

    say("command: python3 verify/chests/vc.py " + " ".join("'%s'" % x if " " in x or "(" in x else x for x in a))
    src = os.path.expanduser(src)
    if not os.path.isabs(src) and not os.path.exists(src):
        src = os.path.join(ROOT, src)           # sample paths are given relative to the repository root
    card = gc.load_all(open(src, "rb").read())[0]
    slots = card.slots()
    g = slots[slot]
    if gcs:
        for e in gcs:
            exec(e, {"g": g, "conv": conv, "layout": layout, "tbox": tbox, "mapbit": mapbit})
        card = gc.load(gc.build_gci(card.game_code, [bytes(x) if x is not None else bytes(layout.SAVE_SIZE) for x in slots]))
    mode = opts.pop("all", None)
    options = conv.Options.all(mode, **opts) if mode else conv.Options(**opts)
    f, reports = conv.convert(card, options)
    for c in reports[slot].changes:
        say("converter:", c)
    if slot:
        f.move_to_quest_log_1(slot)
    s = f.slots[0]
    for e in hds:
        exec(e, {"s": s, "conv": conv, "layout": layout, "tbox": tbox, "mapbit": mapbit})
        say("test setup on the converted file:", e)
    s.set_raw("return_place.stage", stage.encode().ljust(8, b"\0"))
    s.set_u("return_place.room", int(room))
    s.set_u("return_place.point", int(point))
    sav = os.path.join(work, "cking.sav")
    open(sav, "wb").write(f.serialize())
    record = int(__import__("json").load(open(verifyenv.STAGES))[stage]["save_table"])
    before = View(s.data, False).summary(record)
    if shots:
        envs.append("WWHD_TEST_SCREENSHOT=" + ",".join(str(int(3400 + 30 * float(t))) for t in shots.split(",")))
        envs.append("WWHD_SCREENSHOT_DIR=" + os.path.join(work, "shots"))
        subprocess.run(["rm", "-rf", os.path.join(work, "shots")])
    env = dict(os.environ)
    if cache:
        env["SHADER_CACHE"] = os.path.join(out_root, "shadercache%s.bin" % cache)
    r = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "scripts/ingame_test.py"), EXE, GAME, sav,
                        os.path.join(work, "run"), end] + envs, capture_output=True, text=True, env=env)
    say(r.stdout.strip())
    if r.stderr.strip():
        say("stderr:", r.stderr.strip()[-800:])
    si = os.path.join(work, "run", "si.bin")
    log = os.path.join(work, "run", "log")
    if os.path.exists(log):
        text = open(log, errors="replace").read()
        say("log: %d lines, halt/crash/assert/fatal lines: %d, test_done: %s" % (
            len(text.splitlines()), sum(any(k in l.lower() for k in ("halt", "crash", "assert", "fatal")) for l in text.splitlines()),
            os.path.exists(os.path.join(work, "run", "test_done"))))
        for l in text.splitlines():
            if "[test] warp" in l or "[test] kill" in l or "] poke " in l or " poke " in l:
                say("   " + l[:160])
    if os.path.exists(si):
        after = View(open(si, "rb").read(), True).summary(record)
        say("%-28s %-20s %s" % ("field", "converted file", "game at the end"))
        for k in after:
            say("%-28s %-20s %s%s" % (k, before.get(k, ""), after[k], "   <-- changed" if k in before and before[k] != after[k] else ""))
    if shots and os.path.isdir(os.path.join(work, "shots")):
        files = sorted(os.listdir(os.path.join(work, "shots")))
        for p, t in zip(files, shots.split(",")):
            say("screenshot (t=%s s):" % t, os.path.join(work, "shots", p))
        try:
            from PIL import Image
            ims = [Image.open(os.path.join(work, "shots", p)).resize((640, 360)) for p in files]
            sheet = Image.new("RGB", (1280, 360 * ((len(ims) + 1) // 2)))
            for n, im in enumerate(ims):
                sheet.paste(im, ((n % 2) * 640, (n // 2) * 360))
            sheet.save(os.path.join(work, "sheet.png"))
            say("contact sheet (left to right, top to bottom):", os.path.join(work, "sheet.png"))
        except Exception as e:
            say("no contact sheet:", e)
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
