"""Packed per-file save data (0x768 bytes) shared by Wind Waker (GameCube) and Wind Waker HD.

Both games serialize the same blocks, with the same sizes, in the same order:
  GameCube: dSv_info_c::memory_to_card  (zeldaret/tww src/d/d_save.cpp, include/d/d_save.h)
  HD:       dSv_info_c::memory_to_card  025BA9FC (ZeldaWWHDDecomp/wwhd wwhd_src/d/d_save_5.cpp)
All integers are big-endian on both consoles.
"""

SAVE_SIZE = 0x768

# (field name, size) in order; "_" prefixed names are padding / fields no code reads.
_STATUS_A = [
    ("max_life", 2), ("life", 2), ("rupee", 2), ("_field_6", 2), ("_field_8", 1),
    ("select_item", 5), ("select_equip", 4), ("wallet_size", 1), ("max_magic", 1),
    ("magic", 1), ("_field_15", 1), ("_field_16", 1), ("_pad_17", 1),
]
_ITEM = [("slot%02d" % i, 1) for i in range(21)]
_ITEM_RECORD2 = [("picture_num", 1), ("arrow_num", 1), ("bomb_num", 1)]
_ITEM_MAX2 = [("reserved1_max", 1), ("arrow_max", 1), ("bomb_max", 1)]
_BAG_ITEM = [("beast", 8), ("bait", 8), ("reserve", 8)]
_BAG_RECORD = [("beast_num", 8), ("bait_num", 8), ("reserve_num", 8)]
_COLLECT = [("collect", 8), ("_field_8", 1), ("tact", 1), ("triforce", 1), ("symbol", 1), ("_field_c", 1)]
_MEMBIT = [("tbox", 4), ("switch", 16), ("item", 4), ("visited_room", 8), ("key_num", 1),
           ("dungeon_item", 1), ("_pad_22", 2)]

_BLOCKS = [
    ("status_a", _STATUS_A),
    ("status_b", [("date_ipl", 8), ("_field_8", 4), ("time", 4), ("date", 2),
                  ("tact_wind_x", 2), ("tact_wind_y", 2), ("_pad_16", 2)]),
    ("return_place", [("stage", 8), ("room", 1), ("point", 1), ("_unk_a", 1), ("_unk_b", 1)]),
    ("item", _ITEM),
    ("get_item", _ITEM),
    ("item_record", [("timer", 2)] + _ITEM_RECORD2 + [("bottle_num", 3)]),
    ("item_max", _ITEM_MAX2 + [("_field_3", 5)]),
    ("bag_item", _BAG_ITEM),
    ("get_bag_item", [("reserve_flags", 4), ("beast_flags", 1), ("bait_flags", 1), ("_unk_6", 6)]),
    ("bag_item_record", _BAG_RECORD),
    ("collect", _COLLECT),
    ("map", [("arrive_grid", 16), ("get_map", 16), ("open_map", 16), ("complete_map", 16),
             ("fmap_bits", 49), ("_field_71", 16), ("triforce_bits", 1), ("_field_82", 2)]),
    ("info", [("_field_0", 16), ("save_count", 2), ("death_count", 2), ("player_name", 17),
              ("_name_25", 17), ("_name_36", 17), ("puzzle", 17), ("clear_count", 1),
              ("random_salvage", 1), ("_field_5a", 2)]),
    ("config", [("ruby", 1), ("sound_mode", 1), ("attention_type", 1), ("vibration", 1), ("_field_4", 1)]),
    ("priest", [("pos", 12), ("angle", 2), ("room", 1), ("flag", 1)]),
]
_STATUS_C = ([("a_" + n, s) for n, s in _STATUS_A] + [("item%02d" % i, 1) for i in range(21)] +
             _ITEM_RECORD2 + _ITEM_MAX2 + _BAG_ITEM + _BAG_RECORD + _COLLECT)
_BLOCKS += [("status_c%d" % i, _STATUS_C) for i in range(4)]
_BLOCKS += [("memory%02d" % i, _MEMBIT) for i in range(16)]
_BLOCKS += [("ocean", [("bits", 0x64)]), ("event", [("flags", 0x100)]), ("reserve", [("bytes", 0x50)])]

BLOCK_SIZES = {
    "status_a": 0x18, "status_b": 0x18, "return_place": 0xC, "item": 0x15, "get_item": 0x15,
    "item_record": 8, "item_max": 8, "bag_item": 0x18, "get_bag_item": 0xC, "bag_item_record": 0x18,
    "collect": 0xD, "map": 0x84, "info": 0x5C, "config": 5, "priest": 0x10, "ocean": 0x64,
    "event": 0x100, "reserve": 0x50,
}

FIELDS = {}   # "block.field" -> (offset, size)
BLOCKS = {}   # "block" -> (offset, size)


