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

## Not run

- The European game, on a console or in an emulator.
- The reload of every sample (`scripts/ingame_batch.py`) was not repeated for this change. For the USA
  game the output changes only for a GameCube file whose `config.ruby` is 0 (two USA sample files), by
  that one byte and its checksum.
