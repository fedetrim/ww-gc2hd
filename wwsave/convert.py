"""GameCube Wind Waker save -> Wind Waker HD save.

Every rule is documented in docs/DIFFERENCES.md (section numbers in the comments).
Rules that are not a 1:1 translation are controlled by `Options`; `Decision` objects describe
each choice that applies to a card.
"""
import unicodedata
from dataclasses import dataclass, field, replace

from . import hd, hdcheck, layout
from .layout import NO_ITEM

ITEM_TINGLE, ITEM_WIND_WAKER, ITEM_PICTO_BOX = layout.ITEM_TINGLE, layout.ITEM_WIND_WAKER, layout.ITEM_PICTO_BOX
ITEM_DELUXE_PICTO_BOX, ITEM_SWIFT_SAIL, ITEM_SAIL = (layout.ITEM_DELUXE_PICTO_BOX, layout.ITEM_SWIFT_SAIL,
                                                     layout.ITEM_SAIL)

# Collect maps (charts) whose GameCube item is a Triforce Chart and whose HD item is a new
# Treasure Chart (DIFFERENCES 3.1): collect map number -> HD Treasure Chart number.
REUSED_CHARTS = {2: 42, 4: 43, 6: 44, 7: 45, 8: 46}
HD_TRIFORCE_PRESET = layout.HD_TRIFORCE_PRESET

