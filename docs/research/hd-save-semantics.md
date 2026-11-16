# GameCube -> Wind Waker HD: semantic differences in persistent save state

Scope: what a GZLE01 per-file block (0x768 bytes) means when copied verbatim into a WWHD slot, and
what HD-only persistent data a converted save should carry.

Sources read:

- `wwhd/docs/hd-differences.md` — all 4110 lines, plus `wwhd/docs/hd-vs-gc-summary.md`.
- HD source under `wwhd/wwhd_src/` (paths below are relative to it) and the GameCube decomp under
  `tww/` for every entry that touches save state.
- `research/notes-chest-flags.md` (existing note) for the Triforce Chart number <-> location mapping.

Conventions:

- "HD `file:line`" = `research/wwhd/wwhd_src/<file>`; "GC `file:line`" = `research/tww/<file>`.
- Event bit `0xBBMM` = byte `0xBB` of the 0x100-byte event block, mask `0xMM`. Registers like
  `0xC407` = byte `0xC4`, mask `0x07`.
- "Packed offset" = offset inside the 0x768 block. I derived these by summing the block sizes in
  the HD serialisation order (`kCardHead` + priest + statusC + memory + ocean + event + reserve,
  HD `d/d_save_5.cpp:223-264`; sizes from HD `include/d/d_save.h`). The sum is exactly 0x768, but
  check them against your own layout before relying on them:

  | Block | Packed offset | Size |
  |---|---|---|
  | status A | 0x000 | 0x18 |
  | status B | 0x018 | 0x18 |
  | return place | 0x030 | 0x0C |
  | item slots `mItems[21]` | 0x03C | 0x15 |
  | get-item flags `mItemFlags[21]` | 0x051 | 0x15 |
  | item record | 0x066 | 0x08 |
  | item max | 0x06E | 0x08 |
  | bag item | 0x076 | 0x18 |
  | get bag item | 0x08E | 0x0C |
  | bag item record | 0x09A | 0x18 |
  | collect | 0x0B2 | 0x0D |
  | map | 0x0BF | 0x84 |
  | player info | 0x143 | 0x5C |
  | config | 0x19F | 0x05 |
  | priest | 0x1A4 | 0x10 |
  | status C x4 | 0x1B4 | 0x1C0 |
  | stage memory x16 | 0x374 | 0x240 |
  | ocean | 0x5B4 | 0x64 |
  | event | 0x618 | 0x100 |
  | reserve | 0x718 | 0x50 |

Confidence labels: **CONFIRMED** = both sides read in code. **CONFIRMED (HD side)** = HD code read,
GameCube side is a stub or data. **INFERRED** = follows from code plus one assumption, stated.
**UNVERIFIED** = depends on stage/archive data that is not in either source tree.

---

## 0. Summary

| # | Finding | Severity if copied verbatim | Action |
|---|---|---|---|
| 1.1 | Triforce Charts 2/4/6/7/8 are direct shards in HD | Possible unwinnable file (depends on HD stage data) | Grant the shard when the chart is owned |
| 1.2 | Lenzo: Deluxe Picto Box moved from the firefly trade to the 3rd assistant task | Deluxe Picto Box permanently unobtainable from one mid-quest state | Grant it when `0xC407 >= 6` |
| 1.3 | Player name is read from an HD-only UTF-16 record | Default name in all dialogue | Write the name record |
| 1.4 | Carlov's pending figurine moved from register `0xA9FF` to an HD-only queue | Pending figurine silently lost | Seed the queue |
| 1.5 | Auction "same item again" index moved from `0xCD03` to an HD-only byte | Wrong item re-offered once | Copy the index |
| 1.6 | Picture count lives in the HD picture store, not in the block | None if the store is empty | Zero `mPictureNum`; keep the HD store consistent |
| 1.7 | Fishman "already talked here" is an HD-only per-sector flag | Map-drawing scene replays once per sector; chart hint button missing | Optional: seed the flags |
| 1.8 | Z-target hold/switch option is read from the HD options record | Option silently reset | Optional: copy it |
| 1.9 | Item buttons 3 and 4 (`mSelectItem[3]`, `[4]`) | Self-healing | Optional: set them |
| 1.10 | Load-time validation: all three slot checksums, CRC over HD records | File rejected as corrupt | Recompute |
| 2.x | Everything HD repairs on load, and differences that need nothing | None | None |

---

## 1. Findings that need (or may need) a conversion rule

### 1.1 Triforce: five charts became direct shards — CONFIRMED mechanism, UNVERIFIED consequence

