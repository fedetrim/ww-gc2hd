# Audit scripts

The scripts behind the four audits that compared the GameCube game (USA, `GZLE01`) with Wind Waker HD
(USA, v0). Each audit asked one question about the difference list in `docs/DIFFERENCES.md`; its report
is published under `docs/research/`. The scripts are the ones the reports name, with paths made
portable. Their logic is unchanged, and so are their limits: most were written to answer one question
once.

| Folder | Question | Report |
|---|---|---|
| `machine-code/` | Does any save flag or item gift differ between the two games at machine-code level, including in the GameCube actors that are not decompiled? | `docs/research/machine-code-audit.md` |
| `rewards/` | Does any place give a different reward in the two games (stage data, both randomizers' location tables, shops, item functions)? | `docs/research/reward-audit.md` |
| `undo/` | When the converter closes a chest again (`rewards` answers), can the player still get there and collect the reward exactly once? | `docs/research/undo-audit.md` |
| `leftovers/` | The points the machine-code audit left open: flags reached from differently named functions, message and event data, `ActorDat.bin`, direct access to the save block. | `docs/DIFFERENCES.md` section 6 (no separate report) |

## Requirements

- Python 3.8 or newer. No package is needed except `capstone` for the three disassembly helpers
  (`machine-code/gcdis.py`, `machine-code/hddis.py`, `leftovers/i8_getters.py`).
- Your own copies of both games and four clones under `research/`, set up as described in
  [docs/SETUP-RESEARCH.md](../docs/SETUP-RESEARCH.md). Nothing in this repository contains game data.
- Run the scripts with `python3 -I` (isolated mode): they read downloaded code and game data, and
  none of them needs the repository's own package on the path. Each script adds the folders it
  imports from by itself.

`audit/auditenv.py` holds every location. All defaults are under `research/` and each can be replaced
with an environment variable (`WW_RESEARCH`, `WW_GC_ISO`, `WW_HD_GAME`, `WW_TWW`, `WW_WWHD`, `WW_WWRANDO`,
`WW_TWWHD_RANDO`, `WW_AUDIT_OUT`). `python3 -I audit/auditenv.py` prints what it resolved and what is
missing.

Outputs go to `research/out/<audit>/` (git-ignored), or to `$WW_AUDIT_OUT/<audit>/`. Scripts that
produce a data file write it there themselves; scripts that print a listing print to stdout, and the
commands below redirect it to the file name the reports use.

## Running

`audit/run.sh [machine-code] [rewards] [undo] [leftovers]` runs the main scripts of the named audits in
order (all four when none is named, about 10 minutes) and writes every output. The steps, if you run
them by hand:

### machine-code (about 1 minute)

| Step | Command | Produces |
|---|---|---|
| 1 | `gc_extract.py` | `gc_calls.json` (30 MB): every call in `main.dol` and the 415 RELs with constant arguments |
| 2 | `hd_extract.py` | `hd_calls.json` (30 MB): the same for `cking.rpx` |
| 3 | `stubs.py --json research/out/machine-code/stubs.json > .../stubs.txt` | the GameCube sources with undecompiled functions |
| 4 | `validate.py > validate.txt` | check of the extractor against the decompiled GameCube sources |
| 5 | `compare.py > diff_all.txt`, `compare.py --global > global_diff.txt` | save-accessor keys present on one side only, per unit and overall |
| 6 | `funcdiff.py > funcdiff.txt` | flags reached from differently named functions (input of `leftovers/`) |
| 7 | `rewards.py --all > rewards_all.txt`, `gtitm.py > gtitm.txt` | item numbers given, per unit |
| 8 | `tables_all.py > tables_all.txt` | GameCube REL data objects not found byte for byte in HD |
| 9 | `stub_table.py > stub_table.md` | the per-actor table of the report |

Helpers for reading one difference: `where.py UNIT`, `flag.py HEX`, `tablecmp.py MODULE SYMBOL`,
`gcdis.py MODULE SYMBOL`, `hddis.py START END`. `ppc.py` is the constant tracker the extractors use.

### rewards (about 6 minutes; steps 1 and 9 take 2 minutes each)

| Step | Command | Produces |
|---|---|---|
| 1 | `stage_all.py` | `stage_all.json` (8 MB): every stage entity of both games |
| 2 | `stage_cmp.py > stage_cmp.txt` | every entity that differs |
| 3 | `stage_types.py > stage_types.txt` | the same counted per actor class and parameter kind |
| 4 | `totals.py > totals.txt` | stage-data sources per item, counts of the unique collectibles |
| 5 | `rando_tables.py > rando_tables.txt` | `rando_tables.json`: the two randomizers' location tables |
| 6 | `rando_match.py > rando_match.txt` | `rando_pairs.json`: locations paired through the stage entity |
| 7 | `rando_final.py > rando_final.txt` | the final location table, stage pairs and name pairs |
| 8 | `reach.py > reach.txt`, `gc_only_stages.py` | GameCube stages nothing leads to; exits into GameCube-only stages |
| 9 | `reach_hd.py > reach_hd.txt` | the same for HD, and the exit lists compared |
| 10 | `misc_tables.py > misc_tables.txt`, `item_table.py` | non-stage data tables; the random drop table |
| 11 | `item_tables.py` | item get and get-check functions per item id |
| 12 | `shops_dump.py`, `shops_callers.py`, `shops_mdata.py`, `shops_tables2.py`, `shops_tables3.py` | every shop item set, entry by entry (`shops_lib.py` is their loader) |

The `npc_*.py` scripts are helpers for the locations that code gives (Mrs. Marie, Lenzo, minigames):
`npc_seqdiff.py` (order of flag and item calls per function, source against source), `npc_msglists.py`
(numeric tables of a GameCube source against the HD binary), `npc_cuts.py`, `npc_events.py`,
`npc_evdump.py` (GameCube event scripts), `npc_gcsym.py`, `npc_mem.py` (dump data by symbol or
address). They take the actor or stage as argument; the audit ran them on the actors the randomizer
tables name.

### undo (2 minutes per script)

This audit is a code reading of the HD source (`research/wwhd/wwhd_src`); the report cites the lines.
The scripts only supply the stage data that reading needs:

| Command | Produces |
|---|---|
| `hd_all.py` | `hd_all.json` (4 MB): every HD stage entity |
| `show.py STAGE [ARC]` | the entities of one stage: which chests, switches and doors are on the way |
| `scls.py DEST...` | every exit that leads to the given stages |

### leftovers (about 1 minute; needs the outputs of machine-code and rewards)

The file prefixes are the item numbers of the author's working list of open points. That list is not
published; what each group covers is in the docstrings.

| Step | Command | Produces |
|---|---|---|
| 1 | `i1_sites.py > i1_sites.txt` | call sites of each `funcdiff.txt` pair |
| 2 | `i1_auto.py > i1_auto.txt` | pairs whose HD source uses the flag in functions of the same names (renamed or inlined in the binary) |
| 3 | `i1_ctx.py "" 3 > i1_ctx.txt` | source context of every pair, for reading (`i1_g.sh UNIT REGEX` greps both sources) |
| 4 | `i67_actordat.py` | the cells of `ActorDat.bin` that differ |
| 5 | `i67_cmp.py > i67_cmp.txt` | every message both games have: price, next message, control tags, numbers (`i67_msglib.py`, `i67_tags.py` are its readers) |
| 6 | `i67_evlist.py` | flags and items the GameCube event scripts carry |
| 7 | `i8_direct.py` | `i8_direct.json`: loads and stores into the save block that bypass the accessors |
| 8 | `i8_cmp.py all > i8_all.txt`, `i8_src.py > i8_src.txt` | those accesses compared per unit; the HD source lines that touch save structures directly |

Helpers: `i345_rpxstr.py STRING` (find a string in `cking.rpx`), `i345_stage.py STAGE [NAME]` (one
stage's entities in both games), `i8_getters.py` (HD functions that return the save pointer).

## Checking a run

The outputs are deterministic for the same inputs. With the commits listed in `docs/SETUP-RESEARCH.md`
the key figures are:

- `gc_extract.py`: 39319 functions, 133272 calls. `hd_extract.py`: 38828 functions, 173502 calls.
- `validate.txt` last line: 354 identical, 13 with differences; 738/744 source constants found.
- `diff_all.txt` last line: 416 one-sided keys.
- `funcdiff.txt` last line: 99.
- `rewards_all.txt` last line: 20 one-sided keys; call sites GC 135 HD 139; units GC 68 HD 67.
- `tables_all.txt` last line: objects compared 2331, found identical in HD 2155.
- `stage_cmp.txt`: totals `gc_inst 18904, hd_inst 18824, identical_inst 18785`.
- `rando_final.txt`: 243 stage-entity pairs, 75 name pairs (the report says 78 locations paired
  through code; which three it adds to the script's 75 is not recorded).
- `shops_dump.py` ends with `ALL SAME`; `item_tables.py` ends with `rows compared: 512 identical names: 508`.

A newer commit of a decompilation or a randomizer changes names and counts (more functions decompiled,
locations renamed), not what the games do. `totals.txt` prints two `Counter` lines whose order of equal
counts can change from run to run.

## Known blind spots

From the reports; none of them was closed by changing these scripts.

- **Machine code**: the comparison is per source unit and per function name, not per basic block, so
  a setter that moved inside one function while every reader stayed is not seen. Stage switches, item
  bits and chest numbers are almost always actor parameters (`?`), so only hard-coded ones are
  compared. Tables that contain pointers (1,352 objects, among them shop item sets and message
  tables) are not compared by `tables_all.py`; the shop sets are covered by `rewards/shops_*.py`. Items
  taken from a shop selection or an actor member are compared only by number of call sites. HD
  functions without an address marker (885, library code) are attributed to the marked function before
  them. `d_a_waterfall` has no HD source file.
- **Rewards**: stage data and tables are compared in full, but a location given by code is paired by
  name with a heuristic (`rando_final.py`), and the two randomizers do not list every reward of the
  game. Message text, prices and `ActorDat.bin` were left to `leftovers/`.
- **Undo**: a reading of the HD source. Message and event data files were not scanned for the flags
  the converter clears.
- **Leftovers**: direct accesses are found only where the constant tracker can follow the base
  address (`i8_direct.py`). The message comparison maps the control tags seen in common messages;
  English text only.
- **All**: USA builds only. HD addresses (`0x101F84DC` and the table addresses in `rewards/shops_*.py`,
  `rewards/item_tables.py`) and the GameCube configuration folder (`config/GZLE01`) are written in the
  scripts.

## Extending

- **Another accessor or item-giving function**: add it to `FREE` (free functions, with the number of
  key arguments) or let it match `dSv_*` in `machine-code/compare.py`; item functions go in `FUNCS` of
  `machine-code/rewards.py` with the register that holds the item number. Then run `compare.py` or
  `rewards.py` again; the two JSON extractions already hold every call.
- **A new question about calls**: `gc_calls.json` and `hd_calls.json` list every `bl` with the constant
  values of r3..r7, the calling function and its source file. `where.py` and `flag.py` are ten-line
  examples of a query.
- **A new question about instructions** (not calls): pass an `on_ins` hook to `ppc.scan_function`, as
  `machine-code/gtitm.py` and `leftovers/i8_direct.py` do.
- **Stage data**: `stage_all.json` holds every entity with its raw parameters; `stage_cmp.py` and
  `totals.py` show how to read chests, salvage points and item actors from them.
- **Another region or version**: `gc_extract.py` reads `config/GZLE01`; the HD scripts assume the USA
  v0 `cking.rpx`. Both would need their constants replaced, and the HD decompilation's address
  markers are for the USA binary only.
- New scripts should take their locations from `auditenv.py` and write under `auditenv.out_dir(...)`.

## Not published

Scripts of the working folders that were left out:

- `imm_diff.py` (machine-code): an experiment that compared the byte immediates of whole units. The
  report does not use it and no output of it was kept.
- `dump_stage.py` (undo): a first version of `show.py` that read a chest-and-actor dump at an absolute
  path and saw fewer chunk types.
- `i67_probe.py`, `i67_attr.py`, `i67_hdfind.py` (leftovers): one-off probes used to find where HD
  keeps its messages and how the attribute bytes are laid out; their findings are in `i67_msglib.py`
  and `i67_cmp.py`.

The generated outputs (JSON extractions, listings) are not published either; `audit/run.sh` recreates
them.
