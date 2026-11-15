# Audit of the "rewards" undo edits (code reading, HD source)

Verdict: every undo leaves its reward obtainable exactly once in any later state.

- Opening a chest writes its chest bit and at most one switch (`d_a_tbox.cpp:737-752`); nothing clears a chest
  bit; no other actor reads the bits the converter clears. Switches 128-255 are not saved.
- Triforce chests (TF_04, TF_01, TF_02, Cave09 room 20): type 6, appear switch saved, so the closed chest is
  visible on arrival. Rooms on the way use unsaved switches and are played again. No keys.
- Ghost Ship: at register 0x8803 == 3 the ship is never created (`d_a_ghostship.cpp:309`). The only writer sets
  3 when the chest scene ends, so 0 is the state of a file that never boarded. Boarding needs the Ghost Ship
  Chart (collect map 36), the same item on the GameCube, not consumed.
- Lookout chests: Horseshoe appears when its floor button is pressed again (unsaved switch); Star Belt is
  visible at once. Pawprint cave chest (type 2) appears when the room has no enemies; they return each visit.
- Floor-50 chest: type 0, visible. Item 0x43 is given nowhere else.
- Mrs. Marie: 0x1C04 is used only by `d_a_npc_ho.cpp`. With it clear, 0x1C08 set and register 0xC0FF >= 40,
  showing a Joy Pendant gives item 0xF8 and sets 0x1C04, also at the register cap of 99.
- Lenzo: at register 5 a picture with result 3 is accepted and item 0x26 given. The picture needs Anton and
  Linda on the street, there while register 0xB907 < 2, which normal play cannot pass without the Deluxe
  Picto Box (the converter does not offer `rewards` otherwise).
- Collect map 8: a completed chart's salvage point is not registered (`d_salvage.cpp:57`); item 0xF7 comes
  only from the Cave07 chest.

Not determined: message and event data files were not scanned for these flags.
