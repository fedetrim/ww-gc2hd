"""Tests. The sample-based ones run on every save under samples/ (skipped when it is absent)."""
import glob
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from wwsave import convert as conv, gc, hd, hdcheck, layout, picture  # noqa: E402

GC_FILES = sorted(f for f in glob.glob(os.path.join(ROOT, "samples/gc/**/*.gci"), recursive=True)
                  if "Hacked_File" not in f and "/rejected/" not in f)
HD_FILES = sorted(f for f in glob.glob(os.path.join(ROOT, "samples/hd/**/cking.sav"), recursive=True)
                  if "/rejected/" not in f)
# fields no code reads and the game leaves uninitialised
GARBAGE = ("return_place._unk_a", "return_place._unk_b", "get_bag_item._unk_6", "priest.pos", "priest.angle",
           "priest.room", "config.ruby") + tuple("status_c%d.a__pad_17" % i for i in range(4))


def _read(path):
    with open(path, "rb") as f:
        return f.read()


def _used_gc_slots():
    for path in GC_FILES:
        card = gc.load(_read(path))
        for s, save in enumerate(card.slots()):
            if save is not None and not save.is_new():
                yield path, card, s, save


class Formats(unittest.TestCase):
    def test_gc_checksums(self):
        self.assertTrue(GC_FILES or not os.path.isdir(os.path.join(ROOT, "samples", "gc")))
        for path in GC_FILES:
            card = gc.load(_read(path))
            for block_ok, slots_ok in card.copy_status():
                self.assertTrue(block_ok and all(slots_ok), path)

    def test_gc_second_copy_is_used_when_first_is_damaged(self):
        save = hd.fresh_slot()
        save.set_raw("info.player_name", b"Test".ljust(17, b"\0"))
        raw = bytearray(gc.build_gci(b"GZLE01", [save, save, save]))
        raw[gc.DENTRY + gc.BLOCK + 8 + 5] ^= 0xFF          # damage file 1 in the first copy
        slots = gc.load(bytes(raw)).slots()
        self.assertEqual(bytes(slots[0]), bytes(save))
        raw[gc.DENTRY + 2 * gc.BLOCK + 8 + 5] ^= 0xFF      # and in the second
        self.assertIsNone(gc.load(bytes(raw)).slots()[0])

    def test_gc_file_2_is_restored_as_the_game_does(self):
        """mDoMemCdRWm_Restore tests the second copy's file 3, not its file 2, before restoring file 2."""
        save = hd.fresh_slot()
        save.set_raw("info.player_name", b"Test".ljust(17, b"\0"))
        raw = bytearray(gc.build_gci(b"GZLE01", [save, save, save]))
        file2, file3 = 8 + gc.GAMEDATA + 5, 8 + 2 * gc.GAMEDATA + 5
        raw[gc.DENTRY + gc.BLOCK + file2] ^= 0xFF          # file 2 damaged in the first copy
        self.assertEqual(bytes(gc.load(bytes(raw)).slots()[1]), bytes(save))        # taken from the second
        raw[gc.DENTRY + 2 * gc.BLOCK + file3] ^= 0xFF      # second copy: file 3 damaged, file 2 still good
        slots = gc.load(bytes(raw)).slots()
        self.assertIsNone(slots[1])                         # the game does not restore file 2 then
        self.assertEqual(bytes(slots[2]), bytes(save))      # file 3 comes from the first copy

    def test_gc_containers(self):
        save = hd.fresh_slot()
        gci = gc.build_gci(b"GZLE01", [save, save, save])
        self.assertEqual(gc.load(bytes(0x110) + gci).source, "gcs")
        self.assertEqual(gc.load(bytes(0x80) + gci).source, "sav")
        # raw memory card image: header, 2 directory blocks, 2 block maps, then the file
        card = bytearray(gc.BLOCK * (5 + gc.FILE_BLOCKS))
        entry = bytearray(gci[:gc.DENTRY])
        entry[0x36:0x38] = (5).to_bytes(2, "big")
        for d in (1, 2):
            card[gc.BLOCK * d:gc.BLOCK * d + gc.DENTRY] = entry
        for b in (3, 4):
            for i in range(gc.FILE_BLOCKS):
                nxt = 0xFFFF if i == gc.FILE_BLOCKS - 1 else 6 + i
                card[gc.BLOCK * b + 0x0A + 2 * i:gc.BLOCK * b + 0x0C + 2 * i] = nxt.to_bytes(2, "big")
        card[gc.BLOCK * 5:] = gci[gc.DENTRY:]
        self.assertEqual(bytes(gc.load(bytes(card)).slots()[0]), bytes(save))
        with self.assertRaises(gc.GcError):
            gc.load(b"not a save")
        # a card image without the game's file says so, not "not a card image"
        with self.assertRaisesRegex(gc.GcError, "no Wind Waker save"):
            gc.load(bytes(gc.BLOCK * 16))

    def test_hd_real_saves_roundtrip(self):
        for path in HD_FILES:
            raw = _read(path)
            f = hd.HdFile.parse(raw)                       # checksums, format word, CRC
            self.assertEqual(f.serialize(), raw, path)
            for tail in f.tails:
                self.assertFalse(any(tail), path)

    def test_hd_fresh_slot_matches_real_empty_quest_logs(self):
        fresh = hd.fresh_slot()
        skip = set()
        for name in GARBAGE:
            off, size = layout.FIELDS[name]
            skip.update(range(off, off + size))
        n = 0
        for path in HD_FILES:
            f = hd.HdFile.parse(_read(path))
            for s in range(3):
                save = f.slots[s]
                if save.u("info.save_count") or save.u("info.clear_count"):
                    continue
                n += 1
                diff = [i for i in range(layout.SAVE_SIZE) if i not in skip and save.data[i] != fresh.data[i]]
                self.assertEqual(diff, [], path)
                self.assertEqual(f.extras[s]["playlog"], hd.default_extra()["playlog"])
        self.assertTrue(n or not HD_FILES)

    def test_hd_load_model_on_real_saves(self):
        """the model of HD's load-time rewrites leaves real HD saves unchanged"""
        for path in HD_FILES:
            f = hd.HdFile.parse(_read(path))
            for save in f.slots:
                if not save.u("info.save_count"):
                    continue
                unsettled = hdcheck.unsettled_fields(save)
                if save.raw("status_a.select_item")[3] in (3, 0xD):      # sailing item left on the button
                    unsettled = [u for u in unsettled if u != "status_a.select_item"]
                self.assertEqual(unsettled, [], path)


