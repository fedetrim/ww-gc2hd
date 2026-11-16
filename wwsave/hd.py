"""Wind Waker HD (Wii U) save file `cking.sav`, 8966 bytes, big-endian.

Layout (ZeldaWWHDDecomp/wwhd: wwhd_src/d/d_menu_save_card.cpp, d_menu_save_storage.cpp,
hd_save_holders.cpp; checked here against real console and Cemu saves):

  0x0000  3 x 0xA94   per Quest Log: 0x768 bytes of save data (same packed layout as GameCube),
                      zero up to 0xA8C, then u32 byte sum and u32 complement sum of those 0xA8C bytes
  0x1FBC  3 x 16      options record   (hdSaveSlotFlags_c)
  0x1FEC  3 x 4       pair record      (hdSavePair_c)
  0x1FF8  3 x 20      HD inventory     (hdSaveInventory_c)
  0x2034  3 x 18      player name, UTF-16BE, up to 8 characters + terminator
  0x206A  3 x 220     play log         (hdSavePlayLog_c)
  0x22FE  u32         format word (4)
  0x2302  u32         CRC-32 of the five HD sections (0x342 bytes), with the quirk that each name
                      contributes only its first (characters + 1) BYTES, zero padded to 18
"""
import collections
import struct
import zlib

from . import layout
from .layout import SAVE_SIZE, Save

SLOT_SIZE = 0xA94
SLOT_SUMMED = 0xA8C
SECTIONS = [("options", 16), ("pair", 4), ("inventory", 20), ("name", 18), ("playlog", 220)]
EXTRA_SIZE = 3 * sum(size for _, size in SECTIONS)
FORMAT_WORD = 4
FILE_SIZE = 3 * SLOT_SIZE + EXTRA_SIZE + 8
assert EXTRA_SIZE == 0x342 and FILE_SIZE == 8966
NAME_CHARS = 8

# options record (hdSaveSlotFlags_c) byte indices
OPT_LOCK_ON = 0       # Z-targeting: 0 hold, 1 switch (GameCube: config.attention_type)
OPT_BUILD = 3         # default of the game build: 0 in files of the USA game, 1 in files of the European
                      # one, in every Quest Log, used or empty; no reader found (docs/DIFFERENCES.md, 4b)
OPT_LANGUAGE = 4      # PAL language, written by the game from the console setting
OPT_GYRO = 5          # 1 = motion aiming enabled (default of a fresh file)
OPT_HERO_MODE = 6     # 1 = Hero Mode


# HD inventory record (hdSaveInventory_c)
INV_ENTRIES = 4       # Carlov's figurine queue, 12 bytes (figure table indices)
INV_COUNT = 16        # number of queued figurines
INV_AUCTION_ITEM = 17 # auction item re-offered after losing a bid
# play log (hdSavePlayLog_c): 0x18 bytes of map-view state, then 49 x u32 per sea sector
PLAYLOG_FLAGS = 0x18  # bit 0: this sector's Fishman has drawn the chart
PRECHARTED_SECTORS = (0, 10, 43)   # Forsaken Fortress, Windfall, Outset: charted in a new file


# The game builds a file can be written for. `build` (options byte OPT_BUILD) and `ruby` (config.ruby) are
# the defaults the build gives a Quest Log when it clears it; they go together in every real file, per
# Quest Log. Nothing else in the file depends on the build.
Region = collections.namedtuple("Region", "game title build ruby")
REGIONS = {"usa": Region("USA", "0005000010143500", 0, 1),
           "europe": Region("European", "0005000010143600", 1, 0)}
DEFAULT_REGION = "usa"


def set_region(slots, extras, region):
    """Give all three Quest Logs, used or empty, the defaults of that build of the game."""
    target = REGIONS[region]
    for save, extra in zip(slots, extras):
        save.set_u("config.ruby", target.ruby)
        options = bytearray(extra["options"])
        options[OPT_BUILD] = target.build
        extra["options"] = bytes(options)


