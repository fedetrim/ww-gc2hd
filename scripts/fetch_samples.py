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
            else:
                shutil.copytree(top, dest, dirs_exist_ok=True)
        with open(os.path.join(dest, "COMMIT.txt"), "w") as f:
            f.write(src["commit"] + "\n")
        return "downloaded"
    target = os.path.join(dest, src.get("archive_dir", ""), src["name"])
    extracted = os.path.join(dest, src.get("extracted", "extracted"))
    done = extracted if kind == "archive" and src.get("keep_archive", True) is False else target
    if os.path.exists(done) and (kind == "file" or os.path.isdir(extracted)):
        return "present"
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "wb") as f:
        f.write(download(src["url"]))
    if kind == "archive":
        unpack(target, extracted, src.get("members"))
        if src.get("keep_archive", True) is False:
            os.remove(target)
    if src.get("raw_card"):                     # also cut the game's file out of the raw card image
        from wwsave import gc
        with open(target, "rb") as f:
            card = gc.load(f.read())
        out = os.path.join(dest, "extracted-gci")
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "01-GZLE-gczelda.gci"), "wb") as f:
            f.write(card.dentry + card.blocks)
    return "downloaded"


def check():
    expected = {}
    with open(os.path.join(SAMPLES, "checksums.sha256")) as f:
        for line in f:
            digest, path = line.rstrip("\n").split("  ", 1)
            expected[path] = digest
    have = set()
    for folder, _, files in os.walk(SAMPLES):
        for name in files:
            if name.endswith((".gci", ".raw", ".sav")):
                with open(os.path.join(folder, name), "rb") as f:
                    have.add(hashlib.sha256(f.read()).hexdigest())
    same_path = sum(1 for path, digest in expected.items()
                    if os.path.exists(os.path.join(SAMPLES, path)) and digest in have)
    by_content = sum(1 for digest in expected.values() if digest in have)
    print("expected files: %d; present with the same content: %d (%d at the same path)" % (
        len(expected), by_content, same_path))
    missing = sorted(path for path, digest in expected.items() if digest not in have)
    for path in missing[:20]:
        print("  missing: %s" % path)
    if len(missing) > 20:
        print("  ... and %d more" % (len(missing) - 20))
    return not missing


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
