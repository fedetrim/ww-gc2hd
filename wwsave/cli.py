"""ww-gc2hd: convert a GameCube Wind Waker save into a Wind Waker HD (Wii U) save."""
import argparse
import textwrap
import time
import os
import struct
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
    # by size, or by the name the game gives its save (a damaged one is then reported as an HD save)
    return (os.path.isdir(path) or os.path.getsize(path) == hd.FILE_SIZE
            or os.path.basename(path).lower() == "cking.sav")


def _flag(key):
    return "--" + key.replace("_", "-")


def _ask(decision, slot):
    print()
    question, choices = decision.text(slot)
    print("Quest Log %d: %s" % (slot + 1, question))
    for i, (_, text) in enumerate(choices):
        print("  %d) %s" % (i + 1, text))
    while True:
        try:
            answer = input("Choice (1 or 2): ").strip()
        except EOFError:
            sys.exit("\nno choice made for %s" % _flag(decision.key))
        if answer in [str(i + 1) for i in range(len(choices))]:
            return choices[int(answer) - 1][0]


def _case_value(text):
    """'steps' | 'rewards' for every Quest Log, or per Quest Log: '1=steps,3=rewards'."""
    if text in conv.MODES:
        return text
    value = {}
    for part in text.split(","):
        log, _, mode = part.partition("=")
        if log not in ("1", "2", "3") or mode not in conv.MODES:
            raise argparse.ArgumentTypeError("use steps, rewards, or per Quest Log like 1=steps,2=rewards")
        if int(log) - 1 in value:
            raise argparse.ArgumentTypeError("Quest Log %s is answered twice" % log)
        value[int(log) - 1] = mode
    return value


