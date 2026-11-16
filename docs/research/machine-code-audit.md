# Stub audit: save flags and rewards, GameCube machine code vs HD

Scope: GameCube USA (GZLE01) `main.dol` + all 415 RELs against HD `cking.rpx` and `wwhd_src`. Read-only; everything
here is in `audit/machine-code/`.

## 1. Method

Both sides are compared at machine-code level, so the result does not depend on whether zeldaret/tww has source
for an actor.

- `ppc.py` — PowerPC constant tracker (`li/lis/addi/addis/ori/andi./rlwinm/mr/extsb/extsh`, `lwz` from a constant
  address, merge of values at forward branch joins, loop-head and jump-table handling). At every `bl` it reports the
  possible constant values of r3..r7. Non-constant arguments are reported as `?`, never guessed.
- `gc_extract.py` — reads `main.dol` and every REL (loose and inside `RELS.arc`, Yaz0) from the disc, applies the REL
  relocation tables (calls into the dol are resolved through the relocation addend to `config/GZLE01/symbols.txt`),
  attributes each function to its source file through `splits.txt`. 39,319 functions.
- `hd_extract.py` — decompresses `.text` of `cking.rpx`, attributes code to source files through the
  `/* 0XXXXXXX */` function markers in `wwhd_src` (38,828 functions). Accessor identity = call target address of the
  `dSv_*` functions in `d/d_save*.cpp` and the `dComIfGs_*` helpers in `d/d_com_inf_game.cpp`, so local wrapper
  names in the HD source (`Bj1_isEventBit`, `auction_isEventBit`, ...) do not matter.
- `compare.py` — per source unit, set of (accessor, event/tmp, constant). Event vs. temporary bits are told apart by
  the `this` pointer (GC `g_dComIfG_gameInfo+0x624` / `+0x1158`; HD `*(0x101F84DC)+0x644` / `+0x1178`). Calls made
  through a wrapper whose flag argument is its own parameter (`dLib_setFirstMsg`, `chkReg`, `dLetter_*`, ...) are
  expanded to the wrapper's call sites. HD split files (`_exec`, `_msg`, ...) are folded into the GameCube unit name.
  Accessors covered: all `dSv_event_c`, `dSv_info_c`/`memBit`/`danBit`/`zoneBit`/`zoneActor` (switch, item, tbox,
  actor, dungeon item, visited room), `dSv_player_get_item_c`, `dSv_player_collect_c` (collect, tact, triforce,
  symbol), `dSv_player_map_c`, `dSv_player_bag_item_c`, `dSv_player_get_bag_item_c`, `dSv_ocean_c`,
  `dComIfGs_checkGetItem(Num)`, `dComIfGs_isStageTbox/onStageTbox/isStageBossEnemy/isStageLife/onStageLife`.
- `funcdiff.py` — same data per function name (finds a flag whose reader/setter sits in a different function).
- `rewards.py`, `gtitm.py` — item numbers passed to `fopAcM_createItem*`, `fopAcM_fastCreateItem*`,
  `fopAcM_createItemFor*Demo`, `fopAcM_createShopItem`, `fopAcM_createRaceItem*`, `fopAcM_createDemoItem`,
  `execItemGet`, and constants stored to the event controller's get-item byte (`dComIfGp_event_setGtItm`).
- `tables_all.py`, `tablecmp.py` — every pointer-free data object of every REL searched byte-for-byte in HD
  `.rodata`/`.data`.
- `stubs.py` — a function counts as undecompiled when its body is only `/* Nonmatching */`.
- Helpers: `gcdis.py`, `hddis.py` (disassembly), `where.py`, `flag.py` (call sites of a unit / of a flag).

Outputs kept: `diff_all.txt` (all one-sided keys per unit), `global_diff.txt`, `funcdiff.txt`, `rewards_all.txt`,
`tables_all.txt`, `validate.txt`, `stubs.txt`, `stub_table.md`. `gc_calls.json` / `hd_calls.json` (30 MB each) are the
raw extractions and can be regenerated (`python3 -I gc_extract.py gc_calls.json`, same for HD).

### Validation

- `validate.py`: for the 367 GameCube actors that are decompiled, the event bit/register constants written in the
  source (`dComIfGs_is/on/offEventBit`, `get/setEventReg`, literals and `dSv_event_flag_c::` names) were compared with
  what the machine-code extractor found. 738 of 744 source constants were found. The 6 misses are all inside
  `#if VERSION == VERSION_DEMO` blocks, i.e. not in the USA binary (`d_a_npc_rsh1.cpp:1690-1710`,
  `d_a_agb.cpp:1202-1203`, `d_a_tag_md_cb.cpp:526-527`). 354 actors identical; in the other 13 the machine code has
  *more* constants than the source text search (inlines/tables such as `dLetter_*`), none fewer.
- `d_a_npc_aj1` (stub) by hand: GC and HD lists are identical and equal the HD source (`d_a_npc_aj1.cpp:136-1197`).
- Cross-side agreement: of the pointer-free REL data objects, 2,155 of 2,331 are byte-identical in HD.

## 2. Stub list (task 1)

