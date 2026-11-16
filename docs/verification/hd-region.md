# `--hd-region`: runs in the game

Only the USA game is available here (the author's copy). The European game was not run.

## The USA game loads a file written for the European game

```
./ww-gc2hd convert CARD.raw -o out --all steps --hd-region europe
python3 scripts/ingame_test.py research/port-src/build/cmake/wwhd research/hd-game/game out/cking.sav RUN_DIR
```

Input: the author's own card (one used file). The converted file differs from the one written without
the option in 16 bytes: `config.ruby` of each Quest Log with its two checksum bytes (9), options byte 3
of each Quest Log (3) and the CRC of the HD records (4).

Result (2026-11-16, native port built from ZeldaWWHDRecomp 1af1d61, USA game v0): the game goes from the
title screen into Quest Log 1; after 6 seconds of play its in-memory save holds all 441 compared fields
as in the file.

What this shows: the USA build reads a Quest Log that carries the European pair. What it does not show:
anything about the European build.

## The USA game loads a file whose `config.ruby` the conversion set to 1

The only USA sample card whose files carry `config.ruby` 0 is
`samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci`
(files 1 and 3). Converted with `--all steps --no-pictures` and with `--all rewards --no-pictures` for the
USA game, the report of both files says the setting was set to 1. File 1 was loaded as it is, file 3 after moving it to Quest Log 1
(`HdFile.move_to_quest_log_1`).

Result (2026-11-16, same build): in both modes both files go into gameplay and keep all 442 compared
fields.

## Not run

- The European game, on a console or in an emulator.
- The reload of every sample (`scripts/ingame_batch.py`) was not repeated for this change. Instead the
  conversions for the USA game of all 34 USA sample cards, with `--all steps` and with `--all rewards` (68
  outputs), were compared with those of the commit before this change: 66 are the same bytes, and the two
  that differ are the card above, which was played in both modes.
