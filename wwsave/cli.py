"""ww-gc2hd: convert a GameCube Wind Waker save into a Wind Waker HD (Wii U) save."""
import argparse
import textwrap
import os
import sys

from . import convert as conv
from . import describe, gc, hd

CEMU_HINT = "mlc01/usr/save/00050000/10143500/user/80000001/cking.sav"


def _read_gc(path):
    with open(path, "rb") as f:
        return gc.load(f.read())


def _read_hd(path):
    if os.path.isdir(path):
        path = os.path.join(path, "cking.sav")
    with open(path, "rb") as f:
        return hd.HdFile.parse(f.read(), strict=False)


def _is_hd(path):
    return os.path.isdir(path) or os.path.getsize(path) == hd.FILE_SIZE


def _flag(key):
    return "--" + key.replace("_", "-")


def _ask(decision, slot):
    print()
    print("Quest Log %d: %s" % (slot + 1, decision.question))
    for i, (_, text) in enumerate(decision.choices):
        print("  %d) %s" % (i + 1, text))
    while True:
        try:
            answer = input("Choice (1 or 2): ").strip()
        except EOFError:
            sys.exit("\nno choice made for %s" % _flag(decision.key))
        if answer.isdigit() and 1 <= int(answer) <= len(decision.choices):
            return decision.choices[int(answer) - 1][0]


def _case_value(text):
    """'steps' | 'rewards' for every Quest Log, or per Quest Log: '1=steps,3=rewards'."""
    if text in conv.MODES:
        return text
    value = {}
    for part in text.split(","):
        log, _, mode = part.partition("=")
        if log not in ("1", "2", "3") or mode not in conv.MODES:
            raise argparse.ArgumentTypeError("use steps, rewards, or per Quest Log like 1=steps,2=rewards")
        value[int(log) - 1] = mode
    return value


def cmd_convert(a):
    card = _read_gc(a.input)
    if card.game_code != b"GZLE01" and not a.allow_region:
        sys.exit("%s is a %s save (%s). Only USA (GZLE01) saves are supported; --allow-region converts it "
                 "anyway (unverified)." % (a.input, card.region, card.game_code.decode()))
    slots = card.slots()
    if not any(s is not None and not s.is_new() for s in slots):
        sys.exit("%s holds no used save file." % a.input)

    options = conv.Options(name=a.name,
                           swift_sail=bool(a.swift_sail), hero_mode=bool(a.hero_mode))
    for key in conv.Options.CASES:
        setattr(options, key, getattr(a, key) or a.all)
    # A case has no default: ask (terminal) or stop and name the options (script).
    while True:
        open_cases = [(d, s) for d in conv.decisions_for(slots, options) for s in d.slots
                      if getattr(options.for_slot(s), d.key) is None]
        if not open_cases:
            break
        if not sys.stdin.isatty():
            lines = ["%s holds states the two games do not share. Choose for each one (or --all for all;"
                     % a.input, "per Quest Log: 1=steps,2=rewards):"]
            for d in dict.fromkeys(d.key for d, _ in open_cases):
                d = next(x for x, _ in open_cases if x.key == d)
                lines.append("")
                lines.append("%s steps|rewards   (Quest Log %s)" % (
                    _flag(d.key), ", ".join(str(s + 1) for x, s in open_cases if x.key == d.key)))
                lines.append("  " + d.question)
                lines.extend("    %s" % text for _, text in d.choices)
            sys.exit("\n".join(lines))
        d, s = open_cases[0]
        options.answer(d.key, s, _ask(d, s))

    out_file, reports = conv.convert(card, options)
    data = out_file.serialize()
    hd.HdFile.parse(data)                      # the output must pass the same checks as a real save

    target = os.path.join(a.output, "cking.sav")
    if os.path.exists(target) and not a.force:
        sys.exit("%s already exists. Use --force to replace it (the old file is kept as cking.sav.bak)."
                 % target)
    os.makedirs(a.output, exist_ok=True)
    if os.path.exists(target):
        os.replace(target, target + ".bak")
    with open(target, "wb") as f:
        f.write(data)
    album = {} if a.no_pictures else conv.convert_pictures(card)
    for name, content in album.items():
        with open(os.path.join(a.output, name), "wb") as f:
            f.write(content)

    print()
    print("%s (%s, %s) -> %s" % (a.input, card.game_code.decode(), card.source, target))
    for rep in reports:
        if not rep.used:
            print("Quest Log %d: empty" % (rep.slot + 1))
        else:
            print("Quest Log %d: %s" % (rep.slot + 1, out_file.name(rep.slot)))
            if not a.quiet:
                print(describe.format_summary(describe.summarize(out_file.slots[rep.slot],
                                                                 out_file.name(rep.slot), hd=True), "    "))
        if rep.changes:
            print("    What changed and why:")
        for c in rep.changes:
            print(textwrap.fill(c, 100, initial_indent="    - ", subsequent_indent="      "))
        if rep.totals:
            print("    What you hold, GameCube -> HD (each difference is explained above):")
            for label, before, after in rep.totals:
                delta = " (%+d)" % (after - before) if isinstance(after, int) else ""
                print("      %-16s %s -> %s%s" % (label + ":", before, after, delta))
        if rep.pictures:
            print("    %s" % ("%d Picto Box picture(s) converted to the HD album (cking_pic%d_*.sav, "
                              "cking_pic_order%d.sav)" % (rep.pictures, rep.slot, rep.slot) if not a.no_pictures
                              else "%d Picto Box picture(s) left out (--no-pictures)" % rep.pictures))
        for w in rep.warnings:
            print("    WARNING: %s" % w)
    print()
    print("Copy %s into the game's save folder (Cemu, USA: %s)." % (
        "cking.sav and the cking_pic* files" if album else "cking.sav", os.path.dirname(CEMU_HINT)))
    print("It replaces all three Quest Logs, so back up the existing save folder first.")