# Places whose GameCube reward was replaced by one of those HD charts (DIFFERENCES 3.2):
# collect map -> (how the save records that the place was already collected, description)
HD_CHART_SOURCES = {
    4: (("tbox", 1, 26), "Horseshoe Island north-western lookout chest (GameCube: Skull Necklace)"),
    6: (("tbox", 1, 11), "Star Belt Archipelago lookout chest (GameCube: Red Rupee)"),
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
# Set only through the Tingle Tuner on the GameCube; HD has no setter (0 of 56 real HD Quest Logs):
# Knuckle found, Tuner message sent, two Tuner states, Tuner trigger area.
TUNER_FLAGS = (0x1708, 0x1A20, 0x1A08, 0x1A10, 0x2E08)
WHIRLPOOL_HINT = 0x1940     # GameCube: set in every whirlpool; HD: only with the bomb bag (d_a_ship.cpp:3481)
HINTS_DONE = 0x2B04         # gossips' hints all told; HD needs the Swift Sail for the last one
GHOST_SHIP_REG = 0x8803     # 3 once the Ghost Ship chest scene has ended: the ship never appears again
LOOKOUT_CASES = {"horseshoe_chest": 4, "star_belt_chest": 6}      # option -> collect map of the HD chart
MODES = ("steps", "rewards")
MIN_MAX_LIFE = 12                       # three hearts, in quarters: what a new file has
DECIPHER_FEE = 398                      # what Tingle charges per Triforce Chart, both games
HD_WALLET = layout.WALLET_HD
HD_BUTTONS = ("X", "Y", "R (the GameCube's Z)")     # the three item buttons, by index in select_item
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
    hd_region: str = "usa"              # the HD game the file is for: "usa" | "europe" (hd.REGIONS)

    CASES = ("triforce_chart_2", "triforce_chart_4", "triforce_chart_6", "triforce_chart_7",
             "triforce_chart_8", "horseshoe_chest", "star_belt_chest", "floor50", "marie", "pawprint_chest",
             "lenzo")           # asking order: what Mrs. Marie and the Pawprint chest imply depends on the
                                # answers before them

    def for_slot(self, slot):
        """The options of one file: a case may hold {file index: mode} instead of one mode for all."""
        return replace(self, **{k: getattr(self, k).get(slot) for k in self.CASES + ("name",)
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
    choices: list           # [(value, description)]; there is no default
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
    unhealthy: list = field(default_factory=list)   # why the file was not converted (see health)


def _map_bit(save, field_name, n):
    """collect map n (1-based) in one of the 128-bit chart flag sets"""
    return layout.chart_bit(save.raw(field_name), n)


def _set_map_bit(save, field_name, n, on):
    off = layout.FIELDS[field_name][0] + 4 * ((n - 1) >> 5)
    word = int.from_bytes(save.data[off:off + 4], "big")
    mask = 1 << ((n - 1) & 31)
    word = (word | mask) if on else (word & ~mask)
    save.data[off:off + 4] = word.to_bytes(4, "big")


def _collected(save, flag):
    """Chest flag ("tbox", stage record, bit) of a save."""
    return bool(save.u("memory%02d.tbox" % flag[1]) >> flag[2] & 1)


def _set_tbox(save, record, bit, on):
    name = "memory%02d.tbox" % record
    save.set_u(name, (save.u(name) | 1 << bit) if on else (save.u(name) & ~(1 << bit)))


def _take_spoil(save, index, item):
    """Remove one spoil (Spoils Bag counter `index`, item number `item`). Returns None if none is left,
    else a note for the report (empty unless the last one was on an item button, which is then emptied)."""
    counts = bytearray(save.raw("bag_item_record.beast_num"))
    if not counts[index]:
        return None
    note = ""
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
                        note = " It was your last one, so the %s button it was on is now empty." % HD_BUTTONS[b]
        save.set_raw("bag_item.beast", bytes(bag))
        save.set_raw("status_a.select_item", bytes(sel))
    return note


def _with_owned_items(g):
    """A copy of a GameCube file with its inventory as HD will hold it: HD puts the item back in every slot
    whose ownership bit is set when it loads a file (hdcheck.load_fixups). In a healthy file that only fills
    empty slots (the bow taken away in the final battle). Every rule reads the inventory from this copy."""
    fixed = hdcheck.load_fixups(g)
    out = g.copy()
    for slot in range(21):
        out.set_raw("item.slot%02d" % slot, fixed.raw("item.slot%02d" % slot))
    return out


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


def _triforce_chest_open(g, k):
    """The chest that holds Triforce Chart k on the GameCube (for chart 4, any of the Ghost Ship's three
    copies of it)."""
    record, bits = TRIFORCE_CHESTS[k]
    return any(_collected(g, ("tbox", record, b)) for b in bits)


def _stuck_chart(g, k):
    """GameCube Triforce Chart k owned, its shard not salvaged yet."""
    return _map_bit(g, "map.get_map", k) and not g.u("collect.triforce") >> (k - 1) & 1


_item = layout.item


def _set_item(save, slot, item):
    save.data[layout.FIELDS["item.slot%02d" % slot][0]] = item


_get_bits = layout.get_bits


def _set_get_bits(save, slot, value):
    save.data[layout.FIELDS["get_item.slot%02d" % slot][0]] = value


def _hd_buttons(save, select_field, item_fmt):
    """HD item buttons: [0..2] X/Y/Z, [3] GamePad button (Wind Waker), [4] sail button."""
    sel = bytearray(save.raw(select_field))
    moved = []
    for i in range(3):
        if sel[i] in (layout.SLOT_SAIL, layout.SLOT_WIND_WAKER):
            moved.append(HD_BUTTONS[i])
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
    folded = unicodedata.normalize("NFKC", name).strip()
    kept = folded[:hd.NAME_CHARS]               # only what is written has to be in the HD font
    if not kept.strip():
        return "Link", "name %r is empty; using 'Link'" % name
    if not all(0x20 <= ord(c) < 0x250 and not 0x7F <= ord(c) < 0xA0 for c in kept):
        return "Link", "name %r cannot be shown by the HD font; using 'Link'" % name
    if len(folded) > hd.NAME_CHARS:
        short = folded[:hd.NAME_CHARS].rstrip()
        return short, "name %r shortened to %r (HD allows 8 characters%s)" % (
            name, short, "; a space left at the end is dropped" if len(short) < hd.NAME_CHARS else "")
    if folded != name:
        why = ("spaces at the ends removed" if folded == name.strip() else
               "characters replaced by their plain form")
        return folded, "name %r written as %r (%s)" % (name, folded, why)
    return folded, None


_STEPS = "by steps: "
_REWARDS = "by rewards: "


def decisions_for(slots, options=None):
    """The cases these GameCube files are in (list of Decision, in asking order). `options` matters for the
    texts: an answer already given to one case changes what the answers to another imply (floor 50 by
    rewards keeps the Pawprint chest open, so that case is then about its Silver Rupee only)."""
    all_options = options or Options()
    out = {}

    def need(key, question, steps, rewards, s):
        choices = [("steps", _STEPS + steps), ("rewards", _REWARDS + rewards)]
        d = out.setdefault(key, Decision(key, question, choices))
        d.slots.append(s)
        d.per_slot[s] = (question, choices)

    for s, g in enumerate(slots):
        if not is_converted(g):                             # no cases for a file that is not converted
            continue
        g = _with_owned_items(g)
        opts = all_options.for_slot(s)
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
                 "Chart 46 owned and salvaged%s). " % (
                     "; the Silver Rupee taken from that chest follows the answer to the Pawprint case"
                     if _collected(g, PAWPRINT_CHEST) else "") + (
                     "The floor-50 chest then follows the Mrs. Marie case: it stays open if you keep the "
                     "Hero's Charm there, and is closed again otherwise" if marie else
                     "The floor-50 chest is closed again; open it in HD to get the Hero's Charm"), s)
        if _collected(g, PAWPRINT_CHEST):
            # Floor 50 by rewards keeps this chest open with its chart salvaged whatever is answered here,
            # so the answer is then about the Silver Rupee only. While floor 50 is not answered, say both.
            question = ("%s is open. In HD it holds Treasure Chart 46 (which leads to a Piece of Heart), and "
                        "the Silver Rupee is the sunken treasure of Treasure Chart 45 (Mrs. Marie's reward)." %
                        HD_CHART_SOURCES[8][1])
            paw_lose = ("lose the Silver Rupee (200 rupees, as far as still held); in HD you get it by "
                        "salvaging the treasure of Treasure Chart 45")
            # kept, the rupee's HD place has to be marked done, which needs Treasure Chart 45 in hand
            if marie and opts.marie == "steps":
                paw_keep = ("keep the Silver Rupee; the treasure of Treasure Chart 45, which you get from "
                            "Mrs. Marie by steps, is marked as salvaged")
            elif marie and opts.marie is None:
                paw_keep = ("keep the Silver Rupee. With Mrs. Marie by steps the treasure of Treasure Chart 45 "
                            "is marked as salvaged; with Mrs. Marie by rewards you do not have that chart yet, "
                            "and its treasure stays to be found: a second Silver Rupee (a chart cannot be "
                            "marked as salvaged before it is owned)")
            else:
                paw_keep = ("keep the Silver Rupee. You do not have Treasure Chart 45 yet%s, so its treasure "
                            "cannot be marked as salvaged and stays to be found: a second Silver Rupee, which "
                            "an HD player does not get" % (" (Mrs. Marie by rewards)" if marie else ""))
            if f50 and opts.floor50 == "rewards":
                need("pawprint_chest", question + " Floor 50 by rewards keeps this chest open with the chart "
                     "salvaged, so this answer is about the Silver Rupee only.",
                     "you " + paw_lose, "you " + paw_keep, s)
            elif f50 and opts.floor50 is None:
                need("pawprint_chest", question + " With floor 50 by rewards the chest stays open with its "
                     "chart already salvaged whatever is answered here, and this answer is about the Silver "
                     "Rupee only.",
                     "you " + paw_lose + ". With floor 50 by steps you also get Treasure Chart 46, its "
                     "treasure still to be salvaged",
                     "you " + paw_keep + ". With floor 50 by steps the chest is closed again; open it in HD to "
                     "get the chart", s)
            else:
                need("pawprint_chest", question,
                     "the chest stays open: you get Treasure Chart 46 and " + paw_lose,
                     "the chest is closed again; open it in HD to get the chart. You " + paw_keep, s)
        if marie:
            if not f50:
                lose = "and lose the Hero's Charm until you open the floor-50 chest in HD"
            elif opts.floor50 == "steps":
                lose = "and keep the Hero's Charm (the floor-50 chest stays open)"
            elif opts.floor50 == "rewards":
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
        if _lenzo_stuck(g):
            need("lenzo",
                 "Lenzo accepted the third picture and the Picto Box is not the Deluxe one. On the GameCube "
                 "that gave a Joy Pendant and the Deluxe Picto Box came later for a Forest Firefly; HD gives "
                 "the Deluxe Picto Box for the third picture and a Joy Pendant for each firefly.",
                 "the third picture stays accepted: you get the Deluxe Picto Box and lose the Joy Pendant "
                 "(if still held)",
                 "the third task is pending again; bring Lenzo that picture in HD to get the Deluxe Picto "
                 "Box. You keep the Joy Pendant", s)
    return [out[k] for k in Options.CASES if k in out]


def is_converted(g):
    """Whether a file of the card is translated: it is readable, used, and healthy. The one test every part
    of the tool uses (cases, pictures, report, rigs)."""
    return g is not None and not g.is_new() and not health(g)


def health(g):
    """What makes a used GameCube file one that normal play cannot have written (empty list: healthy).
    The conversion rules rely on each of these, so a file that fails one is not converted at all: it would
    have to be repaired first, and guessing how is not this tool's job."""
    bad = []
    if not MIN_MAX_LIFE <= g.u("status_a.max_life") <= 80:
        bad.append("maximum life is %s (3 to 20 hearts are possible)" % _hearts(g.u("status_a.max_life")))
    if g.u("status_a.life") > g.u("status_a.max_life"):
        bad.append("current life is above the maximum")
    if g.u("status_a.life") < MIN_MAX_LIFE:     # the game saves at least three hearts (d_save.cpp:1710)
        bad.append("current life is %s (the game never saves less than 3 hearts)" % _hearts(g.u("status_a.life")))
    if g.u("status_a.wallet_size") > 2:
        bad.append("wallet size %d does not exist" % g.u("status_a.wallet_size"))
    elif g.u("status_a.rupee") > layout.WALLET_GC[g.u("status_a.wallet_size")]:
        bad.append("%d rupees do not fit in the wallet (%d)" % (
            g.u("status_a.rupee"), layout.WALLET_GC[g.u("status_a.wallet_size")]))
    if g.u("config.attention_type") not in (0, 1):
        bad.append("targeting mode %d does not exist" % g.u("config.attention_type"))
    if g.u("item_record.picture_num") > 3:
        bad.append("%d pictures (the Picto Box holds 3)" % g.u("item_record.picture_num"))
    if _item(g, layout.SLOT_SAIL) == ITEM_SWIFT_SAIL or _get_bits(g, layout.SLOT_SAIL) & 2:
        bad.append("the Swift Sail, which the GameCube game does not have")
    as_loaded = hdcheck.load_fixups(g)
    for slot in range(21):
        if slot in hdcheck.BOTTLE_SLOTS or _item(g, slot) == NO_ITEM:
            continue                            # an empty slot with its flag set is normal (see below)
        if not _get_bits(g, slot) & 1:
            bad.append("inventory slot %d holds item 0x%02X without its ownership flag" % (slot, _item(g, slot)))
        elif _item(as_loaded, slot) != _item(g, slot):
            bad.append("inventory slot %d holds item 0x%02X, but its ownership flags (0x%02X) are those of "
                       "item 0x%02X" % (slot, _item(g, slot), _get_bits(g, slot), _item(as_loaded, slot)))
    for k in REUSED_CHARTS:
        chest = _triforce_chest_open(g, k)
        chart = _map_bit(g, "map.get_map", k)
        shard = bool(g.u("collect.triforce") >> (k - 1) & 1)
        if shard and not chart:
            bad.append("Triforce Shard %d without Triforce Chart %d, which leads to it" % (k, k))
        if g.u("map.triforce_bits") >> (k - 1) & 1 and not chart:
            bad.append("Triforce Chart %d was deciphered by Tingle but is not owned" % k)
        if chart != chest:
            bad.append("Triforce Chart %d is %s but the %s chest that holds it is %s" % (
                k, "owned" if chart else "not owned", TRIFORCE_PLACES[k], "open" if chest else "closed"))
    charm = bool(g.raw(HEROS_CHARM[0])[HEROS_CHARM[1]] & HEROS_CHARM[2])
    if charm != g.event_bit(MARIE_EVENT):
        bad.append("the Hero's Charm is %s but Mrs. Marie's reward, which is the charm, is %s" % (
            "held" if charm else "not held", "given" if g.event_bit(MARIE_EVENT) else "not given"))
    if _collected(g, SAVAGE_FLOOR_50) and g.u("status_a.max_life") <= MIN_MAX_LIFE:
        bad.append("the Savage Labyrinth floor-50 chest is open but the file has no Piece of Heart from it")
    ghost = _triforce_chest_open(g, 4)
    if (g.event_reg(GHOST_SHIP_REG) == 3) != ghost:
        bad.append("the Ghost Ship is %s but its chest is %s" % (
            "cleared" if g.event_reg(GHOST_SHIP_REG) == 3 else "not cleared", "open" if ghost else "closed"))
    deluxe = _item(g, layout.SLOT_CAMERA) == ITEM_DELUXE_PICTO_BOX or _get_bits(g, layout.SLOT_CAMERA) & 2
    if deluxe and g.event_reg(LENZO_REG) < 6:
        bad.append("the Deluxe Picto Box is held before Lenzo's third task is done")
    if g.event_reg(LENZO_REG) >= 6 and _item(g, layout.SLOT_CAMERA) == NO_ITEM \
            and not _get_bits(g, layout.SLOT_CAMERA):
        bad.append("Lenzo's third task is done without a Picto Box")
    if g.event_reg(0xB907) >= 2 and not deluxe:
        bad.append("Anton and Linda are a couple (which needs a colour picture) without the Deluxe Picto Box")
    return bad


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
    extra = hd.default_extra()
    if not rep.used:
        # An unused GameCube file has no name. It becomes an empty HD Quest Log.
        return hd.fresh_slot(), extra, rep
    problems = health(g)
    if problems:
        # Not a file normal play can have written: it is not translated at all (no repair is attempted).
        rep.used = False
        rep.unhealthy = problems
        rep.warnings.append("NOT CONVERTED, written as an empty Quest Log: normal play cannot have written "
                            "this file (edited, made with glitches, or damaged), and the tool translates "
                            "consistent files only: " + "; ".join(problems))
        return hd.fresh_slot(), extra, rep
    card_file, g = g, _with_owned_items(g)                  # see _with_owned_items: one inventory for all rules
    out = g.copy()
    for name in hdcheck.changed_fields(card_file, g):
        rep.changes.append("%s: %s -> %s. The file owns that item (its ownership flag is set) but the slot was "
                           "empty; HD puts the item back every time it loads a file, so it is written that "
                           "way." % (name, card_file.raw(name).hex(), g.raw(name).hex()))

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
    # Conventions of the HD file that change nothing the player holds: listed in one line of the report.
    conventions = ["the player name is kept in HD's name record"]
    if out.u("config.sound_mode") != 2:
        conventions.append("the sound setting is the value HD writes on every load")
    if out.u("map.triforce_bits") & HD_TRIFORCE_PRESET != HD_TRIFORCE_PRESET:
        conventions.append("the decipher marks of the five Triforce Charts HD does not have are set, as in "
                           "every HD file")
    if any(_collected(g, ("tbox", TRIFORCE_CHESTS[4][0], b)) for b in TRIFORCE_CHESTS[4][1][1:]) \
            and not (_stuck_chart(g, 4) and options.triforce_chart_4 == "rewards"):
        conventions.append("the Ghost Ship chest is recorded under the one flag HD has for it")
    conventions.append("the inventory snapshots for the boss rematches use HD's button layout")
    if _item(out, layout.SLOT_WIND_WAKER) == ITEM_WIND_WAKER or _item(out, layout.SLOT_SAIL) in (
            ITEM_SAIL, ITEM_SWIFT_SAIL):
        conventions.append("the Wind Waker and the Sail are assigned to the dedicated buttons HD has for them")
    if g.raw("return_place.stage").split(b"\0", 1)[0].ljust(8, b"\0") != g.raw("return_place.stage"):
        conventions.append("the name of the place the file returns to is padded as HD pads it")
    if any(g.raw("map.fmap_bits")[sector] & 1 for sector in range(49) if sector not in hd.PRECHARTED_SECTORS):
        conventions.append("the sea sectors a Fishman has charted are also noted in HD's play log, where HD "
                           "remembers that he was met")
    rep.changes.append("File conventions of HD applied, with no effect on what you hold: %s." %
                       "; ".join(conventions))
    out.set_u("config.sound_mode", 2)
    out.set_u("map.triforce_bits", out.u("map.triforce_bits") | HD_TRIFORCE_PRESET)
    if out.u("item_record.picture_num") or out.event_reg(0x89FF) or any(
            out.u("status_c%d.picture_num" % i) for i in range(4)):
        rep.changes.append("Picture counts (also in the inventory snapshots for the boss rematches) and the "
                           "list of erased picture slots set to 0: HD keeps the pictures and their count in "
                           "the album files, not in the save.")
    out.set_u("item_record.picture_num", 0)
    out.set_event_reg(0x89FF, 0)       # GameCube: picture slots erased this session; cleared when it loads
    for i in range(4):
        out.set_u("status_c%d.picture_num" % i, 0)

    # Outset, after Aryll's kidnapping (event 0x0E20): files from normal HD play carry switch 1 of the
    # sea stage from then on; GameCube never sets it. Switch 9 (the scene's trigger) means the same in
    # both games and is kept.
    if out.event_bit(OUTSET_KIDNAP_EVENT) and not out.u("memory00.switch") >> (96 + HD_OUTSET_SWITCH) & 1:
        out.set_u("memory00.switch", out.u("memory00.switch") | 1 << (96 + HD_OUTSET_SWITCH))
        rep.changes.append("Sea switch 1 set: in HD the scene of Aryll's kidnapping on Outset, which this file "
                           "has seen, starts another way and leaves that switch set.")

    # sea chart: bit 1 of a sector is the GameCube "arrived" mark kept for the Tingle Tuner. HD never
    # sets it (and has no reader); only the three sectors charted from the start carry it.
    fmap = bytearray(out.raw("map.fmap_bits"))
    arrived = sum(1 for sector in range(49) if sector not in hd.PRECHARTED_SECTORS and fmap[sector] & 2)
    for sector in range(49):
        if sector not in hd.PRECHARTED_SECTORS:
            fmap[sector] &= ~2 & 0xFF
    out.set_raw("map.fmap_bits", bytes(fmap))
    if arrived:
        rep.changes.append("'Arrived' mark cleared in %d sea sectors: the GameCube keeps it for the Tingle "
                           "Tuner, HD never sets it. What is charted and visited is unchanged." % arrived)

    # item buttons: HD has dedicated buttons for the Wind Waker and the sail; X/Y/Z never hold them
    moved = _hd_buttons(out, "status_a.select_item", "item.slot%02d")
    if moved:
        rep.changes.append("Button(s) %s emptied: they held the Sail or the Wind Waker. HD has dedicated buttons "
                           "for both and never keeps them on an item button." % ", ".join(moved))
    # recollection records (inventory snapshots for the boss rematches): GameCube leaves an unused
    # record zeroed, HD fills it with the values of an empty inventory
    menu_flag = 0
    for i in range(4):
        block = "status_c%d" % i
        off, size = layout.BLOCKS[block]
        if not any(out.data[off:off + size]):
            out.data[off:off + size] = hd.EMPTY_RECOLLECTION
        else:
            _hd_buttons(out, block + ".a_select_item", block + ".item%02d")
            menu_flag |= out.data[layout.FIELDS[block + ".collect"][0] + 3] & 0x02
            out.data[layout.FIELDS[block + ".collect"][0] + 3] &= ~0x02 & 0xFF    # as in the main block, below

    # --- 3.1 charts whose ids HD reuses --------------------------------------------------------
    for k, hd_chart in REUSED_CHARTS.items():
        record, bits = TRIFORCE_CHESTS[k]
        if _triforce_chest_open(g, k):
            _set_tbox(out, record, bits[0], True)           # the Ghost Ship copy HD keeps
            for b in bits[1:]:
                _set_tbox(out, record, b, False)            # HD has no chest for the other two
        if not _map_bit(g, "map.get_map", k):
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
                out.set_event_reg(GHOST_SHIP_REG, 0)        # at 3 the ship is gone for good; it sails again
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
                                       "does not." + took if took is not None else "The Skull Necklace the "
                                       "GameCube gave in that chest could not be removed: you no longer hold "
                                       "one.")
                else:
                    rupees.append(-20)
                    rep.changes.append("20 rupees to take back: the Red Rupee the GameCube gave in that chest, "
                                       "which HD does not give.")
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
        # In HD the Hero's Charm and the floor-50 chest go together. (A healthy GameCube file holds the charm
        # exactly when Mrs. Marie gave her reward.)
        f50_open = a == "steps" or b == "rewards"
        _set_tbox(out, SAVAGE_FLOOR_50[1], SAVAGE_FLOOR_50[2], f50_open)
        if f50_open:
            out.data[charm_off] |= HEROS_CHARM[2]
            if not marie:
                rep.changes.append("Hero's Charm added (floor 50 by steps): in HD it is what the Savage "
                                   "Labyrinth floor-50 chest, which you opened, holds.")
            if not f50:
                rep.changes.append("Savage Labyrinth floor-50 chest marked as opened (Mrs. Marie by rewards): "
                                   "in HD the Hero's Charm comes from that chest, and you keep the charm, so "
                                   "the chest must not give a second one. The Piece of Heart the GameCube had "
                                   "there is under Two-Eye Reef in HD (Treasure Chart 46).")
        else:
            if marie:
                out.data[charm_off] &= ~(HEROS_CHARM[2] | HEROS_CHARM_ACTIVE) & 0xFF
                for i in range(4):              # the boss-rematch records copy the field: a record cannot
                    rec = layout.FIELDS["status_c%d.collect" % i][0] + HEROS_CHARM[1]      # hold a charm
                    out.data[rec] &= ~(HEROS_CHARM[2] | HEROS_CHARM_ACTIVE) & 0xFF         # the file lacks
                rep.changes.append("Hero's Charm removed (Mrs. Marie by steps): in HD she gives Treasure Chart "
                                   "45 instead, and the charm is in the Savage Labyrinth floor-50 chest (%s). "
                                   "Open it to get the charm back." % (
                                       "closed again" if f50 else "not opened yet"))
            if f50:
                rep.changes.append("Savage Labyrinth floor-50 chest closed again (floor 50 by rewards): in HD it "
                                   "holds the Hero's Charm, which you do not have. Open it again to get it.")
    if a == "steps":
        max_life = out.u("status_a.max_life") - 1
        out.set_u("status_a.max_life", max_life)
        if out.u("status_a.life") > max_life:
            out.set_u("status_a.life", max_life)
            rep.changes.append("Current life lowered to %s, the new maximum." % _hearts(max_life))
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
                               "again to get the chart. You keep its Silver Rupee." % HD_CHART_SOURCES[8][1])
    if b == "steps":
        give_chart(7)
        rep.changes.append("Treasure Chart 45 added (Mrs. Marie by steps): in HD it is her reward for 40 Joy "
                           "Pendants, which she already gave you.")
    if paw:
        # The Pawprint chest's Silver Rupee is the sunken treasure of Treasure Chart 45 in HD. Kept, that
        # treasure is marked as salvaged, which needs the chart in hand; without the chart the rupee is kept
        # all the same (the answer says so) and the report warns that it can be found a second time.
        keep = options.pawprint_chest == "rewards"
        if keep:
            if a == "rewards":                  # otherwise said with the chest, above
                rep.changes.append("Pawprint chest by rewards: you keep its Silver Rupee. The chest itself "
                                   "stays open: floor 50 by rewards needs it so.")
            if b == "steps":
                give_chart(7, salvaged=True)
                rep.changes.append("Treasure Chart 45 marked as salvaged: its treasure in HD is the Silver "
                                   "Rupee you keep from the Pawprint chest, so it must not be collectable a "
                                   "second time.")
            else:
                rep.warnings.append("you keep the Silver Rupee of the Pawprint chest, and in HD the same rupee "
                                    "is the sunken treasure of Treasure Chart 45, which this file does not "
                                    "have yet (a chart cannot be marked as salvaged before it is owned): it "
                                    "can be collected once more, 200 rupees")
        else:
            rupees.append(-200)
            if a == "rewards":
                rep.changes.append("Pawprint chest by steps: the chest stays open, as floor 50 by rewards "
                                   "already has it, with Treasure Chart 46 salvaged.")
            rep.changes.append("200 rupees to take back (Pawprint chest by steps): the Silver Rupee the "
                               "GameCube gave in that chest. In HD it is the sunken treasure of Treasure "
                               "Chart 45 (Mrs. Marie's reward, then Seven-Star Isles): salvage it to get it "
                               "back.")
    # Tingle's fee for deciphering a Triforce Chart that HD does not have: HD never charges it.
    paid = [k for k in REUSED_CHARTS if g.u("map.triforce_bits") >> (k - 1) & 1]
    if paid:
        fee = DECIPHER_FEE * len(paid)
        rupees.append(fee)
        rep.changes.append("%d rupees to give back: what you paid Tingle to decipher Triforce Chart(s) %s. HD "
                           "has no such chart%s, so an HD player never pays that." % (
                               fee, ", ".join(str(k) for k in paid), "" if len(paid) == 1 else "s"))
    if rupees:
        # One balance: what is taken back and what is given back are applied together, so that neither is
        # cut short by the order they are listed in.
        limit = HD_WALLET[out.u("status_a.wallet_size")]
        before = out.u("status_a.rupee")
        wanted = before + sum(rupees)
        out.set_u("status_a.rupee", max(0, min(limit, wanted)))
        line = "Rupees after the amounts above (%+d in all): %d -> %d." % (
            sum(rupees), before, out.u("status_a.rupee"))
        if wanted < 0:
            line += " %d of the rupees to take back were already spent and could not be removed." % -wanted
        elif wanted > limit:
            line += " %d of the rupees to give back do not fit: the wallet holds %d." % (wanted - limit, limit)
        rep.changes.append(line)
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
        if options.lenzo == "steps":
            _set_item(out, layout.SLOT_CAMERA, ITEM_DELUXE_PICTO_BOX)
            _set_get_bits(out, layout.SLOT_CAMERA, _get_bits(out, layout.SLOT_CAMERA) | 2)
            rep.changes.append("Deluxe Picto Box added (Lenzo by steps): HD gives it when he accepts the third "
                               "picture, which he already did.")
            took = _take_spoil(out, *JOY_PENDANT)
            rep.changes.append("One Joy Pendant removed: the GameCube gave it for that picture and HD does not."
                               + took if took is not None else "The Joy Pendant the GameCube gave for that "
                               "picture could not be removed: you no longer hold one.")
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
    if out.data[off] & 0x02 or menu_flag:
        rep.changes.append("A flag of the GameCube collection screen cleared (collect byte 3, bit 1, also in "
                           "the records kept for the boss rematches): HD never sets it.")
    out.data[off] &= ~0x02 & 0xFF       # set by the GameCube collection menu only (d_menu_collect.cpp:3744)
    tuner = [f for f in TUNER_FLAGS if out.event_bit(f)]
    for f in tuner:
        out.set_event_bit(f, False)
    if tuner:
        rep.changes.append("Tingle Tuner flags cleared (%s): only the Game Boy Advance link sets them, so no HD "
                           "file has them.%s" % (
                               ", ".join("0x%04X" % f for f in tuner),
                               " Tingle's lines for Knuckle found with the Tuner (0x1708) and for a Tuner "
                               "message sent (0x1A20) are not said in HD, where Knuckle appears once the five "
                               "Tingle Statues are found." if set(tuner) & {0x1708, 0x1A20} else ""))
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
    # (0 hold, 1 switch). The field of the save block is 0 in every real HD Quest Log, also in the one whose
    # options record says "switch".
    opt[hd.OPT_LOCK_ON] = g.u("config.attention_type")
    extra["options"] = bytes(opt)
    out.set_u("config.attention_type", 0)
    if g.u("config.attention_type"):
        rep.changes.append("Targeting mode 'switch' carried over: HD keeps that setting in its options record.")

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
        rep.changes.append("The auction item to be offered again after a lost bid moved to HD's record for it.")
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
    for name in hdcheck.changed_fields(out, settled):
        rep.changes.append("%s: %s -> %s. HD recomputes this from the ownership flags every time it loads a "
                           "file; it is written as HD will hold it." % (
                               name, out.raw(name).hex(), settled.raw(name).hex()))
    rep.totals = _totals(card_file, settled)
    return settled, extra, rep


