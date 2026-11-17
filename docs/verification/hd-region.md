# `--hd-region`: runs in the game

The runs here use the USA game in the native port. The European game was tested once on a real Wii U (a
converted save loads and shows what the file holds); by the author's decision that run has no report here.

## The USA game loads a file written for the European game

```
./ww-gc2hd convert CARD.raw -o out --all steps --hd-region europe
python3 scripts/ingame_test.py research/port-src/build/cmake/wwhd research/hd-game/game out/cking.sav RUN_DIR
```

Input: the author's own card (one used file). The converted file differs from the one written without
the option in 16 bytes: `config.ruby` of each Quest Log with its two checksum bytes (9), options byte 3
of each Quest Log (3) and the CRC of the HD records (4).

Result (2026-11-16, native port built from ZeldaWWHDRecomp 1af1d61, USA game v0): the game goes from the
title screen into Quest Log 1; after 6 seconds of play the 441 fields the script compares are as in the
file, none differs (a field the game changes while playing is left out of the comparison, not counted
as equal).

This run compares the save block only, which holds `config.ruby` but not the options record. The next run
covers options byte 3.

## The USA game loads, saves and keeps the European pair, on every sample

```
python3 scripts/ingame_save_batch.py research/port-src/build/cmake/wwhd research/hd-game/game RUN_DIR 3 --europe
```

Every used file of the USA samples that passes the health check (42 distinct files), converted with
`--all steps --hd-region europe`, loaded as Quest Log 1; Link walks two seconds and the game saves from
the pause menu. The file the game writes is compared with the converted one, HD records included.

Result (2026-11-16, same build, working tree of commit 06fe53b plus the rig option): all 42 load into
gameplay. 36 save (the other six start in a scene where the menu is not available). In all 36 the options
record the game writes is the one in the converted file, so options byte 3 stays 1, and `config.ruby`
stays 0. In 31 the file differs only in date, time of day, save counter and current life; in the other
five the game changed the return place (in two also the play log) or an event flag. These are the same
counts as the run for the USA game with `--all steps` (`docs/DIFFERENCES.md`, Verification).

The same with every case by `rewards`, Swift Sail and Hero Mode (`--alt --europe`, run on the working tree
after commit a4931aa): all 42 load, 36 save, and in all 36 the options record is written back as it was (it
also holds the Hero Mode byte). In 30 nothing else differs; in the other six the game changed the return
place (in two also the play log) or an event flag. Again the counts of the USA run in that mode.

What these runs show: the USA build reads a Quest Log that carries the European pair and writes it back
unchanged. What they do not show: anything about the European build.

## The USA game loads a file whose `config.ruby` the conversion set to 1

The only USA sample card whose files carry `config.ruby` 0 is
`samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci`
(files 1 and 3). Converted with `--all steps --no-pictures` and with `--all rewards --no-pictures` for the
USA game, the report of both files says the setting was set to 1. File 1 was loaded as it is, file 3 after moving it to Quest Log 1
(`HdFile.move_to_quest_log_1`).

Result (2026-11-16, same build): in both modes both files go into gameplay and keep all 442 compared
fields.

## Not run

- The European game in the port or an emulator.
- For the USA target the reload of every sample (`scripts/ingame_batch.py`) was not repeated. Instead the
  conversions for the USA game of all 34 USA sample cards, with `--all steps` and with `--all rewards` (68
  outputs), were compared with those of the commit before this change: 66 are the same bytes, and the two
  that differ are the card above, which was played in both modes.

## A European GameCube save, written for the game of its own region

Without `--hd-region` a European GameCube save (`--allow-region`) is written for the European game.
`samples/gc/archive-org-zeldasaves/extracted/NGC/PAL/the-legend-of-zelda-the-wind-waker.14259.gci`, File 1,
converted with `--all steps --allow-region --no-pictures` and with `--all rewards --allow-region
--no-pictures`, loaded with `scripts/ingame_test.py` for 6 seconds.

Result (2026-11-17, same build, the USA game): in both modes the file goes into gameplay and keeps all 442
compared fields.

Not checked: the same file in the European game, on a console or otherwise. European GameCube saves remain
unanalysed (`docs/DIFFERENCES.md`, Known gaps).
