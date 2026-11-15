"""Human-readable summary of a save block (works for GameCube and HD data: same layout)."""
import struct

from . import layout
from .layout import Save

ITEM_NAMES = {
    0x1F: "Joy Pendant", 0x20: "Telescope", 0x21: "Tingle Tuner (GC) / Tingle Bottle (HD)", 0x22: "Wind Waker",
    0x23: "Picto Box", 0x24: "Spoils Bag", 0x25: "Grappling Hook", 0x26: "Deluxe Picto Box", 0x27: "Hero's Bow",
    0x28: "Power Bracelets", 0x29: "Iron Boots", 0x2A: "Magic Armor", 0x2C: "Bait Bag", 0x2D: "Boomerang",
    0x2F: "Hookshot", 0x30: "Delivery Bag", 0x31: "Bombs", 0x33: "Skull Hammer", 0x34: "Deku Leaf",
    0x35: "Bow (Fire & Ice Arrows)", 0x36: "Bow (Light Arrows)", 0x38: "Hero's Sword",
    0x39: "Master Sword", 0x3A: "Master Sword (half power)", 0x3B: "Hero's Shield", 0x3C: "Mirror Shield",
    0x3E: "Master Sword (full power)", 0x42: "Pirate's Charm", 0x43: "Hero's Charm",
    0x45: "Skull Necklace", 0x46: "Boko Baba Seed", 0x47: "Golden Feather", 0x48: "Knight's Crest",
    0x49: "Red Chu Jelly", 0x4A: "Green Chu Jelly", 0x4B: "Blue Chu Jelly",
    0x50: "Empty Bottle", 0x51: "Red Potion", 0x52: "Green Potion", 0x53: "Blue Potion",
    0x54: "Elixir Soup (half)", 0x55: "Elixir Soup", 0x56: "Water", 0x57: "Fairy", 0x58: "Forest Firefly",
    0x59: "Forest Water", 0x77: "Swift Sail (HD)", 0x78: "Sail", 0x82: "All-Purpose Bait", 0x83: "Hyoi Pear",
    0x8C: "Town Flower", 0x8D: "Sea Flower", 0x8E: "Exotic Flower", 0x8F: "Hero's Flag",
    0x90: "Big Catch Flag", 0x91: "Big Sale Flag", 0x92: "Pinwheel", 0x93: "Sickle Moon Flag",
    0x94: "Skull Tower Idol", 0x95: "Fountain Idol", 0x96: "Postman Statue", 0x97: "Shop Guru Statue",
    0x98: "Father's Letter", 0x99: "Note to Mom", 0x9A: "Maggie's Letter", 0x9B: "Moblin's Letter",
    0x9C: "Cabana Deed", 0x9D: "Complimentary ID", 0x9E: "Fill-Up Coupon",
}
SLOT_NAMES = ["Telescope", "Sail", "Wind Waker", "Grappling Hook", "Spoils Bag", "Boomerang", "Deku Leaf",
              "Tingle Tuner / Tingle Bottle", "Picto Box", "Iron Boots", "Magic Armor", "Bait Bag", "Bow",
              "Bombs", "Bottle 1", "Bottle 2", "Bottle 3", "Bottle 4", "Delivery Bag", "Hookshot",
              "Skull Hammer"]
SONGS = ["Wind's Requiem", "Ballad of Gales", "Command Melody", "Earth God's Lyric", "Wind God's Aria",
         "Song of Passing"]
PEARLS = ["Nayru's Pearl", "Din's Pearl", "Farore's Pearl"]
DUNGEON_BITS = ["map", "compass", "boss key", "boss defeated", "heart container", "boss intro seen"]
WALLET_GC, WALLET_HD = layout.WALLET_GC, layout.WALLET_HD


def item_name(item):
    if item == 0xFF:
        return None
    return ITEM_NAMES.get(item, "item 0x%02X" % item)


def _bits(value, width):
    return [i for i in range(width) if value >> i & 1]


def _cstr(raw, encoding="latin-1"):
    return raw.split(b"\0", 1)[0].decode(encoding, "replace")