def convert(card, options=None):
    """GcCardFile -> (HdFile, [SlotReport])."""
    options = options or Options()
    if options.hd_region not in hd.REGIONS:
        raise ConversionError("unknown HD region %r (%s)" % (options.hd_region, " or ".join(hd.REGIONS)))
    slots, extras, reports = [], [], []
    pictures = card.pictures()
    for s, g in enumerate(card.slots()):
        if g is None:
            rep = SlotReport(s, used=False, unhealthy=["the game cannot read this file"])
            rep.warnings.append("the game cannot read this file (bad checksum on the memory card, and not "
                                "restorable from the second copy); written as an empty Quest Log")
            slots.append(hd.fresh_slot())
            extras.append(hd.default_extra())
            reports.append(rep)
            continue
        out, extra, rep = convert_slot(g, s, options, card.game_code)
        if rep.used and pictures[s]:
            rep.pictures = len(pictures[s])
        lost = g.u("item_record.picture_num") - len(pictures[s]) if rep.used else 0
        if lost > 0:
            rep.warnings.append("%d of the file's %d picture(s) could not be read from the card (damaged or "
                                "missing picture data) and %s left out" % (
                                    lost, g.u("item_record.picture_num"), "was" if lost == 1 else "were"))
        slots.append(out)
        extras.append(extra)
        reports.append(rep)
    # After everything else: each build of the HD game gives every Quest Log, used or empty, its own two
    # defaults (hd.REGIONS). A GameCube file carries its own region's value of the first.
    target = hd.REGIONS[options.hd_region]
    for rep, g in zip(reports, slots):
        if not rep.used:
            continue
        if options.hd_region != "usa":
            rep.changes.append("File written for the %s game (--hd-region %s), with no effect on what you "
                               "hold: the two settings that game gives every Quest Log differently from "
                               "the USA one are set its way (the reading-aid setting for Japanese text, "
                               "and one options byte)." % (target.game, options.hd_region))
            rep.warnings.append("the %s game itself was not run and its disc was not compared: every rule "
                                "here, and each case's two answers, was established on the USA game. A "
                                "published comparison of the two programs finds them the same except for "
                                "language code (docs/DIFFERENCES.md, 4b)" % target.game)
        elif g.u("config.ruby") != target.ruby:
            rep.changes.append("The reading-aid setting for Japanese text set to %d, with no effect on "
                               "what you hold: the %s HD game gives every Quest Log that value." % (
                                   target.ruby, target.game))
    hd.set_region(slots, extras, options.hd_region)
    return hd.HdFile(slots, extras), reports


def convert_pictures(card):
    """The HD album files for the Picto Box pictures on the card: {file name: bytes}.
    Only for files that have pictures; HD creates the album files of the other Quest Logs itself."""
    from . import picture
    out = {}
    slots = card.slots()
    for s, blocks in enumerate(card.pictures()):
        if not blocks or not is_converted(slots[s]):
            continue                            # no album for a file that is not converted
        for key, data in picture.build_album(blocks).items():
            if key == "order":
                out["cking_pic_order%d.sav" % s] = data
            else:
                out["cking_pic%d_%s.sav" % (s, key[4:])] = data
    return out
