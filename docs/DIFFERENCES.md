# Wind Waker (GameCube, NTSC-U) vs. Wind Waker HD (Wii U): save differences

Everything `ww-gc2hd` does is listed here with its evidence. Evidence tags:

- **[CODE]** read in the decompilations: GameCube `zeldaret/tww` (`research/tww` in a working copy; clone it there), HD `ZeldaWWHDDecomp/wwhd`
  (`research/wwhd`, verified decompilation of the USA `cking.rpx`).
- **[DATA]** observed in real save files (`samples/`, provenance in `samples/SOURCES.md`): 260 GameCube `.gci`
  (257 are in the repository; the other three were modified by an exploit tool and are left out)
  (34 USA, 222 Japan, 4 Europe; 477 used files) and 45 HD `cking.sav` (56 used Quest Logs, 53 distinct).
- **[RANDO]** vanilla item placements from the randomizers' data: GameCube `wwrando/logic/item_locations.txt`,
  HD `TWWHD-Randomizer/logic/data/location_data.yaml` and `logic/GameItem.hpp`.
- **[DISC]** stage data of both games, read from the author's copies with `scripts/gc_stage_dump.py` and
  `scripts/hd_stage_dump.py` (every chest with its save record, open flag and content; every actor with its
  parameters) and compared with `scripts/stage_diff.py` (result: `docs/research/stage-diff.txt`; its first section shows
  that every stage keeps its save record: 131 stages on both discs, none differs).
- **[AP]** save flag numbers from the Archipelago Wind Waker world (`research/archipelago-tww/Locations.py`).

Longer research notes: `docs/research/hd-save-semantics.md` (code review of every HD/GameCube difference that
touches saved state) and `docs/research/chest-flags.md` (chest and reward flags).

See "Verification" at the end for what was tested in the game itself.

## 1. Container formats

### GameCube card file [CODE][DATA]
- `.gci`: 0x40 directory entry + 12 blocks of 0x2000 (`.gcs` adds a 0x110 header, `.sav` a 0x80 header).
  Block 0 banner/icon/comment; blocks 1 and 2 two copies of `card_savedata`; blocks 3..11 Picto Box pictures.
- `card_savedata`: u32 save_count, u32 data_version, 3 x (0x768 save + u64 checksum), u32 block checksum at 0x1FFC.
- File checksum: (sum of bytes) << 32 | (sum of `0xFFFFFFFF - byte`), each mod 2^32
  (`mDoMemCdRWm_CalcCheckSumGameData`). Valid in 3 x 260 files of the collection, both copies.
- The loader uses copy 1 of a file, and copy 2 when copy 1 fails its checksum (`mDoMemCdRWm_Restore`).

### HD `cking.sav` [CODE][DATA]
8966 bytes, big-endian:

| Offset | Size | Content |
|---|---|---|
| 0x0000 | 3 x 0xA94 | Quest Log: 0x768 save block, zeros to 0xA8C, u32 byte sum, u32 complement sum (over 0xA8C bytes) |
| 0x1FBC | 3 x 16 | options (`hdSaveSlotFlags_c`) |
| 0x1FEC | 3 x 4 | controller settings (`hdSavePair_c`) |
| 0x1FF8 | 3 x 20 | HD inventory record (`hdSaveInventory_c`) |
| 0x2034 | 3 x 18 | player name, UTF-16BE, 8 characters + terminator |
| 0x206A | 3 x 220 | play log (`hdSavePlayLog_c`) |
| 0x22FE | 4 | format word 4 |
| 0x2302 | 4 | CRC-32 of the five HD sections; each name contributes only (characters + 1) bytes (game quirk) |

All 45 real files parse with valid checksums and CRC and re-serialize byte-identically; bytes 0x768..0xA8C are
zero in every Quest Log. HD rejects the file unless all three Quest Log checksums and the CRC are valid
(`d_menu_save_storage.cpp:37-55,143-156`). `cking_pic*.sav`, `cking_playlog.sav`, `cking_miiverse.sav` are
separate files that HD creates when missing (stated by the ZeldaWWHDRecomp project; not re-checked here).

## 2. The 0x768-byte save block

Same blocks, sizes and order in both games (`dSv_info_c::memory_to_card`: GameCube `d_save.cpp:1703`, HD
`d_save_5.cpp` 025BA9FC). Field names below are those of `wwsave/layout.py`.

### 2.1 Fields with different conventions