def cmd_info(a):
    if _is_hd(a.file):
        f = _read_hd(a.file)
        print("Wind Waker HD save")
        for p in f.problems:
            print("  PROBLEM: %s" % p)
        for s in range(3):
            save = f.slots[s]
            if save.u("info.save_count") == 0:
                print("Quest Log %d: empty%s" % (s + 1, " (New Game+ ready)" if save.u("info.clear_count") else ""))
                continue
            print("Quest Log %d:" % (s + 1))
            print(describe.format_summary(describe.summarize(save, f.name(s), hd=True)))
            opt = f.extras[s]["options"]
            print("  %-22s %s" % ("Hero Mode:", "yes" if opt[hd.OPT_HERO_MODE] == 1 else "no"))
    else:
        card = _read_gc(a.file)
        print("Wind Waker GameCube save (%s, %s)" % (card.game_code.decode(), card.region))
        for k, (block_ok, slot_ok) in enumerate(card.copy_status()):
            if not block_ok or not all(slot_ok):
                print("  note: save copy %d has a bad checksum" % (k + 1))
        pictures = card.pictures()
        for s, save in enumerate(card.slots()):
            if save is None:
                print("File %d: damaged (bad checksum in both copies)" % (s + 1))
            elif save.is_new():
                print("File %d: empty" % (s + 1))
            else:
                print("File %d:" % (s + 1))
                print(describe.format_summary(describe.summarize(save, conv.gc_name(save, card.game_code))))
                print("  %-22s %d" % ("Pictures:", len(pictures[s])))


def cmd_verify(a):
    f = _read_hd(a.file)
    if f.problems:
        for p in f.problems:
            print("PROBLEM: %s" % p)
        sys.exit(1)
    print("OK: size, three Quest Log checksums, format word and HD section CRC are valid.")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ww-gc2hd", description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)

    c = sub.add_parser("convert", help="GameCube save (.gci/.gcs/.sav or raw memory card) -> HD cking.sav")
    c.add_argument("input")
    c.add_argument("-o", "--output", required=True, help="folder to write cking.sav into")
    modes = list(conv.MODES)
    c.add_argument("--all", choices=modes, help="answer for every case not given its own option")
    for k in (2, 4, 6, 7, 8):
        c.add_argument("--triforce-chart-%d" % k, type=_case_value, metavar="MODE",
                       help="Triforce Chart %d owned without its shard (HD: the chest holds the shard)" % k)
    c.add_argument("--horseshoe-chest", type=_case_value, metavar="MODE", help="Horseshoe Island lookout chest open (HD: Treasure Chart 43)")
    c.add_argument("--star-belt-chest", type=_case_value, metavar="MODE", help="Star Belt Archipelago lookout chest open (HD: Treasure Chart 44)")
    c.add_argument("--floor50", type=_case_value, metavar="MODE",
                   help="Savage Labyrinth floor-50 chest open (GameCube: Piece of Heart, HD: Hero's Charm)")
    c.add_argument("--pawprint-chest", type=_case_value, metavar="MODE", help="Pawprint Isle Wizzrobe cave chest open (HD: Treasure Chart 46)")
    c.add_argument("--marie", type=_case_value, metavar="MODE",
                   help="Mrs. Marie's 40 Joy Pendant reward given (GameCube: Hero's Charm, HD: Treasure Chart 45)")
    c.add_argument("--lenzo", type=_case_value, metavar="MODE",
                   help="Lenzo's third picture accepted without the Deluxe Picto Box (HD gives it at that step)")
    c.add_argument("--swift-sail", dest="swift_sail", action="store_true", default=None,
                   help="upgrade an owned Sail to the HD Swift Sail")
    c.add_argument("--no-swift-sail", dest="swift_sail", action="store_false")
    c.add_argument("--hero-mode", dest="hero_mode", action="store_true", default=None, help="enable HD Hero Mode")
    c.add_argument("--no-hero-mode", dest="hero_mode", action="store_false")
    c.add_argument("--no-pictures", action="store_true",
                   help="do not write the Picto Box album files (cking_pic*.sav)")
    c.add_argument("--name", help="player name for the HD save (max 8 characters; default: the GameCube name)")
    c.add_argument("--force", action="store_true", help="replace an existing cking.sav (kept as .bak)")
    c.add_argument("--allow-region", action="store_true", help="also accept Japanese / European saves (unverified)")
    c.add_argument("--quiet", action="store_true", help="do not print the save summary")
    c.set_defaults(func=cmd_convert)

    i = sub.add_parser("info", help="show what a GameCube or HD save contains")
    i.add_argument("file")
    i.set_defaults(func=cmd_info)

    v = sub.add_parser("verify", help="check the structure and checksums of an HD cking.sav")
    v.add_argument("file")
    v.set_defaults(func=cmd_verify)

    a = ap.parse_args(argv)
    try:
        a.func(a)
    except (gc.GcError, hd.HdError, conv.ConversionError, OSError) as e:
        sys.exit("error: %s" % e)


if __name__ == "__main__":
    main()
