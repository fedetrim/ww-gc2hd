# Chest / reward save flags (GC GZLE01, also valid for HD)

Researched 2026-11-14. Flags are positions inside the 0x768-byte save data, which
GC and HD share (same packed layout).

## Sources

- **AP** = Archipelago "The Wind Waker" world, `worlds/tww/Locations.py` and
  `TWWClient.py` (last change to Locations.py: commit cf0ae5e3, 2025-03-22).
  Saved raw copies: `research/archipelago-tww/Locations.py`,
  `research/archipelago-tww/TWWClient.py`, `research/archipelago-tww/Items.py`.
  URL: https://github.com/ArchipelagoMW/Archipelago/blob/main/worlds/tww/Locations.py
  It targets the randomizer build (GZLE99), but wwrando only rewrites the open
  flag of four chests it adds or moves (`wwrando/tweaks.py:401,418,438,1608,1710`:
  FF jail chest, Mother & Child chest, Jabun chest, Master Sword chest). None of
  the chests below is touched, so AP's numbers are the vanilla ones.
- **decomp** = `research/tww` (zeldaret/tww), **HD decomp** = `research/wwhd/wwhd_src`.
- **saves** = empirical check: diffing consecutive saves of the sample speedrun
  save sets in `samples/gc` (bit appears exactly in the save taken after the named
  segment), plus bit-set comparison against complete GC and HD saves.
- **wwrando** = `research/wwrando/logic/item_locations.txt` (stage/room path only,
  no flag numbers).

No public per-chest dump of stage data (TRES entries with flag numbers) was found.
Web searches turned up only the Winditor terminology page
(https://lordned.github.io/Winditor/tutorials/basics/terminology.html), which
describes the mechanism (32 chest open flags per stage save info) without a list.
The repos tww-gz, TWW-Coop, TWW-PopTracker and TWWHDRAutoTracker contain no
per-location chest tables. So for every chest the first source is AP and the
second is the empirical save diff, not a second document.

## Requested chests

"mem" = index of the `dSv_memBit_c` record (stage save-table id); bit = bit number
in `mTbox` (big-endian u32 at record offset 0; bit n = `1 << n`).

| # | Location | Stage / room (wwrando path) | mem | Kind | Bit | Sources | Confidence |
|---|---|---|---|---|---|---|---|
| 1 | Savage Labyrinth floor 50 (GC Piece of Heart) | `Cave10/Room20` Chest000 (not Cave11) | 0xD | tbox | 12 | AP Locations.py:155-156; saves: never set in the speedrun sets, but set (with 11) in complete GC save `dasaves/.../the-legend-of-zelda-the-wind-waker.14259.gci`, `pack1/Wind Waker/9th save.gci`, and in HD complete saves | medium-high (one document; saves only show the bit exists and is set after 11) |
| 2 | Savage Labyrinth floor 30 (Triforce Chart 6) | `Cave09/Room20` Chest000 | 0xD | tbox | 11 | AP :152-153; saves: cryze 100% 26-BeforeSavageLabyrinth -> 27-AfterSavage sets only D:11; glitchless 07 -> 08_AfterSavage sets D:11 | high |
| 3 | Horseshoe Island NW lookout platform (Skull Necklace) | `sea/Room43` Chest001 | **0x1** | tbox | 26 | AP :950-951; decomp for the record index (see below); saves: complete saves have bit 26 set, no diff isolates it | medium (NW=26 / SE=27 assignment rests on AP alone) |
| 4 | Star Belt Archipelago lookout platform (Red Rupee) | `sea/Room21` Chest000 | **0x1** | tbox | 11 | AP :974-975; saves: bit exists in complete saves only | medium (AP alone for the identity) |
| 5 | Pawprint Isle Wizzrobe cave (Silver Rupee) | `Cave07` (stage) Chest000 | 0xD | tbox | 2 | AP :810-811; saves: bit set only in complete saves | medium (AP alone for the identity) |
| 6 | Private Oasis cabana labyrinth upper floor (Triforce Chart 2) | `TF_04` (stage) Chest000 | 0xC | tbox | 17 | AP :726-727; saves: cryze 22 -> 23-AfterCabana sets C:17 | high |
| 7 | Ghost Ship (Triforce Chart 4) | `PShip` (stage) Chest000/Chest001; only the room-2 chest is reachable (`wwrando/tweaks.py:1535-1550`) | **0xA** | tbox | 23 | AP :715-716; saves: cryze 21-BeforeGhostShip -> 22 sets A:23; glitchless 10_AfterWT_AfterGhostShip sets A:23 | high |
| 8 | Stone Watcher Island cave (Triforce Chart 7) | `TF_01` Chest000 | 0xC | tbox | 10 | AP :769-770; saves: cryze 24 -> 25-AfterStonewatcher sets C:10 (and C:6 = Star Island cave) | high |
| 9 | Overlook Island cave (Triforce Chart 8) | `TF_02` Chest000 | 0xC | tbox | 11 | AP :788-789; saves: set in all three routes; the glitchless route (collects exactly the 8 Triforce charts) ends with C = {0,1,3,4,10,11,16,17} | high |
| 10a | Islet of Steel interior (Triforce Chart 1) | `ShipD` Chest000 | 0xC | tbox | 4 | AP :780-781; saves: glitchless 04_AfterJabun sets C:4 together with the gunboat salvage | high |
| 10b | Bird's Peak Rock cave (Triforce Chart 3) | `TF_03` Chest000 | 0xC | tbox | 16 | AP :793-794; saves: cryze 14 -> 15 and glitchless 09 set C:16 | high |

Corrections to the working assumptions:

- The Ghost Ship is in record **0xA** (ship interiors), not 0xD.
- Lookout-platform chests on the sea are not in record 0 but in record **1**
  (`STAGE_SEA2`). The tbox actor does this itself: behaviour types 7 and 8
  (`FUNC_TYPE_EXTRA_SAVE_INFO`, `..._SPAWN`) read and write
  `dComIfGs_isTbox/onStageTbox(dSv_save_c::STAGE_SEA2, n)` instead of the current
  stage's record (`tww/src/d/actor/d_a_tbox.cpp:30-31, 314-320, 854-858`; HD:
  `wwhd_src/d/actor/d_a_tbox.cpp:739-743`).