def slot_region(save, extra):
    """The build whose defaults one Quest Log carries: 'usa' | 'europe', or None for another pair."""
    for region, r in REGIONS.items():
        if (extra["options"][OPT_BUILD], save.u("config.ruby")) == (r.build, r.ruby):
            return region
    return None


def region_of(hd_file):
    """'usa' | 'europe' when all three Quest Logs carry that build's defaults, else None (a file whose
    Quest Logs were created by different builds, which the ports can produce)."""
    found = {slot_region(s, e) for s, e in zip(hd_file.slots, hd_file.extras)}
    return found.pop() if len(found) == 1 else None


class HdError(Exception):
    pass


def slot_checksum(block):
    """SaveMgr::checksum 02721AC4: (sum of bytes, sum of ~byte as u32) over 0xA8C bytes."""
    s = sum(block[:SLOT_SUMMED])
    return s & 0xFFFFFFFF, (SLOT_SUMMED * 0xFFFFFFFF - s) & 0xFFFFFFFF


def encode_name(name):
    b = name.encode("utf-16-be")
    if len(b) > 2 * NAME_CHARS:
        raise HdError("player name %r is longer than %d characters" % (name, NAME_CHARS))
    return b.ljust(18, b"\0")


def decode_name(raw):
    chars = []
    for i in range(0, 18, 2):
        if raw[i:i + 2] == b"\0\0":
            break
        chars.append(raw[i:i + 2].decode("utf-16-be", "replace"))
    return "".join(chars)


def default_extra(name="Link"):
    """HD-only data of a freshly created Quest Log (hdSaveHolders_c::clearSlot 0271FF4C)."""
    options = bytearray(16)
    options[OPT_GYRO] = 1
    return {"options": bytes(options), "pair": bytes(4), "inventory": bytes(20),
            "name": encode_name(name), "playlog": bytes(220)}


def _empty_recollection():
    """dSv_player_status_c_c of a fresh HD file: status A, items and bags of an empty inventory."""
    b = bytearray(0x70)
    b[0:4] = b"\x00\x0c\x00\x0c"          # max life, life
    b[9:18] = b"\xff" * 9                   # item buttons, equipment
    b[0x18:0x2D] = b"\xff" * 21             # items
    b[0x33:0x4B] = b"\xff" * 24             # bags
    return bytes(b)


EMPTY_RECOLLECTION = _empty_recollection()


def fresh_slot():
    """Save block of an unused HD Quest Log (dSv_info_c::initdata_to_card 025BAC50); fields the game
    leaves uninitialised are zero here."""
    s = Save(bytes(SAVE_SIZE))
    s.set_u("status_a.max_life", 12)
    s.set_u("status_a.life", 12)
    s.set_raw("status_a.select_item", b"\xff" * 5)
    s.set_raw("status_a.select_equip", b"\xff" * 4)
    s.set_raw("status_b.time", struct.pack(">f", 150.0))
    s.set_raw("status_b.tact_wind_x", b"\xff\xff")
    s.set_raw("status_b.tact_wind_y", b"\xff\xff")
    s.set_raw("status_b._pad_16", b"\xff\xff")
    s.set_raw("return_place.stage", b"sea".ljust(8, b"\0"))
    s.set_u("return_place.room", 0x2C)
    s.set_u("return_place.point", 0xCE)
    off, size = layout.BLOCKS["item"]
    s.data[off:off + size] = b"\xff" * size
    off, size = layout.BLOCKS["bag_item"]
    s.data[off:off + size] = b"\xff" * size
    fmap = bytearray(49)
    fmap[0] = fmap[10] = fmap[43] = 3        # Forsaken Fortress, Windfall, Outset
    s.set_raw("map.fmap_bits", bytes(fmap))
    s.set_u("map.triforce_bits", layout.HD_TRIFORCE_PRESET)
    s.set_u("config.ruby", 1)
    s.set_u("config.sound_mode", 2)
    s.set_u("config.vibration", 1)
    for i in range(4):
        off, size = layout.BLOCKS["status_c%d" % i]
        s.data[off:off + size] = EMPTY_RECOLLECTION
    s.set_event_reg(0x7EFF, 0x0E)
    s.set_event_reg(0xBEFF, 20)
    return s


