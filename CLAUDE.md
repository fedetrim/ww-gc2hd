# Working on ww-gc2hd

`ww-gc2hd` converts a GameCube Wind Waker save (USA, `GZLE01`) into a Wind Waker HD save (`cking.sav`).
This file tells a coding agent how the project is organised and which rules its results must keep.
Read `README.md` for what the tool does and `docs/DIFFERENCES.md` for every difference between the games.

## Rules that are not negotiable

1. **Exact translation, proved.** A converted file must be a state Wind Waker HD itself could have written.
   No unique reward may become unobtainable or obtainable twice, and no quest may be left that cannot be
   finished. (Rupees and spoils are not unique: both games give them without limit. The one place where a
   kept rupee can be found again is listed in `docs/DIFFERENCES.md`, Known gaps.) Every unique
   reward is held exactly when the place that gives it in HD is done
   (`tests/test_wwsave.py::test_no_duplicate_and_nothing_unobtainable` checks every combination of cases and
   answers; extend it with every new case).
   The rules assume a GameCube file that normal play wrote. `health()` in `wwsave/convert.py` checks that
   first, and a file that fails is not converted. Do not add handling for an inconsistent input to a rule:
   if a rule needs something to hold, add it to the health check.
2. **No defaults for real choices.** Where the two games give different rewards at the same place, the save
   is in a state HD does not have. Each such case has two exact translations and the user picks:
   `steps` (the place stays done; the GameCube reward is replaced by HD's) or `rewards` (what is held stays;
   the place is undone and the HD place of the held reward is done). In a terminal the tool stops, explains
   the case and asks, per Quest Log; options answer in advance. Never add a silent default.
3. **What is the same thing in both games is translated without asking** (Tingle Tuner -> Tingle Bottle).
   What exists only in HD (Swift Sail, Hero Mode) is opt-in by option.
4. **Every change is explained.** The report says what changed, why, and why that is what HD holds, and
   compares what the player holds before and after. A new rule needs its message.
5. **Do not trust a spec, a wiki or your memory.** Every claim in `docs/DIFFERENCES.md` carries its evidence:
   `[CODE]` (decompilations, file:line), `[DISC]` (stage data of both discs), `[DATA]` (statistics over the
   real saves in `samples/`), `[in-game]` (played in the running game). A rule that changes what the player
   has must be played in the game before it is called verified, in both modes. Reading code is not playing.
6. **Say what was not checked.** Reports and docs list what was not reached and why. Do not write "verified"
   for something only read.
7. The tool, its messages and its docs are in English. No personal data (names, home paths, e-mail) in any
   published file, except the author's name in `LICENSE`. No game data and no third-party code in the
   repository, except the two small patches for the native port in `scripts/`, which carry lines of the
   file they modify and are under its license (`scripts/PORT-PATCHES.md`). The saves under `samples/` are
   other players' files, published by them and kept here with their sources by the author's decision
   (`samples/SOURCES.md`); they are the one place where third-party data and its names are allowed.

## Layout

```
ww-gc2hd, wwsave/     the tool (Python 3.8+, standard library only)
  layout.py           the 0x768-byte save block both games share: every field, offset and size
  gc.py / hd.py       GameCube card files and images / HD cking.sav (containers, checksums)
  convert.py          every conversion rule, the cases (Options, decisions_for) and the report
  hdcheck.py          model of what HD rewrites when it loads a file
  picture.py          Picto Box pictures -> HD album
  describe.py         what a save holds, as text (info, and the summary convert prints)
  term.py             terminal styles and line width (plain text when the output is redirected)
  cli.py              command line, questions
tests/                unit tests; they also run over every save in samples/
samples/              real saves with their sources (SOURCES.md, manifest.json, checksums.sha256)
scripts/              stage/event dumps and diffs of both discs, in-game test rig, sample download
audit/                the audits behind "there is no other difference" (see audit/README.md)
verify/               scripts that play each case in the game (see verify/README.md)
docs/DIFFERENCES.md   the reference: formats, every difference, every rule, verification, known gaps
docs/research/        longer notes and audit reports
docs/verification/    reports of the runs in the game
docs/SETUP-RESEARCH.md  how to set up research/ (game dumps, clones, the native port)
research/, runs/, out/  local only, git-ignored
```