def _build():
    off = 0
    for block, fields in _BLOCKS:
        start = off
        for name, size in fields:
            FIELDS[block + "." + name] = (off, size)
            off += size
        BLOCKS[block] = (start, off - start)
        expect = (0x70 if block.startswith("status_c") else
                  0x24 if block.startswith("memory") else BLOCK_SIZES[block])
        assert off - start == expect, (block, hex(off - start), hex(expect))
    assert off == SAVE_SIZE, hex(off)


_build()

# Stage memory slots (dSv_save_c::SaveStageTbl)
STAGE_NAMES = ["Sea", "Sea (alt)", "Forsaken Fortress", "Dragon Roost Cavern", "Forbidden Woods",
               "Tower of the Gods", "Earth Temple", "Wind Temple", "Ganon's Tower", "Hyrule",
               "Ship interiors", "Houses / misc", "Caves", "Caves / ghost ship", "Blue Chu Jelly", "Test"]

# Inventory slots (dInvSlot_*): index into item / get_item
(SLOT_TELESCOPE, SLOT_SAIL, SLOT_WIND_WAKER, SLOT_GRAPPLING, SLOT_SPOILS_BAG, SLOT_BOOMERANG,
 SLOT_DEKU_LEAF, SLOT_TINGLE, SLOT_CAMERA, SLOT_IRON_BOOTS, SLOT_MAGIC_ARMOR, SLOT_BAIT_BAG,
 SLOT_BOW, SLOT_BOMBS, SLOT_BOTTLE0, SLOT_BOTTLE1, SLOT_BOTTLE2, SLOT_BOTTLE3, SLOT_DELIVERY_BAG,
 SLOT_HOOKSHOT, SLOT_HAMMER) = range(21)

NO_ITEM = 0xFF


class Save:
    """A mutable 0x768-byte save block with named-field access."""

    def __init__(self, data):
        if len(data) != SAVE_SIZE:
            raise ValueError("save block must be 0x768 bytes, got %#x" % len(data))
        self.data = bytearray(data)

    def copy(self):
        return Save(self.data)

    def raw(self, name):
        off, size = FIELDS[name]
        return bytes(self.data[off:off + size])

    def set_raw(self, name, value):
        off, size = FIELDS[name]
        if len(value) != size:
            raise ValueError("%s is %d bytes, got %d" % (name, size, len(value)))
        self.data[off:off + size] = value

    def u(self, name):
        return int.from_bytes(self.raw(name), "big")

    def set_u(self, name, value):
        self.set_raw(name, value.to_bytes(FIELDS[name][1], "big"))

    def block(self, name):
        off, size = BLOCKS[name]
        return bytes(self.data[off:off + size])

    # event flags: 0xBBMM = byte BB of the event block, mask MM (dSv_event_c)
    def event_bit(self, flag):
        return bool(self.data[FIELDS["event.flags"][0] + (flag >> 8)] & (flag & 0xFF))

    def set_event_bit(self, flag, on=True):
        i = FIELDS["event.flags"][0] + (flag >> 8)
        self.data[i] = (self.data[i] | (flag & 0xFF)) if on else (self.data[i] & ~(flag & 0xFF) & 0xFF)

    def event_reg(self, reg):
        return self.data[FIELDS["event.flags"][0] + (reg >> 8)] & (reg & 0xFF)

    def set_event_reg(self, reg, value):
        i = FIELDS["event.flags"][0] + (reg >> 8)
        mask = reg & 0xFF
        self.data[i] = (self.data[i] & ~mask & 0xFF) | (value & mask)

    def is_new(self):
        """GameCube file select treats a file without a player name as empty."""
        return self.raw("info.player_name")[0] == 0

    def __bytes__(self):
        return bytes(self.data)


# map.triforce_bits of a new HD file, forced again on every load: the bits of collect maps 2, 4, 6, 7, 8
HD_TRIFORCE_PRESET = 0xEA
# rupee limit by wallet size (HD: d_meter_02.cpp:282)
WALLET_GC = (200, 1000, 5000)
WALLET_HD = (500, 1000, 5000)

# item numbers the conversion and the load model both name
ITEM_TINGLE = 0x21          # Tingle Tuner (GameCube) / Tingle Bottle (HD)
ITEM_WIND_WAKER = 0x22
ITEM_PICTO_BOX = 0x23
ITEM_DELUXE_PICTO_BOX = 0x26
ITEM_SWIFT_SAIL = 0x77
ITEM_SAIL = 0x78


def item(save, slot):
    """Item number in an inventory slot (0xFF: none)."""
    return save.data[FIELDS["item.slot%02d" % slot][0]]


def get_bits(save, slot):
    """Ownership bits of an inventory slot."""
    return save.data[FIELDS["get_item.slot%02d" % slot][0]]


def chart_bit(words, n):
    """Collect map n (1-based) in the 16 bytes of one of the chart flag sets (get / open / complete)."""
    i = 4 * ((n - 1) >> 5)
    return bool(int.from_bytes(words[i:i + 4], "big") >> ((n - 1) & 31) & 1)
