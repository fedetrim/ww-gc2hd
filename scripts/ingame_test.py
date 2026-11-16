#!/usr/bin/env python3
"""Load an HD save in the game itself and compare what the game holds in memory with the file.

Uses the native port of Wind Waker HD (ZeldaWWHDRecomp, built from your own copy of the game) and its
scenario runner: the game boots hidden and muted, goes from the title screen into Quest Log 1, runs
END seconds and dumps its in-memory save block (dSv_info_c).

usage: ingame_test.py EXE GAME_DIR CKING.SAV OUT_DIR [END_SECONDS]

Exit code: 0 the game holds every field as in the file; 2 it reached the end but some fields differ (they are
printed; expected when the scenario plays something); 1 the game did not reach the end of the scenario.
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from wwsave import hd, layout  # noqa: E402

RUNNER = os.environ.get("WW_RUNNER") or os.path.join(
    os.environ.get("WW_RESEARCH") or os.path.join(ROOT, "research"), "port-src/tools/gametest/run_scenario.sh")
# offset of each packed block inside the in-memory dSv_save_c (alignment padding differs)
MEM = {"status_a": 0x000, "status_b": 0x018, "return_place": 0x030, "item": 0x03C, "get_item": 0x051,
       "item_record": 0x066, "item_max": 0x06E, "bag_item": 0x076, "get_bag_item": 0x090,
       "bag_item_record": 0x09C, "collect": 0x0B4, "map": 0x0C4, "info": 0x148, "config": 0x1A4,
       "priest": 0x1AC, "ocean": 0x5C0, "event": 0x624, "reserve": 0x724}
MEM.update({"status_c%d" % i: 0x1BC + 0x70 * i for i in range(4)})
MEM.update({"memory%02d" % i: 0x380 + 0x24 * i for i in range(16)})
# fields the running game changes by itself within seconds of loading
VOLATILE = ("status_b.time", "status_b.date", "status_b.date_ipl", "status_b._field_8", "status_a.life")


def main():
    exe, game, sav, out = [os.path.abspath(p) for p in sys.argv[1:5]]
    end = sys.argv[5] if len(sys.argv) > 5 else "6"
    f = hd.HdFile.parse(open(sav, "rb").read())
    save_dir = out + ".save"
    shutil.rmtree(save_dir, ignore_errors=True)
    os.makedirs(os.path.join(save_dir, "user"))
    shutil.copy(sav, os.path.join(save_dir, "user", "cking.sav"))
    for extra in os.listdir(os.path.dirname(sav)):          # album files written next to the save
        if extra.startswith("cking_pic"):
            shutil.copy(os.path.join(os.path.dirname(sav), extra), os.path.join(save_dir, "user", extra))
    env = dict(os.environ, BOOT_TRIES="2")
    zsh = shutil.which("zsh")
    if not zsh:
        print("FAIL: the port's scenario runner (%s) is a zsh script and zsh was not found" % RUNNER)
        return 1
    r = subprocess.run([zsh, RUNNER, exe, game, save_dir, out, end] + sys.argv[6:], env=env,
                       capture_output=True, text=True)
    shutil.rmtree(save_dir, ignore_errors=True)             # the runner worked on its own copy
    print(r.stdout.strip())
    log = ""
    if os.path.exists(os.path.join(out, "log")):
        with open(os.path.join(out, "log"), errors="replace") as log_file:
            log = log_file.read()
    else:
        print("the runner wrote no log (%s); its output:\n%s" % (RUNNER, (r.stderr or "")[-800:]))
    done = os.path.exists(os.path.join(out, "test_done"))
    si = os.path.join(out, "si.bin")
    if not done or not os.path.exists(si):
        print("FAIL: the game did not reach the end of the scenario")
        print("\n".join(log.splitlines()[-25:]))
        return 1
    mem = open(si, "rb").read()
    src = f.slots[int(os.environ.get("WW_SLOT", "0"))]     # Quest Log to compare (0-based)
    # locate the save block inside the dump (dSv_info_c starts with dSv_save_c)
    base = 0x20                   # the dump starts at the save object; dSv_info_c is at +0x20
    diffs, same = [], 0
    for name, (off, size) in layout.FIELDS.items():
        block = name.split(".")[0]
        boff, _ = layout.BLOCKS[block]
        m = mem[base + MEM[block] + off - boff:base + MEM[block] + off - boff + size]
        if m == src.data[off:off + size]:
            same += 1
        elif name not in VOLATILE:
            diffs.append((name, src.data[off:off + size].hex(), m.hex()))
    print("in memory after %s s of play: %d fields identical to the file, %d differ" % (end, same, len(diffs)))
    for name, a, b in diffs:
        print("   %-28s file %s  game %s" % (name, a[:48], b[:48]))
    for line in log.splitlines():
        if any(k in line.lower() for k in ("halt", "crash", "assert", "fatal", "[save]")):
            print("   log:", line[:200])
    return 2 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