class Pictures(unittest.TestCase):
    def test_real_hd_albums_follow_the_documented_format(self):
        n = 0
        for path in glob.glob(os.path.join(ROOT, "samples/hd/**/cking_pic_order*.sav"), recursive=True):
            raw = _read(path)
            self.assertEqual(len(raw), 205, path)
            records, order, count = picture.parse_order(raw)
            self.assertEqual(count, sum(1 for o in order if o != 0xFF), path)
            for i, (checksum, detail, used, colour, subject, size) in enumerate(records):
                pic = os.path.join(os.path.dirname(path), "cking_pic%s_%d.sav" % (path[-5], i))
                if os.path.exists(pic):
                    n += 1
                    self.assertEqual(checksum, picture.record_checksum(size, _read(pic)), pic)
        self.assertTrue(n or not HD_FILES)

    def test_cmpr_block(self):
        # one 8x8 block: four sub-blocks, each all colour 0 (red, green, blue, white)
        data = b"".join(struct_pack for struct_pack in (
            bytes.fromhex("f8000000") + bytes(4), bytes.fromhex("07e00000") + bytes(4),
            bytes.fromhex("001f0000") + bytes(4), bytes.fromhex("ffff0000") + bytes(4)))
        img = picture.decode_cmpr(data, 8, 8)
        self.assertEqual((img[0][0], img[0][4], img[4][0], img[4][4]),
                         ((255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)))

    def test_only_pictures_the_game_would_load(self):
        """An erased picture stays on the NTSC card; the count and the erased-slot register decide."""
        stale = 0
        for path in GC_FILES:
            card = gc.load(_read(path))
            for n, (g, pics) in enumerate(zip(card.slots(), card.pictures())):
                if g is None or g.is_new():
                    self.assertEqual(pics, [], path)
                    continue
                self.assertLessEqual(len(pics), g.u("item_record.picture_num"), path)
                stale += g.u("item_record.picture_num") == 0 and any(
                    any(card._copy(3 + n * 3 + i)[:0x1EE0]) for i in range(3))
        self.assertTrue(stale or not GC_FILES)      # the samples include cards with left-over picture data

    def test_album_from_gamecube_pictures(self):
        for path in GC_FILES:
            card = gc.load(_read(path))
            blocks = next((p for p in card.pictures() if p), None)
            if blocks:
                break
        else:
            self.skipTest("no GameCube sample with pictures")
        files = picture.build_album(blocks)
        self.assertEqual(sorted(files), sorted(["order"] + ["pic_%d" % i for i in range(12)]))
        records, order, count = picture.parse_order(files["order"])
        self.assertEqual(count, len(blocks))
        self.assertEqual(order[:count], list(range(count)))
        for i, (checksum, detail, used, colour, subject, size) in enumerate(records):
            data = files["pic_%d" % i]
            self.assertEqual(len(data), picture.HD_DATA_SIZE)
            self.assertEqual(checksum, picture.record_checksum(size, data))
            if i < count:
                src = picture.GcPicture(blocks[i])
                self.assertEqual((used, colour, subject, detail), (1, int(src.colour), src.subject, src.detail))
                self.assertEqual(data[:4], b"\xff\xd8\xff\xe0")
                self.assertEqual(data[size - 2:size], b"\xff\xd9")
                self.assertFalse(any(data[size:]))
                sof = data.index(b"\xff\xc0")
                self.assertEqual(data[sof + 5:sof + 9], (450).to_bytes(2, "big") + (800).to_bytes(2, "big"))
            else:
                self.assertEqual((used, size), (0, 0))
        self.assertEqual(files["order"][16 * count:16 * count + 16], bytes.fromhex("157b5558") + bytes(12))


