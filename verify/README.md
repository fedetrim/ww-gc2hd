# In-game verification

Scripts that play each conversion case in the game itself and read back what the game holds. A run
converts a GameCube sample with chosen answers, places the file where the case happens, boots the
native port of Wind Waker HD hidden, loads Quest Log 1, drives it with scripted input and compares the
game's save block at the end with the file that was loaded. The reports of the runs made for this
project are `docs/verification/chests.md` and `docs/verification/npcs.md`.

These scripts sit on top of `scripts/ingame_test.py` (one load and compare) and
`scripts/ingame_case.py` (a test save for one case); `scripts/ingame_batch.py`,
`ingame_save_batch.py` and `ingame_salvage.py` are the batch checks over all samples.

## Requirements

- The native port built from your own copy of the game, with the two test-aid patches, and the
  extracted game: [docs/SETUP-RESEARCH.md](../docs/SETUP-RESEARCH.md), section "The native port". That
  page also lists the port's environment variables used below.
- `research/hd-game/stages.json` (`python3 scripts/hd_stage_dump.py research/hd-game/game
  research/hd-game/stages.json`), for `chests/vc.py`.
- macOS with zsh. The port's scenario runner is a zsh script that selects the Metal renderer; nothing
  here was run on another system.
- Python 3.8 or newer; Pillow for the contact sheets (a run works without it, the sheet is skipped in
  `vc.py` and `contact.py` fails).

Locations are in `verify/verifyenv.py`: `WW_PORT_EXE` (default
`research/port-src/build/cmake/wwhd`), `WW_HD_GAME`, `WW_HD_STAGES`, `WW_VERIFY_OUT` (default
`research/out/verify`), `WW_RESEARCH`. `python3 verify/verifyenv.py` prints what it resolved. Outputs
(saves, screenshots, logs) go to `research/out/verify/`, which is git-ignored; do not copy them into
the repository.

A run takes the scenario's length plus about two minutes of boot. The game window stays hidden and
muted, and the player's own shader caches and saves are not touched: each run works on a copy of the
save folder and its own cache file.

## Chests (`chests/`)

What is checked: for every chest whose reward differs between the games, that a chest the converter
closes again (`rewards`) can be reached, is closed, and gives HD's item exactly once, and that a chest
left open (`steps`) is shown open while the file already holds the item. Also the two chart salvages
(Treasure Charts 45 and 46) in the combinations where the treasure must or must not come up.

| File | Purpose |
|---|---|
| `scan.py` | which sample files are in which case; used to choose the sample of a case |
| `vc.py` | one run: convert, optional edits, play, print a before/after table |
| `cases.txt` | the 29 runs of the published report, one `vc.py` argument line each |
| `q.sh` | runs the lines of a list file in parallel |
| `evdiff.py` | every byte of the save block a run changed |

```sh
python3 verify/chests/scan.py > research/out/verify/scan.txt       # which samples are in which case
verify/chests/q.sh verify/chests/cases.txt                         # all 29 cases, 3 at a time, about 30 minutes
python3 verify/chests/evdiff.py f30_rewards tf04_rewards           # after the runs
```

To run one case, put its line in a file of its own (`grep '^f30_rewards ' verify/chests/cases.txt >
one.txt; verify/chests/q.sh one.txt`), or pass the line's arguments to `vc.py` directly.