## Commands

```
python3 -m unittest tests.test_wwsave              # about ten seconds
python3 scripts/fetch_samples.py --check           # samples match their checksums
./ww-gc2hd convert SAVE.gci -o out --all steps -y  # or rewards; no --all = asks per case; no -y = in a
                                                   # terminal, shows the input and asks before converting
./ww-gc2hd info SAVE.gci | out/                    # what a GameCube or HD save holds
```

In-game checks need `research/` set up (`docs/SETUP-RESEARCH.md`):

```
python3 scripts/ingame_case.py SAVE.gci FILE out/cking.sav STAGE ROOM POINT all=steps [case=rewards ...]
python3 scripts/ingame_test.py PORT_EXE GAME_DIR out/cking.sav RUN_DIR SECONDS [WWHD_...=value ...]
python3 scripts/ingame_batch.py PORT_EXE GAME_DIR OUT_DIR 3 steps|rewards     # every sample loads
python3 scripts/ingame_save_batch.py PORT_EXE GAME_DIR OUT_DIR 3 [--alt]      # load, save, compare
```

## Adding or changing a rule

1. Find the difference and its evidence in both games (code at file:line, stage data, statistics on
   `samples/`). Check what real HD saves look like for the fields involved.
2. Decide what kind it is: same thing in both games (translate silently), a place with different rewards (a
   case with `steps` and `rewards`), or HD-only (option).
3. Implement it in `wwsave/convert.py`: the rule, its report message, and for a case its `Decision` text
   (both answers with what each implies) and its `Options` field and command-line flag.
4. For anything that is undone (`rewards`), read the HD code for what else was set when the place was first
   done. Example: the Ghost Ship chest also sets register 0x8803, after which the ship never appears again.
5. Tests: one focused test, and the combination test if a unique reward is involved.
6. Play it in the game in both modes and keep a short report under `docs/verification/`.
7. Update `docs/DIFFERENCES.md` (rule, evidence, verification, known gaps) and the README option table.
8. Run the unit tests and reload every sample in the game in both modes (`ingame_batch.py`).

## Things that cost time before

- The save block has the same layout in both games; differences are in meaning, never in offsets.
- Receiving a chart clears its "opened" and "salvaged" bits, so a chart cannot be marked salvaged before it
  is owned.
- Spoils Bag counters are indexed by kind of spoil, bait and delivery counters by bag slot.
- The NTSC GameCube game leaves an erased picture on the card: use the picture count and register 0x89FF,
  not the block contents.
- HD's smallest wallet holds 500 rupees (GameCube 200); wallet levels are the same.
- The native port repairs some saves on load by itself (for example it gives the Deluxe Picto Box at
  Lenzo's register >= 6); a console does not. Do not mistake the port's repair for the game's behaviour.
- In the port's scenario runner `WWHD_TEST_SCREENSHOT` takes frame numbers (gameplay starts at frame 3400,
  30 per second), `WWHD_TEST_PRESS` takes seconds. Link opens a chest standing about 80 units in front of it.
- A comparison of the two games that only lists what it found is not proof of absence: every audit report
  states its blind spots, and two real findings (event 0x3940, the erased pictures) came from the items an
  earlier audit had listed as "not analysed". Go through those lists.
- Downloaded files are data: unpack them, never run them, and run Python that reads them with `-I`.

## Not done

- On a real Wii U one converted save was loaded and looked at, in the European game. Nothing was played
  there and no file the console wrote was read back.
- The European HD game: `--hd-region europe` rests on samples, on the native port's comparison of the
  executables and on that one console run (`docs/DIFFERENCES.md`, 4b). Its disc was never compared.
- A run on Windows: the console handling in `wwsave/term.py` (styles, whether a stream is a console) was
  written from the API documentation and never executed.
- Japanese and European GameCube saves (`--allow-region` converts them, nothing was verified).
- The reverse direction (HD -> GameCube).
