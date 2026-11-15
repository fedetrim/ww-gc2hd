#!/usr/bin/env python3
"""Download the public Wind Waker saves the tests and the verification scripts use.

The saves are in the repository (samples/gc, samples/hd). This script checks them against
samples/checksums.sha256, and can fetch them again from the public places listed in samples/SOURCES.md
(GitHub repositories at pinned commits, archive.org, a few save sites, attachments of public GitHub
issues), including the original archives, which the repository does not keep.

    python3 scripts/fetch_samples.py            # download what is missing, then check
    python3 scripts/fetch_samples.py --check    # only compare samples/ with the expected checksums
    python3 scripts/fetch_samples.py --only gc/gc-saves.com --only gc/cryze

Downloads are data only: archives are unpacked, nothing in them is run. Archives other than .zip (.7z,
.rar, .tar.gz) need `bsdtar` (part of macOS; package libarchive-tools on Linux). A source that has gone
offline is reported and skipped; the tests run on whatever is present.
"""
import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES = os.path.join(ROOT, "samples")
sys.path.insert(0, ROOT)


def download(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (fetch_samples)"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def _safe(name):
    return not (name.startswith(("/", "\\")) or ".." in name.replace("\\", "/").split("/"))


def unpack(archive, dest, members=None):
    """Unpack an archive file into dest. Entries that would leave dest are refused."""
    os.makedirs(dest, exist_ok=True)
    if zipfile.is_zipfile(archive) and not members:
        with zipfile.ZipFile(archive) as z:
            names = [n for n in z.namelist() if _safe(n)]
            if len(names) != len(z.namelist()):
                raise RuntimeError("archive has entries outside its folder")
            z.extractall(dest, names)
        return
    if not shutil.which("bsdtar"):
        raise RuntimeError("bsdtar is needed to unpack %s" % os.path.basename(archive))
    listing = subprocess.run(["bsdtar", "-tf", archive], capture_output=True, text=True, check=True).stdout
    if not all(_safe(n) for n in listing.splitlines()):
        raise RuntimeError("archive has entries outside its folder")
    subprocess.run(["bsdtar", "-xf", archive, "-C", dest, "--no-same-owner", "--no-same-permissions"]
                   + (members or []), check=True)


def no_links(folder):
    """Refuse unpacked content that holds a symbolic link: copying it would follow the link and bring the
    content of a local file into samples/."""
    for base, dirs, files in os.walk(folder):
        for name in dirs + files:
            if os.path.islink(os.path.join(base, name)):
                raise RuntimeError("archive holds a symbolic link (%s)" % name)


def fetch(src):
    dest = os.path.join(SAMPLES, src["dest"])
    kind = src["kind"]
    if kind == "github":
        if os.path.exists(os.path.join(dest, "COMMIT.txt")):
            return "present"
        data = download("https://codeload.github.com/%s/zip/%s" % (src["repo"], src["commit"]))
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                if not all(_safe(n) for n in z.namelist()):
                    raise RuntimeError("archive has entries outside its folder")
                z.extractall(tmp)
            no_links(tmp)
            top = os.path.join(tmp, os.listdir(tmp)[0])
            os.makedirs(dest, exist_ok=True)
            if src.get("unpack_zips"):          # a repository of zipped saves: keep and unpack only those
                for folder, _, files in os.walk(os.path.join(top, src["only"])):
                    for name in files:
                        if name.endswith(".zip"):
                            os.makedirs(os.path.join(dest, "archives"), exist_ok=True)
                            kept = os.path.join(dest, "archives", name)
                            shutil.copy(os.path.join(folder, name), kept)
                            unpack(kept, os.path.join(dest, "extracted", name[:-4]))
                            no_links(os.path.join(dest, "extracted", name[:-4]))
            else:
                shutil.copytree(top, dest, dirs_exist_ok=True)
        with open(os.path.join(dest, "COMMIT.txt"), "w") as f:
            f.write(src["commit"] + "\n")
        return "downloaded"
    target = os.path.join(dest, src.get("archive_dir", ""), src["name"])
    extracted = os.path.normpath(os.path.join(dest, src.get("extracted", "extracted")))
    marker = os.path.join(dest, ".fetched-" + src["name"])      # written last: a failed fetch is retried
    if os.path.exists(marker) or (kind == "file" and os.path.exists(target)):
        return "present"
    os.makedirs(os.path.dirname(target), exist_ok=True)
    part = target + ".part"
    try:
        with open(part, "wb") as f:
            f.write(download(src["url"]))
        if kind == "archive":
            with tempfile.TemporaryDirectory(dir=dest) as tmp:
                unpack(part, tmp, src.get("members"))
                no_links(tmp)
                shutil.copytree(tmp, extracted, dirs_exist_ok=True)
        if kind == "archive" and src.get("keep_archive", True) is False:
            os.remove(part)
        else:
            os.replace(part, target)
    finally:
        if os.path.exists(part):
            os.remove(part)
    if src.get("raw_card"):                     # also cut the game's file out of the raw card image
        from wwsave import gc
        with open(target, "rb") as f:
            card = gc.load(f.read())
        out = os.path.join(dest, "extracted-gci")
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "01-GZLE-gczelda.gci"), "wb") as f:
            f.write(card.dentry + card.blocks)
    if kind == "archive":
        with open(marker, "w") as f:
            f.write(src["url"] + "\n")
    return "downloaded"


