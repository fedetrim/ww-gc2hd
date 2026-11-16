# In-game verification of the chest rules (GameCube -> HD converter)

> These are the reports of the runs as they were made. The scripts are published in `verify/` (see
> `verify/README.md`); paths such as `runs/verify-...` are the author's local output folders. Rules added to
> the converter afterwards (for example giving back Tingle's deciphering fee) change some rupee counts
> quoted here; the fields each case is about are unchanged.
> On 2026-11-16 the Silver Rupee of the Pawprint chest began to follow `--pawprint-chest` also with
> `floor50=rewards`. Four runs were made that day with that rule: `salv45_f50rewards_kept`,
> `salv45_f50rewards_taken`, and `paw_f50rewards` and `salv46_f50rewards` again, with
> `pawprint_chest=rewards` named (the answer they had implied before). The two `f50_rewards_marie...` runs
> were not repeated: their command now takes the 200 rupees back, which is not what they are about.

Date: 2026-11-15 (four runs on 2026-11-16, see above). Everything below was observed in the running native port of Wind Waker HD: each run converts a
GameCube sample with the stated options, boots the game hidden, loads Quest Log 1, drives it with scripted input
and reads the game's save block at the end. No result here comes from code reading.

Root of all paths: `runs/verify-chests/ of the author's working copy, not in this repository` (called V below).

## Result

No rule was contradicted. Every chest that `rewards` closes again was reachable, present, closed, and gave HD's item
exactly once; every chest that `steps` leaves open is shown open and the converted save holds the item. No run
halted (31 of 31 logs: 0 halt/crash/assert/fatal lines, scenario finished).

| Chest | rewards | steps |
|---|---|---|
| Savage Labyrinth floor 30 (Shard 6) | VERIFIED in game: `collect.triforce` 00 -> 20, chest flag bit 11 set in the live record. `f30_rewards/` | VERIFIED in game: chest shown open, file holds 20. `f30_steps/` |
| Savage Labyrinth floor 50 (Hero's Charm), 4 combinations | VERIFIED in game, see next table | VERIFIED in game, see next table |
| Private Oasis cabana labyrinth, TF_04 (Shard 2) | VERIFIED in game: triforce 05 -> 07. Also with the author's own memory card: 20 -> 22. `tf04_rewards/`, `user_tf04_rewards/` | VERIFIED in game: chest shown open, file holds CF. `tf04_steps/` |
| Stone Watcher Island cave, TF_01 (Shard 7) | VERIFIED in game: triforce 05 -> 45. Author's card: 20 -> 60. `tf01_rewards/`, `user_tf01_rewards/` | VERIFIED in game: chest shown open. `tf01_steps/` |
| Overlook Island cave, TF_02 (Shard 8) | VERIFIED in game: triforce 05 -> 85. `tf02_rewards/` | VERIFIED in game: chest shown open. `tf02_steps/` |
| Ghost Ship (Shard 4) | VERIFIED in game: ship actor exists at night in the sector of the moon phase, takes Link aboard, chest closed, triforce 05 -> 0D, record 0xA bit 23 set, register 0x8803 0 -> 3, Link returned to the sea. `ghost_rewards/` | VERIFIED in game: with register 3 the ship actor is never created (control, same position and time). Chest shown open when the file is started inside the ship. `ghost_steps/`, `ghost_steps_inside/` |
| Horseshoe Island lookout (Treasure Chart 43) | VERIFIED in game: chest appears when the button on the other lookout is stepped on, chart 43 get bit 0 -> 1, record 1 bit 26 set. `horseshoe_rewards/` | VERIFIED in game: chest shown open, chart owned. `horseshoe_steps/` |
| Star Belt Archipelago lookout (Treasure Chart 44) | VERIFIED in game: chart 44 get bit 0 -> 1, record 1 bit 11 set. `starbelt_rewards_C/` | VERIFIED in game: chest shown open, chart owned. `starbelt_steps/` |
| Pawprint Isle Wizzrobe cave (Treasure Chart 46) | VERIFIED in game: chest appears once the room has no enemies, chart 46 get bit 0 -> 1. `paw_rewards/` | VERIFIED in game: chest shown open, chart owned. `paw_steps/` |
| Pawprint chest with `floor50=rewards` | VERIFIED in game: chest shown open in Cave07; crane at Two-Eye Reef brings up nothing (rupees and maximum life unchanged). `paw_f50rewards/`, `salv46_f50rewards/` | |
| Chart 46 with `floor50=steps pawprint_chest=steps` | | VERIFIED in game: salvage gives the Piece of Heart, maximum life 79 -> 80, chart completed. `salv46_f50steps/` |
| Chart 45 kept as salvaged (`pawprint_chest=rewards marie=steps`) | VERIFIED in game: crane at Seven-Star Isles brings up nothing, rupees stay 4980. `salv45_kept/` | |
| Chart 45 otherwise (all steps) | | VERIFIED in game: same crane script brings the Silver Rupee, rupees 4780 -> 4980, chart completed. `salv45_given/` |
| Chart 45 with `floor50=rewards pawprint_chest=rewards` (Silver Rupee kept) | VERIFIED in game: crane at Seven-Star Isles brings up nothing, rupees stay 1000 (set for the run: the file's wallet is full). `salv45_f50rewards_kept/` | |
| Chart 45 with `floor50=rewards pawprint_chest=steps` (Silver Rupee taken back) | | VERIFIED in game: same crane script brings the Silver Rupee, rupees 1000 -> 1200, chart completed. `salv45_f50rewards_taken/` |

NOT REACHED: none. FAILED: none.

Floor 50, sample 14259 file 1 (both floor 50 and Mrs. Marie done on the GameCube, maximum life 80), DIFFERENCES 3.2 table:

| floor50 | marie | chest in game | charm bit (`collect.collect[4]` & 1) | maximum life | evidence |
|---|---|---|---|---|---|
| rewards | steps | closed; opening it gives the Hero's Charm (0 -> 1), nothing else changes | 0 in file | 80 | `f50_rewards_marieSteps/` |
| rewards | rewards | shown open | 1 | 80 | `f50_rewards_marieRewards/` |
| steps | steps | shown open | 1 | 79 | `f50_steps_marieSteps/` |
| steps | rewards | shown open | 1 | 79 | `f50_steps_marieRewards/` |

All four match the documented table.

## Screenshots

Each case folder has `shots/*.png` (1280x720) and `sheet.png` (contact sheet, left to right, top to bottom, times
listed in `result.txt`). Overviews assembled from them:

- `V/rewards_overview.png`: rows Horseshoe, Pawprint, TF_04, TF_01, TF_02, Star Belt in rewards mode (chest
  appearing or closed with the "Open" prompt, opening, item message).
- `V/steps_overview1.png`: rows TF_01, TF_02, Pawprint (steps), Pawprint (floor50=rewards), Star Belt, Ghost Ship
  interior: chest shown open.
- `V/steps_overview2.png`: the three floor-50 combinations with the chest open.
- `V/salvage_overview.png`: rows Chart 46 (Piece of Heart), Chart 45 (Silver Rupee), Chart 45 kept (empty claw).
- `V/ghost_rewards/sheet.png`: sea at night, inside the ship, ladder, closed chest, shard message, back on the sea.
- `V/f30_rewards/sheet.png`, `V/f50_rewards_marieSteps/sheet.png`, `V/tf04_steps/strip.png`, `V/f30_steps/strip.png`,
  `V/horseshoe_steps/strip.png`, `V/salv46_f50rewards/strip.png`.

## Every other save byte that changed

`V/evdiff.txt` (`python3 evdiff.py CASE...`) lists every byte of the saved block that differs between the converted
file and the game at the end, except the clock/date block and the return place. Besides the fields in the tables:

- `status_a+0x03` (current life) dropped in some runs: enemy or storm damage, not a chest effect.
- `tf04_steps` and `user_tf04_rewards`: rupees -140 / -100. The cabana labyrinth's rats took them before the script
  removed the rats; `tf04_rewards` (rats removed first) shows no rupee change.
- `ghost_rewards`: `event+0x85` and `event+0xC3` (the return room/spawn registers 0x85FF, 0xC3FF the ship writes
  when Link is taken aboard), `event+0x88` (register 0x8803, 0 -> 3), `event+0xBB` 02 -> 03 and `event+0xCF`
  00 -> 01. The last two also change in the control `ghost_steps`, so they belong to sailing in that sector at
  night, not to the ship.
- `salv46_f50steps`, `salv45_given`: `event+0xAD` 31 -> 32 (changes only in the two runs where a treasure came up).
- A chest flag of the current stage sits in the live stage record until the stage is left, so it shows in the
  `live stage record tbox` line of `result.txt` and not in `memoryNN.tbox`. Sea chests and the Ghost Ship (left at
  the end of the scene) show in the saved record.

## What the runs did not do the way a player would

- Positions: Link or the boat was moved with `WWHD_LINK_WARP` / `WWHD_SHIP_WARP`. The Savage Labyrinth floors were
  entered by starting the file in Cave09/Cave10 room 20, not by descending.
- Enemies were removed with a new aid (`WWHD_KILL_ENEMIES`, asks the game to delete every actor of the enemy
  group), not fought. For the Pawprint chest this is the appear condition itself (no enemy actor in the room); the
  chest then ran its own appear scene. In the Ghost Ship the ladder to the chest deck appeared after the removal.
- Stone Watcher / Overlook: the first door was opened by walking into it and pressing A. The door from the hub to
  the chest room is barred until the four side rooms are cleared; those switches (dungeon switches 0x80-0xBF, not
  saved) were set with `WWHD_TEST_POKE` instead of clearing the rooms, then that door was opened with A. A player
  re-entering has to clear the side rooms again, as on a first visit.
- Ghost Ship: the converted file's time was set to 330.0 and the date to 5 (night, moon phase 5 = sector 21), the
  boat was moved next to the ship's path. The ship actor's existence is shown by the actor dump
  (`ghost_rewards/ayush.bin`, 1.8 MB of executes; `ghost_steps/ayush.bin` is empty) and by Link being taken aboard.
  No screenshot shows the ship itself clearly on the sea. The Ghost Ship chest is a plain chest (always present);
  only the ladder depends on the fight.
- Salvage: the Grappling Hook was put on X and the chart marked opened on the converted file (what the player does
  on the chart screen), as `scripts/ingame_salvage.py` does.
- `paw_rewards_nokill` (control without removing enemies): the chart was not obtained and no "Open" prompt
  appeared, but the screenshots are covered by enemies, so "chest absent" is not shown by a picture.

## Failed attempts that were test-script errors, not game results

- `tf04_rewards_xplus/`, `_xminus/`, `_zminus/` and the first front attempt: no "Open" prompt. Cause: a rat knocked
  Link away from the front of the chest right after the warp (Link's trace shows him moved 100 units); from the
  other three sides a chest cannot be opened. With the rats removed first the chest opens (`tf04_rewards/`).
- `starbelt_rewards/`, `_A/`, `_B/`, `_D/`: Link stood beside or behind the chest, or 101 units away after a
  higher drop (the chest's limit is 100). `starbelt_rewards_C/` (60 units in front) opens it. Earlier Star Belt
  attempts also failed to leave the boat or warped Link into a sector that was not loaded.
- `tf01_try_room6/`: starting the file in a room with no spawn point gives a black screen.
- First TF_01/TF_02 attempts warped Link into rooms that were not loaded (he falls and respawns).

## Binary and aid

The shared binary `research/port-src/build/cmake/wwhd` was not rebuilt and no file under `research/port-src` was
changed. The aid was compiled from a patched copy of `test_aids.cpp` and linked into a separate binary:

- `V/port-aid.patch` (diff against `research/port-src/runtime/src/test_aids.cpp`, adds `WWHD_KILL_ENEMIES=step,...`)
- `V/aidbuild/test_aids.cpp`, `V/aidbuild/wwhd` (compile command from `build/cmake/compile_commands.json`, link
  command from `build/cmake/CMakeFiles/wwhd.dir/link.txt` with the object and output paths replaced)

Runs `f30_*` and `f50_*` used the shared binary; all others used `V/aidbuild/wwhd` (`VC_EXE`).

## Scripts

- `V/vc.py`: one run (convert with options, optional GameCube-side or test-setup edits, run `scripts/ingame_test.py`,
  print the conversion's change list, the rig's field differences and a before/after table). Usage in its docstring.
- `V/q.sh LIST [WORKERS]`: runs the lines of a list file in parallel with `VC_EXE=V/aidbuild/wwhd`.
- `V/evdiff.py`, `V/scan.py` (`scan.txt`: which sample files are in which case).
- `V/logs/CASE.out` and `V/CASE/result.txt`: full output of each run.

## Exact commands (run from V; prefix `VC_EXE=$PWD/aidbuild/wwhd` except for f30_* and f50_*)

### f30_rewards

```
python3 vc.py f30_rewards '../../samples/gc/pack1/Wind Waker/5th save.gci' 1 Cave09 20 0 30 --opt all=rewards --shots 6,7.5,10,13,16,19,22,29 WWHD_LINK_WARP=150:0:-70:-4320:-32768 WWHD_TEST_PRESS=8-8.2:8000,14-14.2:8000,17-17.2:8000,20-20.2:8000,23-23.2:8000,26-26.2:8000 --cache f30_rewards
```

log: 256 lines, halt/crash/assert/fatal lines: 0, test_done: True

### f30_steps

```
python3 vc.py f30_steps '../../samples/gc/pack1/Wind Waker/5th save.gci' 1 Cave09 20 0 30 --opt all=steps --shots 6,7.5,10,13,16,19,22,29 WWHD_LINK_WARP=150:0:-70:-4320:-32768 WWHD_TEST_PRESS=8-8.2:8000,14-14.2:8000,17-17.2:8000,20-20.2:8000,23-23.2:8000,26-26.2:8000 --cache f30_steps
```

log: 256 lines, halt/crash/assert/fatal lines: 0, test_done: True

### f50_rewards_marieSteps

```
python3 vc.py f50_rewards_marieSteps ../../samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci 1 Cave10 20 0 30 --opt all=steps --opt floor50=rewards --opt marie=steps --shots 6,7.5,10,13,16,19,22,29 WWHD_LINK_WARP=150:0:-70:-4410:-32768 WWHD_TEST_PRESS=8-8.2:8000,14-14.2:8000,17-17.2:8000,20-20.2:8000,23-23.2:8000,26-26.2:8000 --cache f50_rewards_marieSteps
```

log: 248 lines, halt/crash/assert/fatal lines: 0, test_done: True

### f50_rewards_marieRewards

```
python3 vc.py f50_rewards_marieRewards ../../samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci 1 Cave10 20 0 30 --opt all=steps --opt floor50=rewards --opt marie=rewards --shots 6,7.5,10,13,16,19,22,29 WWHD_LINK_WARP=150:0:-70:-4410:-32768 WWHD_TEST_PRESS=8-8.2:8000,14-14.2:8000,17-17.2:8000,20-20.2:8000,23-23.2:8000,26-26.2:8000 --cache f50_rewards_marieRewards
```

log: 246 lines, halt/crash/assert/fatal lines: 0, test_done: True

### f50_steps_marieSteps

```
python3 vc.py f50_steps_marieSteps ../../samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci 1 Cave10 20 0 30 --opt all=steps --opt floor50=steps --opt marie=steps --shots 6,7.5,10,13,16,19,22,29 WWHD_LINK_WARP=150:0:-70:-4410:-32768 WWHD_TEST_PRESS=8-8.2:8000,14-14.2:8000,17-17.2:8000,20-20.2:8000,23-23.2:8000,26-26.2:8000 --cache f50_steps_marieSteps
```

log: 246 lines, halt/crash/assert/fatal lines: 0, test_done: True

### f50_steps_marieRewards

```
python3 vc.py f50_steps_marieRewards ../../samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci 1 Cave10 20 0 30 --opt all=steps --opt floor50=steps --opt marie=rewards --shots 6,7.5,10,13,16,19,22,29 WWHD_LINK_WARP=150:0:-70:-4410:-32768 WWHD_TEST_PRESS=8-8.2:8000,14-14.2:8000,17-17.2:8000,20-20.2:8000,23-23.2:8000,26-26.2:8000 --cache f50_steps_marieRewards
```

log: 256 lines, halt/crash/assert/fatal lines: 0, test_done: True

### tf04_rewards

```
python3 vc.py tf04_rewards ../../samples/gc/cryze/100%/26-BeforeSavageLabyrinth.gci 1 TF_04 0 0 30 --opt all=rewards --shots 5.2,6,7.5,10,13,16,19,22,29 WWHD_KILL_ENEMIES=120,135,149,152,155,158,161 WWHD_LINK_WARP=150:4150:50:30:-32768 WWHD_TEST_PRESS=5.4-5.6:8000,11-11.2:8000,14-14.2:8000,17-17.2:8000,20-20.2:8000,23-23.2:8000,26-26.2:8000 --cache tf04_rewards
```

log: 274 lines, halt/crash/assert/fatal lines: 0, test_done: True

### tf04_steps

```
python3 vc.py tf04_steps ../../samples/gc/cryze/100%/26-BeforeSavageLabyrinth.gci 1 TF_04 0 0 30 --opt all=steps --shots 6,7.5,10,13,16,19,22,29 WWHD_LINK_WARP=150:4150:50:30:-32768 WWHD_TEST_PRESS=8-8.2:8000,14-14.2:8000,17-17.2:8000,20-20.2:8000,23-23.2:8000,26-26.2:8000 --cache tf04_steps
```

log: 261 lines, halt/crash/assert/fatal lines: 0, test_done: True

### tf01_rewards

```
python3 vc.py tf01_rewards ../../samples/gc/cryze/100%/26-BeforeSavageLabyrinth.gci 1 TF_01 0 0 50 --opt all=rewards WWHD_TEST_POKE=4:*101F84DC+7C0:FFFFFFFFFFFFFFFF WWHD_TEST_STICK=5-8:0:1,14.5-17:0:1 WWHD_KILL_ENEMIES=400,430,700,730 WWHD_LINK_WARP=420:1250:10:0:16384,720:2520:40:0:16384 WWHD_TEST_PRESS=8.5-8.7:8000,9.5-9.7:8000,10.5-10.7:8000,17.5-17.7:8000,18.5-18.7:8000,19.5-19.7:8000,27-27.2:8000,33-33.2:8000,36-36.2:8000,39-39.2:8000,42-42.2:8000,45-45.2:8000 --shots 8.3,12,14.3,17.3,20,23,25,26.5,30,34,37,40,48 --cache tf01_rewards
```

log: 305 lines, halt/crash/assert/fatal lines: 0, test_done: True

### tf01_steps

```
python3 vc.py tf01_steps ../../samples/gc/cryze/100%/26-BeforeSavageLabyrinth.gci 1 TF_01 0 0 50 --opt all=steps WWHD_TEST_POKE=4:*101F84DC+7C0:FFFFFFFFFFFFFFFF WWHD_TEST_STICK=5-8:0:1,14.5-17:0:1 WWHD_KILL_ENEMIES=400,430,700,730 WWHD_LINK_WARP=420:1250:10:0:16384,720:2520:40:0:16384 WWHD_TEST_PRESS=8.5-8.7:8000,9.5-9.7:8000,10.5-10.7:8000,17.5-17.7:8000,18.5-18.7:8000,19.5-19.7:8000,27-27.2:8000,33-33.2:8000,36-36.2:8000,39-39.2:8000,42-42.2:8000,45-45.2:8000 --shots 8.3,12,14.3,17.3,20,23,25,26.5,30,34,37,40,48 --cache tf01_steps
```

log: 305 lines, halt/crash/assert/fatal lines: 0, test_done: True

### tf02_rewards

```
python3 vc.py tf02_rewards ../../samples/gc/cryze/100%/26-BeforeSavageLabyrinth.gci 1 TF_02 0 0 50 --opt all=rewards WWHD_TEST_POKE=4:*101F84DC+7C0:FFFFFFFFFFFFFFFF WWHD_TEST_STICK=5-8:0:1,14.5-17:0:1 WWHD_KILL_ENEMIES=400,430,700,730 WWHD_LINK_WARP=420:1250:10:0:16384,720:2520:40:0:16384 WWHD_TEST_PRESS=8.5-8.7:8000,9.5-9.7:8000,10.5-10.7:8000,17.5-17.7:8000,18.5-18.7:8000,19.5-19.7:8000,27-27.2:8000,33-33.2:8000,36-36.2:8000,39-39.2:8000,42-42.2:8000,45-45.2:8000 --shots 8.3,12,14.3,17.3,20,23,25,26.5,30,34,37,40,48 --cache tf02_rewards
```

log: 295 lines, halt/crash/assert/fatal lines: 0, test_done: True

### tf02_steps

```
python3 vc.py tf02_steps ../../samples/gc/cryze/100%/26-BeforeSavageLabyrinth.gci 1 TF_02 0 0 50 --opt all=steps WWHD_TEST_POKE=4:*101F84DC+7C0:FFFFFFFFFFFFFFFF WWHD_TEST_STICK=5-8:0:1,14.5-17:0:1 WWHD_KILL_ENEMIES=400,430,700,730 WWHD_LINK_WARP=420:1250:10:0:16384,720:2520:40:0:16384 WWHD_TEST_PRESS=8.5-8.7:8000,9.5-9.7:8000,10.5-10.7:8000,17.5-17.7:8000,18.5-18.7:8000,19.5-19.7:8000,27-27.2:8000,33-33.2:8000,36-36.2:8000,39-39.2:8000,42-42.2:8000,45-45.2:8000 --shots 8.3,12,14.3,17.3,20,23,25,26.5,30,34,37,40,48 --cache tf02_steps
```

log: 304 lines, halt/crash/assert/fatal lines: 0, test_done: True

### user_tf04_rewards

```
python3 vc.py user_tf04_rewards AUTHORS_CARD.raw 1 TF_04 0 0 30 --opt all=rewards --shots 5.2,6,7.5,10,13,16,19,22,29 WWHD_KILL_ENEMIES=120,135,149,152,155,158,161 WWHD_LINK_WARP=150:4150:50:30:-32768 WWHD_TEST_PRESS=5.4-5.6:8000,11-11.2:8000,14-14.2:8000,17-17.2:8000,20-20.2:8000,23-23.2:8000,26-26.2:8000 --cache user_tf04_rewards
```

log: 275 lines, halt/crash/assert/fatal lines: 0, test_done: True

### user_tf01_rewards

```
python3 vc.py user_tf01_rewards AUTHORS_CARD.raw 1 TF_01 0 0 50 --opt all=rewards WWHD_TEST_POKE=4:*101F84DC+7C0:FFFFFFFFFFFFFFFF WWHD_TEST_STICK=5-8:0:1,14.5-17:0:1 WWHD_KILL_ENEMIES=400,430,700,730 WWHD_LINK_WARP=420:1250:10:0:16384,720:2520:40:0:16384 WWHD_TEST_PRESS=8.5-8.7:8000,9.5-9.7:8000,10.5-10.7:8000,17.5-17.7:8000,18.5-18.7:8000,19.5-19.7:8000,27-27.2:8000,33-33.2:8000,36-36.2:8000,39-39.2:8000,42-42.2:8000,45-45.2:8000 --shots 8.3,12,14.3,17.3,20,23,25,26.5,30,34,37,40,48 --cache user_tf01_rewards
```

log: 295 lines, halt/crash/assert/fatal lines: 0, test_done: True

### ghost_rewards

```
python3 vc.py ghost_rewards ../../samples/gc/cryze/100%/26-BeforeSavageLabyrinth.gci 1 sea 21 0 60 --opt all=rewards --hd 's.set_raw('status_b.time', __import__('struct').pack('>f', 330.0)); s.set_u('status_b.date', 5)' --shots 4,5.5,7,12,16,21,22.5,26,30,34,38,44,50,58 WWHD_SHIP_WARP=150:302973:-84873 WWHD_KILL_ENEMIES=590,620 WWHD_LINK_WARP=600:0:-550:-3760:-32768 WWHD_TEST_PRESS=23-23.2:8000,29-29.2:8000,32-32.2:8000,35-35.2:8000,38-38.2:8000,41-41.2:8000 WWHD_SAVEINFO_AT=4,22 WWHD_ACTOR_DUMP=runs/verify-chests/ of the author's working copy, not in this repositoryghost_rewards/ayush.bin:0214A9A4:330 --cache ghost_rewards
```

log: 328 lines, halt/crash/assert/fatal lines: 0, test_done: True

### ghost_steps

```
python3 vc.py ghost_steps ../../samples/gc/cryze/100%/26-BeforeSavageLabyrinth.gci 1 sea 21 0 30 --opt all=steps --hd 's.set_raw('status_b.time', __import__('struct').pack('>f', 330.0)); s.set_u('status_b.date', 5)' --shots 4,5.5,7,12,16,28 WWHD_SHIP_WARP=150:302973:-84873 WWHD_ACTOR_DUMP=runs/verify-chests/ of the author's working copy, not in this repositoryghost_steps/ayush.bin:0214A9A4:330 --cache ghost_steps
```

log: 252 lines, halt/crash/assert/fatal lines: 0, test_done: True

### ghost_steps_inside

```
python3 vc.py ghost_steps_inside ../../samples/gc/cryze/100%/26-BeforeSavageLabyrinth.gci 1 PShip 2 0 20 --opt all=steps --shots 4,7,9,12,18 WWHD_KILL_ENEMIES=140,160 WWHD_LINK_WARP=150:0:-550:-3760:-32768 WWHD_TEST_PRESS=10-10.2:8000 --cache ghost_steps_inside
```

log: 240 lines, halt/crash/assert/fatal lines: 0, test_done: True

### horseshoe_rewards

```
python3 vc.py horseshoe_rewards ../../samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci 1 sea 43 0 40 --opt all=rewards --shots 4,7,10,13,16,18.5,22,25,28,38 WWHD_KILL_ENEMIES=145,200,400 WWHD_LINK_WARP=150:-289800:2050:325200:0,420:-293743.4:1950:321256.6:-24576 WWHD_TEST_PRESS=17-17.2:8000,23-23.2:8000,26-26.2:8000,29-29.2:8000,32-32.2:8000,35-35.2:8000 --cache horseshoe_rewards
```

log: 302 lines, halt/crash/assert/fatal lines: 0, test_done: True

### horseshoe_steps

```
python3 vc.py horseshoe_steps ../../samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci 1 sea 43 0 40 --opt all=steps --shots 4,7,10,13,16,18.5,22,25,28,38 WWHD_KILL_ENEMIES=145,200,400 WWHD_LINK_WARP=150:-289800:2050:325200:0,420:-293743.4:1950:321256.6:-24576 WWHD_TEST_PRESS=17-17.2:8000,23-23.2:8000,26-26.2:8000,29-29.2:8000,32-32.2:8000,35-35.2:8000 --cache horseshoe_steps
```

log: 302 lines, halt/crash/assert/fatal lines: 0, test_done: True

### starbelt_rewards_C

```
python3 vc.py starbelt_rewards_C ../../samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci 1 sea 21 0 50 --opt all=rewards WWHD_SHIP_WARP=60:335000:-102000 WWHD_KILL_ENEMIES=680,695,740,770 WWHD_TEST_PRESS=5-5.2:4000,11-11.2:4000,19.5-19.7:4000,21-21.2:4000,26-26.2:8000,32-32.2:8000,35-35.2:8000,38-38.2:8000,41-41.2:8000,44-44.2:8000 --shots 19,20.5,22,24,25.5,27.5,31,34,37,40,43,48 WWHD_LINK_WARP=690:330357.6:2110:-105357.6:24576 WWHD_ACTOR_DUMP=runs/verify-chests/ of the author's working copy, not in this repositorystarbelt_rewards_C/tbox.bin:024B577C:B08 --cache starbelt_rewards_C
```

log: 301 lines, halt/crash/assert/fatal lines: 0, test_done: True

### starbelt_steps

```
python3 vc.py starbelt_steps ../../samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci 1 sea 21 0 50 --opt all=steps WWHD_SHIP_WARP=60:335000:-102000 WWHD_KILL_ENEMIES=680,695,740,770 WWHD_TEST_PRESS=5-5.2:4000,11-11.2:4000,19.5-19.7:4000,21-21.2:4000,26-26.2:8000,32-32.2:8000,35-35.2:8000,38-38.2:8000,41-41.2:8000,44-44.2:8000 --shots 19,20.5,22,24,25.5,27.5,31,34,37,40,43,48 WWHD_LINK_WARP=690:330357.6:2110:-105357.6:24576 --cache starbelt_steps
```

log: 301 lines, halt/crash/assert/fatal lines: 0, test_done: True

### paw_rewards

```
python3 vc.py paw_rewards ../../samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci 1 Cave07 0 0 50 --opt all=rewards --opt floor50=steps --shots 4,8,12,16,20,24,26,30,34,38,42,48 WWHD_KILL_ENEMIES=300,400,500 WWHD_LINK_WARP=150:2000:60:0:16384,750:2420:27:0:16384 WWHD_TEST_PRESS=27-27.2:8000,33-33.2:8000,36-36.2:8000,39-39.2:8000,42-42.2:8000,45-45.2:8000 --cache paw_rewards
```

log: 303 lines, halt/crash/assert/fatal lines: 0, test_done: True

### paw_rewards_nokill

```
python3 vc.py paw_rewards_nokill ../../samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci 1 Cave07 0 0 30 --opt all=rewards --opt floor50=steps --shots 4,8,12,16,20,28 WWHD_LINK_WARP=150:2000:60:0:16384,600:2420:27:0:16384 WWHD_TEST_PRESS=24-24.2:8000 --cache paw_rewards_nokill
```

log: 239 lines, halt/crash/assert/fatal lines: 0, test_done: True

### paw_steps

```
python3 vc.py paw_steps ../../samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci 1 Cave07 0 0 50 --opt all=steps --shots 4,8,12,16,20,24,26,30,34,38,42,48 WWHD_KILL_ENEMIES=300,400,500 WWHD_LINK_WARP=150:2000:60:0:16384,750:2420:27:0:16384 WWHD_TEST_PRESS=27-27.2:8000,33-33.2:8000,36-36.2:8000,39-39.2:8000,42-42.2:8000,45-45.2:8000 --cache paw_steps
```

log: 303 lines, halt/crash/assert/fatal lines: 0, test_done: True

### paw_f50rewards

```
python3 vc.py paw_f50rewards ../../samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci 1 Cave07 0 0 50 --opt all=steps --opt floor50=rewards --opt pawprint_chest=rewards --shots 4,8,12,16,20,24,26,30,34,38,42,48 WWHD_KILL_ENEMIES=300,400,500 WWHD_LINK_WARP=150:2000:60:0:16384,750:2420:27:0:16384 WWHD_TEST_PRESS=27-27.2:8000,33-33.2:8000,36-36.2:8000,39-39.2:8000,42-42.2:8000,45-45.2:8000 --cache paw_f50rewards
```

log: 275 lines, halt/crash/assert/fatal lines: 0, test_done: True

### salv46_f50rewards

```
python3 vc.py salv46_f50rewards ../../samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci 1 sea 46 0 50 --opt all=steps --opt floor50=rewards --opt pawprint_chest=rewards --hd 's.data[layout.FIELDS['status_a.select_item'][0]] = 3; mapbit(s,'map.open_map',8,True)' WWHD_SHIP_WARP=150:8300:285300,315:8300:285300 WWHD_TEST_PRESS=8-8.3:2000,11-21:8000,32-32.2:8000,35-35.2:8000,38-38.2:8000,41-41.2:8000,44-44.2:8000,47-47.2:8000 --shots 9,14,20,26,31,34,40,49 --cache salv46_f50rewards
```

log: 253 lines, halt/crash/assert/fatal lines: 0, test_done: True

### salv46_f50steps

```
python3 vc.py salv46_f50steps ../../samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci 1 sea 46 0 50 --opt all=steps --hd 's.data[layout.FIELDS['status_a.select_item'][0]] = 3; mapbit(s,'map.open_map',8,True)' WWHD_SHIP_WARP=150:8300:285300,315:8300:285300 WWHD_TEST_PRESS=8-8.3:2000,11-21:8000,32-32.2:8000,35-35.2:8000,38-38.2:8000,41-41.2:8000,44-44.2:8000,47-47.2:8000 --shots 9,14,20,26,31,34,40,49 --cache salv46_f50steps
```

log: 271 lines, halt/crash/assert/fatal lines: 0, test_done: True

### salv45_kept

```
python3 vc.py salv45_kept ../../samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci 1 sea 6 0 50 --opt all=steps --opt pawprint_chest=rewards --hd 's.data[layout.FIELDS['status_a.select_item'][0]] = 3; mapbit(s,'map.open_map',7,True)' WWHD_SHIP_WARP=150:227100:-312700,315:227100:-312700 WWHD_TEST_PRESS=3-3.2:8000,8-8.3:2000,11-21:8000,32-32.2:8000,35-35.2:8000,38-38.2:8000,41-41.2:8000,44-44.2:8000,47-47.2:8000 --shots 4,9,14,20,26,31,34,40,49 --cache salv45_kept
```

log: 270 lines, halt/crash/assert/fatal lines: 0, test_done: True

### salv45_given

```
python3 vc.py salv45_given ../../samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci 1 sea 6 0 50 --opt all=steps --hd 's.data[layout.FIELDS['status_a.select_item'][0]] = 3; mapbit(s,'map.open_map',7,True)' WWHD_SHIP_WARP=150:227100:-312700,315:227100:-312700 WWHD_TEST_PRESS=3-3.2:8000,8-8.3:2000,11-21:8000,32-32.2:8000,35-35.2:8000,38-38.2:8000,41-41.2:8000,44-44.2:8000,47-47.2:8000 --shots 4,9,14,20,26,31,34,40,49 --cache salv45_given
```

log: 270 lines, halt/crash/assert/fatal lines: 0, test_done: True

### salv45_f50rewards_kept

```
python3 vc.py salv45_f50rewards_kept ../../samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci 1 sea 6 0 50 --opt all=steps --opt floor50=rewards --opt pawprint_chest=rewards --hd 's.data[layout.FIELDS['status_a.select_item'][0]] = 3; mapbit(s,'map.open_map',7,True); s.set_u('status_a.rupee', 1000)' WWHD_SHIP_WARP=150:227100:-312700,315:227100:-312700 WWHD_TEST_PRESS=3-3.2:8000,8-8.3:2000,11-21:8000,32-32.2:8000,35-35.2:8000,38-38.2:8000,41-41.2:8000,44-44.2:8000,47-47.2:8000 --shots 4,9,14,20,26,31,34,40,49
```

log: 252 lines, halt/crash/assert/fatal lines: 0, test_done: True

### salv45_f50rewards_taken

```
python3 vc.py salv45_f50rewards_taken ../../samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci 1 sea 6 0 50 --opt all=steps --opt floor50=rewards --hd 's.data[layout.FIELDS['status_a.select_item'][0]] = 3; mapbit(s,'map.open_map',7,True); s.set_u('status_a.rupee', 1000)' WWHD_SHIP_WARP=150:227100:-312700,315:227100:-312700 WWHD_TEST_PRESS=3-3.2:8000,8-8.3:2000,11-21:8000,32-32.2:8000,35-35.2:8000,38-38.2:8000,41-41.2:8000,44-44.2:8000,47-47.2:8000 --shots 4,9,14,20,26,31,34,40,49
```

log: 252 lines, halt/crash/assert/fatal lines: 0, test_done: True