def cmd_convert(a):
    card = _read_gc(a.input)
    if card.game_code != b"GZLE01" and not a.allow_region:
        sys.exit("%s is a %s save (%s). Only USA (GZLE01) saves are supported; --allow-region converts it "
                 "anyway (unverified)." % (a.input, card.region, card.code))
    slots = card.slots()
    if not any(s is not None and not s.is_new() for s in slots):
        sys.exit("%s holds no used save file." % a.input)

    if os.path.exists(a.output) and not os.path.isdir(a.output):
        sys.exit("%s is a file; -o takes the folder to write cking.sav into." % a.output)
    # Checked before any question is asked. A save is cking.sav plus its album files. One already in the folder is never mixed with the new one
    # and never lost: with --force all of it is moved to a backup folder first.
    target = os.path.join(a.output, "cking.sav")
    existing = []
    if os.path.isdir(a.output):
        existing = sorted(n for n in os.listdir(a.output)
                          if n == "cking.sav" or (n.startswith("cking_pic") and n.endswith(".sav")))
    if existing and not a.force:
        sys.exit("%s already holds a save (%s). Use --force to replace it: the files there are first moved to "
                 "a backup folder inside it." % (a.output, ", ".join(existing[:3]) +
                                                 (" and %d more" % (len(existing) - 3) if len(existing) > 3 else "")))
    used = [s for s, g in enumerate(slots) if g is not None and not g.is_new()]
    names = {}
    for value in a.name or []:
        log, sep, name = value.partition("=")
        if sep and log in ("1", "2", "3"):
            if int(log) - 1 in names:
                sys.exit("--name: Quest Log %s is named twice." % log)
            if int(log) - 1 not in used:
                sys.exit("--name %s: Quest Log %s is not a used file on this card (used: %s)." % (
                    value, log, ", ".join(str(s + 1) for s in used)))
            names[int(log) - 1] = name
        elif sep and log.isdigit():
            sys.exit("--name %s: there is no Quest Log %s (1 to 3)." % (value, log))
        elif len(used) == 1:
            if used[0] in names:
                sys.exit("--name: Quest Log %d is named twice." % (used[0] + 1))
            names[used[0]] = value
        else:
            sys.exit("--name %s: this card has %d used files. Say which Quest Log gets the name, for example "
                     "--name %d=%s (the option can be repeated)." % (value, len(used), used[0] + 1, value))
    options = conv.Options(name=names or None, swift_sail=bool(a.swift_sail), hero_mode=bool(a.hero_mode))
    for key in conv.Options.CASES:
        value = getattr(a, key)
        if isinstance(value, dict):                         # a copy: answers given later are not "typed"
            value = {**({s: a.all for s in range(3)} if a.all else {}), **value}
        setattr(options, key, value or a.all)
    # A case has no default: ask (terminal) or stop and name the options (script).
    def open_cases(opts):
        return [(d, s) for d in conv.decisions_for(slots, opts) for s in d.slots
                if getattr(opts.for_slot(s), d.key) is None]

    while True:
        pending = open_cases(options)
        if not pending:
            break
        # questions need a terminal on both ends: with the output redirected they would go into the file
        if not (sys.stdin.isatty() and sys.stdout.isatty()):
            listed = {}
            for d, s in pending:
                question, choices = d.text(s)
                dep = d.depends.get(s)
                note = ""
                if dep and getattr(options.for_slot(s), dep[0]) is None:
                    note = "   only needed with %s %s" % (_flag(dep[0]), dep[1])
                listed.setdefault((d.key, question, tuple(choices), note), []).append(s)
            lines = ["%s holds states the two games do not share. Choose for each one (or --all for all;"
                     % a.input, "per Quest Log: 1=steps,2=rewards):"]
            for (key, question, choices, note), logs in listed.items():
                lines.append("")
                lines.append("%s steps|rewards   (Quest Log %s)%s" % (
                    _flag(key), ", ".join(str(s + 1) for s in sorted(set(logs))), note))
                lines.append("  " + question)
                lines.extend("    %s" % text for _, text in choices)
            sys.exit("\n".join(lines))
        d, s = pending[0]
        options.answer(d.key, s, _ask(d, s))

    out_file, reports = conv.convert(card, options)
    # An answer typed for a Quest Log that is not in that case did nothing: say so (a mistyped number
    # would otherwise leave the intended Quest Log with the --all answer).
    in_case = {(d.key, s) for d in conv.decisions_for(slots, options) for s in d.slots}
    in_case |= set(conv.settled_answers(slots, options))
    for key in conv.Options.CASES:
        typed = getattr(a, key)
        if isinstance(typed, dict):
            for s, mode in sorted(typed.items()):
                if (key, s) not in in_case:
                    print("note: %s %d=%s was not used: Quest Log %d is not in that case." % (
                        _flag(key), s + 1, mode, s + 1), file=sys.stderr)
    for (key, s), (why, applied) in conv.settled_answers(slots, options).items():
        given = getattr(a, key)                 # an answer typed by hand that had no effect is said
        given = given.get(s) if isinstance(given, dict) else given
        if given and given != applied:
            reports[s].warnings.append("%s %s was not used: %s" % (_flag(key), given, why))
    data = out_file.serialize()
    hd.HdFile.parse(data)                      # the output must pass the same checks as a real save

    album = {} if a.no_pictures else conv.convert_pictures(card)       # everything is built before writing

    os.makedirs(a.output, exist_ok=True)
    backup = None
    if existing:
        stamp, n = time.strftime("backup-%Y%m%d-%H%M%S"), 0
        backup = os.path.join(a.output, stamp)
        while os.path.exists(backup):
            n += 1
            backup = os.path.join(a.output, "%s-%d" % (stamp, n))
        os.makedirs(backup)
        for name in existing:
            os.replace(os.path.join(a.output, name), os.path.join(backup, name))
    try:
        with open(target, "wb") as f:
            f.write(data)
        for name, content in album.items():
            with open(os.path.join(a.output, name), "wb") as f:
                f.write(content)
    except OSError as e:
        sys.exit("error: %s\nThe new save in %s is incomplete.%s" % (
            e, a.output, " The save that was there is untouched in %s." % backup if backup else ""))

    print()
    print("%s (%s, %s) -> %s" % (a.input, card.code, card.source, target))
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
    print("It replaces all three Quest Logs and their albums: back up the game's save folder first, and remove "
          "its cking_pic* files before copying.")
    if backup:
        print("The save that was in %s is in %s." % (a.output, backup))


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
        print("Wind Waker GameCube save (%s, %s)" % (card.code, card.region))
        for k, (block_ok, slot_ok) in enumerate(card.copy_status()):
            if not block_ok or not all(slot_ok):
                print("  note: save copy %d has a bad checksum" % (k + 1))
        pictures = card.pictures()
        for s, save in enumerate(card.slots()):
            if save is None:
                print("File %d: damaged (the game cannot read it: bad checksum)" % (s + 1))
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
    c.add_argument("--swift-sail", action="store_true", help="upgrade an owned Sail to the HD Swift Sail")
    c.add_argument("--hero-mode", action="store_true", help="enable HD Hero Mode")
    c.add_argument("--no-pictures", action="store_true",
                   help="do not write the Picto Box album files (cking_pic*.sav)")
    c.add_argument("--name", action="append", metavar="NAME or N=NAME",
                   help="player name for the HD save (max 8 characters; default: the GameCube name). With more "
                        "than one used file, name a Quest Log: --name 2=Zelda (repeatable)")
    c.add_argument("--force", action="store_true",
                   help="replace a save already in the output folder (it is moved to a backup folder there)")
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
    for stream in (sys.stdout, sys.stderr):     # a name the terminal cannot show must not stop the report
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")
    try:
        a.func(a)
    except KeyboardInterrupt:
        sys.exit("\ninterrupted")
    except (gc.GcError, hd.HdError, conv.ConversionError, OSError, OverflowError, ValueError, struct.error) as e:
        sys.exit("error: %s" % e)


if __name__ == "__main__":
    main()
