#!/usr/bin/env python3
"""Convert every used file of every USA GameCube sample and load each result in the game
(scripts/ingame_test.py). Exit code: 0 every file loads with every field kept; 2 some load with fields the
game changed (read them in summary.txt); 1 some did not load.
usage: ingame_batch.py EXE GAME_DIR OUT_DIR [WORKERS [steps|rewards]]"""
import concurrent.futures
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from sample_jobs import sample_jobs  # noqa: E402
from wwsave import convert as conv  # noqa: E402

exe, game, out = [os.path.abspath(p) for p in sys.argv[1:4]]
workers = int(sys.argv[4]) if len(sys.argv) > 4 else 3
MODE = sys.argv[5] if len(sys.argv) > 5 else "steps"      # steps | rewards, for every case
OPTIONS = conv.Options.all(MODE)
os.makedirs(out, exist_ok=True)
jobs = sample_jobs(OPTIONS, out)


def run(job):
    name, path, sav = job
    env = dict(os.environ, SHADER_CACHE=os.path.join(out, name + ".shadercache"))
    r = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "scripts/ingame_test.py"), exe, game, sav,
                        os.path.join(out, name), "6"], capture_output=True, text=True, env=env)
    return name, path, r.returncode, r.stdout.strip()


with concurrent.futures.ThreadPoolExecutor(workers) as ex, open(os.path.join(out, "summary.txt"), "w") as log:
    results = {0: 0, 1: 0, 2: 0}
    for name, path, rc, text in ex.map(run, jobs):
        results[rc if rc in results else 1] += 1
        verdict = {0: "OK", 2: "DIFFERS"}.get(rc, "FAILED")
        line = "%s %s %s\n%s\n" % (name, verdict, path, "\n".join("    " + t for t in text.splitlines()))
        log.write(line)
        log.flush()
        print(line, end="", flush=True)
    total = "%d files: %d load with every field kept, %d load with fields the game changed, %d did not load\n" % (
        len(jobs), results[0], results[2], results[1])
    log.write(total)
    print(total, end="")
sys.exit(1 if results[1] else 2 if results[2] else 0)