- Floor 50 of the Savage Labyrinth is stage `Cave10`, room 20.

Chest parameter decode (`tww/include/d/actor/d_a_tbox.h:35-37`,
`d_a_tbox.cpp:397`): behaviour type = `params & 0x7F`, open flag =
`(params >> 7) & 0x1F`, appear switch = `(params >> 12) & 0xFF`, item id =
high byte of the z rotation. HD uses the same decode
(`wwhd_src/d/actor/d_a_tbox.cpp:282, 360, 474`).

### GC vs HD flag numbers

HD saves in `samples/hd` use the same bits: complete HD saves have
record 0xA = {0,1,2,3,4,6,7,23}, record 0xD = {0,1,2,4,5,6,9,11,12,15,22},
record 1 a subset of 0..27 without 9 and 22, which are exactly the sets AP lists
for GC (plus D:4, which AP does not list). A complete GC save has record 1 =
0..27 without 9 and 22 and record 0xD = {0,1,2,4,5,6,9,11,12,15,22}. So the
flag numbers carry over unchanged; only the chest contents differ.

## Non-chest rewards

Event flags are `0xBBMM`: byte `BB` of `dSv_event_c::mFlags` (0x100 bytes), mask `MM`.

| Reward | Kind | Flag | Source (file:line) | Confidence |
|---|---|---|---|---|
| Mrs. Marie, 40 Joy Pendants (GC Hero's Charm, item 0x43) | event bit | 0x1C04 (byte 0x1C, bit 2) | `tww/src/d/actor/d_a_npc_ho.cpp:349-353` sets it when giving `dItemNo_HEROS_CHARM_e`; checked at :262, :329, :413. AP Locations.py:187-188 (0x803C5248 bit 2). saves: cryze 19 -> 20-AfterWindfallCleanup sets 1C bits 1,2,3 | high |
| Mrs. Marie, 20 more pendants (Cabana Deed) | event bit | 0x1C08 (byte 0x1C, bit 3) | `d_a_npc_ho.cpp:314-318` (also sets tmp bit 0x0104); checked at :264, :409. AP :184-185 (0x803C5248 bit 3) | high |
| Mrs. Marie, pendant counter | event reg | 0xC0FF (byte 0xC0, whole byte) = pendants handed in; the 40 reward needs >= 0x28 | `d_a_npc_ho.cpp:329` | high |
| Mrs. Marie, first Joy Pendant | event byte | AP checks 0x803C52EC bit 0 = event byte 0xC0, bit 0, which is the low bit of the pendant counter register above | AP :181-182 only | low (not a dedicated flag; true only while the count is odd) |
| Dampa pig game, first win | event bit | 0x2A04 | `tww/src/d/actor/d_a_npc_people.cpp:7244-7246` (set when `isPigOk()` on return); read at :6659 only to shorten the timer (0x708 instead of 0xE10). HD identical: `wwhd_src/d/actor/d_a_npc_people_msg.cpp:683-685`, `d_a_npc_people_talk.cpp:539` | high for what the bit means |
| Dampa pig game, other state | event bits | 0x2440 first talk (:7274-7276); 0x2640 rules explained / first game accepted (:6709, :7296); 0x2680 game in progress today (:6708, :6725; cleared at :7267); 0x2620 Skull Necklace (big pig) variant accepted once (:6726, :6853) | same file | high |
| Needle Rock Isle golden gunboat (Triforce Chart 5) | ocean salvage bit | `dSv_ocean_c` u16 index 29 (sea room 29), bit 2 | AP :748-749 (0x803C5202, bit 2; 0x803C5202 - 0x803C51C8 = 0x3A = 2*29). decomp: `tww/src/d/d_save.cpp:1163-1175`, set by `daSalvage_c::end_salvage`, `tww/src/d/actor/d_a_salvage.cpp:504-518`. saves: all three routes set ocean[29] bit 2 in the segment that collects the chart | high |

Notes on these:

- The gunboat flag records that the **light-ring salvage was pulled up**, not that
  the boat was sunk. Sinking the boat sets a stage switch (the oship's switch
  number, `d_a_salvage.cpp:471-498`), whose number is in stage data I could not
  read. For "does the player have the reward" the ocean bit is the right one.
  The same 16-bit word holds the other per-sector salvage bits; bit 0 is used for
  Big Octo rewards in the Big Octo sectors (AP `BOCTO` entries).
- The pig game has no "reward already given" flag for the Skull Necklace variant
  that pays the Purple Rupee (wwrando: `rels/d_a_npc_people.rel@5BDF`). 0x2A04 is
  only set by the plain game. None of the sample 100% saves (GC or HD) has 0x2A04
  set; HD complete saves have byte 0x2A = 0xFB. The game is not an Archipelago
  location, so there is no AP entry to compare.
- HD decomp of Mrs. Marie uses the same two event bits
  (`wwhd_src/d/actor/d_a_npc_ho.cpp:332-334, 345, 367-369`). At :367 the 40-pendant
  item id is 0xF8, which in the GC item table is `dItemNo_COLLECT_MAP_07_e`
  (`tww/include/d/d_item_data.h:255`); the decomp's comment there calls it
  HEROS_CHARM, which looks wrong. That fits "HD moved the Hero's Charm elsewhere".

## How the Archipelago table encodes a check

`LOCATION_TABLE` maps a location name to
`TWWLocationData(code, flags, region, stage_id, type, bit, address=None)`.
`code` and `flags` are Archipelago bookkeeping. Decode by `type`
(`TWWClient.py:447-540`):

| type | count | Meaning | Where in the save |
|---|---|---|---|
| `CHEST` | 170 | chest open flag | record `stage_id`, `mTbox` (offset 0x00, u32), bit `bit` |
| `SWTCH` | 3 | stage switch | record `stage_id`, switches read as one 10-byte big-endian integer starting at record offset 0x04; bit `bit` of that integer. This is NOT the game's switch number: AP bit n is the byte at record offset `0x04 + 9 - n//8`, mask `1 << (n%8)`. With r = 9 - n//8, the game's switch number is `(r//4)*32 + (3 - r%4)*8 + n%8` (AP 52 -> switch 4, AP 53 -> 5, AP 64 -> 56) |
| `PCKUP` | 22 | item pickup flag | record `stage_id`, `mItem` (offset 0x14, u32), bit `bit` |
| `EVENT` | 55 | event bit | `address - 0x803C522C` = event byte index, mask `1 << bit`; i.e. event flag `(index << 8) | (1 << bit)` |
| `BOCTO` | 7 | ocean salvage bit (Big Octos, gunboats) | `(address - 0x803C51C8) / 2` = sea room number, u16 big-endian, bit `bit` |
| `CHART` | 49 | sunken treasure | 8-byte big-endian integer at 0x803C4CFC (save offset 0xF4); the bit number is not in `LOCATION_TABLE` but in `ISLAND_NAME_TO_SALVAGE_BIT` at the end of Locations.py (island -> bit), remapped at run time for shuffled charts (TWWClient.py:268-284, 525-528). I did not match offset 0xF4 to a named field of the map block |
| `SPECL` | 5 | special-cased | `check_special_location` (TWWClient.py:391-445): letters, Lenzo, Tingle statues etc. |

Address bases for GZLE01 RAM (TWWClient.py:40-46): record `i` starts at
`0x803C4F88 + 0x24*i` (chests +0, switches +4, pickups +0x14); event bytes start
at 0x803C522C; ocean words start at 0x803C51C8 (= event base - 0x64). The client
only polls records 0..0xD and also reads the live copy of the current stage's
record at 0x803C5380, because the saved record is only updated when leaving the
stage (on a real save file the record is already merged).

Coverage: 311 locations, i.e. every location wwrando randomizes. It does not
cover chests wwrando leaves alone (e.g. rupee-only extras it never listed) or
the pig game. Entries commented out in the file have no flag data.
Entries for the chests wwrando adds or re-flags (FF jail chest set to flag
0x11, Mother & Child Isles chest 0x1C, Jabun's cave chest 6, Master Sword
chamber chest 0; `wwrando/tweaks.py:401-438, 1608, 1710`) describe the
randomizer build, not the vanilla game.

An HD equivalent of this table was not found. The HD randomizer
(`research/twwhd-rando/logic/data/location_data.yaml`) identifies chests by
file path and byte offset, not by flag, and `research/TWWHDRAutoTracker`
only maps inventory addresses.
