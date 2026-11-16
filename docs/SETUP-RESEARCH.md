# Setting up `research/`

The converter itself (`ww-gc2hd`, `wwsave/`, `tests/`) needs nothing but Python and the saves in
`samples/`. This page is for repeating the research and the checks in the game: the scripts in
`scripts/`, `audit/` and `verify/` read your own copies of both games and clones of other projects.
All of that lives in `research/`, which is git-ignored and never published. Nothing below is included
in this repository or will be provided.

What was determined from the author's working copy is stated as fact. What could not be determined is
marked "not recorded".

## Layout

```
research/
  gc-disc/<any name>.iso      GameCube disc image, USA (GZLE01)
  gc-disc/stages.json         made by scripts/gc_stage_dump.py   (optional, see "Derived files")
  gc-disc/fst.json            made by audit/auditenv.py --fst    (optional)
  hd-game/game/               extracted Wind Waker HD, USA v0: code/, content/, meta/
  hd-game/stages.json         made by scripts/hd_stage_dump.py   (needed by verify/chests/vc.py)
  tww/                        clone of zeldaret/tww
  wwhd/                       clone of ZeldaWWHDDecomp/wwhd
  wwrando/                    clone of LagoLunatic/wwrando
  twwhd-rando/                clone of SuperDude88/TWWHD-Randomizer
  port-src/                   clone of ZeldaWWHDRecomp/ZeldaWWHDRecomp, built (in-game checks only)
  out/                        everything the audit and verify scripts write
```

Every location can be replaced with an environment variable instead of using this layout:
`audit/auditenv.py` (audits) and `verify/verifyenv.py` (in-game checks) list them, and each prints what
it resolved when run by itself.

## What needs what

| To run | You need |
|---|---|
| `ww-gc2hd`, `tests/`, `scripts/compare_with_hd.py`, `scripts/fetch_samples.py` | nothing from `research/` |
| `scripts/gc_stage_dump.py`, `hd_stage_dump.py`, `stage_diff.py`, `evnt_diff.py`, `event_diff.py` | both games |
| `audit/machine-code`, `audit/leftovers` | both games, `tww`, `wwhd` |
| `audit/rewards` | both games, `tww`, `wwhd`, `wwrando`, `twwhd-rando` |
| `audit/undo` | the HD game (and `wwhd` to read the code the report cites) |
| `scripts/ingame_*.py`, `verify/` | the HD game, `port-src` built |

## The games

### GameCube disc image

*The Legend of Zelda: The Wind Waker*, USA: game ID `GZLE01`, disc 0, revision 0 (bytes 0-7 of the
image). Put the image in `research/gc-disc/` with the extension `.iso`; the file name does not matter
as long as it is the only `.iso` there (or set `WW_GC_ISO`). The scripts read the file table at the
standard place (offset `0x424`) and the files at the offsets it gives. The author's image is an NKit
image (`.nkit.iso`, 1,086,173,184 bytes), which keeps that layout; a full 1.46 GB image works the same
way. Compressed formats (`.rvz`, `.gcz`, `.ciso`) are not read. How the author's image was dumped is
not recorded.

### Wind Waker HD

USA, title `00050000-10143500`, title version 0 (`meta/meta.xml`: product code `WUP-P-BCZE`,
`title_version` 0), extracted so that `research/hd-game/game/` holds `code/cking.rpx`, `content/` and
`meta/`. SHA-1 of the `code/cking.rpx` the audits ran on: `bdcbc4f815ae4c9b0a1f4a16238f96c197b38239`.
The audit scripts contain addresses of this binary, and the HD decompilation's address markers are for
it; another version or region gives wrong results without an error.

Ways to extract it from your own console and disc:

