"""GameCube Wind Waker save -> Wind Waker HD save.

Every rule is documented in docs/DIFFERENCES.md (section numbers in the comments).
Rules that are not a 1:1 translation are controlled by `Options`; `Decision` objects describe
each choice that applies to a card.
"""
import unicodedata
from dataclasses import dataclass, field

from . import hd, hdcheck, layout
from .layout import NO_ITEM, Save

ITEM_TINGLE = 0x21          # Tingle Tuner (GameCube) / Tingle Bottle (HD)
ITEM_WIND_WAKER = 0x22
ITEM_PICTO_BOX = 0x23
ITEM_DELUXE_PICTO_BOX = 0x26
ITEM_SWIFT_SAIL = 0x77
ITEM_SAIL = 0x78

# Collect maps (charts) whose GameCube item is a Triforce Chart and whose HD item is a new
# Treasure Chart (DIFFERENCES 3.1): collect map number -> HD Treasure Chart number.
REUSED_CHARTS = {2: 42, 4: 43, 6: 44, 7: 45, 8: 46}
HD_TRIFORCE_PRESET = layout.HD_TRIFORCE_PRESET

# Places whose GameCube reward was replaced by one of those HD charts (DIFFERENCES 3.2):
# collect map -> (how the save records that the place was already collected, description)
HD_CHART_SOURCES = {
    4: (("tbox", 1, 26), "Horseshoe Island north-western lookout chest (GameCube: Skull Necklace)"),
    6: (("tbox", 1, 11), "Star Belt Archipelago lookout chest (GameCube: Red Rupee)"),
    7: (("event", 0x1C04), "Mrs. Marie's reward for 40 Joy Pendants (GameCube: Hero's Charm)"),
    8: (("tbox", 0xD, 2), "Pawprint Isle Wizzrobe cave chest (GameCube: Silver Rupee)"),
}
SAVAGE_FLOOR_50 = ("tbox", 0xD, 12)     # GameCube: Piece of Heart, HD: Hero's Charm
HEROS_CHARM = ("collect.collect", 4, 0x01)
HEROS_CHARM_ACTIVE = 0x02               # same byte: the charm is switched on
MARIE_EVENT = 0x1C04                    # Mrs. Marie's reward for 40 Joy Pendants was given
PAWPRINT_CHEST = HD_CHART_SOURCES[8][0]
# Chests that hold a Triforce Chart on the GameCube and the Triforce Shard itself in HD (DIFFERENCES 3.3).
# The GameCube Ghost Ship has three copies of its chest (bits 21-23); HD has the one with bit 23.
TRIFORCE_CHESTS = {2: (0xC, [17]), 4: (0xA, [23, 21, 22]), 6: (0xD, [11]), 7: (0xC, [10]), 8: (0xC, [11])}
TRIFORCE_PLACES = {2: "Private Oasis cabana labyrinth", 4: "Ghost Ship", 6: "Savage Labyrinth floor 30",
                   7: "Stone Watcher Island cave", 8: "Overlook Island cave"}
# Set only through the Tingle Tuner on the GameCube; HD has no setter (0 of 112 real HD Quest Logs):
# Knuckle found, Tuner message sent, two Tuner states, Tuner trigger area.
TUNER_FLAGS = (0x1708, 0x1A20, 0x1A08, 0x1A10, 0x2E08)
WHIRLPOOL_HINT = 0x1940     # GameCube: set in every whirlpool; HD: only with the bomb bag (d_a_ship.cpp:3481)
HINTS_DONE = 0x2B04         # gossips' hints all told; HD needs the Swift Sail for the last one
GHOST_SHIP_REG = 0x8803     # 3 once the Ghost Ship chest scene has ended: the ship never appears again
LOOKOUT_CASES = {"horseshoe_chest": 4, "star_belt_chest": 6}      # option -> collect map of the HD chart
MODES = ("steps", "rewards")
DECIPHER_FEE = 398                      # what Tingle charges per Triforce Chart, both games
HD_WALLET = layout.WALLET_HD
BEAST_SLOT_FIRST = 24                   # item-button value of the first Spoils Bag slot
SKULL_NECKLACE = (0, 0x45)              # Spoils Bag counter, item number
JOY_PENDANT = (7, 0x1F)
# What the GameCube gave at a place that gives an HD-only chart: taken back by "steps" when still held.
GC_LOOKOUT_REWARD = {4: "Skull Necklace", 6: "Red Rupee"}

OUTSET_KIDNAP_EVENT = 0x0E20    # Aryll kidnapped on Outset
HD_OUTSET_SWITCH = 1            # sea-stage switch that normally played HD files have after it (DIFFERENCES 2.1)

LENZO_REG = 0xC407          # Lenzo's Picto Box quest stage (event register, both games)


class ConversionError(Exception):
    pass


