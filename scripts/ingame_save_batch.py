#!/usr/bin/env python3
"""For every USA GameCube sample: convert (every case by steps; with --alt every case by rewards plus Swift Sail and Hero Mode), load the
result in the game, walk a little, save from the pause menu, and compare the file the game writes with the
converted one.  usage: ingame_save_batch.py EXE GAME_DIR OUT_DIR [WORKERS] [--alt]"""
import concurrent.futures
import glob
import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from wwsave import convert as conv, gc, hd, layout  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith("--")]
exe, game, out = [os.path.abspath(p) for p in args[:3]]
workers = int(args[3]) if len(args) > 3 else 3
ALT = "--alt" in sys.argv
OPTIONS = (conv.Options.all("rewards", swift_sail=True, hero_mode=True) if ALT
           else conv.Options.all("steps"))
RUNNER = os.path.join(out, "run_scenario_keep.sh")
os.makedirs(out, exist_ok=True)
src = open(os.path.join(ROOT, "research/port-src/tools/gametest/run_scenario.sh")).read()
open(RUNNER, "w").write(src.replace("\nrm -rf save states\n", "\nrm -rf states\n"))
EXPECTED = {"status_b.date_ipl", "status_b.time", "status_b.date", "info.save_count", "status_a.life",
            "status_b.tact_wind_x", "status_b.tact_wind_y"}

jobs, seen = [], set()
for path in sorted(glob.glob(os.path.join(ROOT, "samples/gc/**/*.gci"), recursive=True)):
    if "Hacked_File" in path:
        continue
    card = gc.load(open(path, "rb").read())
    slots = card.slots()
    if card.game_code != b"GZLE01" or slots[0] is None or slots[0].is_new():
        continue
    key = hashlib.md5(bytes(slots[0])).hexdigest()
    if key in seen:
        continue
    seen.add(key)
    name = "%02d" % len(jobs)
    sav = os.path.join(out, name + ".sav")
    open(sav, "wb").write(conv.convert(card, OPTIONS)[0].serialize())
    jobs.append((name, path, sav))


def run(job):
    name, path, sav = job
    env = dict(os.environ, SHADER_CACHE=os.path.join(out, name + ".shadercache"), WW_RUNNER=RUNNER)
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts/ingame_test.py"), exe, game, sav,
                        os.path.join(out, name), "22", "WWHD_TEST_STICK=2-4:0:1",
                        "WWHD_TEST_PRESS=6-6.3:0008,13-13.3:8000,17-17.3:8000",
                        "WWHD_TEST_TOUCH=10-10.4:0.187:0.281"], capture_output=True, text=True, env=env)
    lines = [l for l in r.stdout.splitlines() if "in memory" in l or "FAIL" in l]
    written = os.path.join(out, name, "save", "user", "cking.sav")
    verdict = "no file"
    if os.path.exists(written):
        a = hd.HdFile.parse(open(sav, "rb").read())
        try:
            b = hd.HdFile.parse(open(written, "rb").read())
        except hd.HdError as e:
            return name, path, "game wrote an INVALID file: %s" % e, lines
        saved = b.slots[0].u("info.save_count") > a.slots[0].u("info.save_count")
        diff = [n for n in layout.FIELDS if a.slots[0].raw(n) != b.slots[0].raw(n) and n not in EXPECTED]
        extra = [s for s in ("options", "pair", "inventory", "name", "playlog") if a.extras[0][s] != b.extras[0][s]]
        verdict = "%s; other block fields changed: %s; HD records changed: %s" % (
            "SAVED by the game" if saved else "not saved (menu unavailable here)", diff or "none", extra or "none")
    return name, path, verdict, lines


with concurrent.futures.ThreadPoolExecutor(workers) as ex, open(os.path.join(out, "summary.txt"), "w") as log:
    for name, path, verdict, lines in ex.map(run, jobs):
        text = "%s %s\n    %s\n    %s\n" % (name, os.path.relpath(path, ROOT), " | ".join(l.strip() for l in lines), verdict)
        log.write(text)
        log.flush()
        print(text, end="", flush=True)
