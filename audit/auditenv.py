"""Locations shared by the audit scripts (audit/*/).

Nothing here is specific to one machine: every path is derived from the repository root (the parent of this
folder) and can be replaced with an environment variable.

    variable          default                       what it must hold
    WW_RESEARCH       <repo>/research               the working folder described in docs/SETUP-RESEARCH.md
    WW_GC_ISO         the only *.iso in             GameCube disc image, USA (GZLE01); a plain or NKit .iso whose
                      $WW_RESEARCH/gc-disc/         file table (FST) is readable
    WW_HD_GAME        $WW_RESEARCH/hd-game/game     extracted Wind Waker HD, USA v0 (code/cking.rpx, content/...)
    WW_TWW            $WW_RESEARCH/tww              clone of zeldaret/tww (GameCube decompilation)
    WW_WWHD           $WW_RESEARCH/wwhd             clone of ZeldaWWHDDecomp/wwhd (holds wwhd_src/)
    WW_WWRANDO        $WW_RESEARCH/wwrando          clone of LagoLunatic/wwrando
    WW_TWWHD_RANDO    $WW_RESEARCH/twwhd-rando      clone of SuperDude88/TWWHD-Randomizer
    WW_AUDIT_OUT      $WW_RESEARCH/out              where the scripts write; one subfolder per audit

Outputs never go into the published tree: out_dir("rewards") is $WW_AUDIT_OUT/rewards, created on demand
(research/ is git-ignored).

Run `python3 -I audit/auditenv.py` to print the resolved locations and whether each exists.
`python3 -I audit/auditenv.py --fst OUT.json` writes the disc's file table as {path: [offset, size]}, the
GC_FST.json argument of scripts/event_diff.py.
"""
import glob
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT = os.path.join(ROOT, "audit")
SCRIPTS = os.path.join(ROOT, "scripts")                 # gc_stage_dump.py / hd_stage_dump.py container readers
MACHINE_CODE = os.path.join(AUDIT, "machine-code")      # modules other audits import (gc_extract, compare, ...)
REWARDS = os.path.join(AUDIT, "rewards")

RES = os.environ.get("WW_RESEARCH") or os.path.join(ROOT, "research")
HD_GAME = os.environ.get("WW_HD_GAME") or os.path.join(RES, "hd-game", "game")
TWW = os.environ.get("WW_TWW") or os.path.join(RES, "tww")
WWHD = os.environ.get("WW_WWHD") or os.path.join(RES, "wwhd")
WWRANDO = os.environ.get("WW_WWRANDO") or os.path.join(RES, "wwrando")
TWWHD_RANDO = os.environ.get("WW_TWWHD_RANDO") or os.path.join(RES, "twwhd-rando")
OUT = os.environ.get("WW_AUDIT_OUT") or os.path.join(RES, "out")


def gc_iso():
    """Path of the GameCube disc image: $WW_GC_ISO, else the only .iso in research/gc-disc/."""
    p = os.environ.get("WW_GC_ISO")
    if p:
        return p
    found = sorted(glob.glob(os.path.join(RES, "gc-disc", "*.iso")))
    if len(found) != 1:
        sys.exit("GameCube disc image: expected exactly one .iso in %s (found %d); put it there or set WW_GC_ISO"
                 % (os.path.join(RES, "gc-disc"), len(found)))
    return found[0]


_fst = None


def gc_fst():
    """{path on the disc: (offset in the image, size)} read from the image's file table."""
    global _fst
    if _fst is None:
        with open(gc_iso(), "rb") as f:
            h = f.read(0x440)
            fst_off, fst_size = struct.unpack(">II", h[0x424:0x42C])
            f.seek(fst_off)
            fst = f.read(fst_size)
        n = struct.unpack(">I", fst[8:12])[0]
        strs = n * 12
        dirs, paths, i = [(n, "")], {}, 1
        while i < n:
            while i >= dirs[-1][0]:
                dirs.pop()
            is_dir = fst[i * 12]
            name_off = int.from_bytes(fst[i * 12 + 1:i * 12 + 4], "big")
            a, b = struct.unpack(">II", fst[i * 12 + 4:i * 12 + 12])
            name = fst[strs + name_off:fst.index(b"\0", strs + name_off)].decode("latin-1")
            p = dirs[-1][1] + "/" + name
            if is_dir:
                dirs.append((b, p))
            else:
                paths[p] = (a, b)
            i += 1
        _fst = paths
    return _fst


def out_dir(audit):
    """$WW_AUDIT_OUT/<audit>, created when missing."""
    d = os.path.join(OUT, audit)
    os.makedirs(d, exist_ok=True)
    return d


def out_file(audit, name):
    return os.path.join(out_dir(audit), name)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--fst"]:
        import json
        json.dump({k: list(v) for k, v in gc_fst().items()}, open(sys.argv[2], "w"))
        sys.exit(0)
    rows = [("WW_RESEARCH", RES), ("WW_HD_GAME", HD_GAME), ("WW_TWW", TWW), ("WW_WWHD", WWHD),
            ("WW_WWRANDO", WWRANDO), ("WW_TWWHD_RANDO", TWWHD_RANDO), ("WW_AUDIT_OUT", OUT)]
    isos = [os.environ["WW_GC_ISO"]] if os.environ.get("WW_GC_ISO") else sorted(glob.glob(os.path.join(RES, "gc-disc", "*.iso")))
    rows.insert(1, ("WW_GC_ISO", isos[0] if len(isos) == 1 else "(%d .iso files in %s)" % (len(isos), os.path.join(RES, "gc-disc"))))
    for k, v in rows:
        print("%-15s %-7s %s" % (k, "ok" if os.path.exists(v) else "MISSING", os.path.relpath(v, ROOT) if v.startswith(ROOT) else v))
