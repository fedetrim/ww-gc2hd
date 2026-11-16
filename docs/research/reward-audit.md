# Reward audit: GameCube (GZLE01) vs Wind Waker HD (USA)

Result: no place gives a different reward in the two games beyond the list in `docs/DIFFERENCES.md` 3.2.

Method (scripts in `audit/rewards/`; outputs are regenerated under `research/out/`):
- Stage data: every entry of chunk types ACTR, SCOB, TRES, TGOB, TGSC, TGDR, DOOR and PLYR in all 130 common
  stages, byte-wise (`stage_all.py`, `stage_cmp.py` -> `stage_cmp.txt`, `stage_types.txt`): 18,904 GameCube
  and 18,824 HD entries, 18,785 identical. Reward differences: the 9 chests and the 5 chart salvage points
  (4 instances each). The other 469 salvage instances, 237 item actors and all fixed-drop pots are identical.
- Randomizer tables (wwrando, twwhd-rando): 243 locations paired through the stage entity, 78 through code
  (75 by name, 3 by hand)
  (`rando_final.txt`). Differing: the same chests and salvage points, Mrs. Marie, Lenzo (two steps), Tingle's
  first gift, the pig game (HD: Treasure Chart 42 while not owned, else the GameCube Purple Rupee).
- Shops: every `d_shop` item set identical in `main.dol` and `cking.rpx` (`shops_*.py`). Auction: same four
  entries and bits, plus the Swift Sail (obtained = inventory slot 1 holds 0x77).
- Item get / get-check functions: same identity per item id except 0x14 and 0x77 (`item_tables.py`).
- Totals reconcile (`totals.txt`): Pieces of Heart 32/32 stage sources (-1 floor 50, +1 Two-Eye Reef).

GameCube only: 13 Tingle Tuner triggers (`agbTBOX`). What they reveal is rupees and consumables (one Yellow
Rupee chest in `M_NewD2`, Purple Rupee items, pots); HD keeps the data but nothing can trigger it.

Not a reward difference: `SirenMB` Room23 `Hys2` sets switch 0x18 in HD (GameCube: none), a new setter of an
existing switch; chest model changed on the three chests that hold charts; event 0x2B04 (a hint) is set
under different conditions.

Not covered: message text and prices, `ActorDat.bin` contents, the order of flag writes inside one function.
