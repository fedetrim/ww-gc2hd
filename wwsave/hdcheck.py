"""Checks of an HD save block against what Wind Waker HD itself does and expects.

`load_fixups` re-implements what the game changes when it loads a Quest Log
(SaveMgr::startup 02720E34, saveMgrRefreshEquipment 02721730, SaveMgr::refreshGame 02721880,
dSv_info_c::card_to_memory 025BA7B0 in ZeldaWWHDDecomp/wwhd). A block the game would leave untouched
is "settled": real HD saves are (checked in the tests), and converted saves must be too.

`invariants` lists properties that hold in every real HD save of the sample collection.
"""
from . import layout
from .layout import NO_ITEM, Save

# Item of each inventory slot when its get-item bit 0 is set (bottles excluded): the table behind
# fopMsgM_getTableByte 025DB5AC, observed in real HD saves; upgrades are handled separately.
SLOT_ITEM = {0: 0x20, 1: 0x78, 2: 0x22, 3: 0x25, 4: 0x24, 5: 0x2D, 6: 0x34, 7: 0x21, 8: 0x23, 9: 0x29,
             10: 0x2A, 11: 0x2C, 12: 0x27, 13: 0x31, 18: 0x30, 19: 0x2F, 20: 0x33}
BOTTLE_SLOTS = (14, 15, 16, 17)


def _item_off(slot):
    return layout.FIELDS["item.slot%02d" % slot][0]


def _get(save, slot):
    return save.data[layout.FIELDS["get_item.slot%02d" % slot][0]]


def _bag_item(save, index):
    """item behind an item-button index (saveItemOffset in d_menu_save_bootstrap.cpp)"""
    if index < 21:
        return save.data[_item_off(index)]
    for base, name in ((0x18, "bag_item.beast"), (0x24, "bag_item.bait"), (0x30, "bag_item.reserve")):
        if base <= index < base + 8:
            return save.data[layout.FIELDS[name][0] + index - base]
    return NO_ITEM


def load_fixups(save):
    """Returns a copy of `save` as HD holds it right after loading."""
    s = save.copy()
    sel = layout.FIELDS["status_a.select_item"][0]

    def refresh(button):
        # saveRefreshSelection: a button whose inventory slot is empty is cleared
        if s.data[sel + button] != NO_ITEM and _bag_item(s, s.data[sel + button]) == NO_ITEM:
            s.data[sel + button] = NO_ITEM

    s.set_u("config.sound_mode", 2)
    for slot, item in SLOT_ITEM.items():
        if _get(s, slot) & 1:
            s.data[_item_off(slot)] = item
            if slot == 2:
                s.data[sel + 3] = 2
                refresh(3)
    if _get(s, 1) & 2:
        s.data[_item_off(1)] = 0x77
        s.data[sel + 4] = 1
        refresh(4)
    if _get(s, 8) & 2:
        s.data[_item_off(8)] = 0x26
    if _get(s, 12) & 4:
        s.data[_item_off(12)] = 0x36
    elif _get(s, 12) & 2:
        s.data[_item_off(12)] = 0x35
    # saveMgrRefreshEquipment
    collect = s.raw("collect.collect")
    equip = layout.FIELDS["status_a.select_equip"][0]
    for bit, item in ((3, 0x3E), (2, 0x3A), (1, 0x39), (0, 0x38)):
        if collect[0] >> bit & 1:
            s.data[equip] = item
            break
    for bit, item in ((1, 0x3C), (0, 0x3B)):
        if collect[1] >> bit & 1:
            s.data[equip + 1] = item
            break
    if collect[2] & 1:
        s.data[equip + 2] = 0x28
    s.set_u("map.triforce_bits", s.u("map.triforce_bits") | layout.HD_TRIFORCE_PRESET)
    return s


def unsettled_fields(save):
    """Fields the game would rewrite on load (empty for a settled save)."""
    fixed = load_fixups(save)
    return [name for name, (off, size) in layout.FIELDS.items()
            if save.data[off:off + size] != fixed.data[off:off + size]]


def invariants(save):
    """Violations of properties seen in all real HD saves (empty list = none)."""
    bad = []
    if save.u("info.save_count") == 0:
        return bad                        # empty Quest Log
    sel = save.raw("status_a.select_item")
    if any(b in (1, 2) for b in sel[:3]):
        bad.append("Sail or Wind Waker on an X/Y/Z button")
    if sel[3] not in (NO_ITEM, 2, 3, 0xD):
        bad.append("unexpected item on the GamePad button: %#x" % sel[3])
    if sel[4] not in (NO_ITEM, 1):
        bad.append("unexpected item on the sail button: %#x" % sel[4])
    if save.u("config.sound_mode") != 2:
        bad.append("sound mode is not 2")
    if save.u("map.triforce_bits") & layout.HD_TRIFORCE_PRESET != layout.HD_TRIFORCE_PRESET:
        bad.append("Triforce map bits 1,3,5,6,7 not set")
    if save.u("item_record.picture_num") != 0:
        bad.append("picture count not 0")
    if save.u("status_a.life") < 12 or save.u("status_a.life") > save.u("status_a.max_life"):
        bad.append("life out of range")
    if save.u("status_a.max_life") > 80:
        bad.append("more than 20 hearts")
    bad += ["would be rewritten on load: " + f for f in unsettled_fields(save)]
    return bad