**What differs**

- HD new game sets the "chart deciphered by Tingle" byte to `0xEA`
  (`dSv_player_map_c::mTriforceBits`, map +0x81, packed offset 0x140): HD `d/d_save_3.cpp:26-41`
  (`init`, 025B7E74). GameCube initialises it to 0: GC `src/d/d_save.cpp:839-841`.
- HD also forces the same five bits on **every load**: `SaveMgr::refreshGame` (02721880) calls
  `dSv_player_map_c::onTriforce(n)` (025B82A0) for n = 1, 3, 5, 6, 7 — HD `d/d_menu_save_card.cpp:141-148`,
  called from `SaveMgr::loadCard` (02721908) at `:150-162`.
- `onTriforce` takes a 0-based bit; the game-facing wrappers pass `i - 1`
  (HD `include/gc_api/d/d_com_inf_game.h:325-326`; GC `include/d/d_com_inf_game.h:1220-1229`). So
  the pre-set bits are **Triforce Charts 2, 4, 6, 7, 8** (1-based). The hd-differences text
  "charts 1, 3, 5, 6, 7" is the raw bit numbers.
- Charts 1, 3 and 5 still need Tingle. Tingle's decipher loop is unchanged: HD
  `d/actor/d_a_npc_tc_msg.cpp:399-420`, `d/actor/d_a_npc_tc_cut.cpp:414-424`; GC
  `src/d/actor/d_a_npc_tc_msg_normal2.inc:176-205`.
- Chart number <-> location (from `research/notes-chest-flags.md:40-49,89`): 1 Islet of Steel,
  2 Private Oasis, 3 Bird's Peak Rock, 4 Ghost Ship, 5 Needle Rock gunboat, 6 Savage Labyrinth,
  7 Stone Watcher, 8 Overlook. The pre-set set {2,4,6,7,8} therefore matches "the five chests that
  hold a shard directly in HD". **This last step is an inference**: the chest contents are stage
  data and are in neither source tree. I found no code that swaps a chart for a shard
  (`d/actor/d_a_tbox*.cpp` has no Triforce handling).

**Unchanged logic that matters here**

- Salvage point for a chart is active only when the chart is opened, not complete, and — for a
  Triforce item — deciphered: GC `src/d/actor/d_a_salvage.cpp:306-321`; HD
  `d/actor/d_a_salvage.cpp:370-371` (calls 025B8308).
- The gunboats tied to a Triforce chart spawn only when that chart is deciphered and
  `mRandomSalvagePoint` matches: GC `src/d/actor/d_a_oship.cpp:1022-1029`; HD
  `d/actor/d_a_oship.cpp:1241-1255`. (The "+1" difference noted in hd-differences is cancelled by
  the wrapper; not a behaviour change.)
- Shard pickup is unchanged: `item_func_triforceN` sets collect `mTriforce` bit N-1 (HD
  `d/d_item_2.cpp:215-242`).

**Affected GameCube states**

A file that owns Triforce Chart k for k in {2,4,6,7,8} (get-map bit k-1 set, chest already open)
but has not yet salvaged shard k (collect `mTriforce` bit k-1 clear, packed offset 0x0BC).

**Consequence in HD**

- The chest is already open, so HD's direct shard cannot be collected from it.
- The chart becomes "deciphered" for free on load (bits forced), so the only remaining route is the
  salvage point. Whether HD's sea stage data still contains the salvage points for shards
  2/4/6/7/8 is **UNVERIFIED**. If they were removed, the file cannot complete the Triforce.

**Recommended rule**

For each k in {2,4,6,7,8}: if get-map bit (k-1) is set and collect `mTriforce` bit (k-1) is clear,
set the shard bit and set the chart's "complete" bit (so a surviving salvage point stays inert).

- get-map bits: `mMapFlags[1]`, packed 0x0CF..0x0D2 (big-endian u32 word 0; bit k-1 is in byte 0x0D2).
- complete bits: `mMapFlags[3]`, packed 0x0EF..0x0F2 (byte 0x0F2 for k <= 8).
- shards: collect `mTriforce`, packed 0x0BC.

This is safe in both cases (points removed or kept). Test one such file on hardware/emulator to
settle the UNVERIFIED part.

No action needed for the decipher byte itself: HD ORs in `0xEA` on load.