@dataclass
class Options:
    """Every case below is a place whose reward differs between the games. There is no default:
    "steps"   = the place stays done; the GameCube reward is replaced by what HD gives there
    "rewards" = what the player holds stays; the place whose HD reward is not held is undone, and the
                place that gives the held reward in HD is done."""
    triforce_chart_2: str = None
    triforce_chart_4: str = None
    triforce_chart_6: str = None
    triforce_chart_7: str = None
    triforce_chart_8: str = None
    horseshoe_chest: str = None         # HD: Treasure Chart 43
    star_belt_chest: str = None         # HD: Treasure Chart 44
    floor50: str = None                 # Savage Labyrinth floor 50: Piece of Heart / Hero's Charm
    pawprint_chest: str = None          # HD: Treasure Chart 46
    marie: str = None                   # Hero's Charm / Treasure Chart 45
    lenzo: str = None                   # third picture: Joy Pendant / Deluxe Picto Box
    swift_sail: bool = False            # upgrade an owned Sail to the HD Swift Sail
    hero_mode: bool = False             # HD Hero Mode
    name: str = None                    # player name override (max 8 characters), or {file index: name}

    CASES = ("triforce_chart_2", "triforce_chart_4", "triforce_chart_6", "triforce_chart_7",
             "triforce_chart_8", "horseshoe_chest", "star_belt_chest", "floor50", "pawprint_chest", "marie",
             "lenzo")

    def for_slot(self, slot):
        """The options of one file: a case may hold {file index: mode} instead of one mode for all."""
        import dataclasses
        return dataclasses.replace(self, **{k: getattr(self, k).get(slot) for k in self.CASES + ("name",)
                                            if isinstance(getattr(self, k), dict)})

    def answer(self, key, slot, mode):
        """Record the answer to a case for one file."""
        current = getattr(self, key)
        if not isinstance(current, dict):
            current = {} if current is None else {s: current for s in range(3)}
        current[slot] = mode
        setattr(self, key, current)

    @classmethod
    def all(cls, mode, **kw):
        """The same mode for every case."""
        return cls(**dict({k: mode for k in cls.CASES}, **kw))


@dataclass
class Decision:
    key: str                # Options attribute
    question: str
    choices: list           # [(value, description)], first = default
    slots: list = field(default_factory=list)
    per_slot: dict = field(default_factory=dict)    # file index -> (question, choices): the text can differ

    def text(self, slot):
        return self.per_slot.get(slot, (self.question, self.choices))


@dataclass
class SlotReport:
    slot: int
    used: bool
    name: str = ""
    changes: list = field(default_factory=list)     # what the converter changed, and why
    warnings: list = field(default_factory=list)    # things the user should know
    pictures: int = 0                               # Picto Box pictures on the GameCube card
    totals: list = field(default_factory=list)      # (label, GameCube, HD) where what you hold differs


def _map_bit(save, field_name, n):
    """collect map n (1-based) in one of the 128-bit chart flag sets"""
    off = layout.FIELDS[field_name][0] + 4 * ((n - 1) >> 5)
    word = int.from_bytes(save.data[off:off + 4], "big")
    return bool(word >> ((n - 1) & 31) & 1)


def _set_map_bit(save, field_name, n, on):
    off = layout.FIELDS[field_name][0] + 4 * ((n - 1) >> 5)
    word = int.from_bytes(save.data[off:off + 4], "big")
    mask = 1 << ((n - 1) & 31)
    word = (word | mask) if on else (word & ~mask)
    save.data[off:off + 4] = word.to_bytes(4, "big")


def _collected(save, flag):
    if flag[0] == "tbox":
        return bool(save.u("memory%02d.tbox" % flag[1]) >> flag[2] & 1)
    return save.event_bit(flag[1])


def _set_tbox(save, record, bit, on):
    name = "memory%02d.tbox" % record
    save.set_u(name, (save.u(name) | 1 << bit) if on else (save.u(name) & ~(1 << bit)))


def _take_spoil(save, index, item):
    """Remove one spoil (Spoils Bag counter `index`, item number `item`); False if none is left."""
    counts = bytearray(save.raw("bag_item_record.beast_num"))
    if not counts[index]:
        return False
    counts[index] -= 1
    save.set_raw("bag_item_record.beast_num", bytes(counts))
    if not counts[index]:                                   # as dSv_player_bag_item_c::setBeastItemEmpty
        bag = bytearray(save.raw("bag_item.beast"))
        sel = bytearray(save.raw("status_a.select_item"))
        for i in range(8):
            if bag[i] == item:
                bag[i] = NO_ITEM
                for b in range(3):
                    if sel[b] == BEAST_SLOT_FIRST + i:
                        sel[b] = NO_ITEM
        save.set_raw("bag_item.beast", bytes(bag))
        save.set_raw("status_a.select_item", bytes(sel))
    return True