def summarize(save, name=None, hd=False):
    s = save
    sword = s.raw("collect.collect")[0]
    shield = s.raw("collect.collect")[1]
    info = {
        "name": name if name is not None else _cstr(s.raw("info.player_name")),
        "hearts": "%s/%s" % (_quarters(s.u("status_a.life")), _quarters(s.u("status_a.max_life"))),
        "rupees": s.u("status_a.rupee"),
        "wallet": (WALLET_HD if hd else WALLET_GC)[min(s.u("status_a.wallet_size"), 2)],
        "magic": "%d/%d" % (s.u("status_a.magic"), s.u("status_a.max_magic")),
        "items": [item_name(b) for b in s.block("item") if b != 0xFF],
        "buttons": [(SLOT_NAMES[b] if b < 21 else "bag item 0x%02X" % b) for b in s.raw("status_a.select_item")
                    if b != 0xFF],
        "equipment": [item_name(b) for b in s.raw("status_a.select_equip") if b != 0xFF],
        "sword": ["none", "Hero's Sword", "Master Sword", "Master Sword (half)", "Master Sword (full)"][
            4 if sword & 8 else 3 if sword & 4 else 2 if sword & 2 else 1 if sword & 1 else 0],
        "shield": ["none", "Hero's Shield", "Mirror Shield"][2 if shield & 2 else 1 if shield & 1 else 0],
        "arrows": "%d/%d" % (s.u("item_record.arrow_num"), s.u("item_max.arrow_max")),
        "bombs": "%d/%d" % (s.u("item_record.bomb_num"), s.u("item_max.bomb_max")),
        "spoils": _bag(s, "beast"), "bait": _bag(s, "bait"), "delivery": _bag(s, "reserve"),
        "songs": [SONGS[i] for i in _bits(s.u("collect.tact"), 6)],
        "triforce_shards": [i + 1 for i in _bits(s.u("collect.triforce"), 8)],
        "triforce_charts_deciphered": [i + 1 for i in _bits(s.u("map.triforce_bits"), 8)],
        "pearls": [PEARLS[i] for i in _bits(s.u("collect.symbol"), 3)],
        "charts_owned": bin(int.from_bytes(s.raw("map.get_map"), "big")).count("1"),
        "charts_opened": bin(int.from_bytes(s.raw("map.open_map"), "big")).count("1"),
        "charts_completed": bin(int.from_bytes(s.raw("map.complete_map"), "big")).count("1"),
        "sea_squares_mapped": sum(1 for b in s.raw("map.fmap_bits") if b & 1),
        "dungeons": {},
        "location": "%s room %d point %d" % (_cstr(s.raw("return_place.stage")),
                                             struct.unpack(">b", s.raw("return_place.room"))[0],
                                             s.u("return_place.point")),
        "time_of_day": round(struct.unpack(">f", s.raw("status_b.time"))[0] / 15.0, 2),
        "deaths": s.u("info.death_count"),
        "clear_count": s.u("info.clear_count"),
        "save_count": s.u("info.save_count"),
        "pictures": s.u("item_record.picture_num"),
    }
    for i in range(2, 9):
        bits = s.u("memory%02d.dungeon_item" % i)
        keys = s.u("memory%02d.key_num" % i)
        if bits or keys:
            info["dungeons"][layout.STAGE_NAMES[i]] = (
                [DUNGEON_BITS[b] for b in _bits(bits, 6)] + (["%d small key(s)" % keys] if keys else []))
    return info


def _quarters(v):
    return ("%d" % (v // 4)) if v % 4 == 0 else ("%.2f" % (v / 4.0)).rstrip("0")


_BEAST_KIND = {0x45: 0, 0x46: 1, 0x47: 2, 0x48: 3, 0x49: 4, 0x4A: 5, 0x4B: 6, 0x1F: 7}


def _bag(s, kind):
    items = s.raw("bag_item." + kind)
    nums = s.raw("bag_item_record.%s_num" % kind)
    out = []
    for slot, item in enumerate(items):
        # Spoils counters are indexed by kind (dBeastIdx), bait and delivery counters by bag slot.
        n = nums[_BEAST_KIND.get(item, slot)] if kind == "beast" else nums[slot]
        if item != 0xFF:
            out.append("%s x%d" % (item_name(item), n) if n > 1 else item_name(item))
    return out


def format_summary(info, indent="  "):
    lines = []

    def add(label, value):
        if isinstance(value, (list, tuple)):
            value = ", ".join(str(v) for v in value) if value else "-"
        lines.append("%s%-22s %s" % (indent, label + ":", value))

    add("Name", info["name"])
    add("Hearts", info["hearts"])
    add("Rupees", "%d (wallet %d)" % (info["rupees"], info["wallet"]))
    add("Magic", info["magic"])
    add("Sword / shield", "%s / %s" % (info["sword"], info["shield"]))
    add("Items", info["items"])
    add("Item buttons", info["buttons"])
    add("Arrows / bombs", "%s / %s" % (info["arrows"], info["bombs"]))
    add("Spoils bag", info["spoils"])
    add("Bait bag", info["bait"])
    add("Delivery bag", info["delivery"])
    add("Songs", info["songs"])
    add("Pearls", info["pearls"])
    add("Triforce shards", info["triforce_shards"])
    add("Charts", "%d owned, %d opened, %d completed; %d/49 sea squares mapped" % (
        info["charts_owned"], info["charts_opened"], info["charts_completed"], info["sea_squares_mapped"]))
    for stage, things in info["dungeons"].items():
        add(stage, things)
    add("Location", info["location"])
    add("Deaths / clears", "%d / %d" % (info["deaths"], info["clear_count"]))
    return "\n".join(lines)