Side note (CONFIRMED HD side, reachability unknown): the Windfall NPC "SA5" reward branch gives
item `0xFD` (= collect map 2 = Triforce Chart 2, `include/d/d_item_data.h:263`) when it is not
owned, otherwise item 5 — HD `d/actor/d_a_npc_people_talk.cpp:475-482`; GameCube always gives
item 5, GC `src/d/actor/d_a_npc_people.cpp:6583-6587`. The branch belongs to the pig mini-game
dialogue (GC `:7231-7270`), which I believe is unused content; I did not confirm that.

### 1.2 Lenzo: where the Deluxe Picto Box is awarded — CONFIRMED

**What differs**

Quest register `0xC407` (byte 0xC4, mask 0x07; packed 0x6DC) has the same values in both games:
0 none, 1/3/5 task given, 2/4 task done, 6 or 7 third task done (7 also on a first playthrough; what tells 6 from 7 was not worked out).

| Step | GameCube | HD |
|---|---|---|
| Third task accepted (message token 6, register -> 6) | Joy Pendant (item 31) | **Deluxe Picto Box** (0x26) |
| Showing a Forest Firefly at register >= 6 | Deluxe Picto Box, only if not owned | **Joy Pendant** (0x1F), no ownership check |
| Talk at register >= 6 without Deluxe box | "bring me a firefly" lines | generic line 0x2A57 |

- HD: `d/actor/d_a_npc_photo_exec.cpp:414-424` (reward after talk), `d/actor/d_a_npc_photo_msg.cpp:43-55`
  (tokens 7 and 9), `:219-229` (firefly branch), `:283-287` (no "not colour" lines);
  `d/actor/d_a_npc_photo.cpp:285-299` (`XyEventCB` has no firefly branch); tables at `:64-65`.
- GC: `src/d/actor/d_a_npc_photo.cpp:1749-1757` (firefly branch gives the Deluxe box),
  `:1816-1822`, tokens at `:1639-1681`, tables at `:443-456`.

**Affected GameCube states**

Register `0xC407 >= 6` and Deluxe Picto Box not owned (third task finished, firefly not yet shown).

**Consequence in HD**

There is no remaining path to the Deluxe Picto Box. Showing the firefly yields a Joy Pendant.
Everything gated on it is dead: Lenzo's legendary pictographs and Carlov's colour check.

**Recommended rule**

If `(event[0xC4] & 0x07) >= 6` and get-item flag bit 1 of slot 8 is clear: set
`mItems[8] = 0x26` (packed 0x044) and `mItemFlags[8] |= 0x03` (packed 0x059).

### 1.3 Player name comes from an HD-only record — CONFIRMED

- HD dialogue fetches the name through `hdSaveHolders_c::getCurrentName` (02720170), i.e. the
  HD-only UTF-16 name of slot `mDataNum`: HD `d/d_mesg_state.cpp:84-96`, `d/hd_save_holders.cpp:163-166`.
- `dSv_player_info_c::mPlayerName` in the block (packed 0x157, 17 bytes) has no gameplay reader in
  HD that I found; New Game+ no longer preserves it (HD `d/d_save_5.cpp:44-88` vs GC
  `src/d/d_save.cpp:1437-1438,1473`).
- The name record is 18 bytes per slot in the file (`SaveMgr::readName`, HD
  `d/d_menu_save_storage.cpp:112-127`) and is part of the CRC (see 1.10).

**Consequence**: with a fresh-default record the game shows its default name everywhere.

**Rule**: write the GameCube name as UTF-16BE, NUL-terminated, into the slot's 18-byte name record
(max 8 characters). hd-differences also notes that a name of only spaces is replaced by the
localised default (`hd_scene_file_select` entry); I did not re-read that code.

### 1.4 Carlov (Nintendo Gallery): pending figurine — CONFIRMED

**What differs**

- GameCube keeps the one figurine being sculpted in register `0xA9FF` (byte 0xA9; packed 0x6C1),
  stored as the figure table index (photo number - 0x49): GC `src/d/actor/d_a_npc_mt.cpp:919-945`,
  consumed at `:970-1002`.
- HD keeps a queue of up to 12 table indices in the HD-only 20-byte per-slot record
  (`hdSaveInventory_c`: `mEntries[12]` at +0x04, `mCount` at +0x10): HD
  `include/d/hd_save_inventory.h`, `d/actor/d_a_npc_mt.cpp:63`, `:1048-1080` (get/submit/make),
  `:636-711` (`getMsg`), `:944-963` (`XyCheckCB`). `0xA9FF` is not read by HD's Carlov.
- The surrounding event bits are shared: `0x2F02` met, `0x2F01` order placed, `0x3080` ready,
  `0x4080` handed over, `0x3F01`, `0x4040`, `0x3A01`, `0x3401`, `0x3D08` gallery complete.

