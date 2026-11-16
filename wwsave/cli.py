"""ww-gc2hd: convert a GameCube Wind Waker save into a Wind Waker HD (Wii U) save."""
import argparse
import textwrap
import time
import os
import sys

from . import convert as conv
from . import describe, gc, hd, term
from .term import paint

EXIT_PARTIAL = 3            # convert wrote the save, but left out a used file that is not healthy
                            # (1: nothing written; 2: wrong arguments, as argparse reports them)
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


def _summary(save, name, indent="  ", hd_save=False):
    """The summary of one file; in a terminal with dimmed labels and long values wrapped."""
    on = term.styled()
    return describe.format_summary(describe.summarize(save, name, hd=hd_save), indent,
                                   width=term.width() if on else None,
                                   label_style=(lambda label: paint(label, "dim")) if on else None)


def _flag(key):
    return "--" + key.replace("_", "-")


def _ask(decision, slot):
    print()
    question, choices = decision.text(slot)
    if not term.styled():
        print("Quest Log %d: %s" % (slot + 1, question))
        for i, (_, text) in enumerate(choices):
            print("  %d) %s" % (i + 1, text))
    else:
        print(paint("Quest Log %d  %s" % (slot + 1, _flag(decision.key)), "bold", "cyan"))
        print("\n".join(term.wrap(question)))
        for i, (_, text) in enumerate(choices):
            head, sep, body = text.partition(": ")          # "by steps: what it implies"
            if not (sep and head.startswith("by ")):
                head, body = "", text
            lines = term.wrap(text, "  %d) " % (i + 1), "     ")
            start = "  %d) %s" % (i + 1, head + ":" if head else "")
            if head and lines[0].startswith(start):
                lines[0] = "  %s %s%s" % (paint("%d)" % (i + 1), "bold", "cyan"), paint(head + ":", "bold"),
                                          lines[0][len(start):])
            print("\n".join(lines))
    while True:
        try:
            answer = input(paint("Choice (1 or 2): ", "bold")).strip()
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


def _print_gc(card):
    """What a GameCube card file holds, file by file."""
    print(paint("Wind Waker GameCube save (%s, %s)" % (card.code, card.region), "bold"))
    for k, (block_ok, slot_ok) in enumerate(card.copy_status()):
        if not block_ok or not all(slot_ok):
            print("  %s save copy %d has a bad checksum" % (paint("note:", "yellow"), k + 1))
    pictures = card.pictures()
    for s, save in enumerate(card.slots()):
        if save is None:
            print("%s %s" % (paint("File %d:" % (s + 1), "bold"),
                             paint("damaged (the game cannot read it: bad checksum)", "red")))
        elif save.is_new():
            print("%s %s" % (paint("File %d:" % (s + 1), "bold"), paint("empty", "dim")))
        else:
            print(paint("File %d:" % (s + 1), "bold", "cyan"))
            print(_summary(save, conv.gc_name(save, card.game_code)))
            print("  %s %d" % (paint("%-22s" % "Pictures:", "dim"), len(pictures[s])))
            for p in conv.health(save):
                print("\n".join(term.wrap(p, "  NOT CONVERTIBLE: ", "    ")).replace(
                    "NOT CONVERTIBLE:", paint("NOT CONVERTIBLE:", "bold", "red"), 1)
                    if term.styled() else "  NOT CONVERTIBLE: %s" % p)


def _confirm(a, card):
    """In a terminal: show what the input holds and ask before going on (--yes skips this), so that a
    wrong file is noticed before its cases are answered."""
    print(paint(a.input, "dim"))
    _print_gc(card)
    print()
    try:
        answer = input(paint("Convert this save to %s? (y/n): " % os.path.join(a.output, "cking.sav"),
                             "bold")).strip().lower()
    except EOFError:
        answer = ""
    if answer not in ("y", "yes"):
        sys.exit(paint("Nothing was converted.", "yellow", stream=sys.stderr))