class CommandLine(unittest.TestCase):
    """End to end through the command line, on a GameCube card file built here (no game data needed)."""

    def _run(self, *args):
        import subprocess, sys
        return subprocess.run([sys.executable, os.path.join(ROOT, "ww-gc2hd")] + list(args),
                              capture_output=True, text=True, stdin=subprocess.DEVNULL)

    def test_convert_info_verify(self):
        import tempfile
        save = hd.fresh_slot()
        save.set_raw("info.player_name", b"Tester".ljust(17, b"\0"))
        save.set_u("status_a.max_life", 48)
        save.set_u("status_a.life", 48)
        save.set_u("status_a.rupee", 150)
        save.set_u("memory13.tbox", 1 << 12)                # Savage Labyrinth floor-50 chest open
        save.set_u("map.triforce_bits", 1 << 5)             # Triforce Chart 6 deciphered
        with tempfile.TemporaryDirectory() as tmp:
            gci, out = os.path.join(tmp, "card.gci"), os.path.join(tmp, "out")
            with open(gci, "wb") as f:
                f.write(gc.build_gci(b"GZLE01", [save, save.copy(), hd.fresh_slot()]))
            self.assertIn("Tester", self._run("info", gci).stdout)
            # a case without an answer: nothing is written, the case is named
            r = self._run("convert", gci, "-o", out)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("--floor50 steps|rewards", r.stderr)
            self.assertFalse(os.path.exists(os.path.join(out, "cking.sav")))
            # answered per Quest Log
            r = self._run("convert", gci, "-o", out, "--floor50", "1=steps,2=rewards")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("One Piece of Heart removed", r.stdout)
            self.assertIn("what you paid Tingle", r.stdout)
            self.assertIn("do not fit: the wallet holds 500", r.stdout)
            self.assertIn("Maximum life:    12 hearts -> 11 hearts + 3/4", r.stdout)
            self.assertEqual(self._run("verify", out).returncode, 0)
            back = hd.HdFile.parse(_read(os.path.join(out, "cking.sav")))
            self.assertEqual([back.slots[i].u("status_a.max_life") for i in (0, 1)], [47, 48])
            self.assertEqual([back.slots[i].u("status_a.rupee") for i in (0, 1)], [500, 500])   # HD wallet limit
            self.assertEqual(back.name(0), "Tester")
            self.assertEqual(back.slots[2].u("info.save_count"), 0)
            self.assertIn("Tester", self._run("info", out).stdout)
            # an existing file is not replaced without --force
            self.assertNotEqual(self._run("convert", gci, "-o", out, "--all", "steps").returncode, 0)
            self.assertEqual(self._run("convert", gci, "-o", out, "--all", "steps", "--force").returncode, 0)
            backups = [n for n in os.listdir(out) if n.startswith("backup-")]
            self.assertEqual(len(backups), 1)
            self.assertEqual(os.listdir(os.path.join(out, backups[0])), ["cking.sav"])
            # --all answers the Quest Logs a per-Quest-Log value does not name
            r = self._run("convert", gci, "-o", out, "--force", "--all", "steps", "--floor50", "1=rewards")
            self.assertEqual(r.returncode, 0, r.stderr)
            back = hd.HdFile.parse(_read(os.path.join(out, "cking.sav")))
            self.assertEqual([back.slots[i].u("status_a.max_life") for i in (0, 1)], [48, 47])
            # an album left in the folder by another save does not stay attached to the new Quest Logs,
            # and a second --force does not destroy the first backup
            with open(os.path.join(out, "cking_pic_order1.sav"), "wb") as f:
                f.write(b"old album")
            self.assertEqual(self._run("convert", gci, "-o", out, "--force", "--all", "steps").returncode, 0)
            self.assertFalse(os.path.exists(os.path.join(out, "cking_pic_order1.sav")))
            backups = sorted(n for n in os.listdir(out) if n.startswith("backup-"))
            self.assertEqual(len(backups), 3)
            self.assertTrue(any(os.path.exists(os.path.join(out, b, "cking_pic_order1.sav")) for b in backups))
            # a name goes to one Quest Log; with two used files a bare name is refused
            r = self._run("convert", gci, "-o", out, "--force", "--all", "steps", "--name", "Zed")
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("--name 1=Zed", r.stderr)
            r = self._run("convert", gci, "-o", out, "--force", "--all", "steps", "--name", "2=Zed")
            self.assertEqual(r.returncode, 0, r.stderr)
            back = hd.HdFile.parse(_read(os.path.join(out, "cking.sav")))
            self.assertEqual([back.name(0), back.name(1)], ["Tester", "Zed"])
            r = self._run("convert", gci, "-o", out, "--force", "--all", "steps", "--name", "3=Zed")
            self.assertNotEqual(r.returncode, 0)            # Quest Log 3 is not a used file
            self.assertIn("not a used file", r.stderr)
            # a case answered for one Quest Log only: the other is still listed
            r = self._run("convert", gci, "-o", out, "--force", "--floor50", "1=steps")
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("--floor50 steps|rewards   (Quest Log 2)", r.stderr)