**Affected GameCube states**

`0x2F01` set (order placed), or `0x3080` set with `0x4080` clear (ready, not yet collected).

**Consequence in HD**

`makeFigures` iterates an empty queue (HD `:1066-1080`), so the paid-for figurine is never
registered; the bits then advance normally. Nothing hangs — Carlov's create phase clears the
cycle bits on re-entry (HD `:170-203`).

**Rule**: if `0x2F01` or `0x3080` is set, write `mEntries[0] = event[0xA9]` and `mCount = 1` in the
slot's 20-byte record.

Related, no action: gallery completion needs 0x85 figures in HD (`isComp`, HD `:1015-1017`);
GameCube accepts 0x84 unless figure 0x32 is owned (GC `:1389-1401`). A file with `0x3D08` already
set stays complete (HD `:180-183`).

### 1.5 Auction: re-offered item index — CONFIRMED

- GameCube: after losing, bit `0x4008` is set and the item index is stored in register `0xCD03`
  (byte 0xCD, mask 0x03; packed 0x6E5): GC `src/d/actor/d_a_auction.cpp:1428-1430`, read at `:414-416`.
- HD: same bit `0x4008`, but the index is byte +0x11 of the HD-only 20-byte record (five prizes do
  not fit in two bits): HD `d/actor/d_a_auction.cpp:409-417` (read), `:1570-1578` (write),
  `include/d/actor/d_a_auction.h:336-342`. I found no HD reader of `0xCD03`.
- HD prize table has a fifth entry, item 0x77 (Swift Sail), starting bid 100, no event bit;
  "obtained" means `mItems[1] == 0x77`: HD `d/actor/d_a_auction.cpp:63-69`, `:1651-1663`, `:1674-1690`.

**Affected states**: `0x4008` set.
**Consequence**: HD re-offers index 0 (Joy Pendant) instead of the lost item, once.
**Rule**: if `0x4008` is set, write `record[0x11] = event[0xCD] & 0x03`.

### 1.6 Pictographs: count and storage — CONFIRMED

- GameCube counts pictures in `mItemRecord.mItemRecord2.mPictureNum` (packed 0x068).
- HD never reads that byte for gameplay. Every count goes through the HD picture store
  (`getScratchPicture`, 02720144; count byte at +0x3C030C): Carlov HD `d/actor/d_a_npc_mt.cpp:961-962`,
  Lenzo HD `d/actor/d_a_npc_photo_msg.cpp:212`, townspeople HD `d/actor/d_a_npc_people.cpp:739-741`,
  HUD HD `d/d_meter_02.cpp:1016-1020`, New Game+ HD `d/d_save_5.cpp:59-60,85-86`.
- Album size is 12 (GameCube 3): HD `d/actor/d_a_npc_photo.cpp:289`, `d/actor/d_a_npc_photo_msg.cpp:212`.

**Consequence**: GameCube pictures do not carry over unless you also convert the images. With an
empty HD store the game is consistent; quests that need a picture just need it retaken.

**Rule**: leave the HD picture store empty (count 0) unless you write real picture records; set
packed 0x068 to 0 for tidiness. Do not write a non-zero count without matching picture data.

### 1.7 Fishman: "already visited" is an HD-only flag — CONFIRMED (index mapping INFERRED)

- GameCube decides between "draw the chart" (0x32D1) and "hint" (0x32D4) with
  `dComIfGs_isSaveArriveGrid(room - 1)`, i.e. bit 0 of `mFmapBits[room-1]`: GC
  `src/d/actor/d_a_npc_so.cpp:620-626`.
- HD asks the HD map object instead: `isSavedSeaCell` (02689174) -> `hdSavePlayLog_c::isVisited`
  (027208EC), bit 0 of `mFlags[cell]` in the HD-only 220-byte record (`mFlags[49]` at +0x18): HD
  `d/actor/d_a_npc_so_mode.cpp:796-803`, `d/hd_screen_map_display_coordinator.cpp:1561-1567`,
  `d/hd_save_play_log.cpp` (027208A0..027208EC), `include/d/hd_save_play_log.h`.
- The flag is set when message 0x32CA or 0x32D0 is shown: HD `d/actor/d_a_npc_so_mode.cpp:772-773,876-878`
  -> `saveLocationSelection` (0268A80C), coordinator `:1881-1886`.
- The same flag enables the sea-chart "Fishman hint" command (0x47): HD
  `d/hd_screen_command_button.cpp:241-262`, coordinator `:1583-1603`.