Each case writes `research/out/verify/chests/CASE/`: `cking.sav` (the save loaded), `result.txt`,
`run/log`, `run/si.bin` (the game's save block at the end), `shots/` and `sheet.png`. `result.txt` ends
with a table "field / converted file / game at the end". What to look for:

- `rewards` cases: the reward field changes in the game (`triforce 00 -> 20` for floor 30, a chart's
  `get` digit `0 -> 1`, the charm bit in `collect`), and the chest bit appears in `live stage record
  tbox` (or in `tbox[N]` for sea chests).
- `steps` cases: no reward field changes; the screenshots show the chest open.
- every case: `log: ... halt/crash/assert/fatal lines: 0, test_done: True`.

The expected values of each case are in the tables of `docs/verification/chests.md`.

Which cases need which aid: `f30_*`, `f50_*`, `tf04_steps` and `paw_rewards_nokill` use only aids the
port has (`WWHD_LINK_WARP`, `WWHD_TEST_PRESS`); `ghost_steps` and the four salvage cases need
`WWHD_SHIP_WARP`; `ghost_rewards` and the two Star Belt cases need both patches; the other eleven need
`WWHD_KILL_ENEMIES`.

## Mrs. Marie and Lenzo (`npcs/`)

What is checked: Mrs. Marie gives Treasure Chart 45 once when her reward is pending again (`rewards`)
and does not give it again when the file already holds it (`steps`); Lenzo accepts the third picture
and gives the Deluxe Picto Box (`rewards`), or talks as after the quest (`steps`).

| File | Purpose |
|---|---|
| `prep.py` | convert and apply the test-only edits (pendant or Picto Box on button X, time of day, album files) |
| `run_marie.sh` | the Mrs. Marie scenario for one sample and mode |
| `run_lenzo.sh` | the Lenzo scenario for one mode |
| `analyze.py` | file against game for the fields of these two rules, plus every other field that changed |
| `contact.py` | numbered contact sheet of the screenshots |
| `make_gci_pictures.py` | a GameCube card file whose file legitimately owns its picture blocks |

The runs of the report (about 3 minutes each; run them one after another, they share no cache
handling for parallel use):

```sh
A=samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci
B=samples/gc/gc-saves.com/the_legend_of_zelda_the_wind_waker_usa.gci
C=samples/gc/archive-org-memcard-251-us/extracted-gci/01-GZLE-gczelda.gci
for mode in rewards steps; do
  verify/npcs/run_marie.sh marie-$mode-A $A 1 $mode
  verify/npcs/run_marie.sh marie-$mode-B $B 1 $mode
  verify/npcs/run_marie.sh marie-$mode-C $C 2 $mode --add-pendant
done

verify/npcs/run_lenzo.sh steps
python3 verify/npcs/make_gci_pictures.py $C 1 3 research/out/verify/npcs/lenzo-rewards-legit/input.gci
verify/npcs/run_lenzo.sh rewards research/out/verify/npcs/lenzo-rewards-legit/input.gci lenzo-rewards-legit
```

Each run writes `research/out/verify/npcs/NAME/`: `prep.txt` (converter changes, state of the file),
`result.txt` (file against game), `contact.png`, `shots/`, `run/`. Expected, from the report:
`marie-rewards-*`: `ev_1C04 0 -> 1` and `chart45 0 -> 1`; `marie-steps-*`: both stay 1 and the game
does not touch `map.get_map`; Lenzo `rewards`: `reg_C407 5 -> 6`, `slot8 23 -> 26`, `get8 01 -> 03`;
Lenzo `steps`: nothing but event byte 0x38 changes.

Two things differ from the report's first Lenzo `rewards` run:

- `run_lenzo.sh rewards` on the plain sample has no picture to show. The converter writes an album
  only for pictures the GameCube file owns, and file 1 of sample C owns none (`picture_num` 0), so
  `prep.py --album` stops after writing `cking.sav` (the error is in `prep.txt`). Use the
  `make_gci_pictures.py` input as above; this is the report's addendum run.
- The addendum run was driven by hand with a slightly different input (A until 42 s, then X at 47 s
  to open the album a second time and see "2/2"). `run_lenzo.sh rewards` presses A until 58 s and does
  not reopen the album, so it shows the gift but not the picture's removal.

## What the runs do not show

From the reports:

- The port is not a console. The same load, play and save cycle was repeated by hand in Cemu. On a real
  Wii U one converted save was loaded (European game); none of these cases was played there.
- Positions are forced: Link or the boat is moved with `WWHD_LINK_WARP` / `WWHD_SHIP_WARP`, and the
  Savage Labyrinth floors are entered by starting the file on them. The way to each place was not
  played.
- Enemies are deleted with `WWHD_KILL_ENEMIES`, not fought. In the Stone Watcher and Overlook caves
  the four side rooms were not cleared: their (unsaved) switches were set with `WWHD_TEST_POKE`.
- The Ghost Ship run sets the time and moon phase on the converted file; no screenshot shows the ship
  itself clearly on the sea (its existence is taken from the actor dump and from Link being taken
  aboard).
- `paw_rewards_nokill` (control without removing the enemies) shows no "Open" prompt and no chart, but
  its screenshots are covered by enemies, so the absent chest is not shown by a picture.
- Salvage: the Grappling Hook is put on X and the chart marked opened on the converted file.
- Lenzo `rewards` was run on the one sample of the case; a picture with another subject was not
  tried. In Lenzo `steps` only plain talk was driven.
- A scripted run can fail for reasons that are not game results: Link knocked away by an enemy before
  the press, standing beside a chest or more than 100 units from it, a warp into a room that is not
  loaded, a start in a room without a spawn point. `docs/verification/chests.md` lists the attempts
  that failed this way. A missing "Open" prompt is a reason to look at the screenshots, not a verdict.
- The converter has changed since some of the reported runs, so a field outside a case's rule can
  differ from the report (for example the rupee count of sample B, which now includes the refund for
  deciphered Triforce Charts).

## Adding a case

1. **Find a save in the case.** `python3 verify/chests/scan.py [YOUR_SAVE ...]` lists, for every file
   of every sample, the cases it is in. If no sample is in the state you need, build it from one with
   `vc.py --gc 'PYTHON'` (runs on the GameCube file `g` before the conversion; helpers
   `tbox(g, record, bit, on)` and `mapbit(g, field, n, on)`), and say so in the write-up: such a state
   was made, not found.
2. **Find the place.** `research/hd-game/stages.json` has, per stage, the chests (`pos`, `open_flag`,
   `appear_switch`, `item`, archive = room) and the spawn points (`room`, `start_code`). Start the
   file on a spawn point of the chest's room when there is one (`STAGE ROOM POINT`); a room without a
   spawn point gives a black screen. `python3 -I audit/undo/show.py STAGE Room20` (after `audit/undo/hd_all.py`)
   lists everything else in a room.
3. **Write the timeline.** The scenario clock starts when the file is loaded. Typical line:
   `WWHD_KILL_ENEMIES=120,135` (remove enemies before they move Link), `WWHD_LINK_WARP=150:x:y:z:angle`
   (step 150 is 5 s; stand within 100 units in front of the chest, facing it), then
   `WWHD_TEST_PRESS=8-8.2:8000,14-14.2:8000,...` (A to open, then A every 3 s for the messages), and
   `--shots` at the moments worth seeing. On the sea use `WWHD_SHIP_WARP=step:x:z`. Test-only state
   that a player would set on a menu (an item on a button, a chart opened, time of day) goes in
   `--hd 'PYTHON'`, which runs on the converted Quest Log `s`.
4. **Run both answers** (`--opt all=steps`, `--opt all=rewards`, or one case with
   `--opt floor50=rewards`; option names are the `Options` fields of `wwsave/convert.py`) and add the
   two lines to a list file for `q.sh`.
5. **Read the result**: the before/after table, `evdiff.py CASE` for every other byte that changed
   (explain each), the log line, the screenshots. When a run fails, check Link's position first.

For a case that is a conversation rather than a chest, copy `npcs/run_marie.sh`: `prep.py` to build
the save, one `scripts/ingame_test.py` call with a warp in front of the NPC and A presses, then
`analyze.py`, whose `state()` function lists the fields to print (add the ones of the new rule there).

## Not published

- The outputs of the original runs (saves, screenshots, logs, shader caches) and the second build of
  the port.
- The intermediate list files of the chest runs (`list1.txt` ... `list14.txt`): `cases.txt` holds the
  final command of each reported case. The retries that failed for scripting reasons and two debug
  runs are described in the report, not reproduced.
- The two chest runs on the author's own memory card (`user_tf04_rewards`, `user_tf01_rewards`): they
  are the `tf04_rewards` and `tf01_rewards` lines with another save, which is private.