81 files under `tww/src` contain undecompiled functions (`stubs.txt`): 74 actors and 7 non-actor files
(`d_camera, d_demo, d_ev_camera, d_map, d_message_paper, d_minigame_terminater, d_particle`). The list in
`notes-hd-save-semantics.md` (15 actors) was incomplete. Stub actors with save-accessor calls that were not on it
include `d_a_bigelf, d_a_npc_ac1, d_a_npc_auction, d_a_npc_bms1, d_a_npc_co1, d_a_npc_de1, d_a_npc_ds1,
d_a_npc_gk1, d_a_npc_kf1, d_a_npc_kg1, d_a_npc_kk1, d_a_npc_kp1, d_a_npc_pf1, d_a_npc_uk,
d_a_npc_yw1, d_a_obj_search, d_a_oq`; the complete list with every constant is the table in section 6 (14 of the
81 files have no save-accessor call on either side). Because the comparison is binary on both sides, all units of
the game were compared, not only these.

## 3. Result: flags

Across the whole game `compare.py` leaves 416 one-sided (accessor, constant) keys in 76 units (49 GameCube units,
27 HD-only `hd_*` units with 96 keys); all but the ones below are in the menu/UI/file-select/message units that HD
rewrote (`d_menu_*`, `d_meter`, `d_file_select`, `d_s_name`, `d_picture_box`, `d_mesg`, `f_op_msg_mng`, `d_map` and
the `hd_*` units) or in the removed Tingle Tuner actors (`d_a_agb`, `d_a_agbsw0`: 102 keys). Several remaining
keys are extraction artefacts where one side resolved a constant and the other reported `?` (`d_a_npc_ji1`
`0xD003`, `d_a_npc_bj1` `0x9AFF`, `d_a_npc_people` `0xFC03`, `d_a_npc_bs1` `0x2C`, `d_a_obj_YLzou` `0x3820`,
`onCollect` second argument); each was checked in the HD source and is the same constant. No constant is used by one actor on GameCube and by a *different*
actor on HD except as listed.

### 3.1 New differences (not in the known list)