class Conversion(unittest.TestCase):
    # fields a conversion may change; everything else must be byte-identical to the GameCube data
    MAY_CHANGE = {"info.save_count", "info.player_name", "info._name_25", "info._name_36",
                  "config.sound_mode", "map.triforce_bits", "item_record.picture_num",
                  "status_a.select_item", "map.get_map", "map.open_map", "map.complete_map",
                  "collect.triforce", "item.slot01", "get_item.slot01", "item.slot07", "get_item.slot07",
                  "item.slot08", "get_item.slot08",
                  "item.slot12", "status_a.select_equip", "collect.collect", "memory00.switch", "map.fmap_bits", "return_place.stage",
                  "status_a.max_life", "status_a.life", "event.flags",      # floor 50, Mrs. Marie, Lenzo
                  "memory01.tbox", "memory10.tbox", "memory12.tbox", "memory13.tbox",   # chests closed again
                  "status_a.rupee", "bag_item.beast", "bag_item_record.beast_num"}     # GameCube rewards taken back

    def _check(self, path, card, options):
        out, reports = conv.convert(card, options)
        data = out.serialize()
        back = hd.HdFile.parse(data)                       # strict: checksums and CRC
        for s, g in enumerate(card.slots()):
            h = back.slots[s]
            if g is None or g.is_new():
                self.assertEqual(bytes(h), bytes(hd.fresh_slot()), path)
                continue
            self.assertGreater(h.u("info.save_count"), 0, path)
            self.assertEqual(hdcheck.invariants(h), [], "%s file %d" % (path, s + 1))
            for name, (off, size) in layout.FIELDS.items():
                if name in self.MAY_CHANGE or name.startswith("status_c"):
                    continue
                self.assertEqual(h.data[off:off + size], g.data[off:off + size], "%s: %s" % (path, name))
            self.assertEqual(back.name(s), conv.hd_name_for(conv.gc_name(g, card.game_code))[0])
        return back, reports

    def test_all_samples_default_options(self):
        n = 0
        for path in GC_FILES:
            card = gc.load(_read(path))
            self._check(path, card, conv.Options.all("steps"))
            n += 1
        self.assertTrue(n or not GC_FILES)

    def test_all_samples_other_options(self):
        opts = conv.Options.all("rewards", swift_sail=True, hero_mode=True)
        for path in GC_FILES:
            self._check(path, gc.load(_read(path)), opts)

    def _card(self, edit):
        save = hd.fresh_slot()
        save.set_raw("info.player_name", b"Tester".ljust(17, b"\0"))
        save.set_u("info.save_count", 0)
        save.set_u("config.sound_mode", 1)
        save.set_u("map.triforce_bits", 0)
        for i in range(4):
            off, size = layout.BLOCKS["status_c%d" % i]
            save.data[off:off + size] = bytes(size)
        edit(save)
        return gc.load(gc.build_gci(b"GZLE01", [save, hd.fresh_slot(), hd.fresh_slot()]))

    def test_triforce_chart_rules(self):
        def edit(s):
            for k in (1, 2, 4, 7):                         # charts 1, 2, 4, 7 owned
                conv._set_map_bit(s, "map.get_map", k, True)
                conv._set_map_bit(s, "map.open_map", k, True)
            conv._set_map_bit(s, "map.complete_map", 7, True)
            s.set_u("collect.triforce", 1 << 6)            # shard 7 salvaged
            s.set_u("map.triforce_bits", 0b01001011)       # 1, 2, 4, 7 deciphered
            s.set_u("memory12.tbox", 1 << 17)              # cabana labyrinth chest (chart 2)
            s.set_u("memory10.tbox", 1 << 22)              # a GameCube copy of the Ghost Ship chest (chart 4)
        card = self._card(edit)
        g_rupees = card.slots()[0].u("status_a.rupee")
        with self.assertRaises(conv.ConversionError):      # no default
            conv.convert(card, conv.Options())
        self.assertEqual([d.key for d in conv.decisions_for(card.slots())],
                         ["triforce_chart_2", "triforce_chart_4"])
        out, reports = conv.convert(card, conv.Options.all("steps"))
        h = out.slots[0]
        self.assertEqual(h.u("collect.triforce"), 0b01001010)                   # shards 2, 4 given; 7 kept
        self.assertEqual(h.raw("map.get_map")[3], 0b00000001)                   # only chart 1 remains
        self.assertEqual(h.raw("map.open_map")[3], 0b00000001)
        self.assertEqual(h.raw("map.complete_map")[3], 0)
        self.assertEqual(h.u("map.triforce_bits"), 0xEB)
        self.assertEqual(h.u("status_a.rupee"), min(500, g_rupees + 3 * 398))   # fee of charts 2, 4, 7 back
        self.assertEqual((h.u("memory12.tbox"), h.u("memory10.tbox")), (1 << 17, 1 << 23))   # HD's one chest
        # by rewards: chart 2 dropped and its chest closed; chart 4 by steps
        h = conv.convert(card, conv.Options(triforce_chart_2="rewards", triforce_chart_4="steps"))[0].slots[0]
        self.assertEqual(h.u("collect.triforce"), 0b01001000)
        self.assertEqual((h.u("memory12.tbox"), h.u("memory10.tbox")), (0, 1 << 23))
        h = conv.convert(card, conv.Options.all("rewards"))[0].slots[0]
        self.assertEqual((h.u("memory12.tbox"), h.u("memory10.tbox"), h.u("collect.triforce")), (0, 0, 1 << 6))
        self.assertEqual(h.raw("map.get_map")[3], 0b00000001)

    def _swapped(self, f50=False, marie=False, paw=False, lookouts=False):
        def edit(s):
            s.set_u("memory01.tbox", (1 << 26 | 1 << 11) if lookouts else 0)
            s.set_u("memory13.tbox", (1 << 12 if f50 else 0) | (1 << 2 if paw else 0))
            s.set_event_bit(0x1C04, marie)
            s.set_raw("collect.collect", bytes([0, 0, 0, 0, 3 if marie else 0, 0, 0, 0]))   # charm, switched on
            s.set_u("status_a.max_life", 48)
            s.set_u("status_a.life", 48)
        return self._card(edit)

    def _state(self, card, **options):
        h = conv.convert(card, conv.Options(**options))[0].slots[0]
        charts = {n: "".join("x" if h.raw(f)[3] >> (k - 1) & 1 else "-" for f in
                             ("map.get_map", "map.open_map", "map.complete_map"))
                  for k, n in conv.REUSED_CHARTS.items()}
        return dict(life=h.u("status_a.max_life"), charm=h.raw("collect.collect")[4],
                    f50=h.u("memory13.tbox") >> 12 & 1, paw=h.u("memory13.tbox") >> 2 & 1,
                    marie=h.event_bit(0x1C04), charts=charts, lookouts=h.u("memory01.tbox"))

    def test_answer_per_file(self):
        save = self._swapped(f50=True).slots()[0]
        card = gc.load(gc.build_gci(b"GZLE01", [save, save.copy(), hd.fresh_slot()]))
        out = conv.convert(card, conv.Options(floor50={0: "steps", 1: "rewards"}))[0]
        self.assertEqual([out.slots[i].u("status_a.max_life") for i in (0, 1)], [47, 48])
        with self.assertRaises(conv.ConversionError):
            conv.convert(card, conv.Options(floor50={0: "steps"}))

    def test_flags_hd_never_or_differently_sets(self):
        def edit(s):
            for f in conv.TUNER_FLAGS + (conv.WHIRLPOOL_HINT, conv.HINTS_DONE):
                s.set_event_bit(f)
            s.set_u("item.slot01", 0x78)                    # Sail
            s.set_raw("get_item.slot01", b"\x01")
        card = self._card(edit)
        h = conv.convert(card, conv.Options())[0].slots[0]
        self.assertFalse(any(h.event_bit(f) for f in conv.TUNER_FLAGS + (conv.WHIRLPOOL_HINT, conv.HINTS_DONE)))
        h = conv.convert(card, conv.Options(swift_sail=True))[0].slots[0]
        self.assertTrue(h.event_bit(conv.HINTS_DONE))       # reachable in HD with the Swift Sail

    def test_last_spoil_taken_back(self):
        def edit(s):
            s.set_u("memory01.tbox", 1 << 26)
            s.set_raw("bag_item.beast", bytes([0x45]) + b"\xff" * 7)
            s.set_raw("bag_item_record.beast_num", bytes([1]) + bytes(7))
            s.set_raw("status_a.select_item", bytes([24, 0xFF, 0xFF, 0xFF, 0xFF]))      # necklace on X
        h = conv.convert(self._card(edit), conv.Options(horseshoe_chest="steps"))[0].slots[0]
        self.assertEqual((h.raw("bag_item.beast")[0], h.raw("bag_item_record.beast_num")[0],
                          h.raw("status_a.select_item")[0]), (0xFF, 0, 0xFF))

    def test_lookout_chests(self):
        card = self._swapped(lookouts=True)
        st = self._state(card, horseshoe_chest="steps", star_belt_chest="rewards")
        self.assertEqual((st["charts"][43], st["charts"][44], st["lookouts"]), ("x--", "---", 1 << 26))

    def test_floor50_and_marie(self):
        # floor 50 only
        card = self._swapped(f50=True)
        self.assertEqual([d.key for d in conv.decisions_for(card.slots())], ["floor50"])
        st = self._state(card, floor50="steps")
        self.assertEqual((st["life"], st["charm"], st["f50"], st["paw"], st["charts"][46]), (47, 1, 1, 0, "---"))
        st = self._state(card, floor50="rewards")
        self.assertEqual((st["life"], st["charm"], st["f50"], st["paw"], st["charts"][46]), (48, 0, 0, 1, "xxx"))
        # Mrs. Marie only
        card = self._swapped(marie=True)
        st = self._state(card, marie="steps")
        self.assertEqual((st["charm"], st["f50"], st["marie"], st["charts"][45]), (0, 0, True, "x--"))
        st = self._state(card, marie="rewards")
        self.assertEqual((st["charm"], st["f50"], st["marie"], st["charts"][45]), (3, 1, False, "---"))
        # both: the chest stays open with the same mode, and follows the charm when the modes differ
        card = self._swapped(f50=True, marie=True)
        for a, b, life, charm, f50, marie in (("steps", "steps", 47, 3, 1, True), ("rewards", "rewards", 48, 3, 1, False),
                                              ("steps", "rewards", 47, 3, 1, False), ("rewards", "steps", 48, 0, 0, True)):
            st = self._state(card, floor50=a, marie=b)
            self.assertEqual((st["life"], st["charm"], st["f50"], st["marie"]), (life, charm, f50, marie), (a, b))
            self.assertEqual((st["charts"][46], st["charts"][45]),
                             ("xxx" if a == "rewards" else "---", "x--" if b == "steps" else "---"), (a, b))

    def test_floor50_by_steps_on_a_file_without_hearts(self):
        def edit(s):
            s.set_u("memory13.tbox", 1 << 12)
            s.set_u("status_a.max_life", 0)
            s.set_u("status_a.life", 0)
        out, reports = conv.convert(self._card(edit), conv.Options(floor50="steps"))
        self.assertEqual(out.slots[0].u("status_a.max_life"), 0)
        self.assertEqual(len(reports[0].warnings), 1)

    def test_triforce_chest_open_without_chart_is_a_case(self):
        """An open chest with neither chart nor shard would leave the shard out of reach in HD."""
        card = self._card(lambda s: s.set_u("memory13.tbox", 1 << 11))      # Savage Labyrinth floor 30
        self.assertEqual([d.key for d in conv.decisions_for(card.slots())], ["triforce_chart_6"])
        h = conv.convert(card, conv.Options(triforce_chart_6="steps"))[0].slots[0]
        self.assertEqual((h.u("collect.triforce"), h.u("memory13.tbox")), (1 << 5, 1 << 11))
        h = conv.convert(card, conv.Options(triforce_chart_6="rewards"))[0].slots[0]
        self.assertEqual((h.u("collect.triforce"), h.u("memory13.tbox")), (0, 0))

    def test_rupees_are_one_balance(self):
        """A take-back is not cut short because the refund is listed after it."""
        def edit(s):
            s.set_u("memory13.tbox", 1 << 2)                # Pawprint chest: Silver Rupee, 200
            s.set_u("status_a.rupee", 100)
            s.set_u("status_a.wallet_size", 1)
            s.set_u("map.triforce_bits", 1 << 5)            # one chart deciphered: 398 back
        out, reports = conv.convert(self._card(edit), conv.Options(pawprint_chest="steps"))
        self.assertEqual(out.slots[0].u("status_a.rupee"), 100 - 200 + 398)
        self.assertEqual(reports[0].warnings, [])

    def test_question_text_is_per_file(self):
        both = self._swapped(f50=True, marie=True).slots()[0]
        card = gc.load(gc.build_gci(b"GZLE01", [both, both.copy(), hd.fresh_slot()]))
        d = next(d for d in conv.decisions_for(card.slots(), conv.Options(floor50={0: "steps", 1: "rewards"}))
                 if d.key == "marie")
        self.assertIn("keep the Hero's Charm", d.text(0)[1][0][1])
        self.assertIn("goes back into the floor-50 chest", d.text(1)[1][0][1])

    def test_name_changes_are_reported(self):
        self.assertEqual(conv.hd_name_for("Link"), ("Link", None))
        self.assertIsNotNone(conv.hd_name_for("N\u00ba1")[1])        # written as "No1": said so
        self.assertEqual(conv.hd_name_for("\u0080\u009fab")[0], "Link")    # control characters are refused

    def test_pawprint_chest(self):
        card = self._swapped(paw=True)
        self.assertEqual(self._state(card, pawprint_chest="steps")["charts"][46], "x--")
        st = self._state(card, pawprint_chest="rewards")
        self.assertEqual((st["charts"][46], st["paw"]), ("---", 0))
        # with the floor-50 Piece of Heart kept, the Pawprint chest is settled and not asked about
        card = self._swapped(f50=True, paw=True)
        keys = lambda o: [d.key for d in conv.decisions_for(card.slots(), o)]
        self.assertEqual(keys(conv.Options()), ["floor50"])
        self.assertEqual(keys(conv.Options(floor50="steps")), ["floor50", "pawprint_chest"])
        self.assertEqual(keys(conv.Options(floor50="rewards")), ["floor50"])
        st = self._state(card, floor50="rewards")
        self.assertEqual((st["charts"][46], st["paw"]), ("xxx", 1))

    def test_no_duplicate_and_nothing_unobtainable(self):
        """Every combination of cases and answers: each unique reward is held exactly when the place that
        gives it in HD is done (held and place open = no duplicate; not held and place closed = obtainable)."""
        import itertools
        chests = conv.TRIFORCE_CHESTS
        n = 0
        for f50, marie, paw, look, lenzo, charts in itertools.product(
                (0, 1), (0, 1), (0, 1), (0, 1), (0, 1), ((), (4,), (2, 6), (2, 4, 6, 7, 8))):
            def edit(s):
                s.set_u("memory01.tbox", (1 << 26 | 1 << 11) if look else 0)
                s.set_u("memory13.tbox", (1 << 12 if f50 else 0) | (1 << 2 if paw else 0))
                s.set_event_bit(0x1C04, bool(marie))
                s.set_raw("collect.collect", bytes([0, 0, 0, 0, 3 if marie else 0, 0, 0, 0]))
                s.set_u("status_a.max_life", 48)
                s.set_u("status_a.life", 48)
                s.set_u("status_a.rupee", 1000)
                s.set_raw("bag_item.beast", bytes([0x45, 0x1F]) + b"\xff" * 6)
                s.set_raw("bag_item_record.beast_num", bytes([2, 0, 0, 0, 0, 0, 0, 3]))
                if lenzo:
                    s.set_u("item.slot08", 0x23)
                    s.set_raw("get_item.slot08", b"\x01")
                    s.set_event_reg(conv.LENZO_REG, 6)
                for k in charts:                            # chart owned and deciphered, shard not salvaged
                    conv._set_map_bit(s, "map.get_map", k, True)
                    conv._set_map_bit(s, "map.open_map", k, True)
                    conv._set_tbox(s, chests[k][0], chests[k][1][-1], True)
                if 4 in charts:
                    s.set_event_reg(conv.GHOST_SHIP_REG, 3)
            card = self._card(edit)
            keys = [d.key for d in conv.decisions_for(card.slots(), conv.Options(floor50="steps"))]
            for answers in itertools.product(conv.MODES, repeat=len(keys)):
                opts = conv.Options(**dict(zip(keys, answers)))
                h = conv.convert(card, opts)[0].slots[0]
                hd.HdFile.parse(conv.convert(card, opts)[0].serialize())
                n += 1
                where = (f50, marie, paw, look, lenzo, charts, dict(zip(keys, answers)))
                got = lambda k: conv._map_bit(h, "map.get_map", k)
                done = lambda k: conv._map_bit(h, "map.complete_map", k)
                tbox = lambda rec, bit: bool(h.u("memory%02d.tbox" % rec) >> bit & 1)
                for k in charts:                            # Triforce Shard k <=> its chest
                    self.assertEqual(bool(h.u("collect.triforce") >> (k - 1) & 1),
                                     tbox(chests[k][0], chests[k][1][0]), where)
                if 4 in charts:                             # the Ghost Ship exists while its chest is closed
                    self.assertEqual(h.event_reg(conv.GHOST_SHIP_REG) == 3, tbox(0xA, 23), where)
                self.assertEqual(got(4), tbox(1, 26), where)            # Treasure Chart 43 <=> Horseshoe chest
                self.assertEqual(got(6), tbox(1, 11), where)            # 44 <=> Star Belt chest
                self.assertEqual(got(7), h.event_bit(0x1C04), where)    # 45 <=> Mrs. Marie
                self.assertEqual(got(8), tbox(0xD, 2), where)           # 46 <=> Pawprint chest
                self.assertEqual(bool(h.raw("collect.collect")[4] & 1), tbox(0xD, 12), where)   # Hero's Charm
                # the floor-50 Piece of Heart is held <=> Treasure Chart 46's treasure is salvaged
                held = bool(f50) and h.u("status_a.max_life") == 48
                self.assertEqual(h.u("status_a.max_life"), 48 if held or not f50 else 47, where)
                self.assertEqual(held, done(8), where)
                self.assertLessEqual(h.u("status_a.life"), h.u("status_a.max_life"), where)
                self.assertFalse(done(4) or done(6), where)
                # consumables: taken back by steps; the Silver Rupee is held <=> Chart 45's treasure is salvaged
                ans = dict(zip(keys, answers))
                self.assertEqual(done(7) and not paw, False, where)
                rupees = 1000 - (20 if ans.get("star_belt_chest") == "steps" else 0) - (
                    200 if paw and not done(7) else 0)
                self.assertEqual(h.u("status_a.rupee"), rupees, where)
                spoils = h.raw("bag_item_record.beast_num")
                self.assertEqual(spoils[0], 2 - (ans.get("horseshoe_chest") == "steps"), where)
                self.assertEqual(spoils[7], 3 - (ans.get("lenzo") == "steps"), where)
                if lenzo:                                   # Deluxe Picto Box <=> third task done
                    self.assertEqual(h.u("item.slot08") == 0x26, h.event_reg(conv.LENZO_REG) >= 6, where)
        self.assertGreater(n, 1000)

    def test_hd_records(self):
        def edit(s):
            fmap = bytearray(s.raw("map.fmap_bits"))
            fmap[5] = 1
            fmap[12] = 3
            fmap[20] = 2                                   # arrived, not charted (GameCube only)
            s.set_raw("map.fmap_bits", bytes(fmap))
            s.set_event_bit(0x2F01)                        # figurine ordered from Carlov
            s.set_event_reg(0xA9FF, 0x24)
            s.set_event_bit(0x4008)                        # lost an auction
            s.set_event_reg(0xCD03, 2)
            s.set_u("config.attention_type", 1)
        out, _ = conv.convert(self._card(edit), conv.Options())
        ex = out.extras[0]
        flags = [int.from_bytes(ex["playlog"][0x18 + 4 * i:0x1C + 4 * i], "big") for i in range(49)]
        self.assertEqual([i for i in range(49) if flags[i]], [5, 12])
        self.assertEqual(set(flags), {0, 1})
        fmap = out.slots[0].raw("map.fmap_bits")
        self.assertEqual((fmap[0], fmap[10], fmap[43], fmap[5], fmap[12], fmap[20]), (3, 3, 3, 1, 1, 0))
        self.assertEqual(ex["inventory"], bytes(4) + bytes([0x24]) + bytes(11) + bytes([1, 2, 0, 0]))
        self.assertEqual(ex["options"], bytes([1, 0, 0, 0, 0, 1]) + bytes(10))
        self.assertEqual(ex["pair"], bytes(4))

    def test_new_game_plus_file_not_started(self):
        def edit(s):
            s.set_u("info.clear_count", 1)                 # fresh_slot already has sea / 0x2C / 0xCE
            s.set_raw("return_place.stage", b"sea\0nM\0\0")
        out, reports = conv.convert(self._card(edit), conv.Options())
        h = out.slots[0]
        self.assertEqual(h.u("info.save_count"), 1)        # 0 would make HD start a plain new game
        self.assertEqual(h.u("info.clear_count"), 1)
        self.assertEqual(h.raw("info.player_name")[:5], b"Link\0")
        self.assertEqual(h.raw("return_place.stage"), b"sea".ljust(8, b"\0"))
        self.assertEqual(out.name(0), "Tester")

    def test_outset_switch(self):
        def edit(s):
            s.set_u("memory00.switch", (1 << 9 | 1 << 8) << 96 | 1 << 5)
            s.set_event_bit(0x0E20)
        h = conv.convert(self._card(edit), conv.Options())[0].slots[0]
        self.assertEqual(h.u("memory00.switch"), (1 << 9 | 1 << 8 | 1 << 1) << 96 | 1 << 5)
        h = conv.convert(self._card(lambda s: None), conv.Options())[0].slots[0]
        self.assertEqual(h.u("memory00.switch"), 0)

    def test_arbitrary_content_never_breaks_the_output(self):
        import random
        rng = random.Random(7)
        for _ in range(200):
            save = hd.fresh_slot()
            save.set_raw("info.player_name", b"Fuzz".ljust(17, b"\0"))
            for _ in range(rng.randint(1, 200)):
                save.data[rng.randrange(len(save.data))] = rng.randrange(256)
            save.data[layout.FIELDS["info.player_name"][0]] = 0x46        # keep the file "used"
            card = gc.load(gc.build_gci(b"GZLE01", [save, hd.fresh_slot(), hd.fresh_slot()]))
            for options in (conv.Options.all("steps"),
                            conv.Options.all("rewards", swift_sail=True, hero_mode=True)):
                out, _ = conv.convert(card, options)
                back = hd.HdFile.parse(out.serialize())
                self.assertEqual(hdcheck.unsettled_fields(back.slots[0]), [])

    def test_buttons(self):
        def edit(s):
            s.set_u("item.slot01", 0x78)
            s.set_u("item.slot02", 0x22)
            s.set_u("item.slot03", 0x25)
            s.set_raw("get_item.slot01", b"\x01")
            s.set_raw("get_item.slot02", b"\x01")
            s.set_raw("get_item.slot03", b"\x01")
            s.set_raw("status_a.select_item", bytes([1, 3, 2, 0xFF, 0xFF]))
        out, _ = conv.convert(self._card(edit), conv.Options(swift_sail=True))
        h = out.slots[0]
        self.assertEqual(h.raw("status_a.select_item"), bytes([0xFF, 3, 0xFF, 2, 1]))
        self.assertEqual((h.u("item.slot01"), h.u("get_item.slot01")), (0x77, 3))

    def test_tingle_tuner_lenzo_hero_mode_and_name(self):
        def edit(s):
            s.set_u("item.slot07", 0x21)
            s.set_raw("get_item.slot07", b"\x01")
            s.set_u("item.slot08", 0x23)
            s.set_raw("get_item.slot08", b"\x01")
            s.set_event_reg(conv.LENZO_REG, 6)
            s.set_raw("status_a.select_item", bytes([7, 8, 0xFF, 0xFF, 0xFF]))
        card = self._card(edit)
        self.assertEqual([d.key for d in conv.decisions_for(card.slots())],
                         ["lenzo"])
        out, _ = conv.convert(card, conv.Options(lenzo="steps"))
        h = out.slots[0]
        self.assertEqual((h.u("item.slot07"), h.u("item.slot08"), h.u("get_item.slot08")), (0x21, 0x26, 3))
        self.assertEqual(out.extras[0]["options"][hd.OPT_HERO_MODE], 0)
        self.assertEqual(out.name(0), "Tester")
        self.assertEqual(h.u("info.save_count"), 1)
        out, _ = conv.convert(card, conv.Options(lenzo="rewards", hero_mode=True,
                                                 name="Zelda"))
        self.assertEqual(out.slots[0].event_reg(conv.LENZO_REG), 5)
        h = out.slots[0]
        self.assertEqual((h.u("item.slot07"), h.u("get_item.slot07"), h.u("item.slot08")), (0x21, 1, 0x23))
        self.assertEqual(h.raw("status_a.select_item")[:2], bytes([7, 8]))
        self.assertEqual(out.extras[0]["options"][hd.OPT_HERO_MODE], 1)
        self.assertEqual(out.name(0), "Zelda")


if __name__ == "__main__":
    unittest.main()