- The island drawing itself still comes from `mFmapBits` bit 0 in the block: HD
  `d/hd_screen_map_area_now.cpp:102-111` (025B8568), set at `d/hd_screen_menu_map_states.cpp:950-955` (025B8484).

**Consequence**: charted islands display correctly. Each Fishman replays the chart-drawing scene on
first contact, and the hint button is unavailable for that sector until then. Nothing breaks.

**Rule (optional)**: for each sector i in 0..48 with `mFmapBits[i] & 1` (packed 0x0FF + i), set bit 0
of `mFlags[i]` in the 220-byte record. Skip i = 0, 0x0A, 0x2B if you want to mimic a native file:
those three are pre-charted at new game in both versions (GC `d_save.cpp:842-844`, HD
`d_save_3.cpp:37-39`). INFERRED: I assumed the "location" index stored by `saveLocationSelection`
equals the sector index used by the Fishman check; I did not read `findLocation`.

The first 0x18 bytes of that record are map-view state (sea/dungeon position and scale): HD
coordinator `:874-894`, `:1318-1329`. Zero is fine.

### 1.8 Options: Z-target type and friends — CONFIRMED

The HD-only 16-byte per-slot record (`hdSaveSlotFlags_c`, reached through 027200D0) is the options
block. Readers:

| Byte | Meaning | Reader |
|---|---|---|
| 0 | lock-on type, 0 = hold | HD `d/d_attention_3.cpp:464-466` (GC reads `mConfig.mAttentionType`: `src/d/d_attention.cpp:848`) |
| 1 | camera X invert | HD `d/d_camera_engine2.cpp:1292-1295` |
| 2 | first-person / cannon Y control | HD `d/d_camera_subject.cpp:89-90`, `d/actor/d_a_canon.cpp:537-538`, `include/d/actor/d_a_ship.h:227` |
| 3 | unidentified; kept across New Game+ when < 2 | HD `d/d_save_5.cpp:55,74-75` |
| 4 | language, rewritten from the console setting at start-up | HD `d/hd_sys_setting.cpp:52-58` |
| 5 | `isCreated`; GamePad gyro enabled when 1 | HD `d/hd_input_ctrl.cpp:329-330`; default 1 in `clear()` (`d/hd_save_slot_flags.cpp`, 0271FBE8) |
| 6 | `isLoaded` == **Hero Mode** | double damage HD `d/actor/d_a_player_main_03.cpp:1866-1870`; no hearts HD `d/actor/d_a_item.cpp:485-489`, `f_op/f_op_actor_mng_3.cpp:205-206`; low-health alarm off HD `JAZelAudio/JAIZelBasic_5.cpp:496-497`; file select HD `d/d_file_select.cpp` (glue `:3067-3068`) |
| 7 | `isChanged`, options-menu value 5 (role not established) | HD `d/hd_screen_sequence_option.cpp:259-275,567-576` |

The 4-byte "pair" record holds two controller settings (byte 0 < 3, byte 1 < 2):
HD `d/hd_screen_sequence_option.cpp:275-292`; other readers are Miiverse screens.

**Consequence of defaults**: none for gameplay. Hero Mode off, hold targeting.

**Rule (optional)**: copy `mConfig.mAttentionType` (packed 0x1A1) into options byte 0. Leave byte 6
at 0 unless you want Hero Mode. Use the `clear()` defaults for the rest (byte 5 = 1, others 0).

Still read from the block in HD: `mConfig.mVibration` (HD `d/d_com_inf_game_2.cpp:664`).
`mConfig.mSoundMode` is overwritten with 2 on every load (HD `d/d_save_5.cpp:249-250`).

### 1.9 Item buttons 3 and 4 — CONFIRMED, self-healing

- HD uses `mSelectItem[3]` (packed 0x00C) for the GamePad shortcut item and `mSelectItem[4]`
  (packed 0x00D) for the sail. GameCube leaves both at 0xFF (GC `d_save.cpp:30-33`).
- Set when obtained: Wind Waker -> `[3] = 2` (HD `d/d_item.cpp:204-211`); sail / Swift Sail ->
  `[4] = 1` (HD `d/d_item_2.cpp:299-315`).
- Repaired on load: `[3] = 2` when the Wind Waker is owned; `[4] = 1` only when the Swift Sail bit
  is set (HD `d/d_menu_save_bootstrap.cpp:144-155`).
- Repaired in play: pressing A on the boat with a sail owned sets `[4] = 1`; the GamePad shortcut
  sets `[3]` (HD `d/actor/d_a_player_main_03.cpp:6213-6224`, `:6253-6278`).

