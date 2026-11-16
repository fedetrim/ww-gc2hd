# In-game verification: Mrs. Marie and Lenzo (GameCube -> HD converter)

> These are the reports of the runs as they were made. The scripts are published in `verify/` (see
> `verify/README.md`); paths such as `runs/verify-...` are the author's local output folders. Rules added to
> the converter afterwards (for example giving back Tingle's deciphering fee) change some rupee counts
> quoted here; the fields each case is about are unchanged.

All runs: native port `research/port-src/build/cmake/wwhd`, game files `research/hd-game/game`, driven by
`scripts/ingame_test.py`. Every run reached the end of its scenario (`run/test_done`) and its log has no
halt/crash/assert line. Each case directory holds `cking.sav` (the save loaded), `prep.txt` (converter changes and
state of the file), `result.txt` (file vs. the game's save block at the end), `contact.png` (all screenshots,
numbered, in time order), `shots/` (full-size screenshots) and `run/` (log, `si.bin`).

Scripts (all in `runs/verify-npc/`): `prep.py` (convert + test-only edits), `analyze.py` (decode `si.bin`),
`contact.py` (contact sheet), `run_marie.sh`, `run_lenzo.sh`.

## Verdicts

| Rule | Mode | Verdict | Evidence |
|---|---|---|---|
| 1a Mrs. Marie | `marie=rewards` | VERIFIED in game (3 samples) | `marie-rewards-A/`, `marie-rewards-B/`, `marie-rewards-C/` |
| 1b Mrs. Marie | `marie=steps` | VERIFIED in game for 2 samples; for the third (99 pendants already given) no chart, but no rupees either | `marie-steps-A/`, `marie-steps-B/`, `marie-steps-C/` |
| 2a Lenzo | `lenzo=rewards` | VERIFIED in game | `lenzo-rewards/` |
| 2b Lenzo | `lenzo=steps` | VERIFIED in game | `lenzo-steps/` |

No behaviour of the game contradicted the converter's rules. One wording point in claim 1b: see sample A below.

## Test-only edits to the converted saves (not converter output)

- Start place set to the NPC's room (`Nitiyou` / `Ocmera`, room 0, point 0); time of day set to noon
  (`status_b.time` = 180.0) so Mrs. Marie is not in her night state and Lenzo is behind the counter.
- Marie: the Joy Pendant bag slot put on button X (`select_item[0]` = 24 + bag slot).
- Marie sample C (file 2 of `01-GZLE-gczelda.gci`) has 0 Joy Pendants: one was added (bag slot, count 1, bag flag)
  so there is something to show.
- Lenzo: the Picto Box slot (8) put on button X; the album files are the converter's own output
  (`convert_pictures`) for file 1, written as Quest Log 1. No picture had to be crafted: the sample's three
  GameCube pictures already have subject 3 (album: count 3, subjects [3, 3, 3]).

## Rule 1 - Mrs. Marie

Command (per case): `runs/verify-npc/run_marie.sh NAME GCI FILE rewards|steps [--add-pendant]`, which runs

    python3 runs/verify-npc/prep.py GCI FILE runs/verify-npc/NAME/cking.sav Nitiyou 0 0 all=MODE --pendant-button --time 12 [--add-pendant]
    python3 scripts/ingame_test.py research/port-src/build/cmake/wwhd research/hd-game/game runs/verify-npc/NAME/cking.sav runs/verify-npc/NAME/run 62 \
      "WWHD_LINK_WARP=150:-4:0:-175:-32768" "WWHD_TEST_PRESS=8-8.2:2000,12-12.2:8000,13.5-13.7:8000,...(A every 1.5 s until 58.5)" \
      "WWHD_TEST_SCREENSHOT=3610,3700,...,5200 (every 3 s)" "WWHD_SCREENSHOT_DIR=runs/verify-npc/NAME/shots"

Samples: A = `samples/gc/archive-org-zeldasaves/extracted/NGC/USA/the-legend-of-zelda-the-wind-waker.14259.gci`
file 1; B = `samples/gc/gc-saves.com/the_legend_of_zelda_the_wind_waker_usa.gci` file 1;
C = `samples/gc/archive-org-memcard-251-us/extracted-gci/01-GZLE-gczelda.gci` file 2 (`--add-pendant`).
The marie-rewards-B run was the first, launched by hand with the same arguments.

Link shows the pendant with X at 8 s; the A presses answer every message and afterwards start ordinary
conversations with her again (visible at the end of each contact sheet; they hand out nothing).

### 1a `rewards` (event 0x1C04 cleared by the converter, Hero's Charm kept)

| Case | 0x1C04 file -> game | Chart 45 (`map.get_map` collect map 7) | Joy Pendants | reg 0xC0FF | rupees / max life / `collect` | all other changed fields |
|---|---|---|---|---|---|---|
| marie-rewards-A | 0 -> 1 | 0 -> 1 | 99 -> 99 | 99 -> 99 | unchanged | none |
| marie-rewards-B | 0 -> 1 | 0 -> 1 | 11 -> 0 | 45 -> 56 | unchanged | bag slot emptied, button X cleared |
| marie-rewards-C | 0 -> 1 | 0 -> 1 | 1 -> 0 | 40 -> 41 | unchanged | bag slot emptied, button X cleared |

Screens (e.g. `marie-rewards-B/contact.png` frames 3-9, `marie-rewards-A/contact.png` frames 3-9): "How many Joy
Pendants have you brought?", "...I shall give you... this!", "You got a Treasure Chart!", "Open this chart on the
Map Screen...". Nothing else is handed out (rupees, hearts and the `collect` bytes with the Hero's Charm are
identical before and after). In sample A she already holds 99 pendants, so she takes none; the chart is given all
the same.

