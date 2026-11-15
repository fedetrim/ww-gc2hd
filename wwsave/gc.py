"""GameCube Wind Waker memory-card save: .gci / .gcs / .sav files and raw memory card images.

Card file layout (zeldaret/tww include/m_Do/m_Do_MemCardRWmng.h, src/m_Do/m_Do_MemCardRWmng.cpp):
  block 0       banner, icon, comment
  block 1, 2    two copies of card_savedata: u32 save_count, u32 data_version,
                3 x card_gamedata (0x768 save + u64 checksum), u32 block checksum at 0x1FFC
  block 3..11   Picto Box pictures (3 per file)
"""
import struct

from .layout import SAVE_SIZE, Save

BLOCK = 0x2000
DENTRY = 0x40
GAMEDATA = 0x770
FILE_BLOCKS = 12
FILE_NAME = b"gczelda"
REGIONS = {b"GZLE": "USA", b"GZLJ": "Japan", b"GZLP": "Europe"}


class GcError(Exception):
    pass


def gamedata_checksum(data):
    """mDoMemCdRWm_CalcCheckSumGameData: u32 byte sum and u32 sum of ~byte (each byte is
    promoted to int before the complement, so every term is 0xFFFFFFFF - byte)."""
    s = sum(data) & 0xFFFFFFFF
    c = (len(data) * 0xFFFFFFFF - sum(data)) & 0xFFFFFFFF
    return (s << 32) | c


def block_checksum(block):
    """mDoMemCdRWm_CalcCheckSum over the 0x1FFC bytes before the checksum word."""
    c0 = c1 = 0
    for (v,) in struct.iter_unpack(">H", block[:BLOCK - 4]):
        c0 = (c0 + v) & 0xFFFF
        c1 = (c1 + (~v & 0xFFFF)) & 0xFFFF
    return (c0 << 16) | c1


def pict_checksum(block):
    """mDoMemCdRWm_CalcCheckSumPictData: u16 byte sum over the block minus its last two bytes."""
    return sum(block[:BLOCK - 2]) & 0xFFFF


class GcCardFile:
    """One 'gczelda' card file: directory entry + 12 blocks."""

    def __init__(self, dentry, blocks, source="gci"):
        self.dentry = bytes(dentry)
        self.blocks = bytes(blocks)
        self.source = source
        self.game_code = self.dentry[0:6]
        if self.dentry[0:4] not in REGIONS:
            raise GcError("not a Wind Waker save (game code %r)" % self.dentry[0:6])
        name = self.dentry[8:0x28].split(b"\0", 1)[0]
        if name != FILE_NAME:
            raise GcError("unexpected card file name %r (expected 'gczelda')" % name)
        if len(self.blocks) < 3 * BLOCK:
            raise GcError("card file too short (%d bytes of data)" % len(self.blocks))

    @property
    def region(self):
        return REGIONS[self.game_code[0:4]]

    def _copy(self, k):
        return self.blocks[BLOCK * k:BLOCK * (k + 1)]

    def copy_status(self):
        """[(block checksum ok, [slot checksum ok x3])] for the two save copies."""
        out = []
        for k in (1, 2):
            blk = self._copy(k)
            slots = []
            for s in range(3):
                g = blk[8 + s * GAMEDATA:8 + (s + 1) * GAMEDATA]
                slots.append(struct.unpack(">Q", g[SAVE_SIZE:])[0] == gamedata_checksum(g[:SAVE_SIZE]))
            out.append((struct.unpack(">I", blk[-4:])[0] == block_checksum(blk), slots))
        return out

    def slots(self):
        """The three save files as the game's own loader picks them (mDoMemCdRWm_Restore,
        m_Do_MemCardRWmng.cpp:135-146): the first copy, or the second copy when the first fails its checksum.
        None when the game cannot read the file. For file 2 the game tests the second copy's file 3 instead
        of its file 2 before restoring (as written in the game), so a good file 2 in the second copy is not
        used when that copy's file 3 is damaged."""
        (_, a), (_, b) = self.copy_status()
        use_second = [not a[0] and b[0], not a[1] and b[2], not a[2] and b[2]]
        out = []
        for s in range(3):
            k = 1 if use_second[s] else 0
            ok = (b if k else a)[s]
            off = 8 + s * GAMEDATA
            out.append(Save(self._copy(k + 1)[off:off + SAVE_SIZE]) if ok else None)
        return out

    def save_count(self):
        return struct.unpack(">I", self._copy(1)[0:4])[0]

    def pictures(self):
        """Per file, the pictures the game itself would load (d_s_name.cpp:1218-1251): it visits the first
        `picture_num` slots that are not marked as erased in event register 0x89FF and keeps those whose
        checksum is right. The NTSC game leaves the data of an erased picture on the card, so the block
        contents alone do not tell which pictures exist."""
        out = []
        slots = self.slots()
        for s in range(3):
            pics = []
            g = slots[s]
            if g is not None and not g.is_new():
                wanted, erased, seen = g.u("item_record.picture_num"), g.event_reg(0x89FF), 0
                for i in range(3):
                    if seen >= wanted:
                        break
                    if erased >> i & 1:
                        continue
                    seen += 1
                    blk = self._copy(3 + s * 3 + i)
                    if len(blk) == BLOCK and struct.unpack(">H", blk[-2:])[0] == pict_checksum(blk):
                        pics.append(blk)
            out.append(pics)
        return out