def _hearts(quarters):
    return "%d hearts%s" % (quarters // 4, " + %d/4" % (quarters % 4) if quarters % 4 else "")


def _totals(g, h):
    """What the player holds, GameCube file vs converted file: [(label, before, after)] where they differ."""
    def charts(s, ks):
        return sum(_map_bit(s, "map.get_map", k) for k in ks)
    rows = [
        ("Rupees", g.u("status_a.rupee"), h.u("status_a.rupee")),
        ("Maximum life", _hearts(g.u("status_a.max_life")), _hearts(h.u("status_a.max_life"))),
        ("Triforce Shards", bin(g.u("collect.triforce")).count("1"), bin(h.u("collect.triforce")).count("1")),
        ("Triforce Charts", charts(g, range(1, 9)), charts(h, (1, 3, 5))),
        ("Treasure Charts", charts(g, range(9, 50)), charts(h, tuple(REUSED_CHARTS) + tuple(range(9, 50)))),
        ("Hero's Charm", "yes" if g.raw(HEROS_CHARM[0])[HEROS_CHARM[1]] & 1 else "no",
         "yes" if h.raw(HEROS_CHARM[0])[HEROS_CHARM[1]] & 1 else "no"),
        ("Picto Box", "Deluxe" if _item(g, layout.SLOT_CAMERA) == ITEM_DELUXE_PICTO_BOX else "plain",
         "Deluxe" if _item(h, layout.SLOT_CAMERA) == ITEM_DELUXE_PICTO_BOX else "plain"),
        ("Skull Necklaces", g.raw("bag_item_record.beast_num")[0], h.raw("bag_item_record.beast_num")[0]),
        ("Joy Pendants", g.raw("bag_item_record.beast_num")[7], h.raw("bag_item_record.beast_num")[7]),
    ]
    return [r for r in rows if r[1] != r[2]]


def _stuck_chart(g, k):
    """GameCube Triforce Chart k taken from its chest, its shard not salvaged yet. The chest alone counts
    too (a file with the chest open and no chart): in HD an open chest without the shard would leave the
    shard out of reach."""
    record, bits = TRIFORCE_CHESTS[k]
    taken = _map_bit(g, "map.get_map", k) or any(_collected(g, ("tbox", record, b)) for b in bits)
    return taken and not g.u("collect.triforce") >> (k - 1) & 1


def _item(save, slot):
    return save.data[layout.FIELDS["item.slot%02d" % slot][0]]


def _set_item(save, slot, item):
    save.data[layout.FIELDS["item.slot%02d" % slot][0]] = item


def _get_bits(save, slot):
    return save.data[layout.FIELDS["get_item.slot%02d" % slot][0]]


def _set_get_bits(save, slot, value):
    save.data[layout.FIELDS["get_item.slot%02d" % slot][0]] = value


def _hd_buttons(save, select_field, item_fmt):
    """HD item buttons: [0..2] X/Y/Z, [3] GamePad button (Wind Waker), [4] sail button."""
    sel = bytearray(save.raw(select_field))
    moved = []
    for i in range(3):
        if sel[i] in (layout.SLOT_SAIL, layout.SLOT_WIND_WAKER):
            moved.append("XYZ"[i])
            sel[i] = NO_ITEM
    ww = save.u(item_fmt % layout.SLOT_WIND_WAKER)
    sail = save.u(item_fmt % layout.SLOT_SAIL)
    sel[3] = layout.SLOT_WIND_WAKER if ww == ITEM_WIND_WAKER else NO_ITEM
    sel[4] = layout.SLOT_SAIL if sail in (ITEM_SAIL, ITEM_SWIFT_SAIL) else NO_ITEM
    save.set_raw(select_field, bytes(sel))
    return moved


def gc_name(save, game_code=b"GZLE01"):
    raw = save.raw("info.player_name").split(b"\0", 1)[0]
    enc = {b"J": "shift_jis", b"P": "cp1252"}.get(game_code[3:4], "latin-1")
    return raw.decode(enc, "replace")


def hd_name_for(name):
    """HD stores up to 8 UTF-16 characters. Returns (name, note or None); the note says whenever the name
    written is not the name given."""
    folded = unicodedata.normalize("NFKC", name)
    if not folded or not all(0x20 <= ord(c) < 0x250 and not 0x7F <= ord(c) < 0xA0 for c in folded):
        return "Link", "name %r cannot be shown by the HD font; using 'Link'" % name
    if len(folded) > hd.NAME_CHARS:
        return folded[:hd.NAME_CHARS], "name %r shortened to %r (HD allows 8 characters)" % (
            name, folded[:hd.NAME_CHARS])
    if folded != name:
        return folded, "name %r written as %r (characters replaced by their plain form)" % (name, folded)
    return folded, None


_STEPS = "by steps: "
_REWARDS = "by rewards: "


def decisions_for(slots, options=None):
    """The cases these GameCube files are in (list of Decision, in asking order). `options` matters for one
    dependency: the Pawprint chest is not a case when --floor50 rewards already settles it."""
    all_options = options or Options()
    out = {}

    def need(key, question, steps, rewards, s):
        choices = [("steps", _STEPS + steps), ("rewards", _REWARDS + rewards)]
        d = out.setdefault(key, Decision(key, question, choices))
        d.slots.append(s)
        d.per_slot[s] = (question, choices)

    for s, g in enumerate(slots):
        if g is None or g.is_new():
            continue
        options = all_options.for_slot(s)
        for k in REUSED_CHARTS:
            if _stuck_chart(g, k):
                need("triforce_chart_%d" % k,
                     "Triforce Chart %d (%s chest) is owned and Triforce Shard %d is not salvaged yet. In HD "
                     "that chest holds the shard itself and the chart does not exist." % (
                         k, TRIFORCE_PLACES[k], k),
                     "the chest stays open and you get Triforce Shard %d now (no deciphering, no salvage)" % k,
                     "the chart is dropped and the chest is closed again; open it in HD to get the shard", s)
        for key, k in LOOKOUT_CASES.items():
            if _collected(g, HD_CHART_SOURCES[k][0]):
                need(key,
                     "%s is open. In HD it holds Treasure Chart %d." % (HD_CHART_SOURCES[k][1], REUSED_CHARTS[k]),
                     "the chest stays open: you get Treasure Chart %d and lose the %s (if still held)" % (
                         REUSED_CHARTS[k], GC_LOOKOUT_REWARD[k]),
                     "the chest is closed again; open it in HD to get the chart. You keep the %s" %
                     GC_LOOKOUT_REWARD[k], s)
        f50, marie = _collected(g, SAVAGE_FLOOR_50), g.event_bit(MARIE_EVENT)
        if f50:
            need("floor50",
                 "The Savage Labyrinth floor-50 chest is open: the GameCube gave a Piece of Heart. In HD that "
                 "chest holds the Hero's Charm, and the Piece of Heart is the sunken treasure of Treasure "
                 "Chart 46 (Two-Eye Reef; the chart is in the Pawprint Isle Wizzrobe cave chest).",
                 "the chest stays open: you get the Hero's Charm and lose the Piece of Heart (maximum life "
                 "-1/4 heart) until you salvage it in HD",
                 "you keep the Piece of Heart; its HD place is marked done (Pawprint chest opened, Treasure "
                 "Chart 46 owned and salvaged; a Silver Rupee already taken from that chest is treated as in "
                 "the Pawprint case by rewards). " + (
                     "The floor-50 chest then follows the Mrs. Marie case: it stays open if you keep the "
                     "Hero's Charm there, and is closed again otherwise" if marie else
                     "The floor-50 chest is closed again; open it in HD to get the Hero's Charm"), s)
        if _collected(g, PAWPRINT_CHEST) and not (f50 and options.floor50 != "steps"):
            need("pawprint_chest",
                 "%s is open. In HD it holds Treasure Chart 46 (which leads to a Piece of Heart), and the "
                 "Silver Rupee is the sunken treasure of Treasure Chart 45 (Mrs. Marie's reward)." %
                 HD_CHART_SOURCES[8][1],
                 "the chest stays open: you get Treasure Chart 46 and lose the Silver Rupee (200 rupees, as "
                 "far as still held)",
                 "the chest is closed again; open it in HD to get the chart. You keep the Silver Rupee if "
                 "Treasure Chart 45 is in hand (Mrs. Marie by steps): its treasure is then marked as "
                 "salvaged. Otherwise the 200 rupees are taken back and wait under Seven-Star Isles", s)
        if marie:
            if not f50:
                lose = "and lose the Hero's Charm until you open the floor-50 chest in HD"
            elif options.floor50 == "steps":
                lose = "and keep the Hero's Charm (the floor-50 chest stays open)"
            elif options.floor50 == "rewards":
                lose = "and the Hero's Charm goes back into the floor-50 chest, which is closed again"
            else:
                lose = ("and keep the Hero's Charm only with --floor50 steps (with rewards it goes back into "
                        "the floor-50 chest, closed again)")
            need("marie",
                 "Mrs. Marie gave her reward for 40 Joy Pendants: on the GameCube the Hero's Charm. In HD she "
                 "gives Treasure Chart 45, and the Hero's Charm is in the Savage Labyrinth floor-50 chest.",
                 "her reward stays given: you get Treasure Chart 45 " + lose,
                 "you keep the Hero's Charm and the floor-50 chest is %s; Mrs. Marie's reward "
                 "is pending again (she gives Treasure Chart 45 the next time you bring her a Joy Pendant)" % (
                     "open" if f50 else "marked as opened"), s)
        if _lenzo_stuck(g) and _couple_on_street(g):
            need("lenzo",
                 "Lenzo accepted the third picture and the Picto Box is not the Deluxe one. On the GameCube "
                 "that gave a Joy Pendant and the Deluxe Picto Box came later for a Forest Firefly; HD gives "
                 "the Deluxe Picto Box for the third picture and a Joy Pendant for each firefly.",
                 "the third picture stays accepted: you get the Deluxe Picto Box and lose the Joy Pendant "
                 "(if still held)",
                 "the third task is pending again; bring Lenzo that picture in HD to get the Deluxe Picto "
                 "Box. You keep the Joy Pendant", s)
    return [out[k] for k in Options.CASES if k in out]


def _couple_on_street(g):
    """The third picture (Anton and Linda looking at each other) can only be taken while register 0xB907 is
    0 or 1 (d_a_npc_people.cpp:120). Normal play cannot pass that without the Deluxe Picto Box."""
    return g.event_reg(0xB907) < 2


def _lenzo_stuck(g):
    return (g.event_reg(LENZO_REG) >= 6 and _item(g, layout.SLOT_CAMERA) == ITEM_PICTO_BOX
            and not _get_bits(g, layout.SLOT_CAMERA) & 2)


def convert_slot(g, slot, options, game_code=b"GZLE01"):
    """One GameCube file -> (HD save block, HD-only records, SlotReport)."""
    options = options.for_slot(slot)
    for d in decisions_for([g], options):
        if getattr(options, d.key) not in MODES:
            raise ConversionError("no choice made for '%s' in file %d (steps or rewards)" % (d.key, slot + 1))
    rep = SlotReport(slot, used=not g.is_new())
    out = g.copy()
    extra = hd.default_extra()
    if not rep.used:
        # An unused GameCube file has no name. It becomes an empty HD Quest Log.
        return hd.fresh_slot(), extra, rep

    # --- name ---------------------------------------------------------------------------------
    name = gc_name(g, game_code)
    rep.name = name
    hd_name, note = hd_name_for(options.name if options.name is not None else name)
    if note:
        rep.warnings.append(note)
    extra["name"] = hd.encode_name(hd_name)
    # HD keeps the name only in its UTF-16 record; the 8-bit name fields of the save block are empty on
    # a first playthrough and "Link" after its New Game+ re-initialisation.
    filler = b"Link" if g.u("info.clear_count") else b""
    for f in ("info.player_name", "info._name_25", "info._name_36"):
        out.set_raw(f, filler.ljust(17, b"\0"))

    # HD pads the return-place stage name with zeros (copyStageName, d_save.cpp 025B5060); GameCube
    # leaves old characters after the terminator
    stage = out.raw("return_place.stage").split(b"\0", 1)[0]
    out.set_raw("return_place.stage", stage.ljust(8, b"\0"))

    # --- 2.1 fields with different conventions ---------------------------------------------------
    # Also for a New Game+ file that was not started yet: with counter 0 the game treats the Quest Log
    # as empty and starts a plain new game (checked in the game); with 1 it shows the Triforce mark and
    # starts the second quest.
    if out.u("info.save_count") == 0:
        out.set_u("info.save_count", 1)
        rep.changes.append("Save counter set to 1 (the GameCube keeps it at 0). HD shows a Quest Log whose "
                           "counter is 0 as empty, so the file would not appear.")
    out.set_u("config.sound_mode", 2)
    out.set_u("map.triforce_bits", out.u("map.triforce_bits") | HD_TRIFORCE_PRESET)
    out.set_u("item_record.picture_num", 0)
    out.set_event_reg(0x89FF, 0)       # GameCube: picture slots erased this session; cleared when it loads
    for i in range(4):
        out.set_u("status_c%d.picture_num" % i, 0)

    # Outset, after Aryll's kidnapping (event 0x0E20): files from normal HD play carry switch 1 of the
    # sea stage from then on; GameCube never sets it. Switch 9 (the scene's trigger) means the same in
    # both games and is kept.
    if out.event_bit(OUTSET_KIDNAP_EVENT):
        out.set_u("memory00.switch", out.u("memory00.switch") | 1 << (96 + HD_OUTSET_SWITCH))

    # sea chart: bit 1 of a sector is the GameCube "arrived" mark kept for the Tingle Tuner. HD never
    # sets it (and has no reader); only the three sectors charted from the start carry it.
    fmap = bytearray(out.raw("map.fmap_bits"))
    for sector in range(49):
        if sector not in hd.PRECHARTED_SECTORS:
            fmap[sector] &= ~2 & 0xFF
    out.set_raw("map.fmap_bits", bytes(fmap))

    # item buttons: HD has dedicated buttons for the Wind Waker and the sail; X/Y/Z never hold them
    moved = _hd_buttons(out, "status_a.select_item", "item.slot%02d")
    if moved:
        rep.changes.append("Button(s) %s emptied: they held the Sail or the Wind Waker. HD has dedicated buttons "
                           "for both and never keeps them on an item button." % "/".join(moved))
    # recollection records (inventory snapshots for the boss rematches): GameCube leaves an unused
    # record zeroed, HD fills it with the values of an empty inventory
    for i in range(4):
        block = "status_c%d" % i
        off, size = layout.BLOCKS[block]
        if not any(out.data[off:off + size]):
            out.data[off:off + size] = hd.EMPTY_RECOLLECTION
        else:
            _hd_buttons(out, block + ".a_select_item", block + ".item%02d")

    # --- 3.1 charts whose ids HD reuses --------------------------------------------------------
    for k, hd_chart in REUSED_CHARTS.items():
        record, bits = TRIFORCE_CHESTS[k]
        if any(_collected(g, ("tbox", record, b)) for b in bits):
            _set_tbox(out, record, bits[0], True)           # the Ghost Ship copy HD keeps
            for b in bits[1:]:
                _set_tbox(out, record, b, False)            # HD has no chest for the other two
        if not _map_bit(g, "map.get_map", k) and not _stuck_chart(g, k):
            continue
        for f in ("map.get_map", "map.open_map", "map.complete_map"):
            _set_map_bit(out, f, k, False)
        if not _stuck_chart(g, k):
            rep.changes.append("Triforce Chart %d removed; Triforce Shard %d is kept. The chart does not exist "
                               "in HD (its number is HD's Treasure Chart %d) and you already salvaged the "
                               "shard it led to." % (k, k, hd_chart))
        elif getattr(options, "triforce_chart_%d" % k) == "steps":
            out.set_u("collect.triforce", out.u("collect.triforce") | 1 << (k - 1))
            rep.changes.append("Triforce Shard %d added and Triforce Chart %d removed (by steps). In HD the %s "
                               "chest, which you opened, holds the shard itself: an HD player with that "
                               "chest open has the shard." % (k, k, TRIFORCE_PLACES[k]))
        else:
            for b in bits:
                _set_tbox(out, record, b, False)
            if k == 4:
                out.set_event_reg(GHOST_SHIP_REG, 0)        # the Ghost Ship sails again
            rep.changes.append("Triforce Chart %d removed and the %s chest closed again (by rewards). In HD "
                               "that chest holds Triforce Shard %d: open it again to get the shard.%s" % (
                                   k, TRIFORCE_PLACES[k], k,
                                   " The Ghost Ship sails again so that you can board it." if k == 4 else ""))

    # --- 3.2 places whose reward differs ------------------------------------------------------------
    def give_chart(k, salvaged=False):
        _set_map_bit(out, "map.get_map", k, True)
        _set_map_bit(out, "map.open_map", k, salvaged)
        _set_map_bit(out, "map.complete_map", k, salvaged)

    rupees = []                             # rupee amounts taken back (-) and given back (+)
    for key, k in LOOKOUT_CASES.items():
        flag, place = HD_CHART_SOURCES[k]
        if _collected(g, flag):
            if getattr(options, key) == "steps":
                give_chart(k)
                rep.changes.append("Treasure Chart %d added (by steps). In HD it is what this chest, which you "
                                   "opened, holds: %s." % (REUSED_CHARTS[k], place))
                if k == 4:
                    took = _take_spoil(out, *SKULL_NECKLACE)
                    rep.changes.append("One Skull Necklace removed: the GameCube gave it in that chest and HD "
                                       "does not." if took else "The Skull Necklace the GameCube gave in that "
                                       "chest could not be removed: you no longer hold one.")
                else:
                    rupees.append(-20)
                    rep.changes.append("20 rupees removed (-20 rupees): the Red Rupee the GameCube gave in that "
                                       "chest, which HD does not give.")
            else:
                _set_tbox(out, flag[1], flag[2], False)
                rep.changes.append("Chest closed again (by rewards): %s. In HD it holds Treasure Chart %d: open "
                                   "it again to get the chart. You keep the %s." % (
                                       place, REUSED_CHARTS[k], GC_LOOKOUT_REWARD[k]))

    f50, marie, paw = _collected(g, SAVAGE_FLOOR_50), g.event_bit(MARIE_EVENT), _collected(g, PAWPRINT_CHEST)
    a = options.floor50 if f50 else None
    b = options.marie if marie else None
    charm_off = layout.FIELDS[HEROS_CHARM[0]][0] + HEROS_CHARM[1]
    if f50 or marie:
        # In HD the Hero's Charm and the floor-50 chest go together.
        had_charm = bool(out.data[charm_off] & HEROS_CHARM[2])
        # "rewards" keeps what is held: it marks the chest opened only for a charm the file really has
        f50_open = a == "steps" or (b == "rewards" and had_charm)
        _set_tbox(out, SAVAGE_FLOOR_50[1], SAVAGE_FLOOR_50[2], f50_open)
        if f50_open:
            out.data[charm_off] |= HEROS_CHARM[2]
            if not had_charm:
                rep.changes.append("Hero's Charm added (floor 50 by steps): in HD it is what the Savage "
                                   "Labyrinth floor-50 chest, which you opened, holds.")
            if not f50:
                rep.changes.append("Savage Labyrinth floor-50 chest marked as opened (Mrs. Marie by rewards): "
                                   "in HD the Hero's Charm comes from that chest, and you keep the charm, so "
                                   "the chest must not give a second one. The Piece of Heart the GameCube had "
                                   "there is under Two-Eye Reef in HD (Treasure Chart 46).")
        else:
            if marie and had_charm:
                out.data[charm_off] &= ~(HEROS_CHARM[2] | HEROS_CHARM_ACTIVE) & 0xFF
                rep.changes.append("Hero's Charm removed (Mrs. Marie by steps): in HD she gives Treasure Chart "
                                   "45 instead, and the charm is in the Savage Labyrinth floor-50 chest (%s). "
                                   "Open it to get the charm back." % (
                                       "closed again" if f50 else "not opened yet"))
            if f50:
                rep.changes.append("Savage Labyrinth floor-50 chest closed again (floor 50 by rewards): in HD it "
                                   "holds the Hero's Charm, which you do not have. Open it again to get it.")
    if a == "steps" and out.u("status_a.max_life") == 0:
        rep.warnings.append("the floor-50 Piece of Heart could not be removed: the file has no hearts at all "
                            "(damaged or edited save)")
    elif a == "steps":
        max_life = out.u("status_a.max_life") - 1
        out.set_u("status_a.max_life", max_life)
        out.set_u("status_a.life", min(out.u("status_a.life"), max_life // 4 * 4))
        rep.changes.append("One Piece of Heart removed (maximum life -1/4 heart; floor 50 by steps): the "
                           "GameCube gave it in the floor-50 chest. In HD that chest gives the Hero's Charm and "
                           "the piece is the sunken treasure of Treasure Chart 46 (Pawprint Isle Wizzrobe cave "
                           "chest, then Two-Eye Reef): salvage it to get the piece back.")
    if a == "rewards":
        _set_tbox(out, PAWPRINT_CHEST[1], PAWPRINT_CHEST[2], True)
        give_chart(8, salvaged=True)
        rep.changes.append("Treasure Chart 46 added, already salvaged%s (floor 50 by rewards): its treasure in "
                           "HD is the Piece of Heart you keep from floor 50, so it must not be collectable a "
                           "second time." % (
                               "" if paw else ", and the Pawprint Isle Wizzrobe cave chest marked as opened"))
    elif paw:
        if options.pawprint_chest == "steps":
            give_chart(8)
            rep.changes.append("Treasure Chart 46 added (by steps). In HD it is what this chest, which you "
                               "opened, holds: %s." % HD_CHART_SOURCES[8][1])
        else:
            _set_tbox(out, PAWPRINT_CHEST[1], PAWPRINT_CHEST[2], False)
            rep.changes.append("Chest closed again (by rewards): %s. In HD it holds Treasure Chart 46: open it "
                               "again to get the chart." % HD_CHART_SOURCES[8][1])
    if b == "steps":
        give_chart(7)
        rep.changes.append("Treasure Chart 45 added (Mrs. Marie by steps): in HD it is her reward for 40 Joy "
                           "Pendants, which she already gave you.")
    if paw:
        # The Pawprint chest's Silver Rupee is the sunken treasure of Treasure Chart 45 in HD. It can be kept
        # only if that treasure can be marked as salvaged, which needs the chart in hand.
        keep = (a == "rewards" or options.pawprint_chest == "rewards") and b == "steps"
        if keep:
            give_chart(7, salvaged=True)
            rep.changes.append("Treasure Chart 45 marked as salvaged: its treasure in HD is the Silver Rupee you "
                               "keep from the Pawprint chest, so it must not be collectable a second time.")
        else:
            rupees.append(-200)
            rep.changes.append("200 rupees removed (-200 rupees): the Silver Rupee the GameCube gave in the "
                               "Pawprint chest. In HD it is the sunken treasure of Treasure Chart 45 (Mrs. "
                               "Marie's reward, then Seven-Star Isles): salvage it to get it back.")
    # Tingle's fee for deciphering a Triforce Chart that HD does not have: HD never charges it.
    paid = [k for k in REUSED_CHARTS if g.u("map.triforce_bits") >> (k - 1) & 1]
    if paid:
        fee = DECIPHER_FEE * len(paid)
        rupees.append(fee)
        rep.changes.append("%d rupees added (+%d rupees): what you paid Tingle to decipher Triforce Chart(s) %s. "
                           "HD has no such chart%s, so an HD player never pays that." % (
                               fee, fee, ", ".join(str(k) for k in paid), "" if len(paid) == 1 else "s"))
    if rupees:
        # One balance: what is taken back and what is given back are applied together, so that neither is
        # cut short by the order they are listed in.
        limit = max(HD_WALLET[min(out.u("status_a.wallet_size"), 2)], out.u("status_a.rupee"))
        wanted = out.u("status_a.rupee") + sum(rupees)
        out.set_u("status_a.rupee", max(0, min(limit, wanted)))
        if wanted < 0:
            rep.warnings.append("%d of the rupees to take back were already spent and could not be removed" %
                                -wanted)
        elif wanted > limit:
            rep.warnings.append("%d of the rupees to give back do not fit: the wallet holds %d" % (
                wanted - limit, limit))
    if b == "rewards":
        out.set_event_bit(MARIE_EVENT, False)
        rep.changes.append("Mrs. Marie's reward for 40 Joy Pendants is pending again (by rewards): in HD it is "
                           "Treasure Chart 45, which you do not have. Bring her one more Joy Pendant to get it.")

    # --- Tingle Tuner ---------------------------------------------------------------------------
    # Same event, slot and item number in both games: the item is HD's Tingle Bottle. Nothing to change.
    if _item(out, layout.SLOT_TINGLE) == ITEM_TINGLE:
        rep.changes.append("The Tingle Tuner is now the Tingle Bottle: HD replaced the item (same event, same "
                           "inventory slot).")

    # --- Lenzo's Picto Box quest ------------------------------------------------------------------
    if _lenzo_stuck(g):
        if options.lenzo == "steps" or not _couple_on_street(g):       # no way back: only "steps" works
            if not _couple_on_street(g):
                rep.warnings.append("Lenzo's case was translated by steps whatever was chosen: the couple of "
                                    "the third picture no longer meets on the street in this file (register "
                                    "0xB907 is %d), so the picture could not be taken again" %
                                    g.event_reg(0xB907))
            _set_item(out, layout.SLOT_CAMERA, ITEM_DELUXE_PICTO_BOX)
            _set_get_bits(out, layout.SLOT_CAMERA, _get_bits(out, layout.SLOT_CAMERA) | 2)
            rep.changes.append("Deluxe Picto Box added (Lenzo by steps): HD gives it when he accepts the third "
                               "picture, which he already did.")
            took = _take_spoil(out, *JOY_PENDANT)
            rep.changes.append("One Joy Pendant removed: the GameCube gave it for that picture and HD does not."
                               if took else "The Joy Pendant the GameCube gave for that picture could not be "
                               "removed: you no longer hold one.")
        else:
            out.set_event_reg(LENZO_REG, 5)
            rep.changes.append("Lenzo's third task is pending again (by rewards): bring him the picture of the "
                               "couple again and HD gives the Deluxe Picto Box. You keep the Joy Pendant.")

    # --- HD-only choices --------------------------------------------------------------------------
    if options.swift_sail and _item(out, layout.SLOT_SAIL) == ITEM_SAIL:
        _set_item(out, layout.SLOT_SAIL, ITEM_SWIFT_SAIL)
        _set_get_bits(out, layout.SLOT_SAIL, _get_bits(out, layout.SLOT_SAIL) | 2)
        rep.changes.append("Sail upgraded to the Swift Sail (--swift-sail): an HD-only item, normally won at the "
                           "Windfall auction.")
    if options.hero_mode:
        opt = bytearray(extra["options"])
        opt[hd.OPT_HERO_MODE] = 1
        extra["options"] = bytes(opt)
        rep.changes.append("Hero Mode enabled (--hero-mode): an HD-only setting.")

    # --- flags HD sets under other conditions, or never (found in no real HD file) ---------------------
    off = layout.FIELDS["collect.collect"][0] + 3
    out.data[off] &= ~0x02 & 0xFF       # set by the GameCube collection menu only (d_menu_collect.cpp:3744)
    tuner = [f for f in TUNER_FLAGS if out.event_bit(f)]
    for f in tuner:
        out.set_event_bit(f, False)
    if tuner:
        rep.changes.append("Tingle Tuner flags cleared (%s): only the Game Boy Advance link sets them, so no HD "
                           "file has them. Two of them changed Tingle's lines (Knuckle found with the Tuner, "
                           "a Tuner message sent); Knuckle appears in HD once the five Tingle Statues are "
                           "found." % ", ".join("0x%04X" % f for f in tuner))
    if out.event_bit(WHIRLPOOL_HINT) and _item(out, layout.SLOT_BOMBS) == NO_ITEM:
        out.set_event_bit(WHIRLPOOL_HINT, False)
        rep.changes.append("Flag 0x1940 cleared: it selects a line of the King of Red Lions after a whirlpool. "
                           "The GameCube sets it always, HD only when you own bombs, and you do not.")
    if out.event_bit(HINTS_DONE) and _item(out, layout.SLOT_SAIL) != ITEM_SWIFT_SAIL:
        out.set_event_bit(HINTS_DONE, False)
        rep.changes.append("Flag 0x2B04 cleared: the two Windfall gossips have told all their hints. In HD their "
                           "last hint is about the Swift Sail and they only finish once you own it, so they "
                           "will tell you that one.")

    # --- 4. state that HD keeps in its own records -------------------------------------------------
    # Z-targeting mode: GameCube config.attention_type, HD options byte 0
    opt = bytearray(extra["options"])
    opt[hd.OPT_LOCK_ON] = g.u("config.attention_type")
    extra["options"] = bytes(opt)

    inv = bytearray(extra["inventory"])
    # Carlov's figurine being sculpted: GameCube register 0xA9FF, HD queue of up to 12 figures
    if g.event_bit(0x2F01) or (g.event_bit(0x3080) and not g.event_bit(0x4080)):
        inv[hd.INV_ENTRIES] = g.event_reg(0xA9FF)
        inv[hd.INV_COUNT] = 1
        rep.changes.append("Carlov's pending figurine moved to HD's figurine queue: HD keeps it in a record of "
                           "its own.")
    # auction item re-offered after losing: GameCube register 0xCD03, HD record byte
    if g.event_bit(0x4008):
        inv[hd.INV_AUCTION_ITEM] = g.event_reg(0xCD03)
    extra["inventory"] = bytes(inv)

    # Fishmen: HD remembers the sectors whose Fishman already drew the chart in its play log; GameCube
    # uses the "charted" bit itself. The three sectors charted from the start are not recorded.
    log = bytearray(extra["playlog"])
    fmap = g.raw("map.fmap_bits")
    for sector in range(49):
        if fmap[sector] & 1 and sector not in hd.PRECHARTED_SECTORS:
            log[hd.PLAYLOG_FLAGS + 4 * sector + 3] |= 1
    extra["playlog"] = bytes(log)

    # --- 2.2 what HD rewrites by itself when it loads a Quest Log -----------------------------------
    # Applied here so that the written file is exactly what the game will hold after loading it.
    settled = hdcheck.load_fixups(out)
    for name, (off, size) in layout.FIELDS.items():
        if out.data[off:off + size] == settled.data[off:off + size]:
            continue
        rep.changes.append("%s: %s -> %s. HD recomputes this from the ownership flags every time it loads a "
                           "file; it is written as HD will hold it." % (
                               name, out.raw(name).hex(), settled.raw(name).hex()))
    rep.totals = _totals(g, settled)
    return settled, extra, rep


def convert(card, options=None):
    """GcCardFile -> (HdFile, [SlotReport])."""
    options = options or Options()
    for d in decisions_for(card.slots(), options):
        for s in d.slots:
            if getattr(options.for_slot(s), d.key) not in MODES:
                raise ConversionError("no choice made for '%s' in file %d (steps or rewards)" % (d.key, s + 1))
    slots, extras, reports = [], [], []
    pictures = card.pictures()
    for s, g in enumerate(card.slots()):
        if g is None:
            rep = SlotReport(s, used=False)
            rep.warnings.append("the game cannot read this file (bad checksum on the memory card, and not "
                                "restorable from the second copy); written as an empty Quest Log")
            slots.append(hd.fresh_slot())
            extras.append(hd.default_extra())
            reports.append(rep)
            continue
        out, extra, rep = convert_slot(g, s, options, card.game_code)
        if rep.used and pictures[s]:
            rep.pictures = len(pictures[s])
        slots.append(out)
        extras.append(extra)
        reports.append(rep)
    return hd.HdFile(slots, extras), reports


def convert_pictures(card):
    """The HD album files for the Picto Box pictures on the card: {file name: bytes}.
    Only for files that have pictures; HD creates the album files of the other Quest Logs itself."""
    from . import picture
    out = {}
    slots = card.slots()
    for s, blocks in enumerate(card.pictures()):
        if not blocks or slots[s] is None or slots[s].is_new():
            continue
        for key, data in picture.build_album(blocks).items():
            if key == "order":
                out["cking_pic_order%d.sav" % s] = data
            else:
                out["cking_pic%d_%s.sav" % (s, key[4:])] = data
    return out