### 1b `steps` (converted save holds Treasure Chart 45, 0x1C04 stays set)

| Case | Chart 45 in file / game | 0x1C04 | Joy Pendants | rupees | all other changed fields |
|---|---|---|---|---|---|
| marie-steps-A | 1 / 1 | 1 -> 1 | 99 -> 99 | 4780 -> 4780 | none at all |
| marie-steps-B | 1 / 1 | 1 -> 1 | 11 -> 0 | 820 -> 920 | reg 0xC0FF 45 -> 56, bag slot emptied, button X cleared |
| marie-steps-C | 1 / 1 | 1 -> 1 | 1 -> 0 | 200 -> 220 | reg 0xC0FF 40 -> 41, bag slot emptied, button X cleared |

She does not give the chart again in any of the three. B: "You got an Orange Rupee!" (`marie-steps-B/contact.png`
frame 6); C: a Red Rupee (+20). Sample A: she has already received 99 pendants (reg 0xC0FF = 99), answers "To be
honest, I can actually only count to 99, anyway." (`marie-steps-A/contact.png` frame 3) and gives nothing and
takes nothing. So "she gives rupees instead" holds while fewer than 99 pendants have been given; at 99 she gives
nothing. `map.get_map` is unchanged by the game in all three.

## Rule 2 - Lenzo

Sample: `samples/gc/archive-org-memcard-251-us/extracted-gci/01-GZLE-gczelda.gci` file 1 (GameCube: register
0xC407 = 7, Picto Box 0x23, 13 Joy Pendants). Commands: `runs/verify-npc/run_lenzo.sh rewards` and
`runs/verify-npc/run_lenzo.sh steps`, which run

    python3 runs/verify-npc/prep.py GCI 1 runs/verify-npc/lenzo-MODE/cking.sav Ocmera 0 0 all=MODE --camera-button --album --time 12
    python3 scripts/ingame_test.py research/port-src/build/cmake/wwhd research/hd-game/game runs/verify-npc/lenzo-MODE/cking.sav runs/verify-npc/lenzo-MODE/run END \
      "WWHD_LINK_WARP=150:-380:0:-259:-16384" "WWHD_TEST_PRESS=..." "WWHD_TEST_SCREENSHOT=... (every 1.5 s)" "WWHD_SCREENSHOT_DIR=..."

    rewards: END 60, press 8-8.2:2000 (X: show the Picto Box), then A every 2 s from 12 s to 58 s
    steps:   END 45, A every 2 s from 8 s to 42 s (plain talk)

(The two runs recorded here were launched by hand with exactly these arguments; `run_lenzo.sh` repeats them.)

How the picture is shown in HD: with the Picto Box on an item button, pressing that button at Lenzo opens the
album in selection mode (`EventControl::photoCheck`, d_event.cpp, needs an album count > 0); A on a picture asks
"Show this pictograph?" with "Yes" preselected; A again starts the talk with `mbInPhoto` set and the picture's
subject as picture result (hd_screen_pictograph_list.cpp `updateReplaceMessage`).

### 2a `rewards` (converter: register 0xC407 = 5, plain Picto Box)