def _card_sums(data):
    """The two checksums the memory card keeps for its directory and block map: the sum of the big-endian
    16-bit words and the sum of their complements, where 0xFFFF is stored as 0."""
    a = b = 0
    for i in range(0, len(data), 2):
        w = data[i] << 8 | data[i + 1]
        a = (a + w) & 0xFFFF
        b = (b + (w ^ 0xFFFF)) & 0xFFFF
    return (0 if a == 0xFFFF else a, 0 if b == 0xFFFF else b)


def _from_raw_card(raw):
    """Find the gczelda file(s) in a raw memory card image (optionally with Dolphin's 0x40 header)."""
    if len(raw) % BLOCK == 0x40:
        raw = raw[0x40:]
    if len(raw) % BLOCK or len(raw) < 5 * BLOCK:
        raise GcError("not a memory card image")

    def counter(blk_no):
        return struct.unpack(">H", raw[BLOCK * blk_no + 0x1FFA:BLOCK * blk_no + 0x1FFC])[0]

    def bat_counter(blk_no):
        return struct.unpack(">H", raw[BLOCK * blk_no + 4:BLOCK * blk_no + 6])[0]

    # Each of the two has a backup copy; the one in use is the valid copy with the higher update counter
    # (directory: checksums over its first 0x1FFC bytes; block map: over everything after its checksums).
    def valid_dir(blk_no):
        blk = raw[BLOCK * blk_no:BLOCK * (blk_no + 1)]
        return _card_sums(blk[:0x1FFC]) == struct.unpack(">HH", blk[0x1FFC:0x2000])

    def valid_bat(blk_no):
        blk = raw[BLOCK * blk_no:BLOCK * (blk_no + 1)]
        return _card_sums(blk[4:]) == struct.unpack(">HH", blk[0:4])

    def pick(first, second, valid, count):
        good = [n for n in (first, second) if valid(n)] or [first, second]     # both bad: as before
        return max(good, key=lambda n: (count(n), -n))

    d = pick(1, 2, valid_dir, counter)
    b = pick(3, 4, valid_bat, bat_counter)
    directory = raw[BLOCK * d:BLOCK * (d + 1)]
    bat = raw[BLOCK * b:BLOCK * (b + 1)]
    total_blocks = len(raw) // BLOCK
    found = []
    for i in range(127):
        e = directory[i * DENTRY:(i + 1) * DENTRY]
        if e[0:4] not in REGIONS or e[8:0x28].split(b"\0", 1)[0] != FILE_NAME:
            continue
        first, count = struct.unpack(">HH", e[0x36:0x3A])
        data, blk = bytearray(), first
        for _ in range(count):
            if not 5 <= blk < total_blocks:
                raise GcError("corrupt block chain in memory card image")
            data += raw[BLOCK * blk:BLOCK * (blk + 1)]
            blk = struct.unpack(">H", bat[0x0A + (blk - 5) * 2:0x0C + (blk - 5) * 2])[0]
        found.append(GcCardFile(e, data, "raw card"))
    if not found:
        raise GcError("no Wind Waker save ('gczelda') on this memory card image")
    return found


def load_all(raw):
    """All Wind Waker card files in `raw` (a .gci/.gcs/.sav file or a raw memory card image)."""
    for header, kind in ((0, "gci"), (0x110, "gcs"), (0x80, "sav")):
        body = raw[header:]
        if len(body) >= DENTRY + 3 * BLOCK and (len(body) - DENTRY) % BLOCK == 0 \
                and body[0:4] in REGIONS and body[8:8 + len(FILE_NAME)] == FILE_NAME:
            return [GcCardFile(body[:DENTRY], body[DENTRY:], kind)]
    if raw[0:3] == b"GZL" or raw[0x110:0x113] == b"GZL" or raw[0x80:0x83] == b"GZL":
        raise GcError("damaged or truncated Wind Waker card file (%d bytes)" % len(raw))
    if len(raw) % BLOCK not in (0, 0x40) or len(raw) < 5 * BLOCK:
        raise GcError("not a Wind Waker GameCube save (.gci/.gcs/.sav) or memory card image")
    return _from_raw_card(raw)                  # its own errors say what is wrong with the card image


def load(raw):
    files = load_all(raw)
    if len(files) > 1:
        raise GcError("memory card image holds %d Wind Waker saves; export one as .gci" % len(files))
    return files[0]


def build_gci(game_code, slots, comment=b"Zelda: The Wind Waker"):
    """A minimal .gci holding `slots` (3 x 0x768 bytes). Used by tests and the reverse check;
    banner/icon are blank."""
    out = bytearray(DENTRY + FILE_BLOCKS * BLOCK)
    out[0:6] = game_code
    out[6] = 0xFF
    out[7] = 1
    out[8:8 + len(FILE_NAME)] = FILE_NAME
    struct.pack_into(">IIHHBBHHHI", out, 0x28, 0, 0, 1, 3, 4, 0, 0, FILE_BLOCKS, 0xFFFF, 0x1C00)
    out[DENTRY + 0x1C00:DENTRY + 0x1C00 + len(comment)] = comment
    sav = bytearray(BLOCK)
    struct.pack_into(">II", sav, 0, 1, 0)
    for s, g in enumerate(slots):
        g = bytes(g)
        assert len(g) == SAVE_SIZE
        o = 8 + s * GAMEDATA
        sav[o:o + SAVE_SIZE] = g
        struct.pack_into(">Q", sav, o + SAVE_SIZE, gamedata_checksum(g))
    struct.pack_into(">I", sav, BLOCK - 4, block_checksum(sav))
    for k in (1, 2):
        out[DENTRY + k * BLOCK:DENTRY + (k + 1) * BLOCK] = sav
    return bytes(out)