**Rule (optional)**: set packed 0x00C = 2 if the Wind Waker is owned and packed 0x00D = 1 if the sail
is owned, to match a native file.

### 1.10 What HD validates on load — CONFIRMED

Not semantic, but a converted file is rejected if these fail (`mReadStatus = -3`):

- **All three** slots must pass the checksum, not just the used one: `SaveMgr::readSlots`, HD
  `d/d_menu_save_storage.cpp:37-55`. Checksum = byte sum and sum of complements over 0xA8C bytes,
  stored at slot +0xA8C / +0xA90: `:17-23`, `d/d_menu_save_card.cpp:114-123`.
- Byte 7 of the return-place stage name (slot +0x30) is forced to NUL: `:25-35`.
- A 4-byte word must equal the in-memory value at save +0x1790 (`hdSaveHolders_c::mSelectedSlot`,
  initialised to 4): `checkSerial`, `:129-141`. I did not trace other writers of that field.
- The last 4-byte word must equal a CRC-32 over the packed HD records (0x342 bytes: 3x16 options,
  3x4 pair, 3x20 inventory, 3x18 names, 3x220 map): `checkVersion`, `:143-156`;
  `hdSaveHolders_c::calculateChecksum`, HD `d/hd_save_holders.cpp:171-198`. Any edit from 1.3-1.8
  changes this CRC. Note the name copy is `length + 1` **bytes** of the UTF-16 text (`:191`), as written.
- Load order is eight stages from a descriptor table at 0x1014094C (data only; order not visible
  in source), then picture files, Miiverse data, play log: `:806-866`.

---

## 2. Differences that need no action

### 2.1 HD rewrites inventory from ownership bits on every load — CONFIRMED

`SaveMgr::startup` (02720E34), HD `d/d_menu_save_bootstrap.cpp:135-175`:

- For each slot i in 0..20 except bottles 14-17: if `mItemFlags[i]` bit 0 is set,
  `mItems[i] = table[i]` (table getter 025DB5AC, HD `f_op/f_op_msg_mng.cpp:156-158`; the table is
  data at 101F3484, not in source — GameCube's equivalent is `itemicon[]`, GC
  `src/f_op/f_op_msg_mng.cpp:56-82`).
- Slot 1 bit 1 -> `mItems[1] = 0x77` (Swift Sail). Slot 8 bit 1 -> 0x26. Slot 12 bit 2 -> 0x36,
  else bit 1 -> 0x35.

GameCube sets the same bits in the same slots (GC `src/d/d_item.cpp:692-835,1121-1122`); slot 1
bit 1 is never set there. Consequences:

- **Tingle Tuner -> Tingle Bottle**: no remap needed. HD still uses item 0x21 in slot 7 with
  ownership bit 0 (HD `d/d_item.cpp:198-202`), with bottle resources (HD
  `d/d_item_data.cpp:152,201`). A file with the Tuner simply has the Tingle Bottle.
  (INFERRED: `table[7]` is 0x21; the table bytes are not in source.)
- **Bow removed in Ganon's Tower**: GameCube empties slot 12 while in stage `GTower` (GC
  `src/d/d_s_play.cpp:1376-1392`); HD does not (HD `d/d_s_play_6.cpp:175-197`). A file saved there
  gets the bow back from the ownership bits, on load and again at scene start.
- Corollary: an item whose slot is filled but whose bit 0 is clear is left alone; an emptied slot
  with bit 0 set is refilled. Keep the bits truthful.

### 2.2 HD re-derives equipped sword/shield/bracelet on load — CONFIRMED

`saveMgrRefreshEquipment` (02721730), HD `d/d_menu_save_card.cpp:124-140`: collect[0] bits 3/2/1/0
-> 0x3E/0x3A/0x39/0x38; collect[1] bits 1/0 -> 0x3C/0x3B; collect[2] bit 0 -> 0x28. Consistent
with the Forsaken Fortress 1 sword removal, which clears the collect bit in both versions (GC
`d_s_play.cpp:1369-1374`, HD `d_s_play_6.cpp:160-172`).

### 2.3 Other confirmed no-ops