`lenzo-rewards/result.txt`: register 0xC407 5 -> 6, `item.slot08` 0x23 -> 0x26, `get_item.slot08` 0x01 -> 0x03
(bit 1 set). Joy Pendants 13 -> 13, rupees and hearts unchanged. Only other change: event byte 0x38 0x56 -> 0x5E
(bit 0x3808, set by Lenzo's first talk as owner of the Deluxe Picto Box, which the trailing A presses started).

Screens (`lenzo-rewards/contact.png`): frames 2-5 the album with "Show this pictograph? No / Yes"; 7-9 "Oh-ho!
This is a finely snapped pictograph indeed! ...I had no idea these two would get along so splendidly!"; 13-16 "You
have completed all of the tasks I set you to... I shall hereby be proud to call you my assistant"; 18-20 "You got
a Deluxe Picto Box!"; 21-24 the colour-pictograph explanation; from 27 the Legendary Pictograph talk.

Not checked: whether the shown picture was removed from the album (the album is not part of the dumped save
block; the code erases it).

### 2b `steps` (converter: Deluxe Picto Box given, one Joy Pendant taken back)

`lenzo-steps/prep.txt`: converted file has slot 8 = 0x26, get bits 0x03, register 0xC407 = 7, Joy Pendants 12
(GameCube 13). `lenzo-steps/result.txt`: the game changes nothing but event byte 0x38 0x56 -> 0x5E (0x3808, as
above); Deluxe Picto Box, register and pendants as in the file.

Screens (`lenzo-steps/contact.png`): Lenzo talks as after the quest - "Guess what, young LINK! Today is a great
day in pictography!", the Legendary Pictograph offer, "If you have any open pictograph slots, I will place the
image in your Deluxe Picto Box." No third-task request.

## Limits

- Runs are on the native port, not Cemu or a Wii U.
- Lenzo rewards was run on the one sample of the case; showing a picture whose subject is not 3 was not tried.
- In 2b only plain talk was driven, not showing a picture to Lenzo after the quest.

## Addendum - Rule 2a redone from a GameCube state that legitimately holds the picture (`lenzo-rewards-legit/`)

Reason: the converter now converts only the pictures the GameCube game itself would load (`wwsave/gc.py
pictures()`: the first `item_record.picture_num` slots not marked in event register 0x89FF, valid checksum).
File 1 of `01-GZLE-gczelda.gci` has picture_num = 0, so its three couple pictures are left-overs of erased
pictures and the current converter writes no album for it; the `lenzo-rewards/` run above used an album from the
earlier picture rule.

GameCube input: `runs/verify-npc/make_gci_pictures.py` copies the sample and, in both save copies, sets file 1's
`item_record.picture_num` to 3 (register 0x89FF was already 0), recomputing the file checksum and the block
checksum; picture blocks and all other bytes are unchanged.

    python3 runs/verify-npc/make_gci_pictures.py samples/gc/archive-org-memcard-251-us/extracted-gci/01-GZLE-gczelda.gci 1 3 runs/verify-npc/lenzo-rewards-legit/input.gci
    ./ww-gc2hd info runs/verify-npc/lenzo-rewards-legit/input.gci        # File 1: "Pictures: 3" (the original sample: 0)
    ./ww-gc2hd convert --all rewards -o runs/verify-npc/lenzo-rewards-legit/cli-out runs/verify-npc/lenzo-rewards-legit/input.gci
        # "Lenzo's third task is pending again (by rewards)...", "3 Picto Box picture(s) converted to the HD album (cking_pic0_*.sav, cking_pic_order0.sav)"
    python3 runs/verify-npc/prep.py runs/verify-npc/lenzo-rewards-legit/input.gci 1 runs/verify-npc/lenzo-rewards-legit/cking.sav Ocmera 0 0 all=rewards --camera-button --album --time 12
        # album: count 3, subjects [3, 3, 3]; its cking_pic0_* / cking_pic_order0 files are byte-identical to the CLI's (cmp)
    python3 scripts/ingame_test.py research/port-src/build/cmake/wwhd research/hd-game/game runs/verify-npc/lenzo-rewards-legit/cking.sav runs/verify-npc/lenzo-rewards-legit/run 58 \
      "WWHD_LINK_WARP=150:-380:0:-259:-16384" "WWHD_TEST_PRESS=$(cat runs/verify-npc/lenzo-rewards-legit/press.txt)" \
      "WWHD_TEST_SCREENSHOT=3610,3655,...(every 1.5 s)" "WWHD_SCREENSHOT_DIR=runs/verify-npc/lenzo-rewards-legit/shots"

Input: X at 8 s (show the Picto Box), A every 2 s from 12 s to 42 s (pick the picture, "Yes", all messages), X
again at 47 s (opens the album a second time; nothing is pressed after that).

Result - VERIFIED in game (`lenzo-rewards-legit/result.txt`, `contact.png`): reached the end, no
halt/crash/assert line. Register 0xC407 5 -> 6, `item.slot08` 0x23 -> 0x26, `get_item.slot08` 0x01 -> 0x03. Joy
Pendants (13), rupees, hearts unchanged; no other field of the save block differs from the file. Screens: frames
2-5 album "3/3" and "Show this pictograph? No / Yes"; 7-11 Lenzo accepts ("finely snapped pictograph indeed...",
"I shall promptly take this pictograph from you"); 13-16 all tasks completed, "my assistant"; 18-20 "You got a
Deluxe Picto Box!".

The shown picture is removed from the HD album: before showing, the album counter reads "3/3" (frames 2-5); when
the album is opened again after the gift it reads "2/2" (frames 28-34). Seen on screen only; the album files on
disk were not read back (the runner deletes its copy of the save folder).

Found on the way, not changed (outside this task): `./ww-gc2hd info` prints "Joy Pendant x19" for this file. The
Spoils Bag counters are indexed by item kind, not by bag slot (the game zeroed counter index 7 when Mrs. Marie
took the pendants while the pendant sat in bag slot 6); this file's Joy Pendant count is counter 7 = 13 (the
converter's `_take_spoil` uses index 7 too), 19 is counter 0. The `info` listing appears to pair counters with bag
slots.