def cmd_convert(a):
    card = _read_gc(a.input)
    if card.game_code != b"GZLE01" and not a.allow_region:
        sys.exit("%s is a %s save (%s). Only USA (GZLE01) saves are supported; --allow-region converts it "
                 "anyway (unverified)." % (a.input, card.region, card.code))
    slots = card.slots()
    if not any(s is not None and not s.is_new() for s in slots):
        if any(s is None for s in slots):
            sys.exit("%s holds no save file the game can read: %s damaged (bad checksum)." % (
                a.input, " and ".join("file %d is" % (i + 1) for i, s in enumerate(slots) if s is None)))
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
    healthy = [s for s, g in enumerate(slots) if conv.is_converted(g)]
    if not healthy:                             # checked first: nothing is asked or written
        problems = ["File %d: %s" % (s + 1, p) for s, g in enumerate(slots)
                    if g is not None and not g.is_new() for p in conv.health(g)]
        sys.exit("%s is not converted: no file on it is one that normal play can have written (edited, made "
                 "with glitches, or damaged). The tool translates consistent files only and does not try to "
                 "repair one.\n  %s" % (a.input, "\n  ".join(problems)))
    used = healthy
    names = {}
    for value in a.name or []:
        log, sep, name = value.partition("=")
        if sep and log in ("1", "2", "3"):
            if int(log) - 1 in names:
                sys.exit("--name: Quest Log %s is named twice." % log)
            if int(log) - 1 not in used:
                sys.exit("--name %s: Quest Log %s is not among the files that are converted (%s)." % (
                    value, log, ", ".join(str(s + 1) for s in used)))
            names[int(log) - 1] = name
        elif len(used) == 1:                    # anything else is the name itself
            if used[0] in names:
                sys.exit("--name: Quest Log %d is named twice." % (used[0] + 1))
            names[used[0]] = value
        else:
            sys.exit("--name %s: this card has %d used files. Say which Quest Log gets the name, for example "
                     "--name %d=%s (the option can be repeated)." % (value, len(used), used[0] + 1, value))
    terminal = sys.stdin.isatty() and sys.stdout.isatty()
    if terminal and not a.yes:
        _confirm(a, card)
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
        if not terminal:
            listed = {}
            for d, s in pending:
                question, choices = d.text(s)
                listed.setdefault((d.key, question, tuple(choices)), []).append(s)
            lines = ["%s holds states the two games do not share. Choose for each one (or --all for all;"
                     % a.input, "per Quest Log: 1=steps,2=rewards):"]
            for (key, question, choices), logs in listed.items():
                lines.append("")
                lines.append("%s steps|rewards   (Quest Log %s)" % (
                    _flag(key), ", ".join(str(s + 1) for s in sorted(set(logs)))))
                lines.append("  " + question)
                lines.extend("    %s" % text for _, text in choices)
            sys.exit("\n".join(lines))
        d, s = pending[0]
        options.answer(d.key, s, _ask(d, s))

    out_file, reports = conv.convert(card, options)
    # An answer typed for a Quest Log that is not in that case did nothing: say so (a mistyped number
    # would otherwise leave the intended Quest Log with the --all answer).
    in_case = {(d.key, s) for d in conv.decisions_for(slots, options) for s in d.slots}
    for key in conv.Options.CASES:
        typed = getattr(a, key)
        if isinstance(typed, dict):
            for s, mode in sorted(typed.items()):
                if (key, s) not in in_case:
                    print("note: %s %d=%s was not used: Quest Log %d is not in that case." % (
                        _flag(key), s + 1, mode, s + 1), file=sys.stderr)
        elif typed and not any(k == key for k, _ in in_case):
            print("note: %s %s was not used: no Quest Log is in that case." % (_flag(key), typed),
                  file=sys.stderr)
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
        try:
            os.makedirs(backup)
            for name in existing:
                os.replace(os.path.join(a.output, name), os.path.join(backup, name))
        except OSError as e:
            sys.exit("error: %s\nNothing was converted. The save that was in %s may be partly in %s: move "
                     "its files back." % (e, a.output, backup))
    try:
        with open(target, "wb") as f:
            f.write(data)
        for name, content in album.items():
            with open(os.path.join(a.output, name), "wb") as f:
                f.write(content)
    except OSError as e:
        sys.exit("error: %s\nThe new save in %s is incomplete.%s" % (
            e, a.output, " The save that was there is untouched in %s." % backup if backup else ""))

    wide = term.width()
    print()
    print(paint("%s (%s, %s) -> %s" % (a.input, card.code, card.source, target), "bold", "green"))
    for rep in reports:
        log = paint("Quest Log %d:" % (rep.slot + 1), "bold", "cyan")
        if rep.unhealthy:
            print("%s %s" % (log, paint("NOT CONVERTED (written empty)", "bold", "red")))
        elif not rep.used:
            print("%s %s" % (log, paint("empty", "dim")))
        else:
            print("%s %s" % (log, paint(out_file.name(rep.slot), "bold")))
            if not a.quiet:
                print(_summary(out_file.slots[rep.slot], out_file.name(rep.slot), "    ", hd_save=True))
        if rep.changes:
            print("    " + paint("What changed and why:", "bold"))
        for c in rep.changes:
            print("\n".join(term.wrap(c, "    - ", "      ", wide)))
        if rep.totals:
            print("    " + paint("What you hold, GameCube -> HD (each difference is explained above):", "bold"))
            for label, before, after in rep.totals:
                delta = ""
                if isinstance(after, int):
                    delta = " " + paint("(%+d)" % (after - before),
                                        *(["green"] if after > before else ["red"] if after < before else ["dim"]))
                print("      %s %s -> %s%s" % (paint("%-16s" % (label + ":"), "dim"), before, after, delta))
        if rep.pictures:
            print("    %s" % ("%d Picto Box picture(s) converted to the HD album (cking_pic%d_*.sav, "
                              "cking_pic_order%d.sav)" % (rep.pictures, rep.slot, rep.slot) if not a.no_pictures
                              else "%d Picto Box picture(s) left out (--no-pictures)" % rep.pictures))
        for w in rep.warnings:
            if term.styled():
                print("\n".join(term.wrap(w, "    WARNING: ", "      ", wide)).replace(
                    "WARNING:", paint("WARNING:", "bold", "yellow"), 1))
            else:
                print("    WARNING: %s" % w)
    print()
    for line in ("Copy %s into the game's save folder (Cemu, USA: %s)." % (
                     "cking.sav and the cking_pic* files" if album else "cking.sav", os.path.dirname(CEMU_HINT)),
                 "It replaces all three Quest Logs and their albums: back up the game's save folder first, and "
                 "remove its cking_pic* files before copying."):
        print(paint("\n".join(term.wrap(line)), "italic") if term.styled() else line)
    if backup:
        print("The save that was in %s is in %s." % (a.output, backup))
    left_out = [rep.slot + 1 for rep in reports if rep.unhealthy]
    if left_out:                                # written, but not all of the card: say so in the exit status
        sys.exit(EXIT_PARTIAL)