def extra_crc(extras):
    """hdSaveHolders_c::calculateChecksum 027201E4."""
    buf = bytearray()
    for sect, size in SECTIONS:
        for s in range(3):
            v = extras[s][sect]
            if sect == "name":
                n = 0
                while n < 9 and v[2 * n:2 * n + 2] != b"\0\0":
                    n += 1
                v = v[:n + 1].ljust(18, b"\0")   # the game copies (length + 1) bytes, not characters
            buf += v
    assert len(buf) == EXTRA_SIZE
    return zlib.crc32(bytes(buf)) & 0xFFFFFFFF


class HdFile:
    def __init__(self, slots, extras, tails=None):
        self.slots = slots                    # 3 x Save
        self.extras = extras                  # 3 x dict(section -> bytes)
        self.tails = tails or [bytes(SLOT_SUMMED - SAVE_SIZE)] * 3   # bytes 0x768..0xA8C of each slot
        self.problems = []                    # filled by parse(strict=False): what is wrong with the file

    def move_to_quest_log_1(self, slot):
        """Swap file `slot` (0-based) with Quest Log 1, save block and HD records. The test rigs load Quest
        Log 1. Album files are named after their Quest Log and are not part of this object: rename them
        separately if the file has pictures."""
        if slot:
            for part in (self.slots, self.extras, self.tails):
                part[0], part[slot] = part[slot], part[0]
        return self

    @classmethod
    def parse(cls, raw, strict=True):
        if len(raw) != FILE_SIZE:
            raise HdError("cking.sav must be %d bytes, got %d" % (FILE_SIZE, len(raw)))
        slots, tails, problems = [], [], []
        for s in range(3):
            blk = raw[s * SLOT_SIZE:(s + 1) * SLOT_SIZE]
            if struct.unpack(">II", blk[SLOT_SUMMED:]) != slot_checksum(blk):
                problems.append("Quest Log %d: checksum mismatch" % (s + 1))
            slots.append(Save(blk[:SAVE_SIZE]))
            tails.append(blk[SAVE_SIZE:SLOT_SUMMED])
        extras = [dict() for _ in range(3)]
        o = 3 * SLOT_SIZE
        for sect, size in SECTIONS:
            for s in range(3):
                extras[s][sect] = raw[o:o + size]
                o += size
        fmt, crc = struct.unpack(">II", raw[o:o + 8])
        if fmt != FORMAT_WORD:
            problems.append("format word %d (expected %d)" % (fmt, FORMAT_WORD))
        if crc != extra_crc(extras):
            problems.append("HD section CRC mismatch")
        if problems and strict:
            raise HdError("; ".join(problems))
        f = cls(slots, extras, tails)
        f.problems = problems
        return f

    def serialize(self):
        out = bytearray()
        for save, tail in zip(self.slots, self.tails):
            blk = bytearray(SLOT_SIZE)
            blk[:SAVE_SIZE] = bytes(save)
            blk[SAVE_SIZE:SLOT_SUMMED] = tail
            struct.pack_into(">II", blk, SLOT_SUMMED, *slot_checksum(blk))
            out += blk
        for sect, size in SECTIONS:
            for s in range(3):
                assert len(self.extras[s][sect]) == size, sect
                out += self.extras[s][sect]
        out += struct.pack(">II", FORMAT_WORD, extra_crc(self.extras))
        assert len(out) == FILE_SIZE
        return bytes(out)

    def name(self, s):
        return decode_name(self.extras[s]["name"])
