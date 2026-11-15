# ww-gc2hd

Converts a *The Legend of Zelda: The Wind Waker* save from the GameCube (NTSC-U, `GZLE01`) into a
*Wind Waker HD* save for the Wii U (`cking.sav`, USA title `00050000-10143500`; also what Cemu uses).

Python 3.8+, no dependencies.

## Why this tool

Nintendo offers no way to bring a GameCube save to Wind Waker HD. One community converter exists:
`tools/savegame/gc2hd.py` of the [ZeldaWWHDRecomp](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp) native
port (read at commit `1af1d61`, 2026-11-13). It copies the save block field by field and applies three rules:
save counter 0 -> 1, Tingle Tuner -> Tingle Bottle, and the Deluxe Picto Box when Lenzo is waiting for the
firefly. Its README lists as not tested: HD saves in Cemu or on a Wii U, and saving and reloading in the game.

That is enough for a save where the two games agree. They do not agree everywhere: HD moved rewards between
places and reused chart numbers, so a plain copy can produce a file that no HD game could have written. For
example, with that converter:

- A GameCube Triforce Chart 2, 4, 6, 7 or 8 becomes HD's Treasure Chart 42-46 (same number, other chart). If
  its shard was not salvaged yet, the shard cannot be obtained any more: in HD it sits in the chest the
  GameCube player already opened.
- The Hero's Charm becomes unobtainable when the Savage Labyrinth floor-50 chest was opened on the GameCube
  before Mrs. Marie gave her reward (HD keeps the charm in that chest), and the floor-50 Piece of Heart can
  be collected a second time under Two-Eye Reef, where HD keeps it.
- Treasure Charts 43-46 cannot be obtained when their chests were opened on the GameCube.
- The Sail and the Wind Waker stay on item buttons, where HD never has them; Picto Box pictures are dropped.

This tool was written to make the conversion exact and to prove it:

| | ZeldaWWHDRecomp `gc2hd.py` | `ww-gc2hd` |
|---|---|---|
| Translation rules | 3 | every difference found between the two games (`docs/DIFFERENCES.md`): 13 fields with other conventions, the HD-only records, and every place whose reward differs |
| Places whose reward differs | not handled | each is a case with two exact translations, `steps` or `rewards`, chosen by the user, no default |
| Guarantee | none stated | every unique reward (shards, charts, Hero's Charm, Pieces of Heart, Deluxe Picto Box) is held exactly when its HD place is done: none lost, none twice (a test runs every combination of cases and answers). Rupees and spoils, which both games give without limit, are translated as far as possible; the exception is in `docs/DIFFERENCES.md`, Known gaps |
| Picto Box pictures | dropped | converted to the HD album |
| Report | short notes | every change with its reason, and what you hold before and after |
| Completeness of the difference list | not stated | both games compared in full: stage data byte by byte, machine code of every save access and item gift, both randomizers' location tables, shops |
| Verified in the game | one load in the port, per its README | every case played in both modes in the port; all 32 sample saves loaded, 28 of them saved from the pause menu (the other four start in a scene without the menu); load and save in Cemu |
| Regions | USA, Japan, Europe | USA (Japan / Europe convert with `--allow-region`, unverified) |
| HD -> GameCube | `hd2gc.py`, shared fields | no |

Not done here either: a run on a real Wii U.

```
./ww-gc2hd info    "My Save.gci"                 # what is in a GameCube or HD save
./ww-gc2hd convert "My Save.gci" -o out          # writes out/cking.sav and reports every change
./ww-gc2hd verify  out/cking.sav                 # checksums and structure of an HD save
```

Input: `.gci`, `.gcs`, `.sav`, or a raw memory card image (Dolphin `MemoryCardA.USA.raw`, a card dump).
All three files of the card are converted to Quest Logs 1-3. The input is never modified, and an existing
save in the output folder is only replaced with `--force`, which first moves it (`cking.sav` and its
`cking_pic*` album files) to a `backup-<date>` folder there.

Install the result as `mlc01/usr/save/00050000/10143500/user/80000001/cking.sav` (Cemu) or with a save
manager such as SaveMii on a console, together with the `cking_pic*` files written next to it. It replaces
all three Quest Logs: back up the game's save folder first and remove its old `cking_pic*` files, which
are the albums of the Quest Logs being replaced.

## Choices

The two games are not the same game. Some places give a different reward in each, so a GameCube save can
be in a state HD does not have. For each such case the save is in, the tool stops, explains it and asks.
There is no default. Each case has two answers:

- `steps`: the place stays done; you lose what the GameCube gave there and get what HD gives there. Consumables
  (rupees, a Skull Necklace, a Joy Pendant) are taken back as far as you still hold them.
- `rewards`: you keep what you have; the place is undone (the chest is closed again) and the place that gives
  your reward in HD is marked done.

An option answers a case in advance, and `--all steps|rewards` answers all of them, so a script never stops.
Without a terminal and without the option, the tool exits and lists the cases. A case can be answered per Quest
Log (`--floor50 1=steps,3=rewards`).

| Option (`steps` / `rewards`) | Case |
|---|---|
| `--triforce-chart-2`, `-4`, `-6`, `-7`, `-8` | that Triforce Chart is owned and its shard is not salvaged (HD: the chest holds the shard) |
| `--horseshoe-chest`, `--star-belt-chest` | that lookout chest is open (HD: Treasure Chart 43 / 44) |
| `--floor50` | the Savage Labyrinth floor-50 chest is open (GameCube: Piece of Heart; HD: Hero's Charm) |
| `--pawprint-chest` | the Pawprint Isle Wizzrobe cave chest is open (HD: Treasure Chart 46) |
| `--marie` | Mrs. Marie's reward for 40 Joy Pendants was given (GameCube: Hero's Charm; HD: Treasure Chart 45) |
| `--lenzo` | Lenzo accepted the third picture and the Picto Box is not the Deluxe one (HD gives it at that step) |

Other options:

| Option | Effect |
|---|---|
| `--swift-sail` | upgrade an owned Sail to HD's Swift Sail (off unless given) |
| `--hero-mode` | HD's Hero Mode (off unless given) |

Picto Box pictures are converted into HD's album files (`cking_pic*.sav`, written next to `cking.sav`;
`--no-pictures` skips them). Not carried over: the card's banner. Everything else
is listed, with evidence, in [docs/DIFFERENCES.md](docs/DIFFERENCES.md).

