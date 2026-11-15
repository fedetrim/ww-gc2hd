#!/usr/bin/env python3
"""Convert every USA GameCube sample and load each result in the game (scripts/ingame_test.py).
usage: ingame_batch.py EXE GAME_DIR OUT_DIR [WORKERS [steps|rewards]]"""
import concurrent.futures
import glob
import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from wwsave import convert as conv, gc  # noqa: E402

exe, game, out = [os.path.abspath(p) for p in sys.argv[1:4]]
workers = int(sys.argv[4]) if len(sys.argv) > 4 else 3
MODE = sys.argv[5] if len(sys.argv) > 5 else "steps"      # steps | rewards, for every case
os.makedirs(out, exist_ok=True)
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
    data = conv.convert(card, conv.Options.all(MODE))[0].serialize()
    sav = os.path.join(out, name + ".sav")
    open(sav, "wb").write(data)
    jobs.append((name, path, sav))


def run(job):
    name, path, sav = job
    env = dict(os.environ, SHADER_CACHE=os.path.join(out, name + ".shadercache"))
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts/ingame_test.py"), exe, game, sav,
                        os.path.join(out, name), "6"], capture_output=True, text=True, env=env)
    return name, path, r.returncode, r.stdout.strip()


with concurrent.futures.ThreadPoolExecutor(workers) as ex, open(os.path.join(out, "summary.txt"), "w") as log:
    for name, path, rc, text in ex.map(run, jobs):
        line = "%s rc=%d %s\n%s\n" % (name, rc, os.path.relpath(path, ROOT), "\n".join("    " + t for t in text.splitlines()))
        log.write(line)
        log.flush()
        print(line, end="", flush=True)
