"""Shared by the in-game batch scripts: one converted save per used file of every USA GameCube sample."""
import glob
import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sample_jobs(options, out):
    """Convert each USA sample card once and write, for every distinct used file on it, a cking.sav with
    that file as Quest Log 1 (the test rig loads Quest Log 1). Returns [(name, label, path of the save)]."""
    import sys
    sys.path.insert(0, ROOT)
    from wwsave import convert as conv, gc

    jobs, seen = [], set()
    for path in sorted(glob.glob(os.path.join(ROOT, "samples/gc/**/*.gci"), recursive=True)):
        if "Hacked_File" in path or "/rejected/" in path:
            continue
        with open(path, "rb") as f:
            card = gc.load(f.read())
        if card.game_code != b"GZLE01":
            continue
        wanted = []
        for slot, g in enumerate(card.slots()):
            if g is None or g.is_new() or conv.health(g):   # only files that are converted
                continue
            key = hashlib.md5(bytes(g)).hexdigest()
            if key not in seen:
                seen.add(key)
                wanted.append(slot)
        if not wanted:
            continue
        data = conv.convert(card, options)[0].serialize()
        for slot in wanted:
            from wwsave import hd
            name = "%02d" % len(jobs)
            sav = os.path.join(out, name + ".sav")
            with open(sav, "wb") as f:
                f.write(hd.HdFile.parse(data).move_to_quest_log_1(slot).serialize())
            jobs.append((name, "%s file %d" % (os.path.relpath(path, ROOT), slot + 1), sav))
    return jobs