def _digest(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def check():
    """Every expected file must be at its path with its content; those that differ or are missing are
    listed. Save files that are not in the list are counted."""
    expected = {}
    with open(os.path.join(SAMPLES, "checksums.sha256")) as f:
        for line in f:
            digest, path = line.rstrip("\n").split("  ", 1)
            expected[path] = digest
    ok, wrong, missing = 0, [], []
    for path, digest in expected.items():
        full = os.path.join(SAMPLES, path)
        if not os.path.exists(full):
            missing.append(path)
        elif _digest(full) != digest:
            wrong.append(path)
        else:
            ok += 1
    print("expected files: %d; present with the expected content: %d; different content: %d; missing: %d" % (
        len(expected), ok, len(wrong), len(missing)))
    for label, paths in (("different", wrong), ("missing", missing)):
        for path in paths[:20]:
            print("  %s: %s" % (label, path))
        if len(paths) > 20:
            print("  ... and %d more" % (len(paths) - 20))
    extra = []
    for folder, _, files in os.walk(SAMPLES):
        for name in files:
            path = os.path.relpath(os.path.join(folder, name), SAMPLES)
            if path not in expected and (name.endswith((".gci", ".raw")) or
                                         (name.startswith("cking") and name.endswith(".sav"))):
                extra.append(path)
    if extra:
        # Not an error: a full download brings files the repository leaves out (.gitignore). But the tests
        # and the statistics read every save under samples/, so these take part in them.
        print("save files not in the list: %d (for example %s)" % (len(extra), sorted(extra)[0]))
    return not wrong and not missing


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="only compare samples/ with samples/checksums.sha256")
    ap.add_argument("--only", action="append", default=[], help="fetch only sources whose folder starts with this")
    a = ap.parse_args()
    if not a.check:
        with open(os.path.join(SAMPLES, "manifest.json")) as f:
            sources = json.load(f)
        failed = 0
        for src in sources:
            if a.only and not any(src["dest"].startswith(o) for o in a.only):
                continue
            label = "%s %s" % (src["dest"], src.get("name", src.get("repo", "")))
            try:
                print("%-11s %s" % (fetch(src), label), flush=True)
            except Exception as e:              # a dead link must not stop the rest
                failed += 1
                print("FAILED      %s: %s" % (label, e), flush=True)
        if failed:
            print("%d source(s) could not be fetched." % failed)
    sys.exit(0 if check() else 1)


if __name__ == "__main__":
    main()