| Topic | HD | GameCube | Why no action |
|---|---|---|---|
| Wallet caps | 500 / 1000 / 5000: `d/d_meter_02.cpp:282-283`, `d/actor/d_a_npc_bs1.cpp:249-258` | 200 / 1000 / 5000: `include/d/d_save.h:20-30` | Same `mWalletSize` values; HD cap is a superset |
| Start time | 150: `d/d_save.cpp:43-53` | 165: `src/d/d_save.cpp:54` | New-game default only |
| Life clamp on save | < 12 -> 12: `d/d_save_5.cpp:276-280` | same: `src/d/d_save.cpp:1710-1712` | Identical |
| Stage item bits | assert < 32: `d/d_save_4.cpp:75-82` | assert < 64 on a one-word array: `src/d/d_save.cpp:1113-1120` | Same storage word; no layout change |
| Blue Tingle (Knuckle) | appears when tbox 0xF is open in stages 3,4,5,7,6: `d/actor/d_a_npc_tc.cpp:1462-1470` | event bit `0x1708` (set only by the GBA link): `src/d/actor/d_a_npc_tc.cpp:1829-1835`, `d_a_agb.cpp:820-821` | Same chest bits; `0x1708` is only read for dialogue in HD (`d_a_npc_tc_msg.cpp:436,631`) and never set |
| Tingle-bomb spots | plain bomb switch, same switch number: `d/actor/d_a_agbsw0.cpp:21-43,69-90` | needed GBA + Tingle bomb | Switch bits mean the same |
| Hero's Charm | collect[4] bit 0 owned, bit 1 worn: `d/d_item_2.cpp:85-87`, `d/actor/d_a_player_main_01.cpp:513-516` | same: `src/d/d_menu_collect.cpp:1283-1286` | Identical |
| Swift Sail | item 0x77, slot 1, ownership bit 1: `d/d_item_2.cpp:299-306`, `d/d_item_4.cpp:356-365`; counts as the sail for Zunari / townspeople | unused item id | Never present in a GameCube file |
| Zunari's HD flags | bits 1 and 2 of the 20-byte record's u32 at +0: `include/d/actor/d_a_npc_rsh1.h:331-334`, `d/actor/d_a_npc_rsh1_msg.cpp:95-112,276-289` | — | Only gate extra dialogue before the sail is owned; zero falls back to the GameCube line 0x288C |
| Letters | Tingle's letter `0xB203` is also auto-stocked at the Hyrule warp: `d/actor/d_a_warpdm20.cpp:137-142`; day-change rule kept: `d/d_kankyo.cpp:133-136` | `src/d/d_kankyo_dayproc.inc:9-13` | Same register values; postbox table identical (HD `d/actor/d_a_obj_toripost.cpp:17-21`, GC `:38-52`) |
| Whirlpool bit `0x1940` | set only with the bomb bag: `d/actor/d_a_ship.cpp:3481-3485` | always: `src/d/actor/d_a_ship.cpp:2825` | Only selects a King of Red Lions hint (GC `:499`); I found no HD reader |
| New Game+ (`reinit`) | keeps sound, vibration, clear count, picture count (HD store), `0x89FF`, options bytes 0 and 3; drops name, attention, ruby: `d/d_save_5.cpp:44-88` | `src/d/d_save.cpp:1401-1492` | Same 17 held registers, same five bits (`0x2F08,0x2F04,0x2F02,0x3A01,0x3401`), same `0xC407 = 7`, same tbox/switches, `mRandomSalvagePoint = 3` |
| `mSaveCount` (info +0x10, packed 0x153) | +1 per save up to 9999: `d/d_menu_save_card.cpp:33-39` | initialised only (`field_0x10`) | Harmless counter |
| Magic Armor | spends rupees, not magic: `d/actor/d_a_player_main_02.cpp:2126-2129` | magic | Runtime only |
| Save-time return place | same decision tree: `d/d_com_inf_game.cpp:806-926` | `src/d/d_com_inf_game.cpp:1295-1396` | Same; the 5-entry check table is data at 101D5E18 (not compared) |
| Ghost Ship chart index | raw 0x23: `d/actor/d_a_ghostship.cpp:374-377` | `0x24` through a `-1` wrapper: `src/d/actor/d_a_ghostship.cpp:333` | Same bit |
| `checkGetItem` | `d/d_com_inf_game.cpp:676-692` | same structure | Identical apart from inlining |
| File-select progress / play-log summary | derived from the block at save time: `d/d_menu_save_storage.cpp:443-541` | — | Recomputed, not an input |
| Heart-piece / message-bottle statistics | counters in the HD picture-info record via 027201DC: `d/d_item.cpp:78-83,161-167` | — | Only Miiverse / SpotPass readers found |

---

## 3. Guesses and open questions

1. **HD salvage points for shards 2/4/6/7/8** — exist or not? Stage data. Rule 1.1 is written to be
   safe either way.
