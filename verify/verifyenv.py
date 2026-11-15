"""Locations shared by the in-game verification scripts (verify/chests, verify/npcs).

Every path is derived from the repository root (the parent of this folder) and can be replaced with an
environment variable:

    variable         default                                 what it must hold
    WW_RESEARCH      <repo>/research                         the working folder of docs/SETUP-RESEARCH.md
    WW_PORT_EXE      $WW_RESEARCH/port-src/build/cmake/wwhd  the native port, built with both test-aid patches
                                                             (scripts/port-ship-warp.patch, port-kill-enemies.patch)
    WW_HD_GAME       $WW_RESEARCH/hd-game/game               extracted Wind Waker HD, USA v0
    WW_HD_STAGES     $WW_RESEARCH/hd-game/stages.json        output of scripts/hd_stage_dump.py (save record per stage)
    WW_VERIFY_OUT    $WW_RESEARCH/out/verify                 where the runs write (chests/CASE/, npcs/NAME/)
    WW_RUNNER        <repo>/research/port-src/tools/gametest/run_scenario.sh
                                                             the port's scenario runner (read by scripts/ingame_test.py)

The shell scripts of these folders (q.sh, run_marie.sh, run_lenzo.sh) use the same variables and defaults.
Run `python3 verify/verifyenv.py` to print the resolved locations and whether each exists.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.environ.get("WW_RESEARCH") or os.path.join(ROOT, "research")
EXE = os.environ.get("WW_PORT_EXE") or os.path.join(RES, "port-src", "build", "cmake", "wwhd")
GAME = os.environ.get("WW_HD_GAME") or os.path.join(RES, "hd-game", "game")
STAGES = os.environ.get("WW_HD_STAGES") or os.path.join(RES, "hd-game", "stages.json")
OUT = os.environ.get("WW_VERIFY_OUT") or os.path.join(RES, "out", "verify")


def out_dir(kind):
    """$WW_VERIFY_OUT/<kind> (chests or npcs), created when missing."""
    d = os.path.join(OUT, kind)
    os.makedirs(d, exist_ok=True)
    return d


if __name__ == "__main__":
    runner = os.environ.get("WW_RUNNER") or os.path.join(ROOT, "research/port-src/tools/gametest/run_scenario.sh")
    for k, v in (("WW_RESEARCH", RES), ("WW_PORT_EXE", EXE), ("WW_HD_GAME", GAME), ("WW_HD_STAGES", STAGES),
                 ("WW_RUNNER", runner), ("WW_VERIFY_OUT", OUT)):
        print("%-14s %-7s %s" % (k, "ok" if os.path.exists(v) else "MISSING", os.path.relpath(v, ROOT) if v.startswith(ROOT) else v))