| Field | GameCube | HD | Evidence | Conversion |
|---|---|---|---|---|
| `info.save_count` | always 0 (477/477) | +1 per save; file select shows `save_count == 0` as an empty Quest Log (`hd_picture_accessor.cpp:30`, `hd_scene_save_data.cpp:182,591`) | CODE, DATA, in-game | used file: 1, including a New Game+ file not started yet (with 0 the game starts a plain new game and the New Game+ state is lost; with 1 it shows the Triforce mark and starts the second quest) |
| `return_place.stage` | old characters may follow the terminator | zero padded (`d_save.cpp` 025B5060) | CODE, DATA | zero padded |
| `info.player_name`, `_name_25`, `_name_36` | player name, "Link", "Link" | empty on a first playthrough, "Link" after New Game+; the name shown everywhere is the UTF-16 record (`d_mesg_state.cpp:84-96`) | CODE, DATA | cleared (or "Link" when `clear_count > 0`); name written to the HD record |
| `status_a.select_item[3]` | 0xFF | GamePad button: 2 once the Wind Waker is owned (`d_item.cpp:209`) | CODE, DATA (30 of 32 owners; the other two hold a sailing item) | 2 if owned |
| `status_a.select_item[4]` | 0xFF | sail button: 1 once a sail is owned (`d_item_2.cpp:304`) | CODE, DATA (32/32) | 1 if owned |
| `status_a.select_item[0..2]` | X/Y/Z, very often the Sail or Wind Waker | never the Sail or Wind Waker (0 of 56 Quest Logs) | DATA | Sail / Wind Waker removed from X/Y/Z |
| `map.triforce_bits` | bit n-1: Triforce Chart n deciphered | new file 0xEA, and bits 1,3,5,6,7 are forced on every load (`d_save_3.cpp:36`, `d_menu_save_card.cpp:141-148`) | CODE, DATA | OR 0xEA |
| `map.fmap_bits[sector]` bit 1 | "arrived" mark for the Tingle Tuner, set when entering a sector (`d_map.cpp:1948`) | only in the three sectors charted from the start; never set in play (0 of 56) and never read | CODE, DATA | cleared except sectors 0, 10, 43 |
| sea stage (`memory00`) switches 9 and 1 | Link leaves the forest rescue scene at Outset spawn point 203 (the scene's `NEXT` step: stage `sea`, room 44, start code 203, same in both games). On the GameCube that spawn point has no start event (`FFFF002C`); Link walks into the event trigger next to it (`TagEv`, parameters 0x01FF0903: type 3, switch 9), which starts Aryll's kidnapping (`STOLENSISTER`), sets event 0x0E20 and switch 9. Set in every save past that point (339/339); switch 1 never | the same spawn point carries start event 1 (`01FF002C`), the only spawn point that differs between the two discs. The game starts `STOLENSISTER` from the spawn and sets the switch the stage's event table gives for that (`EVNT` entry 1, switch 1; `dEvent_exception_c::setStartDemo`, same code and table in both games); 0x0E20 is set and the trigger's switch 9 is not. Console files past that point: 45 of 47 have switch 1 and not 9 (the other two have 9 like a GameCube file). Reproduced in the game: a console file from before the scene, started at spawn point 203, gets switch 1 and 0x0E20 within two seconds and never switch 9; the same file walked into the trigger gets switch 9 | DISC, CODE, DATA, in-game | switch 1 set when event 0x0E20 is set, as HD does; switch 9 kept (only that trigger reads it, and it waits once 0x0E20 is set) |
| `config.sound_mode` | 0/1 | forced to 2 on load (`d_save_5.cpp:249`) | CODE, DATA | 2 |
| `item_record.picture_num` | number of pictures | unused; the count lives in the HD picture store (0 in 56/56) | CODE, DATA | 0 |
| `status_c0..3` (recollection records) | all zero until recorded | unrecorded = values of an empty inventory (life 12/12, 0xFF items) | CODE, DATA | zero record -> HD empty record; recorded ones get the HD button layout |
| `status_b.date_ipl` | GameCube clock | Wii U clock, stamped on every save | CODE | kept; HD overwrites it on the next save |
| `config.attention_type` | Z-targeting hold/switch | ignored; HD reads options byte 0 (`d_attention_3.cpp:464`) | CODE | copied to the HD options record |

Flags that HD never sets, or sets under another condition. They are written as an HD file has them:

| Flag | GameCube | HD | Conversion |
|---|---|---|---|
| events 0x1708, 0x1A20, 0x1A08, 0x1A10, 0x2E08 | set through the Tingle Tuner (Knuckle found, Tuner message sent, Tuner states, trigger area) | no setter; 0 of 56 real Quest Logs. 0x1708 and 0x1A20 still select lines of Tingle; Knuckle appears from the five Tingle Statue chests | cleared |
| event 0x1940 | set in every whirlpool (`d_a_ship.cpp:2825`) | set only with the bomb bag (`d_a_ship.cpp:3481`); selects a line of the King of Red Lions | cleared when no bombs are owned |
| event 0x2B04 | the two Windfall gossips have told every hint; the last check is the Sail | the last check is the Swift Sail (`d_a_npc_people_event.cpp:233-253`); set in 9 real Quest Logs, all with the Swift Sail | cleared unless the converted file has the Swift Sail |
| `collect.collect[3]` bit 1 | set by the collection menu (`d_menu_collect.cpp:3744`) | never set | cleared, also in the four boss-rematch records, which copy the field (set in 0 records of the real HD saves) [DATA] |
| event 0x3940 | set the first time the Deku Tree is asked about the Koroks | set at the end of his explanation; then the sea chart shows the withered-tree icons | copied: who heard the explanation sees the icons |

Left as they are: padding bytes that HD leaves uninitialised (`status_b._pad_16`, `return_place._unk_a/b`,
`get_bag_item._unk_6`).

Same field, different limit: wallet sizes 0/1/2 hold 200/1000/5000 on GameCube and 500/1000/5000 in HD
(`d_meter_02.cpp:282`); a GameCube amount always fits.

### 2.2 What HD rewrites by itself when loading [CODE]
`SaveMgr::startup` 02720E34, `saveMgrRefreshEquipment` 02721730, `SaveMgr::refreshGame` 02721880:
- every inventory slot (except bottles) whose ownership bit 0 is set gets its item id back; slot 1 bit 1 ->
  Swift Sail (0x77); slot 8 bit 1 -> Deluxe Picto Box; slot 12 bits 2/1 -> Light / Fire & Ice arrows;
- equipped sword, shield and bracelet are re-derived from the collection bits;
- `select_item[3] = 2` when the Wind Waker is owned; Triforce map bits ORed with 0xEA; sound mode 2.

`wwsave/hdcheck.py` re-implements this. It leaves all real HD Quest Logs unchanged (except two saved while a
sailing item sat on the GamePad button). The converter applies it to its output, so the written file is what
the game holds after loading. On GameCube saves it changes two things: the bow removed during the final
battle comes back (8 files), and an equipped half-power Master Sword becomes the full-power one when the
full-power bit is already owned (23 files).

## 3. Gameplay differences

### 3.1 Charts: five Triforce Chart ids are other charts in HD [CODE][DATA][RANDO]
Charts are "collect maps" numbered from 1: bit n-1 of `map.get_map` / `open_map` / `complete_map`; item id 0xFF - n.

| Collect map | GameCube | HD |
|---|---|---|
| 1 | Triforce Chart 1 (Islet of Steel chest) | Triforce Chart 1 (same) |
| 2 | Triforce Chart 2 (Private Oasis cabana labyrinth chest) | Treasure Chart 42 (Windfall pig minigame; given when not owned, `d_a_npc_people_talk.cpp:476`) |
| 3 | Triforce Chart 3 (Bird's Peak Rock cave chest) | "Triforce Chart 2" (same place) |
| 4 | Triforce Chart 4 (Ghost Ship chest) | Treasure Chart 43 |
| 5 | Triforce Chart 5 (Needle Rock Isle golden gunboat) | "Triforce Chart 3" (same place) |
| 6 | Triforce Chart 6 (Savage Labyrinth floor 30 chest) | Treasure Chart 44 |
| 7 | Triforce Chart 7 (Stone Watcher Island cave chest) | Treasure Chart 45 |
| 8 | Triforce Chart 8 (Overlook Island cave chest) | Treasure Chart 46 |

In HD the five chests that held Triforce Charts 2, 4, 6, 7, 8 hold Triforce Shards 2, 4, 6, 7, 8, and the sunken
treasures those charts led to are something else (3.2).

Evidence: HD item order (`GameItem.hpp`); real HD saves owning collect maps 4/6/7 with no shard; in the 53
distinct HD Quest Logs each of these holds with no exception: shard 2/4/6/7/8 owned <=> chest flag (table in
3.3) set; collect map 4/6/8 owned <=> the HD chart's chest open; collect map 7 owned <=> event 0x1C04.

Conversion:
- GameCube Triforce Chart k (k = 2, 4, 6, 7, 8): its get/open/complete bits are cleared (otherwise the save
  would own HD's Treasure Chart 42-46, possibly marked as already salvaged, and Chart 42 could never be won).
- If chart k is owned and shard k is not, the save is in a state HD does not have. **Option
  `--triforce-chart-k`** (no default, see 3.2): `steps` gives shard k, as HD's chest would have; `rewards`
  drops the chart and closes the chest again, so it gives the shard when opened in HD.
- A GameCube Ghost Ship chest opened in one of the two copies HD lacks (flags 21, 22) is written as HD's
  one chest: flag 23 set, flags 21 and 22 cleared.

### 3.2 Changed rewards [DISC], flags [DISC][AP][DATA][CODE]

The stage data of the two games differs in exactly nine chests (same position, same save record, same open
flag, other content) and in the five sunken treasures of the reused chart ids:

| Place | GameCube | HD | Saved as | Conversion |
|---|---|---|---|---|
| Private Oasis cabana labyrinth chest | Triforce Chart 2 | Triforce Shard 2 | record 0xC tbox 17 | 3.1 |
| Ghost Ship chest | Triforce Chart 4 | Triforce Shard 4 | record 0xA tbox 23 | 3.1 |
| Savage Labyrinth floor 30 chest | Triforce Chart 6 | Triforce Shard 6 | record 0xD tbox 11 | 3.1 |
| Stone Watcher Island cave chest | Triforce Chart 7 | Triforce Shard 7 | record 0xC tbox 10 | 3.1 |
| Overlook Island cave chest | Triforce Chart 8 | Triforce Shard 8 | record 0xC tbox 11 | 3.1 |
| Horseshoe Island NW lookout chest | Skull Necklace | Treasure Chart 43 (collect map 4) | record 1 tbox 26 | `--horseshoe-chest` |
| Star Belt Archipelago lookout chest | Red Rupee | Treasure Chart 44 (collect map 6) | record 1 tbox 11 | `--star-belt-chest` |
| Pawprint Isle Wizzrobe cave chest | Silver Rupee | Treasure Chart 46 (collect map 8) | record 0xD tbox 2 | `--pawprint-chest` |
| Savage Labyrinth floor 50 chest | Piece of Heart | Hero's Charm | record 0xD tbox 12 | `--floor50` |
| Sunken treasure of collect map 2 (Gale Isle) | Triforce Shard 2 | Orange Rupee | chart complete bit | 3.1 |
| Sunken treasure of collect map 4 (Outset Island) | Triforce Shard 4 | Orange Rupee | chart complete bit | 3.1 |
| Sunken treasure of collect map 6 (Southern Triangle Island) | Triforce Shard 6 | Orange Rupee | chart complete bit | 3.1 |
| Sunken treasure of collect map 7 (Seven-Star Isles) | Triforce Shard 7 | Silver Rupee | chart complete bit | 3.1 |
| Sunken treasure of collect map 8 (Two-Eye Reef) | Triforce Shard 8 | Piece of Heart | chart complete bit | 3.1 |

On the GameCube the Ghost Ship stage has three copies of its chest (flags 21, 22, 23); HD has one (flag 23).

Changed in code, not in stage data:

| Place | GameCube | HD | Saved as | Conversion |
|---|---|---|---|---|
| Mrs. Marie, 40 Joy Pendants | Hero's Charm | Treasure Chart 45 (`d_a_npc_ho.cpp:367`) | event 0x1C04 | `--marie` |
| Lenzo, third picture accepted | Joy Pendant | Deluxe Picto Box (`d_a_npc_photo_exec.cpp:418`) | register 0xC407 = 6 | `--lenzo` |
| Lenzo, Forest Firefly shown | Deluxe Picto Box (`d_a_npc_photo.cpp:1750`) | Joy Pendant | | |
| Tingle's first gift (Windfall jail) | Tingle Tuner | Tingle Bottle (same item id 0x21, slot 7) | | copied (3.5) |
| Windfall auction | 4 prizes | plus the Swift Sail | | `--swift-sail` |
| Windfall pig minigame | rupees | Treasure Chart 42 while not owned | | none needed |

#### Conversion: two modes per place, no default

Each row above where the save already collected the GameCube reward is a case. The tool stops at each case
the save is in, explains it and asks; an option answers it in advance (`--all` answers every case). The two
answers are the two consistent translations:

- `steps`: the place stays done. The GameCube reward is replaced by what HD gives there.
- `rewards`: what the player holds stays. A place whose HD reward is not held is undone (chest closed again),
  and the place that gives the held reward in HD is marked done.

Consumable rewards are translated too. By `steps` the GameCube one is taken back as far as the save still
holds it (a spent rupee or a used spoil cannot be taken): Skull Necklace, Red Rupee (20), Silver Rupee (200),
Lenzo's Joy Pendant. By `rewards` it is kept. One of them has a place in HD, the Silver Rupee (sunken treasure
of Treasure Chart 45): by `rewards` it is kept like the others, and that treasure is marked as salvaged when Chart 45 is in hand
(`--marie steps`). When it is not, the treasure stays to be found, a second Silver Rupee: a chart cannot be
marked as salvaged before it is owned (see below). The report says so.

| Case (option) | Applies when | `steps` | `rewards` |
|---|---|---|---|
| `--triforce-chart-2/4/6/7/8` | chart owned, shard not | shard given | chart dropped, chest closed again; for chart 4 the Ghost Ship register 0x8803 is also set from 3 to 0 (at 3 the ship no longer exists, `d_a_ghostship.cpp:275`) |
| `--horseshoe-chest`, `--star-belt-chest` | lookout chest open | Treasure Chart 43 / 44 given; Skull Necklace / 20 rupees taken back | chest closed again |
| `--floor50` | floor-50 chest open (Piece of Heart held) | Piece of Heart removed (maximum life -1, a full heart becomes three pieces); chest stays open, Hero's Charm given | Piece of Heart kept; Pawprint chest marked opened, Treasure Chart 46 owned, opened and salvaged; floor-50 chest closed again unless the Hero's Charm is held by `--marie rewards` |
| `--pawprint-chest` | Pawprint chest open, and not already settled by `--floor50 rewards` | Treasure Chart 46 given; 200 rupees taken back | chest closed again; Silver Rupee kept, and Chart 45 marked salvaged if `--marie steps` |
| `--marie` | event 0x1C04 set (Hero's Charm held) | Treasure Chart 45 given; Hero's Charm removed unless the floor-50 chest is open by `--floor50 steps` | Hero's Charm kept, floor-50 chest marked opened; 0x1C04 cleared: Mrs. Marie gives Treasure Chart 45 the next time she receives a Joy Pendant (`d_a_npc_ho.cpp:345`, total given stays >= 40) |
| `--lenzo` | register 0xC407 >= 6, Picto Box not Deluxe | Deluxe Picto Box given; one Joy Pendant taken back | register set to 5: the third task is pending again |

In HD the Hero's Charm and the floor-50 chest go together, so the two options combine as:
floor-50 chest open and charm owned <=> `--floor50 steps` or `--marie rewards`.

| GameCube state | `--floor50` | `--marie` | Piece of Heart | Hero's Charm | floor-50 chest | Mrs. Marie | Chart 45 | Chart 46 |
|---|---|---|---|---|---|---|---|---|
| floor 50 only | steps | | removed | given | open | | | from the Pawprint chest |
| floor 50 only | rewards | | kept | no | closed | | | salvaged |
| Mrs. Marie only | | steps | | removed | closed | done | given | |
| Mrs. Marie only | | rewards | | kept | marked open | pending | no | |
| both | steps | steps | removed | kept | open | done | given | from the Pawprint chest |
| both | rewards | rewards | kept | kept | open | pending | no | salvaged |
| both | steps | rewards | removed | kept | open | pending | no | from the Pawprint chest |
| both | rewards | steps | kept | removed | closed | done | given | salvaged |

Tingle's deciphering fee: on the GameCube Triforce Charts 2, 4, 6, 7, 8 are deciphered for 398 rupees each
(decipher bit in `map.triforce_bits`); HD has no such charts and never charges it. For each of those bits
set in the GameCube file, 398 rupees are given back, up to the wallet limit (in both modes, no question).

A case can be answered per Quest Log: `--floor50 1=steps,3=rewards`; in a terminal each Quest Log is asked
separately.

Why the Pawprint chest is marked opened with `--floor50 rewards`: receiving a chart clears its opened and
salvaged bits (`item_func_collectmap_common`), so Chart 46 cannot be left to be found later as already
salvaged. Maximum life is capped at 20 hearts (`d_meter_01.cpp:1203`).

A closed-again chest that appears only after a fight (appear switch) is there at once if the stage record
still holds that switch; the Pawprint cave chest appears when the room's enemies are defeated again.

Other stage-data differences (no effect on saved flags): the 13 Tingle Tuner chests (`agbTBOX`) are gone; the
Ghost Ship rooms 0 and 1 and the Bird's Peak Rock cave rooms lost enemies and their switch helpers; a few
actors moved slightly. Every other chest and switch-carrying actor is identical in both games. Of 1077 player spawn points, one differs (Outset 203, section 2.1); the Ghost Ship's two removed rooms lost theirs, and a save made in the Ghost Ship returns to the sea in both games.

### 3.3 Chest flags used above [DISC][AP][DATA]
"record" = index of the 0x24-byte stage record (`memoryNN`), bit in its `tbox` word. Every row of this table
and of 3.2 was read from the GameCube disc's stage data (record, flag and GameCube content all match), and
each (record, flag) pair belongs to that one chest only (plus unused test stages).

| Chest | Record | Bit |
|---|---|---|
| Private Oasis cabana labyrinth (Chart 2 / Shard 2) | 0xC | 17 |
| Ghost Ship (Chart 4 / Shard 4) | 0xA | 23 |
| Savage Labyrinth floor 30 (Chart 6 / Shard 6) | 0xD | 11 |
| Stone Watcher Island cave (Chart 7 / Shard 7) | 0xC | 10 |
| Overlook Island cave (Chart 8 / Shard 8) | 0xC | 11 |
| Islet of Steel (Chart 1) / Bird's Peak Rock (Chart 3) | 0xC | 4 / 16 |
| Needle Rock golden gunboat (Chart 5) | ocean word 29 | 2 |

Lookout-platform chests are stored in record 1, not in the sea record (`d_a_tbox.cpp:314-320`).

### 3.4 Lenzo's Picto Box quest [CODE]
Register 0xC407: 0 none, 1/3/5 task given, 2/4 done, 6 third task done. GameCube state "register >= 6, Picto
Box not Deluxe" has no way to the Deluxe Picto Box in HD. **Option `--lenzo`** (3.2): `steps` gives it
(slot 8 = 0x26, ownership bit 1); `rewards` sets the register back to 5, where Lenzo accepts the third picture
and gives the Deluxe Picto Box (`d_a_npc_photo_msg.cpp:197-204`, `d_a_npc_photo_exec.cpp:414-424`). In HD a
Forest Firefly shown at register >= 6 gives a Joy Pendant every time (no flag).

### 3.5 Tingle Tuner [CODE][DATA]
HD removed the Game Boy Advance link. Item 0x21 in slot 7 with ownership bit 0 is the Tingle Bottle, given by
the same Windfall event (31 HD Quest Logs hold it). The item is copied: a save with the Tingle Tuner has the
Tingle Bottle. There is no option to remove it; the event that gives it is done, so it could not be obtained
again. Tingle-bomb spots became plain bomb spots with the same switch numbers; Knuckle appears from chest
flags that both games share (`d_a_npc_tc.cpp:1462`).

### 3.6 Pictures [CODE][DATA][in-game]
GameCube stores up to 3 pictures per file inside the card file: a 152x104 CMPR texture, u32 subject
(`snap_result`), u8 detail, u8 capture format (1 = black and white, 4 = colour in every sample).
HD keeps an album of 12 per Quest Log in separate files (`hd_jpeg.cpp`; format checked on 696 records of
real saves): `cking_pic<S>_<I>.sav` is a baseline JPEG (800x450, 4:2:0) zero padded to 0x50000 bytes, and
`cking_pic_order<S>.sav` holds 12 records (CRC-32 over size + the 0x50000 bytes, detail, used, colour,
subject, size), the album order and the picture count. The subject numbering is the same in both games
(`d_snap.h`, 209 entries).

Which pictures exist: the NTSC game does not clear an erased picture from the card (`d_picture_box.cpp:45-54`),
so the card can hold picture data the file no longer has (13 of the 57 GameCube sample files, most of them
after Lenzo took the pictures). The converter takes what the game itself loads (`d_s_name.cpp:1218-1251`):
the first `item_record.picture_num` slots not marked in event register 0x89FF (slots erased since the last
load), with a valid checksum. Register 0x89FF is written as 0, as the GameCube leaves it after loading; HD
only carries it over to a second quest.

Conversion: each picture is decoded, scaled to the HD frame height with black bars at the sides (the
GameCube picture is narrower than 16:9) and written as an HD album entry with its subject, detail and
colour flag. `--no-pictures` skips this. Checked in the game (native port and Cemu): the Picto Box counter
and the camera screen ("1/12") count the picture and the album displays it; for a file with three colour
pictures the album shows all three with the game's "Good!" mark.

## 4. HD-only records

| Record | Field | Meaning | Converted value |
|---|---|---|---|
| options | byte 0 | Z-targeting: 0 hold, 1 switch | GameCube `config.attention_type` |
| | bytes 1, 2 | camera X invert, first-person Y control | 0 |
| | byte 4 | language, rewritten from the console at start-up | 0 |
| | byte 5 | GamePad motion aiming on | 1 (HD default) |
| | byte 6 | Hero Mode (double damage, no heart drops) | `--hero-mode` |
| | bytes 3, 7, 8 | role not established | 0 |
| controller settings | 2 bytes | read by the options and Miiverse screens | 0 |
| HD inventory | u32 flags | Zunari's pre-sail dialogue (bits 1, 2) | 0 |
| | 12 entries + count | Carlov's figurine queue (GameCube: one pending figure in register 0xA9FF) | entry 0 = register, count 1, when event 0x2F01 is set or 0x3080 is set without 0x4080 |
| | byte 0x11 | auction item re-offered after a lost bid (GameCube: register 0xCD03) | register value when event 0x4008 is set |
| name | 18 bytes | player name | GameCube name (`--name` overrides) |
| play log | first 0x18 bytes | map view state | 0 |
| | 49 x u32 | bit 0: this sector's Fishman already drew the chart (GameCube uses the charted bit) | set for every charted sector except 0, 10, 43 |

Play log evidence: in all genuine HD Quest Logs, bit 0 equals the charted bit for every sector other than the
three charted from the start (680 sector pairs, no exception).

## 5. Unused and damaged files
- A GameCube file without a player name is unused; it becomes a fresh HD Quest Log
  (`dSv_info_c::initdata_to_card` 025BAC50; equal to the 65 empty Quest Logs of the real HD files, apart from
  bytes the game leaves uninitialised).
- A raw memory card image keeps a backup copy of its directory and of its block map. The one in use is
  the copy with the higher update counter among those whose checksums are right, as the console picks it.
- The card file holds two copies of the three files. The converter reads them as the game does
  (`mDoMemCdRWm_Restore`, `m_Do_MemCardRWmng.cpp:135-146`): the first copy, or the second when the first
  fails its checksum. For file 2 the game tests the second copy's file 3 before restoring, so a good file 2
  in the second copy is not used when that copy's file 3 is damaged. A file the game cannot read is
  reported and written as an empty Quest Log.

## 5b. Which files are converted: the health check

The rules of section 3 rely on the GameCube file being one that normal play writes: a reward is held exactly
when the place that gives it is done. Before anything else each used file is checked for that
(`wwsave/convert.py`, `health`), and a file that fails is not converted at all: it is written as an empty
Quest Log and the report says why. The tool does not try to repair such a file; the other files of the card
are converted. A file fails when:

- maximum life is outside 3 to 20 hearts, current life is above it, the wallet size does not exist or holds
  more rupees than it can, the targeting mode is not hold or switch, or it counts more than 3 pictures;
- current life is below three hearts (the game never saves less);
- it holds the Swift Sail (an HD item), by the item or by its ownership flag;
- an inventory slot holds an item without its ownership flag, or an item other than the one its flags
  stand for (HD rebuilds the slot from the flags on load, so the item would change);
- for Triforce Chart 2, 4, 6, 7 or 8: the chart is owned and its chest is closed, the chest is open and the
  chart is not owned, the shard is held without the chart, or Tingle deciphered a chart that is not owned;
- the Hero's Charm and Mrs. Marie's reward (event 0x1C04) disagree, or the Savage Labyrinth floor-50 chest
  is open in a file with only the three starting hearts;
- the Ghost Ship is marked as cleared (register 0x8803 = 3) with its chest closed, or the reverse;
- the Deluxe Picto Box is held before Lenzo's third task, that task is done without any Picto Box, or Anton
  and Linda are a couple without the Deluxe Picto Box.

53 of the 477 used GameCube sample files fail (7 of the 53 USA ones): speedrun practice saves, which hold
items without their ownership flags or a Triforce Chart whose chest was never opened; two files of one
public card that hold all eight shards and no chart; and the three files modified by an exploit tool. An
item slot that is empty while its ownership flag is set is not a failure: normal play does that (the bow is
taken away in the final battle), and HD puts the item back on load.

## 6. Known gaps
- Stage data of both games was compared in full (3.2): chests, actors and player spawn points
  (`scripts/stage_diff.py`), the stage event tables (`scripts/evnt_diff.py`, identical in all 93 stages HD
  keeps) and the event scripts of all 130 stages that have them (`scripts/event_diff.py`, byte-identical).
  The statistics on real saves would still miss a flag that only matters in a state none of the 53 HD
  Quest Logs is in.
- The return place (stage, room, spawn point) is copied. Both games choose it with the same rules when saving
  (`dComIfGs_setGameStartStage`: GameCube `d_com_inf_game.cpp:1295`, HD `d_com_inf_game.cpp:806-926`), and the
  early-game places agree in the real saves. Every GameCube spawn point exists in HD except those of the Ghost Ship's two
  removed rooms, which no save can return to (3.2).
- A new-game default differs and is copied as it is: time of day 165 (GameCube) vs 150 (HD).
- Reward places were compared in full (`docs/research/reward-audit.md`): every stage entry of both discs
  byte-wise, both randomizers' location tables, every shop item set and the item functions. Nothing differs
  beyond 3.2. Two differences need no rule: the pig game gives Treasure Chart 42 while it is not owned (a
  repeatable game; the GameCube gave rupees), and the 13 Tingle Tuner triggers HD removed only revealed
  rupees and consumables.
- 81 source files of the GameCube decompilation have undecompiled functions. Both games were therefore
  compared as machine code (`docs/research/machine-code-audit.md`): every call to a save accessor with a constant
  argument, and every item-giving call, in all 415 GameCube RELs and the dol against HD's `cking.rpx`. One
  flag has a different trigger: event 0x3940. On the GameCube it is set the first time the Deku Tree is asked
  about the Koroks (message 0x13AD); in HD it is set at the end of his explanation of where they are, and the
  sea chart shows the eight withered-tree icons once it is set. It is copied: a player who heard the
  explanation sees the icons. Not covered by that audit: a setter that moved inside the same function and
  direct memory access to save data.
- The points the machine-code audit had left open were then analysed (99 flags reached from differently
  named functions, one-sided keys, message and event data, `ActorDat.bin`, direct access to the save
  block): 80 of the 99 are renamed or inlined functions, 9 are code changes with the same flag meaning
  (visual or timing), the rest belong to items of this document. HD changed 25 prices (bait, bombs, arrows
  cost more; spoils sell for more; Lenzo's paid offer 150 instead of 50) and many enemy drops; neither is
  stored in a save. No message or event script writes save data differently.
- `--pawprint-chest rewards` without `--marie steps` keeps the Silver Rupee while its HD place, the sunken
  treasure of Treasure Chart 45, cannot be marked as salvaged yet: that rupee can be collected a second
  time. Rupees are not a unique reward (both games give them without limit), so the file is still one HD
  could have written; the report states it.
- A consumable already used on the GameCube cannot be taken back by `steps` (the report says so when it
  happens).
- Japanese and European GameCube saves convert (`--allow-region`) but were not analysed.

## Verification
- **In the game** (`scripts/ingame_test.py`, `scripts/ingame_batch.py`): the game's own code, recompiled from the
  author's copy of Wind Waker HD (USA, v0) with the ZeldaWWHDRecomp native port, boots hidden, goes from the title
  screen into Quest Log 1 and plays a few seconds; its in-memory save block is then compared with the file.
  - Control: a genuine console save keeps every field (only the wind direction changes while playing).
  - The author's own converted save: all comparable fields identical after loading; screenshots show the
    right hearts, rupees, item buttons, inventory (with the Tingle Bottle), the sea chart, the renamed Private Oasis (name
    record) and chart counters equal to the file's.
  - Saving from the pause menu works: the file the game writes differs from the converted one only in the
    date stamp, time of day and save counter (1 -> 2); the empty Quest Logs come back identical except for
    bytes the game leaves uninitialised. That file loads again.
  - The author's own converted save placed at the forest exit on Outset (where the kidnapping scene starts) does
    not replay the scene.
  - Quest Logs 2 and 3 load the same way (cursor moved at file select).
  - An earlier run over file 1 of each distinct USA sample card (32 files; the run over all 48 used files
    is further down): all load into gameplay, 30 keep every field; two gain an event flag that the game sets on
    entering the scene (boarding the pirate ship; the opening of the second quest). An earlier run exposed
    a wrong rule (a New Game+ file not started yet was written with save counter 0 and the game started a
    plain new game); it was corrected and that file now starts the second quest.
  - Save cycle on every sample (`scripts/ingame_save_batch.py`: load, walk two seconds, save from the pause
    menu, compare the file the game writes with the converted one): 28 of the 32 saved (the other four start
    in a scene where the menu is not available). In 24 the written file differs only in date, time of day,
    save counter and current life. In the other four the game itself changed something: the return place
    (Link walked into the Tower of the Gods, or the game re-derived the spawn point), with the map-view bytes
    of the play log, or a scene flag.
  - Screens of converted saves that exercise the special rules: the Deluxe Picto Box given by the Lenzo rule
    shows in the inventory; saves with eight shards show the complete Triforce; the converted 100% save owns
    60 charts, the same set as a native 100% HD save minus Treasure Chart 42 (the pig minigame, still
    obtainable).
  - `--swift-sail --hero-mode` on the author's own save: loads with every field intact.
  - Save cycle in both modes on every used file of the samples (48 distinct files; the second mode also
    with Swift Sail and Hero Mode): 42 of the 48 save in each mode (the other six start in a scene where
    the menu is not available). In 36 (`steps`) and 35 (`rewards`) the file the game writes differs only
    in date, time of day, save counter and current life; in the others the game itself changed the return
    place or a scene flag. In one file the 18-byte name record differs after the name's terminator only
    (bytes the game leaves as they were in memory); the name is the same.
  - Three minutes of scripted random movement and button presses on the author's own save: no error or halt.
  - HD Treasure Charts 43-46 played to the end (`scripts/ingame_salvage.py`): a GameCube sample whose
    conversion adds all four was converted by steps; for each chart the file was placed in
    the chart's sea sector with the chart marked as opened (what the player does on the chart screen), the
    boat was moved onto the treasure, and the Grappling Hook crane was lowered with scripted input. All four
    treasures come up and the game marks each chart completed; Chart 46 brings the Piece of Heart. A chart
    marked as salvaged brings up nothing: see the Treasure Chart 45 and 46 cases below
    (`docs/verification/chests.md`, `salv45_kept` and `salv46_f50rewards`), where the same crane script that
    brings the treasure up in the control run comes back empty. The same run on the author's own save with
    Treasure Chart 44 shows the chest and "You got an Orange Rupee!", and the rupee count goes from 3953 to
    4053. The boat is moved with a test aid added to the port (`scripts/port-ship-warp.patch`).
  - The Triforce played to the end: the author's own converted save, in which the conversion turned Triforce Charts
    2 and 7 into their shards, was given the five shards it still lacks and placed at the Tower of the Gods.
    Entering the ring with the Master Sword, the King of Red Lions speaks and the boat goes down to Hyrule
    Castle. The control, the same save without those two shards (six shards), stays on the sea.
  - Lenzo after `--lenzo steps`: the sample the case applies to, converted
    and placed at Lenzo's counter in the daytime. He talks as after his quest: he offers a Legendary
    Pictograph and asks for the Deluxe Picto Box to put it in.
  - Every case of 3.2 played in both modes (`docs/verification/chests.md`, `docs/verification/npcs.md`;
    Link and the boat are placed by test aids, enemies are removed by an aid instead of fought, and the
    doors of the Stone Watcher and Overlook caves were opened by setting their unsaved switches):
    - Triforce chests of charts 2, 4, 6, 7, 8: by `rewards` the chest is there, closed, and gives the shard
      (also charts 2 and 7 on the author's card); by `steps` it is shown open.
    - Ghost Ship by `rewards`: the ship exists at night in its moon-phase sector and takes Link aboard, the
      chest gives Shard 4, register 0x8803 goes 0 -> 3 and Link returns to the sea. Control: at 3 the ship
      actor is never created.
    - Horseshoe and Star Belt lookout chests and the Pawprint cave chest: by `rewards` the chest appears
      (after its button, at once, after the room is empty) and gives Treasure Chart 43 / 44 / 46; by `steps`
      it is shown open.
    - Floor-50 chest in the four `--floor50` / `--marie` combinations: chest state, Hero's Charm bit and
      maximum life as in the 3.2 table; the closed one gives the Hero's Charm.
    - Treasure Chart 46: with `--floor50 rewards` the Pawprint chest is shown open and the crane at Two-Eye
      Reef brings up nothing; with `steps` the salvage gives the Piece of Heart (maximum life 79 -> 80).
    - Treasure Chart 45: with the Silver Rupee kept the crane at Seven-Star Isles brings up nothing; otherwise
      it brings the Silver Rupee.
    - Mrs. Marie by `rewards` (three samples): shown a Joy Pendant she gives Treasure Chart 45 and sets
      0x1C04, also with 99 pendants already given; by `steps` she does not give it again.
    - Lenzo by `rewards`: shown the couple's picture from the converted album he gives the Deluxe Picto Box
      and the register goes 5 -> 6; by `steps` he talks as after the quest and one Joy Pendant is gone.
      Run from a GameCube file that holds the couple's pictures;
      the picture shown is removed from the album (3/3 -> 2/2), as on the GameCube.
  - Every undo of `rewards` read against the HD source for later states (`docs/research/undo-audit.md`):
    each reward stays obtainable exactly once.
  - Every used file of the USA samples (48 distinct files, each loaded as Quest Log 1) converted with
    `--all steps` and with `--all rewards` loads into gameplay with the final rules: in each mode 44 keep
    every field and four gain a flag the game sets on entering the scene.
  - The kidnapping scene on Outset started from a console file made before it (2.1): entering at spawn
    point 203 sets switch 1 and event 0x0E20, as in console files; walking into the trigger sets switch 9.
- **In Cemu 2.6** (the Wii U emulator, running the author's copy; input sent to its process): six more converted saves at different points of the game (pirate ship, Outset, open sea
  in the boat, Ganon's Tower, the 100% file) load into gameplay without errors. The author's own converted save appears at file select with its name and place, loads into
  gameplay with the same hearts, rupees and buttons, and saves from the pause menu. A sample converted with
  `--all rewards` (floor 50, Mrs. Marie, both lookout chests undone) also loads into gameplay there. The author's own save converted with the final rules loads there with 4351 rupees
  (3953 plus Tingle's fee for Triforce Chart 6). The file Cemu writes is
  valid and differs from the converted one only in the date stamp, time of day and save counter; the HD
  records are unchanged and the empty Quest Logs differ only in uninitialised bytes. After restarting Cemu the
  saved file loads again.
- Stage data of both games compared in full (3.2); event scripts of every stage byte-identical.
- `python3 -m unittest tests.test_wwsave`: formats on every sample, the model of HD's load on real HD saves,
  conversion of every GameCube sample with two option sets (output valid, settled under HD's load rules, HD
  invariants hold, every field outside the documented rules byte-identical to the GameCube data), and one
  test per rule.
- `python3 scripts/compare_with_hd.py`: after any of ten milestones, the only bits that (nearly) all real HD
  saves have and no converted save has are HD-only content (Swift Sail, Treasure Chart 42) and one potion
  ownership bit; the only reverse case is event 0x2E08 (2.1).
- The ZeldaWWHDRecomp converter (`tools/savegame/gc2hd.py`), written independently, produces
  the same value for every field that the rules above do not touch, on 470 used files.

Limits: not run on a real console; apart from the quests above, the checks load a save and play seconds to
minutes, not a playthrough. In the salvage runs the chart is marked as opened in the file instead of on the
chart screen, and the quest runs start from a file placed next to the goal, not sailed there.