## How it was checked

- Both save formats and every rule come from the decompilations of both games and were checked against
  257 real GameCube saves and 45 real HD saves (`samples/`, sources in `samples/SOURCES.md`).
- `python3 -m unittest tests.test_wwsave` converts every GameCube sample and checks the result against a
  model of what HD does when it loads a Quest Log, against properties of all real HD saves, and that no
  field outside the documented rules changes.
- `python3 scripts/compare_with_hd.py` compares converted saves with real HD saves statistically.
- `python3 scripts/stage_diff.py`, `scripts/evnt_diff.py` and `scripts/event_diff.py` compare the stage data,
  stage event tables and event scripts of the two games.
- `python3 scripts/gc_stage_dump.py DISC.iso out.json` dumps chests and actors from your own GameCube disc
  image; the chest flags the rules rely on were confirmed with it.
- In the game: `scripts/ingame_test.py` loads a save with the game's own code (the ZeldaWWHDRecomp native
  port, built from your copy of Wind Waker HD) and compares the game's memory with the file;
  `scripts/ingame_batch.py` does it for every converted USA sample, and `scripts/ingame_save_batch.py`
  also saves from the pause menu and compares the file the game writes. Loading, playing and saving from the
  pause menu were checked this way, and the same load / play / save / reload cycle was repeated in Cemu.
  `scripts/ingame_case.py` builds a test save for one case with chosen answers and a start place.
  `scripts/ingame_salvage.py` salvages the HD Treasure Charts 43-46 of a converted save (needs the port
  built with `scripts/port-ship-warp.patch`); the Triforce (down to Hyrule with eight shards) and Lenzo's
  dialogue after the Deluxe Picto Box rule were also played from converted saves (docs/DIFFERENCES.md,
  Verification). Not done: a run on a real console.

## Layout

```
ww-gc2hd            command-line entry point
wwsave/layout.py    the 0x768-byte save block both games share
wwsave/gc.py        GameCube card files and memory card images
wwsave/hd.py        HD cking.sav
wwsave/convert.py   conversion rules and options
wwsave/hdcheck.py   model of HD's load-time rewrites and HD invariants
wwsave/picture.py   Picto Box pictures: GameCube texture -> HD album (JPEG)
wwsave/describe.py  human-readable summary
tests/              unit tests (conversion rules, every combination of cases and answers)
scripts/            tools used for the research and for the checks in the running game
docs/DIFFERENCES.md every GameCube/HD difference found, with evidence
docs/research/      longer notes and the audits the difference list rests on
docs/verification/  reports of the runs in the game, case by case
docs/SETUP-RESEARCH.md  how to set up research/ (game dumps, clones, the native port) for what follows
audit/              the scripts of the audits behind "nothing else differs" (audit/README.md)
verify/             the scripts that play each case in the game (verify/README.md)
CLAUDE.md           how a coding agent should work on this project
samples/            real saves used for verification, with their sources (SOURCES.md)
```

## Samples

`samples/` holds the real saves the tests and the checks in the game run on: GameCube saves under
`samples/gc`, Wind Waker HD saves under `samples/hd`. They were shared publicly by their authors and are
included as downloaded, each folder named after its source; `samples/SOURCES.md` lists every source with
its link and what the uploader said about the file. If one of them is yours and you want it removed, open
an issue.

`python3 scripts/fetch_samples.py --check` compares the folder with `samples/checksums.sha256`, and without
`--check` the script downloads everything again from the sources (`samples/manifest.json`). That also brings
what the repository does not keep because nothing here uses it: the original archives, files that failed
validation, save states of the native port, and other files that came along (`.gitignore` lists them).

## What is not in this repository

No game data and no third-party code. To repeat the research or the checks in the game you need your own
copies under `research/`, which is git-ignored (`docs/SETUP-RESEARCH.md` has the steps): your own dumps of
both games, and clones of the projects the research reads: [zeldaret/tww](https://github.com/zeldaret/tww) (GameCube decompilation), the Wind
Waker HD decompilation and [ZeldaWWHDRecomp](https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp) (native
port, used to run converted saves; `scripts/port-ship-warp.patch` and `scripts/port-kill-enemies.patch` add
the test aids the in-game scripts use).

Only USA GameCube saves are supported; `--allow-region` converts Japanese and European ones without any
of the checks above having been made for them.

## License

MIT (`LICENSE`), for the code and documents of this project. Not covered by it: the saves in `samples/`,
which belong to the people who shared them (`samples/SOURCES.md`), and the two patches for the native port
in `scripts/`, which are under the Mozilla Public License 2.0 like the file they modify
(`scripts/PORT-PATCHES.md`).

This project is not affiliated with Nintendo. The Legend of Zelda and The Wind Waker are trademarks of
Nintendo.

## Made with AI assistance

The research, the code, the tests, the in-game verification and the documents of this project were made
with the help of an AI coding assistant (Claude, by Anthropic), directed and reviewed by the author. Treat
the claims here like any other: each one in `docs/DIFFERENCES.md` carries its evidence so that it can be
checked, and what was not verified is listed there.