2. **Chest contents and spawn points in general** are stage data. I could verify no chest-content
   change from code. A return place saved by GameCube (`stage`, `room`, `start code`, packed 0x030)
   is assumed valid for HD's stages; not checked.
3. **`table[7]` and the rest of the slot->item table** (data at 101F3484) are assumed equal to
   GameCube's `itemicon[]` apart from HD additions.
4. **Play-log flag index** (1.7) assumed equal to the sea sector index.
5. **Options byte 7** — role not established. (Byte 3 was established later: the default of the game
   build, `docs/DIFFERENCES.md` 4b.)
6. **"Serial" word** (1.10) — only the comparison was read.
7. **Pig mini-game reward `0xFD`** (1.1 side note) — reachability not established.
8. The HD item-id enum header (`include/d/d_item_data.h`) is textually identical to GameCube's, so
   it is not independent evidence that ids are unchanged; the handlers in `d/d_item*.cpp` are.

---

## 4. Checked and found identical (coverage)

Read in both trees unless marked.

- **Save classes** (`d_save`, all five HD parts): status A/B, return place, item slots, get-item
  flags and the bottle bit formula, item record/max, bag items and counts, get-bag flags, collect
  (sword/shield/bracelet/charms, `mTact`, `mTriforce`, `mSymbol`), map get/open/complete bits,
  `mFmapBits`, ocean bits, event bit/register accessors, `memBit` (tbox, 128 switches, visited
  rooms, keys, dungeon-item bits), `danBit`, zones, restart, priest record, status C (recollection
  copy), reserve (0x50), `card_to_memory` / `memory_to_card` order. Differences are only those
  listed above.
- **Event initialisation**: `0xBEFF = 20`, `0x7EFF = 0x0E` in both (HD `d_save_3.cpp:247-251`).
- **Item handlers** `d_item` parts 1-4: all inventory, bag, collect, map and capacity writes match
  apart from buttons 3/4, item 0x14, item 0x77 and the heart-piece counter. Collect map 8 no longer
  clears its decipher bit on pickup (HD `d_item_3.cpp:282-286` vs GC `d_item.cpp:1958`) — moot,
  since the bit is forced on load.
- **Tingle**: decipher loop, statue payment bits `0x1240, 0x1D08, 0x1D04, 0x1D02, 0x1D01`, rescue
  bits `0x0B40, 0x0B80`.
- **Bits named in hd-differences as HD checks** that turned out to be existing GameCube bits with
  the same setters: `0x0310, 0x0520, 0x2D80, 0x3908, 0x0B80, 0x2420, 0x1E40, 0x3A10, 0x3A20, 0x0901`.
- **Literal event constants**: I extracted every 3-4 digit hex literal passed to an event
  bit/register call in HD `d/`, `f_op/`, `hd/` (379 distinct) and compared with GameCube's
  `d_save_event_flag.inc`. None falls outside the GameCube enum (the only misses were tmp bits and
  struct offsets). This does not catch bits passed through tables or named constants.
- **Medli / Makar**: priest record layout and use unchanged; HD additions are runtime warp actions.
- **`mRandomSalvagePoint`, `mPuzzleData`, `mClearCount`, `mDeathCount`**: same fields, same writers.
- **Sea chart**: discovered islands still come from `mFmapBits` bit 0.

### Not comparable: GameCube side is a stub in zeldaret/tww

HD uses event bits in these actors that I could not check against GameCube source, so a changed
meaning would not have been detected: `d_a_npc_aj1` (`0x3701-0x3708`), `d_a_npc_ko1`
(`0x3801, 0x2C04, 0x3340, 0x3101`), `d_a_npc_ob1` (`0x2C20, 0x2C40, 0x2C80`), `d_a_npc_ym1`
(`0x3540, 0x3580, 0x3140, 0x2904`), `d_a_npc_bj1` (`0x2E10, 0x2902, 0x1D40, 0x1B80`),
`d_a_npc_zk1` (`0x1D80, 0x1C01`), `d_a_npc_gp1` (`0xC5FF, 0x1920`), `d_a_npc_bmcon1`
(`0x2B40, 0x2A40, 0x2901`), `d_a_npc_sarace` (`0x2808-0x2840`), `d_a_obj_ftree` (`0x2E20`, set by
HD `d/actor/d_a_item.cpp:719-723`), `d_a_obj_firewall` / `d_a_pz` (`0x3520`), `d_a_ss` (`0x2B20`),
`d_a_npc_kg2`, `d_a_npc_p2`. hd-differences reports no gameplay change for any of them beyond
what is listed here.