def cmd_info(a):
    if _is_hd(a.file):
        f = _read_hd(a.file)
        print(paint("Wind Waker HD save", "bold"))
        for p in f.problems:
            print("  %s %s" % (paint("PROBLEM:", "bold", "red"), p))
        for s in range(3):
            save = f.slots[s]
            if save.u("info.save_count") == 0:
                print("%s %s" % (paint("Quest Log %d:" % (s + 1), "bold"), paint(
                    "empty%s" % (" (New Game+ ready)" if save.u("info.clear_count") else ""), "dim")))
                continue
            print(paint("Quest Log %d:" % (s + 1), "bold", "cyan"))
            print(_summary(save, f.name(s), hd_save=True))
            opt = f.extras[s]["options"]
            print("  %s %s" % (paint("%-22s" % "Hero Mode:", "dim"), "yes" if opt[hd.OPT_HERO_MODE] == 1 else "no"))
    else:
        _print_gc(_read_gc(a.file))


def cmd_verify(a):
    f = _read_hd(a.file)
    if f.problems:
        for p in f.problems:
            print("PROBLEM: %s" % p)
        sys.exit(1)
    print(paint("OK:", "bold", "green") + " size, three Quest Log checksums, format word and HD section CRC are valid.")


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
    c.add_argument("--pawprint-chest", type=_case_value, metavar="MODE", help="Pawprint Isle Wizzrobe cave chest open (HD: Treasure Chart 46; with --floor50 rewards: about its Silver Rupee only)")
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
    c.add_argument("-y", "--yes", action="store_true",
                   help="in a terminal: do not show the input and ask before converting; go straight to the cases")
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
    except (gc.GcError, hd.HdError, conv.ConversionError, OSError) as e:       # a bug raises as it is
        sys.exit("%s %s" % (paint("error:", "bold", "red", stream=sys.stderr), e))


if __name__ == "__main__":
    main()