| # | Flag | GameCube | HD | Converter impact |
|---|---|---|---|---|
| 1 | event `0x3940` | Deku Tree (`d_a_npc_de1`, stub) `next_msgStatus`: at message `0x13AD` choice 0 without `0x0102`: if `0x3940` set -> msg `0x13AF`, else set `0x3940` and msg `0x13AE`. A "said once" dialogue bit. Machine code `d_a_npc_de1.rel` `next_msgStatus__11daNpc_De1_cFPUl`: `li r4,0x3940; bl isEventBit` / `li r0,0x13af` / `li r4,0x3940; bl onEventBit` / `li r0,0x13ae` (five consecutive blocks after the `0x102` test). No other GameCube user. | Set when the Deku Tree's Korok-location dialogue `0x13C7..0x13CA` finishes: `d/actor/d_a_npc_de1.cpp:333-337`. The `0x13AD` branch no longer tests it (`:285-292`, `0x13AF` unreachable). Read by the sea chart: `d/hd_screen_sea_chart_menu.cpp:1437-1458` — without `0x0102`, the eight icons driven by register `0x9EFF` and Forest Water (`checkBottle(0x59)`) are only updated when `0x3940` is set. | Different trigger, new reader. A GameCube file can have `0x3940` set without the HD dialogue having run (icons shown early) or clear although the player heard the explanation (icons missing until the Deku Tree is asked again via `0x13AA` choice 1). Display only; nothing blocks. Rule if exact HD behaviour is wanted: clear `0x3940` when `0x0102` is clear (HD sets it again on the dialogue); otherwise leave. The "eight withered-tree icons" reading is inferred from `0x9EFF`/`0x0102`/item `0x59`, the same data `d_a_obj_ftree` uses; I did not render the screen. |
| 2 | event `0x3020` | Read by Tingle `next_msgStatusNormal2` (`d_a_npc_tc.rel`, `li r4,0x3020; bl isEventBit`), besides its setter/reader in `d_a_bigelf` (flag table `0x3020,0x3010,0x3008,0x3004,0x3002,0x3001,0x3180`). | Tingle no longer reads it (`d/actor/d_a_npc_tc_msg.cpp:463-470`, "wallet-size messages are absent"). `d_a_bigelf` table identical (`d/actor/d_a_bigelf.cpp:58`). | None (a reader removed; meaning unchanged). |
| 3 | stage switch `0x2A` (room 1) | Not read by `d_a_obj_search` (stub; its only switch reads use the actor's own parameter). | `daObj_Search::Act_c::initialMode` reads it to pick the searchlight parameter set for kinds 10/102: `d/actor/d_a_obj_search.cpp:1857-1865`. Stage data using `0x2A` in `sea` Room1 (cannons, chest appear switch) is identical on both discs. | None (new reader of a switch with the same setters). |
| 4 | event `0x2C01` | `d_a_obj_firewall` (stub) sets it in `retire_act_proc` only. | Also set in `burn_wait_act_proc` as soon as the save switch is seen: `d/actor/d_a_obj_firewall.cpp:614-621`, plus `:248-252`. | None (same meaning, set a few frames earlier). |
| 5 | event `0x0E20` | Set by `d_a_tag_event` `demoInitProc`. | Additionally set when cutscene `Demo04` is created: `d/d_demo.cpp:1070-1074` (`dDemo_DEMO_EVENT_e`, `include/d/d_demo.h:512`). | None (extra setter, same meaning). |
| 6 | event `0x2E20` | Set by `d_a_obj_ftree` (stub) `search_heart_part` when the heart-piece actor it created no longer exists. | Set by the item actor when collected and its parent is actor `0x83`: `d/actor/d_a_item.cpp:719-723`. `place_heart_part` reads it on both sides. | None (setter moved, same meaning). |
| 7 | `isStageBossEnemy(4)` | Not read by `d_a_oq` (stub). | `daOQ_Create` returns error in room `0x29` of the boss stage once the boss flag is set: `d/actor/d_a_oq.cpp:683-686`. | None (new read). |
| 8 | events `0x3508,0x3504,0x3502,0x3501,0x3680..0x3601,0x3780..0x3710` | `d_a_obj_adnno` `_draw` reads the 16-entry `daObjAdnno_event_bit_table` (`src/d/actor/d_a_obj_adnno.cpp:122-131`). | Draw loop removed (`d/actor/d_a_obj_adnno.cpp:67`). | None (readers removed). |

Also seen, part of already-known items: `d_a_npc_auction` (stub) `getMsg` reads `0x0F01,0x1080,0x1040,0x1020`
directly on GameCube; HD asks `Auction_hasAvailableItem` (five-entry table incl. Swift Sail,
`d/actor/d_a_auction.cpp:1665-1671`, `d/actor/d_a_npc_auction.cpp:852-853`) — auction/Swift Sail. `d_a_npc_mt`
`0xA9FF` vs `0x3401` — Carlov. `d_a_auction` `0xCD03` — auction index. `d_a_npc_photo` — Lenzo. `d_a_npc_people`
/`d_a_npc_rsh1`/`d_a_npc_so` `checkGetItem(0x77)`, people `0xFD` — Swift Sail / pig game. `d_s_room` ->
`checkGetItem(0x21)` (Tingle Bottle spawner). `d_item`/`d_menu_save` sword/shield/sail/Triforce-chart handling.
`d_a_lod_bg` `0x3908`, `d_a_player_main` `0x0520`, `d_a_npc_rsh1` `0x0B80`, `d_a_warpdm20` `0xB203` are in the notes.

### 3.2 The 15 actors named in the notes

`d_a_npc_aj1, ko1, ob1, ym1, bj1, zk1, gp1, bmcon1, sarace, kg2, p2, d_a_pz, d_a_ss`: identical sets of
(accessor, constant) on both sides (table in section 6; count differences such as `0x2901` 1/5 are the same
statement duplicated by the HD compiler inside the same function). `d_a_obj_ftree`: item 6 above.
`d_a_obj_firewall`: item 4 above. No changed meaning found.

### 3.3 Flags passed through tables / non-constant arguments

Call sites where the flag is not a constant in a stub actor, checked by hand:
- `d_a_bigelf` `getEventFlag`: GC jump table `0x3020,0x3010,0x3008,0x3004,0x3002,0x3001,0x3180` = HD `l_eventFlags`.
- `d_a_npc_uk` `getFirstTalk` (`0x1202,0x1204,0x1201`), `getCaughtFlag` (tmp `0x08,0x04,0x10`), `getFoundFlag`
  (tmp `0x180,0x140,0x01`): identical (`d/actor/d_a_npc_uk.cpp:134-167`).
- `d_a_npc_bj1` `chkReg/setReg` (`0x96FF..0x9AFF`): identical.
Decompiled actors: every unit with a non-constant flag argument has the same number of such sites in the same
functions on both sides except the known ones (auction, photo, people); the flag tables themselves are covered
by the data comparison: 2,155 of 2,331 pointer-free REL data objects are byte-identical in HD. Of the 176 not
found, the only flag tables are `daObjAdnno_event_bit_table` (item 8) and `l_save_dat` of `d_a_npc_photo` (Lenzo);
the rest are display lists, textures, collision/attribute/float tables and resource-index tables
(`tables_all.txt`). Tables that contain pointers (1,352 objects) were not compared.

### 3.4 One-sided keys in non-actor units, not analysed further

`0x89FF` (get/set in GC `d_picture_box`, `d_s_name`; no HD accessor call with that constant), `0x3510` (GC
`d_s_name` read), message-tag registers in GC `d_mesg`/`f_op_msg_mng` (`0x86FF, 0x8AFF, 0xBA0F, 0xBEFF, 0xC0FF`,
all present in HD in other units), `0x2D80` (`d_message`), `0x1820` (`d_resorce`), `0x7EFF/0xBEFF` init (HD:
`d_save_3.cpp`, already in the notes). See `diff_all.txt`.

## 4. Result: rewards

Code-level item-giving sites found: GC 135, HD 139 call sites in 68/67 units (`rewards_all.txt`).
`dComIfGp_event_setGtItm` is used by only `d_a_bigelf`, `d_a_npc_nz` and the two `fopAcM_createItemFor*Demo`
functions on both sides.

No actor gives a different item at the same step, beyond the known list. Checked individually:

| Actor | GameCube | HD | Same |
|---|---|---|---|
| `d_a_npc_ji1` | `5, 6, 7, 0x0F, 0x38, 0xAA` | same | yes |
| `d_a_npc_kp1` | `7, 0x9A` | same | yes |
| `d_a_npc_md` | `0x25, 0x50, 0x98` | same | yes |
| `d_a_npc_mk`, `d_a_tag_mk`, `d_a_npc_bj1`, `d_a_npc_kf1`, `d_a_npc_hr`, `d_a_npc_fa1`, `d_a_deku_item`, `d_a_arrow` | `7`; `0x1F`; `0x46`; `4`; `0x6D`; `0x16`; `0x34`; `0x10` | same | yes |
| `d_a_npc_kg2` (stub) | by register `0xB703`: 0,1 -> `7`; 2 -> `0xD7`; else `6` (machine code) | `l_prizes = {7, 7, 0xD7}`, else `6` (`d_a_npc_kg2.cpp:19, 493-502`) | yes |
| `d_a_npc_kg1` (stub) | stack tables `{7, 0xCC, 5}` and `{0xF1, 6}` indexed by a win-count register (rodata `07 CC 05`, `F1 06`) | same (`d_a_npc_kg1_dialogue.cpp:150-152, 210-211`) | yes |
| `d_a_npc_ds1` (stub) | potion `0x49/0x4A/0x4B` -> `0x51/0x52/0x53`, else bought item | same (`d_a_npc_ds1_event.cpp:52-61`) | yes |
| `d_a_npc_bmcon1` (stub) | `7`, `5` (`eventMesSet`) | same (`d_a_npc_bmcon1.cpp:868-876`) | yes |
| `d_a_bigelf` (stub) | `0xAB/0xAC` by wallet size, `0xAD/0xAE` bombs > 30, `0xAF/0xB0` arrows > 30, else `4` | same (`d_a_bigelf.cpp:1069-1082`) | yes |
| `d_a_npc_tc` | `0x21`, `0xDC`, `0xB8`, `0xB3..0xB7`, `0x79..0x80` | same (`d_a_npc_tc_cut.cpp:197-219`); `0x21` is the Tingle Bottle in HD (known) | yes |
| `d_a_obj_toripost` | `m_letter` table (13 entries) | byte-identical at HD `.rodata:10031504` | yes |
| `d_a_npc_bms1` (stub), `d_a_npc_bs1`, `d_a_npc_rsh1`, `d_a_npc_nz`, `d_shop` | selected shop item | selected shop item | not compared (see 5) |

One-sided reward keys that are not rewards for a step: `d_a_player_main` HD-only `setDamageRupee` (items 1-6) and
bottle throw (`0x13`); `d_a_agb/agbsw0` (removed). Not examined: `d_a_bdkobj` HD-only `fopAcM_createItem(.., 0, ..)`
in `daBdkobj_Execute`; `d_a_item` `execInitGetDemoDirection` calls `createItemForPresentDemo` in HD where GameCube
calls `createItemForTrBoxDemo` (item number non-constant on both).

## 5. Not covered

- Order/step of a flag inside one function: the comparison is per unit and per function name, not per basic
  block. Item 1 was found only because a reader disappeared; a setter moved to another message *within the same
  function while keeping all readers* would not be detected. `funcdiff.txt` lists the 99 (unit, flag) pairs whose
  functions differ by name; I read through it and they are inlining/renaming, except those reported above; I did
  not disassemble each.
- Stage switches, item bits and chest numbers are almost always actor parameters (`?`); only hard-coded ones are
  compared.
- Flags and items set by data: event scripts (`event_list.dat`), message flow, stage data. Not code.
- Tables containing pointers (shop item sets, message tables), and items taken from a shop selection or an actor
  member where the value is not at the call site: `d_a_npc_ah, d_a_npc_mn, d_a_npc_sv, d_a_npc_roten, d_a_npc_mt,
  d_a_npc_people, d_a_npc_photo, d_a_auction` (`eventGetItemInit`), the shops. For these only the number of
  item-giving sites and the pointer-free data tables were compared.
- `d_a_waterfall` (stub): three switch reads on GameCube, no HD source file for this actor found.
- HD code is attributed to the nearest preceding marked function; the 885 unmarked HD functions (libraries) are
  attributed to their predecessor.
- Direct memory access to save data that bypasses the accessor functions.

## 6. Per-actor table (stub actors)

Format: `kind flag GCcount/HDcount`. `ev.` = event bit/register, `tmp.` = temporary bit/register, `?` =
non-constant argument.

Totals (all units, excluding d_save/d_com_inf_game internals): GC 4121 accessor call sites in 332 units, HD 3816 in 349 units.

| actor | stub fns | accessor constants: `kind flag` GC count/HD count (bold = one side only) |
|---|---|---|
| d_a_bigelf | 65/70 | info.isSwitch ? 2/3; info.onSwitch ? 2/2; ev.isEventBit ? 2/2; ev.onEventBit ? 1/1 |
| d_a_bl | 28/30 | info.isSwitch ? 3/3; info.onActor ? 4/3 |
| d_a_bo | 24/26 | info.onActor ? 2/2 |
| d_a_gm | 23/25 | checkGetItem 2D 1/1; info.isSwitch ? 1/1; info.onActor ? 4/4; info.onSwitch ? 4/4 |
| d_a_gnd | 36/38 | no save accessor calls on either side |
| d_a_gy | 42/47 | checkGetItem 2D 1/1; ev.getEventReg 7EFF 1/1; ev.setEventReg 7EFF 1/1 |
| d_a_himo2 | 2/20 | ev.isEventBit 420 2/2; ev.onEventBit 420 1/1; ev.onEventBit 540 1/1; ev.onEventBit 580 1/1 |
| d_a_icelift | 13/18 | info.isSwitch ? 1/1 |
| d_a_klft | 10/12 | info.isSwitch ? 1/1; info.offSwitch ? 1/1; info.onSwitch ? 1/1 |
| d_a_mant | 7/10 | no save accessor calls on either side |
| d_a_mgameboard | 14/17 | ev.getEventReg BEFF 1/1 |
| d_a_mozo | 15/30 | no save accessor calls on either side |
| d_a_mt | 29/31 | info.isSwitch ? 3/3; info.onActor ? 1/2; info.onSwitch ? 1/2 |
| d_a_npc_ac1 | 60/65 | ev.getEventReg B8FF 1/1; ev.isEventBit 1580 3/3; ev.isEventBit 2E04 1/1; ev.onEventBit 3F02 1/1; ev.setEventReg B8FF 2/2 |
| d_a_npc_aj1 | 89/94 | info.isSwitch ? 1/1; info.onSwitch ? 1/1; ev.isEventBit 1 2/2; ev.isEventBit 2A20 2/2; ev.isEventBit 2A80 2/2; ev.isEventBit 3701 1/1; ev.isEventBit 3702 1/1; ev.isEventBit 3704 2/2; ev.isEventBit 3708 1/1; ev.isEventBit 502 1/1; ev.isEventBit 504 2/2; ev.isEventBit 508 1/1; ev.isEventBit 510 1/1; ev.isEventBit 520 2/2; ev.isEventBit B20 1/1; ev.isEventBit E20 2/2; ev.onEventBit 3701 1/1; ev.onEventBit 3702 1/1; ev.onEventBit 3704 2/2; ev.onEventBit 3708 1/1; ev.onEventBit 502 1/1; ev.onEventBit 504 1/1; ev.onEventBit 508 1/1; ev.onEventBit 510 1/1 |
| d_a_npc_auction | 41/42 | checkGetItem 69 1/1; bag_item.setReserveItemEmpty ? 1/1; ev.isEventBit 1002 1/1; ev.isEventBit 1004 2/2; ev.isEventBit 1008 2/2; **ev.isEventBit 1020 1/0**; **ev.isEventBit 1040 1/0**; **ev.isEventBit 1080 1/0**; ev.isEventBit 1404 1/1; ev.isEventBit A02 1/1; **ev.isEventBit F01 1/0**; ev.onEventBit 1002 1/1; ev.onEventBit 1408 1/1 |
| d_a_npc_bj1 | 119/124 | collect.isSymbol 2 5/5; get_item.isItem 6,0 1/1; ev.getEventReg 96FF 2/1; ev.getEventReg 97FF 3/1; ev.getEventReg 98FF 2/1; ev.getEventReg 99FF 2/1; **ev.getEventReg 9AFF 1/0**; ev.getEventReg 9EFF 2/1; **ev.getEventReg ? 0/1**; ev.isEventBit 102 1/1; ev.isEventBit 1801 4/4; ev.isEventBit 1B80 3/2; ev.isEventBit 1C80 1/1; ev.isEventBit 2902 1/1; ev.isEventBit 2E10 1/1; ev.isEventBit 604 1/1; ev.isEventBit 904 1/1; ev.isEventBit 920 1/1; ev.isEventBit C02 1/1; ev.isEventBit C04 1/1; ev.isEventBit C08 1/1; ev.isEventBit C10 1/1; ev.isEventBit C20 1/1; ev.isEventBit C80 1/1; ev.isEventBit D08 2/2; ev.isEventBit D10 1/1; ev.isEventBit D20 1/1; ev.isEventBit D40 1/1; ev.onEventBit 1B80 1/1; ev.onEventBit 1C80 1/1; ev.onEventBit 1D40 1/1; ev.onEventBit 2902 1/1; ev.onEventBit 2E10 1/1; ev.onEventBit 604 1/1; ev.onEventBit 904 1/1; ev.onEventBit 920 1/1; ev.onEventBit C02 1/1; ev.onEventBit C04 1/1; ev.onEventBit C08 1/1; ev.onEventBit C10 1/1; ev.onEventBit C20 1/1; ev.onEventBit C80 1/1; ev.onEventBit D08 1/1; ev.onEventBit D10 1/1; ev.onEventBit D20 1/1; ev.onEventBit D40 1/1; ev.setEventReg 96FF 1/1; ev.setEventReg 97FF 1/1; ev.setEventReg 98FF 1/1; ev.setEventReg 99FF 1/1 |
| d_a_npc_bmcon1 | 54/59 | ev.getEventReg A7FF 1/1; ev.getEventReg A8FF 1/1; ev.isEventBit 2901 2/2; ev.isEventBit 2A40 2/2; ev.isEventBit 2B40 3/3; ev.onEventBit 2901 1/5; ev.onEventBit 2A40 1/1; ev.onEventBit 2B40 1/1; ev.setEventReg A7FF 1/1; ev.setEventReg A8FF 1/1; tmp.getEventReg F903 2/2; tmp.getEventReg FAFF 1/1; tmp.getEventReg FBFF 1/1; tmp.isEventBit 210 1/1; tmp.offEventBit 210 1/1; tmp.onEventBit 210 1/5; tmp.setEventReg F903 1/2; tmp.setEventReg FAFF 1/1; tmp.setEventReg FBFF 1/1 |
| d_a_npc_bms1 | 45/50 | ev.isEventBit A02 9/8 |
| d_a_npc_co1 | 67/72 | bag_item.setReserveItemEmpty ? 1/1; collect.isSymbol 1 1/1; ev.isEventBit 1810 1/1; ev.isEventBit F04 2/2; ev.isEventBit F08 1/1; ev.onEventBit 1810 1/1; ev.onEventBit F04 2/2; ev.onEventBit F08 1/1 |
| d_a_npc_de1 | 52/57 | checkGetItem 20 1/1; isStageBossEnemy 6 1/1; collect.isSymbol 2 1/1; ev.isEventBit 102 1/2; ev.isEventBit 1801 2/2; ev.isEventBit 1820 1/1; ev.isEventBit 1C20 1/1; ev.isEventBit 1C40 1/1; ev.isEventBit 1D40 1/1; **ev.isEventBit 3940 1/0**; ev.isEventBit E40 1/1; ev.isEventBit E80 1/1; ev.onEventBit 1801 1/1; ev.onEventBit 1C20 1/1; ev.onEventBit 3940 1/1; ev.onEventBit E40 1/1; ev.onEventBit E80 1/1; tmp.onEventBit 308 1/1 |
| d_a_npc_ds1 | 53/58 | ev.isEventBit 1120 3/3; ev.isEventBit D02 1/1; ev.isEventBit D04 1/1; ev.onEventBit 1120 2/2; ev.onEventBit D02 2/2; ev.onEventBit D04 2/2 |
| d_a_npc_gk1 | 57/62 | ev.isEventBit 1640 2/2; ev.isEventBit 1680 1/1; ev.isEventBit 2D01 1/1; ev.isEventBit B02 1/1; ev.isEventBit E08 1/1; ev.onEventBit 1640 1/1; ev.onEventBit 1680 1/1 |
| d_a_npc_gp1 | 66/71 | bag_item.checkReserveItem 9B 1/1; ev.getEventReg C5FF 2/2; ev.isEventBit 1420 1/1; ev.isEventBit 1501 2/2; ev.isEventBit 1804 1/1; ev.isEventBit 1808 1/1; ev.isEventBit 1920 1/1; ev.isEventBit 2D01 1/1; ev.onEventBit 1420 1/1; ev.onEventBit 1501 1/1; ev.onEventBit 1804 1/1; ev.onEventBit 1808 1/1; ev.onEventBit 1920 1/1; ev.setEventReg C5FF 1/1 |
| d_a_npc_kf1 | 90/95 | info.isSwitch ? 1/1; collect.isSymbol 0 1/1; ev.getEventReg BCFF 2/2; ev.isEventBit 2780 2/2; ev.isEventBit 2D01 1/1; ev.isEventBit A02 1/1; ev.isEventBit B02 1/1; ev.onEventBit 2780 1/1; ev.onEventBit B02 1/1; ev.setEventReg BCFF 1/1 |
| d_a_npc_kg1 | 25/27 | ev.getEventReg BEFF 1/1; ev.getEventReg FE07 2/2; ev.getEventReg FF07 2/2; ev.isEventBit E04 1/1; ev.onEventBit 2540 1/1; ev.onEventBit E04 1/1; ev.setEventReg BEFF 1/1; ev.setEventReg FE07 1/1; ev.setEventReg FF07 1/1; tmp.isEventBit 101 1/1; tmp.onEventBit 101 1/1 |
| d_a_npc_kg2 | 34/39 | ev.getEventReg B703 4/4; ev.isEventBit 2508 1/1; ev.isEventBit 2520 1/1; ev.isEventBit 2540 1/1; ev.onEventBit 2508 1/1; ev.onEventBit 2520 1/1; ev.setEventReg B703 1/1; tmp.isEventBit 102 1/1; tmp.onEventBit 102 1/1 |
| d_a_npc_kk1 | 112/117 | info.isSwitch ? 1/1; ev.isEventBit 2D01 1/1; ev.isEventBit E08 2/2; ev.isEventBit E10 1/1; ev.onEventBit E08 1/1; ev.onEventBit E10 1/1 |
| d_a_npc_ko1 | 134/139 | ev.getEventReg BFFF 2/2; ev.isEventBit 104 2/2; ev.isEventBit 208 1/1; ev.isEventBit 210 1/1; ev.isEventBit 220 1/1; ev.isEventBit 240 1/1; ev.isEventBit 2A80 2/2; ev.isEventBit 2C04 1/1; ev.isEventBit 3101 1/1; ev.isEventBit 3340 1/1; ev.isEventBit 3801 1/1; ev.isEventBit 520 4/4; ev.isEventBit E20 4/4; ev.onEventBit 104 1/1; ev.onEventBit 208 1/1; ev.onEventBit 210 1/1; ev.onEventBit 220 1/1; ev.onEventBit 240 1/1; ev.onEventBit 2C04 1/1; ev.onEventBit 3101 1/1; ev.onEventBit 3340 1/1; ev.onEventBit 3801 1/1 |
| d_a_npc_kp1 | 46/51 | bag_item.checkReserveItem 9B 1/1; bag_item.setReserveItemEmpty ? 1/1; get_bag_item.isBeast 0 1/1; get_bag_item.isReserve E 1/1; get_bag_item.isReserve F 1/1; ev.getEventReg CCFF 1/1; ev.isEventBit 2D01 1/1; ev.setEventReg CCFF 1/1 |
| d_a_npc_ob1 | 73/78 | ev.getEventReg B6FF 4/4; ev.isEventBit 2A80 1/1; ev.isEventBit 2C20 1/1; ev.isEventBit 2C40 1/1; ev.isEventBit 2C80 1/1; ev.isEventBit 302 1/1; ev.isEventBit 304 2/2; ev.isEventBit 308 1/1; ev.isEventBit 520 3/3; ev.isEventBit E20 1/1; ev.onEventBit 2C20 1/1; ev.onEventBit 2C40 1/1; ev.onEventBit 2C80 1/1; ev.onEventBit 302 1/1; ev.onEventBit 304 1/1; ev.onEventBit 308 1/1; ev.setEventReg B6FF 1/1 |
| d_a_npc_p2 | 92/97 | info.isSwitch ? 1/1; info.offSwitch ? 2/2; info.onSwitch ? 2/2; ev.isEventBit 1502 1/1; ev.isEventBit 1A04 2/2; ev.isEventBit 701 1/1; ev.isEventBit 702 1/1; ev.isEventBit 704 1/1; ev.isEventBit 710 1/1; ev.isEventBit 720 3/3; ev.isEventBit 808 10/9; ev.isEventBit 940 1/1; ev.isEventBit F02 3/3; ev.onEventBit 1502 1/1; ev.onEventBit 1A04 1/1; ev.onEventBit 701 1/1; ev.onEventBit 702 1/1; ev.onEventBit 704 1/1; ev.onEventBit 710 1/1; ev.onEventBit 720 1/1; ev.onEventBit 808 1/1; ev.onEventBit 940 1/1; ev.onEventBit F02 1/1 |
| d_a_npc_pf1 | 66/71 | ev.isEventBit 2D01 1/1; ev.isEventBit B04 3/3; ev.onEventBit B04 1/1 |
| d_a_npc_pm1 | 43/48 | no save accessor calls on either side |
| d_a_npc_sarace | 26/31 | ev.getEventReg AAFF 1/1; ev.isEventBit 2808 1/1; ev.isEventBit 2810 1/1; ev.isEventBit 2820 1/1; ev.isEventBit 2840 1/1; ev.offEventBit 2820 1/1; ev.onEventBit 2808 1/1; ev.onEventBit 2810 1/1; ev.onEventBit 2820 1/1; ev.onEventBit 2840 1/1; ev.setEventReg AAFF 1/1 |
| d_a_npc_uk | 65/70 | checkGetItem 23 2/2; checkGetItem 26 2/2; ev.isEventBit 1208 2/2; ev.isEventBit 1340 1/1; ev.isEventBit 1E02 2/2; ev.isEventBit 1F80 2/2; ev.isEventBit ? 1/1; ev.onEventBit 1602 1/1; ev.onEventBit 1E04 1/1; ev.onEventBit ? 1/1; tmp.isEventBit 40 3/3; tmp.isEventBit ? 3/3; tmp.onEventBit ? 2/2 |
| d_a_npc_ym1 | 81/86 | ev.getEventReg BFFF 2/2; ev.isEventBit 10 1/1; ev.isEventBit 20 1/1; ev.isEventBit 2904 1/1; ev.isEventBit 2A80 1/1; ev.isEventBit 3004 1/1; ev.isEventBit 3140 1/1; ev.isEventBit 3402 5/5; ev.isEventBit 3540 1/1; ev.isEventBit 3580 1/1; ev.isEventBit 520 6/6; ev.isEventBit 8 1/1; ev.isEventBit 80 1/1; ev.isEventBit B01 1/1; ev.isEventBit E20 2/2; ev.onEventBit 10 1/1; ev.onEventBit 20 1/1; ev.onEventBit 2904 1/1; ev.onEventBit 3140 1/1; ev.onEventBit 3540 1/1; ev.onEventBit 3580 1/1; ev.onEventBit 8 1/1; ev.onEventBit 80 1/1; ev.onEventBit B01 1/1 |
| d_a_npc_yw1 | 77/82 | ev.isEventBit 1 5/7; ev.isEventBit 120 1/1; ev.isEventBit 140 2/2; ev.isEventBit 180 1/1; ev.isEventBit 2A20 4/4; ev.isEventBit 2A80 1/1; ev.isEventBit 3A40 1/1; ev.isEventBit 520 4/4; ev.isEventBit E20 1/1; ev.onEventBit 120 1/1; ev.onEventBit 140 1/1; ev.onEventBit 180 1/1; ev.onEventBit 3A40 1/1 |
| d_a_npc_zk1 | 52/57 | collect.isSymbol 1 1/1; ev.isEventBit 1802 3/3; ev.isEventBit 1A80 1/1; ev.isEventBit 1C01 2/2; ev.isEventBit 1D80 1/1; ev.onEventBit 1802 1/1; ev.onEventBit 1C01 1/1; ev.onEventBit 1D80 1/1 |
| d_a_nz | 32/34 | no save accessor calls on either side |
| d_a_obj_Itnak | 10/15 | info.isSwitch ? 2/2 |
| d_a_obj_Vds | 24/29 | info.isSwitch ? 2/2 |
| d_a_obj_ashut | 20/25 | info.isSwitch ? 4/4 |
| d_a_obj_aygr | 9/14 | no save accessor calls on either side |
| d_a_obj_balancelift | 13/15 | no save accessor calls on either side |
| d_a_obj_buoyflag | 21/21 | no save accessor calls on either side |
| d_a_obj_ekskz | 9/14 | info.isSwitch ? 1/1; info.onSwitch ? 1/1 |
| d_a_obj_firewall | 24/29 | info.isSwitch ? 1/1; ev.isEventBit 3520 1/1; ev.onEventBit 2C01 1/2; ev.onEventBit 3520 1/1 |
| d_a_obj_flame | 31/31 | info.offSwitch ? 1/1; info.onSwitch ? 1/1 |
| d_a_obj_ftree | 69/73 | collect.isSymbol 2 1/1; ev.getEventReg 9AFF 1/1; ev.getEventReg 9B07 1/1; ev.getEventReg 9EFF 3/3; ev.isEventBit 102 3/3; ev.isEventBit 2E20 1/1; ev.onEventBit 102 2/2; **ev.onEventBit 2E20 1/0**; ev.setEventReg 9AFF 1/1; ev.setEventReg 9B07 2/2; ev.setEventReg 9EFF 2/2 |
| d_a_obj_hami2 | 16/21 | info.isSwitch ? 3/3 |
| d_a_obj_htetu1 | 12/17 | info.isSwitch ? 2/2 |
| d_a_obj_kanoke | 24/29 | info.isSwitch ? 2/2; info.onSwitch ? 1/1 |
| d_a_obj_light | 19/24 | info.onSwitch 5D 1/1; ev.isEventBit 1C02 4/4; ev.offEventBit 1C02 2/1; ev.onEventBit 1C02 3/3 |
| d_a_obj_magmarock | 27/27 | ev.isEventBit 380 1/1; ev.onEventBit 380 1/1 |
| d_a_obj_msdan | 3/8 | info.isSwitch ? 2/3 |
| d_a_obj_search | 50/50 | **info.isSwitch 2A 0/1**; info.isSwitch ? 2/2; info.onSwitch ? 2/2; ev.isEventBit 201 2/2; ev.onEventBit 201 1/1; ev.onEventBit 340 1/1 |
| d_a_obj_swflat | 11/16 | info.isSwitch ? 3/4; info.offSwitch ? 3/3; info.onSwitch ? 3/3 |
| d_a_obj_tapestry | 62/67 | info.isSwitch ? 1/1; info.onSwitch ? 1/1 |
| d_a_obj_tntrap | 28/33 | info.isSwitch ? 8/8; info.onSwitch ? 1/1; ev.isEventBit 2C01 1/1; ev.isEventBit 3A04 1/1; ev.onEventBit 3B40 1/1 |
| d_a_obj_trap | 20/25 | no save accessor calls on either side |
| d_a_obj_tribox | 66/71 | info.isSwitch ? 1/1; info.onSwitch ? 1/1; ev.isEventBit 3820 1/1 |
| d_a_obj_try | 43/48 | info.isSwitch ? 1/1; tmp.offEventBit 108 2/2; tmp.offEventBit 110 2/2; tmp.onEventBit 108 1/1; tmp.onEventBit 110 1/1 |
| d_a_obj_vtil | 33/38 | isStageTbox ?,F 1/1 |
| d_a_oq | 19/21 | checkGetItem 2D 1/1; **isStageBossEnemy 4 0/1**; ev.getEventReg 7EFF 1/1; ev.setEventReg 7EFF 1/1 |
| d_a_ph | 31/33 | checkGetItem 2D 2/2; info.onActor ? 1/2; ev.getEventReg 7EFF 1/1; ev.setEventReg 7EFF 1/1 |
| d_a_pt | 20/22 | info.isSwitch ? 7/7; info.onActor ? 2/2; info.onSwitch ? 3/2 |
| d_a_pw | 24/31 | checkGetItem 3C 1/1; info.onActor ? 1/1 |
| d_a_pz | 73/78 | ev.isEventBit 3520 1/1 |
| d_a_ss | 13/15 | info.isSwitch ? 1/1; info.onSwitch ? 1/1; ev.onEventBit 2B20 1/3 |
| d_a_tag_kf1 | 27/32 | no save accessor calls on either side |
| d_a_warpmj | 23/28 | ev.isEventBit 3D02 1/1 |
| d_a_waterfall | 20/24 | **info.isSwitch ? 3/0** |
| d_a_wz | 25/27 | checkGetItem 3C 1/1; info.isSwitch ? 3/3; info.onActor ? 3/2; info.onSwitch ? 4/3 |
| d_camera | 9/128 | memBit.onVisitedRoom ? 1/1 |
| d_demo | 2/65 | **ev.onEventBit E20 0/1** |
| d_ev_camera | 39/39 | no save accessor calls on either side |
| d_map | 14/121 | **memBit.isDungeonItem 0 1/0**; **memBit.isDungeonItem 1 4/0**; **memBit.isVisitedRoom ? 2/0**; **map.isSaveArriveGridForAgb ? 1/0**; map.onSaveArriveGridForAgb ? 1/1 |
| d_message_paper | 55/50 | no save accessor calls on either side |
| d_minigame_terminater | 30/30 | no save accessor calls on either side |
| d_particle | 2/86 | no save accessor calls on either side |