- from a disc image (`.wud`/`.wux` with its disc key and the Wii U common key), with the port's
  extractor: `python3 research/port-src/tools/wudextract.py game.wux extract research/hd-game/game`
  (the port's README, "Requirements" and "Building", has the details and a native `wwhd-extract`);
- from installable title files (NUS format, as dumped by console homebrew), with a decrypter such as
  [VitaSmith/cdecrypt](https://github.com/VitaSmith/cdecrypt).

The author's working copy has `cdecrypt` built in `research/tools/`; which of the two ways produced its
`hd-game/game` is not recorded.

## The clones

Commits are those of the author's working copy. Newer commits should work, but the figures in the
reports (function counts, stub lists, location names) are tied to these.

```sh
cd research
git clone https://github.com/zeldaret/tww.git                              # d217e2b5  GameCube decompilation
git clone https://github.com/ZeldaWWHDDecomp/wwhd.git                      # a13ed11c  HD decompilation (wwhd_src/)
git clone https://github.com/LagoLunatic/wwrando.git                       # 99281a37  GameCube randomizer
git clone https://github.com/SuperDude88/TWWHD-Randomizer.git twwhd-rando  # a66347af  HD randomizer
git clone --recurse-submodules https://github.com/ZeldaWWHDRecomp/ZeldaWWHDRecomp.git port-src   # 1af1d61b  native port
```

What the scripts read from them:

- `tww`: `config/GZLE01/` (symbols and splits of the dol and of every REL), `include/d/*.h`,
  `include/d/d_save_event_flag.inc`, `src/`. It does not have to be built.
- `wwhd`: `wwhd_src/` (sources with `/* 0XXXXXXX */` function address markers).
- `wwrando`: `logic/item_locations.txt`, `data/actor_info.txt`, `data/actor_parameters.txt`.
- `twwhd-rando`: `logic/data/location_data.yaml`.
- `port-src`: built, see below. Its `decomp` submodule is another checkout of `wwhd` (at `2c1deae`
  in the author's copy); the audits read `research/wwhd`, not the submodule.

Reading material the documents cite, used by no script:

- `research/archipelago-tww/`: `Locations.py`, `Items.py` and `TWWClient.py` from `worlds/tww/` of
  [ArchipelagoMW/Archipelago](https://github.com/ArchipelagoMW/Archipelago) (the `[AP]` evidence tag
  of `docs/DIFFERENCES.md`). `docs/research/chest-flags.md` gives the last change to `Locations.py` as
  commit `cf0ae5e3`; the commit the three files were downloaded at is not recorded.
- `research/TWWHDRAutoTracker` ([UnFuzed/TWWHDRAutoTracker](https://github.com/UnFuzed/TWWHDRAutoTracker)),
  `research/recomp` ([asadsi/wwhd-recomp-mods](https://github.com/asadsi/wwhd-recomp-mods)),
  `research/recomp-orig` (a second, partial clone of the port).
- `research/tools/cemu/`: Cemu 2.6.0 (macOS) in portable mode, used by hand for the load / save /
  reload check in Cemu that `docs/DIFFERENCES.md` reports. No script drives it; its setup (keys,
  title installation, controller profile) is not recorded here.

## Derived files

```sh
python3 scripts/gc_stage_dump.py research/gc-disc/*.iso research/gc-disc/stages.json
python3 scripts/hd_stage_dump.py research/hd-game/game research/hd-game/stages.json     # about 2 minutes
python3 -I audit/auditenv.py --fst research/gc-disc/fst.json     # only for scripts/event_diff.py
python3 scripts/stage_diff.py research/gc-disc/stages.json research/hd-game/stages.json
python3 scripts/evnt_diff.py research/gc-disc/*.iso research/hd-game/game
python3 scripts/event_diff.py research/gc-disc/*.iso research/gc-disc/fst.json research/hd-game/game
```

`research/hd-game/stages.json` is read by `verify/chests/vc.py` (the save record of each stage). The
audit scripts read the disc's file table themselves and do not need `fst.json`.

Then: `python3 -I audit/auditenv.py` should print `ok` on every line except `WW_AUDIT_OUT`, which is
created on first use, and `audit/run.sh` runs the audits ([audit/README.md](../audit/README.md)).

## The native port (in-game checks)

The checks in the game run the game's own code through the ZeldaWWHDRecomp native port, built from
your extracted copy. The port's `README.md` is the reference for requirements and platforms; what
follows is what the author's build used (macOS on Apple Silicon, Xcode command line tools, CMake,
`brew install zstd`; CMake cache: `Release`, `WWHD_RENDERER=METAL`).

```sh
cd research/port-src

# 1. the two test aids this project adds (both change runtime/src/test_aids.cpp only)
git apply ../../scripts/port-ship-warp.patch        # WWHD_SHIP_WARP
git apply ../../scripts/port-kill-enemies.patch     # WWHD_KILL_ENEMIES; applies on top of the first

# 2. recompile the game code to C (writes build/gen/, stays on your machine)
python3 tools/recomp/recomp.py ../hd-game/game/code/cking.rpx build/gen

# 3. build -> build/cmake/wwhd
cmake -S . -B build/cmake -DWWHD_RENDERER=METAL && make -C build/cmake -j$(sysctl -n hw.ncpu) wwhd
```

Notes on this procedure:

- Both patches were written against commit `1af1d61`. The second patch's context includes the lines
  the first adds, so apply them in this order. `git apply --check` accepts the second on a tree that
  has the first.
- The author never built one binary with both patches this way. The working copy's
  `build/cmake/wwhd` has the ship-warp patch only; the kill-enemies aid was compiled from a patched
  copy of `test_aids.cpp` and linked into a second binary with the commands taken from
  `build/cmake/compile_commands.json` and `build/cmake/CMakeFiles/wwhd.dir/link.txt`
  (`docs/verification/chests.md`, "Binary and aid"). That second binary has both aids. The steps above
  should give the same result in one build, but that exact sequence was not run.
- The first build recorded in the working copy ended in a linker error and a second `make` succeeded
  (`build-make.log`, `build-make2.log`); the cause is not recorded.
- Without the patches the port still runs everything that uses neither aid: `scripts/ingame_test.py`,
  `ingame_batch.py`, `ingame_save_batch.py`, `verify/npcs/`, and the chest cases whose line in
  `verify/chests/cases.txt` names neither aid (`f30_*`, `f50_*`, `tf04_steps`, `paw_rewards_nokill`).
- The in-game scripts were only run on macOS. `scripts/ingame_test.py` calls the port's
  `tools/gametest/run_scenario.sh` (zsh; it sets `WWHD_RENDERER_RUNTIME=metal` and uses `bc`), so
  Linux or Windows needs at least that runner adapted. Not tried.
- Optional Python package: Pillow, for the contact sheets (`verify/chests/vc.py --shots`,
  `verify/npcs/contact.py`).

Check the setup with `python3 verify/verifyenv.py`, then one short run:

```sh
python3 scripts/ingame_test.py research/port-src/build/cmake/wwhd research/hd-game/game samples/hd/<any>/cking.sav research/out/first-run
```

It should print "first-run: done=y" and "in memory after 6 s of play: 441 fields identical to the
file, 0 differ" (a save the game wrote itself keeps every field; the clock, date and current life are
not compared). A run takes
about two minutes, most of it the boot to the title screen and into Quest Log 1.

### Environment variables of the port that the scripts use

The port reads its test aids from the environment; none does anything unless set. A scenario's clock
starts at TV frame `WWHD_TEST_ORIGIN` (3400 in the runner, after the game has been taken from the title
screen into Quest Log 1).

Passed by this project's scripts as `NAME=value` arguments:

| Variable | Meaning | Where it is defined |
|---|---|---|
| `WWHD_TEST_PRESS=3-3.1:8000,...` | hold buttons (hex mask) from 3 s to 3.1 s of scenario time. Masks: A `8000`, B `4000`, X `2000`, Y `1000`, R `0010`, L `0020`, ZR `0040`, ZL `0080`, + `0008`, - `0004`, d-pad up/down/left/right `0200`/`0100`/`0800`/`0400` | `runtime/src/gfx/input.mm`, `runtime/src/input.h` |
| `WWHD_TEST_STICK=2-5:0:1,...` | left stick at (x, y) from 2 s to 5 s | `runtime/src/gfx/input.mm` |
| `WWHD_LINK_WARP=step:x:y:z:angle,...` | move Link, each entry once, at the given logic step after the origin (30 steps per second in these runs: 150 is 5 s) | `runtime/src/test_aids.cpp` |
| `WWHD_SHIP_WARP=step:x:z,...` | move the boat, and Link with it, keeping heights | `scripts/port-ship-warp.patch` |
| `WWHD_KILL_ENEMIES=step,...` | at each step ask the game to delete every actor of the enemy group | `scripts/port-kill-enemies.patch` |
| `WWHD_TEST_POKE=t:ADDR:HEX,...` | at scenario time t write bytes to guest memory; ADDR is hex or `*PTR+OFF` | `runtime/src/test_aids.cpp` |
| `WWHD_TEST_SCREENSHOT=f1,f2,...` | screenshots at those TV frames (`3400 + 30 * seconds`) | `runtime/src/screenshot.h` |
| `WWHD_SCREENSHOT_DIR=path` | where screenshots go | `runtime/src/screenshot.h` |
| `WWHD_SAVEINFO_AT=t1,t2,...` | extra dumps of the save block at those times (`si.bin.t1`, ...) | `runtime/src/test_aids.cpp` |
| `WWHD_ACTOR_DUMP=path:FN:SIZE` | after every execute of a process whose execute function is FN (hex), append its first SIZE bytes to path | `runtime/src/test_aids.cpp` |

Set by the port's `run_scenario.sh` on every run (no need to pass them): `WWHD_HIDDEN_WINDOWS`,
`WWHD_NO_HOST_INPUT`, `WWHD_NO_AUDIO`, `WWHD_NO_GAMEPAD`, `WWHD_RENDERER_RUNTIME=metal`,
`WWHD_SHADER_CACHE`, `WWHD_VK_SHADER_CACHE`, `WWHD_VK_PIPELINE_CACHE_DIR`, `WWHD_STATE_DIR`, `WWHD_PRESS`
(the A presses that leave the title screen), `WWHD_TEST_ORIGIN`, `WWHD_TEST_END` (writes `test_done`),
`WWHD_SAVEINFO_DUMP=si.bin` (the game's save block, `dSv_info_c`, 0x12A0 bytes, at the end; this is the
file every in-game script compares with the save), `WWHD_LINK_TRACE`, `WWHD_CAM_TRACE`, `WWHD_SE_TRACE`,
`WWHD_RNG_TRACE`, `WWHD_PROC_DIGEST`, `WWHD_PROC_DIGEST_SKIP`.

Read by the runner or by this project's scripts, not by the game:

| Variable | Meaning |
|---|---|
| `SHADER_CACHE` | shader cache file of a run (default: `shadercache.bin` next to the output folder); parallel runs need one each |
| `BOOT_TRIES`, `BOOT_LIMIT`, `ORIGIN`, `PRESS`, `DIGEST` | runner settings (retries of a boot that hangs, time limit, scenario origin) |
| `WW_RUNNER` | another runner script for `scripts/ingame_test.py` |
| `WW_SLOT` | Quest Log (0-based) that `scripts/ingame_test.py` compares |
| `SALVAGE_HOOK_AT`, `SALVAGE_PRE_PRESS` | timing of `scripts/ingame_salvage.py` |
| `WW_PORT_EXE`, `WW_HD_GAME`, `WW_HD_STAGES`, `WW_VERIFY_OUT`, `WW_RESEARCH` | locations for `verify/` (`verify/verifyenv.py`) |

The in-game verification itself is described in [verify/README.md](../verify/README.md).
