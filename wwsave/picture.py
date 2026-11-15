"""Picto Box pictures: GameCube card blocks -> HD album files.

GameCube (card_pictdata, zeldaret/tww include/m_Do/m_Do_MemCardRWmng.h): a 152x104 CMPR texture, then
u32 snap_result (what the picture shows), u8 snap_result_detail, u8 capture_format, u16 byte-sum checksum.

HD (ZeldaWWHDDecomp/wwhd wwhd_src/d/hd_jpeg.cpp; checked on 696 records of real saves):
  cking_pic<S>_<I>.sav      0x50000 bytes: a baseline JPEG (800x450, 4:2:0), zero padded
  cking_pic_order<S>.sav    12 x 16-byte records (u32 CRC-32 of [u32 size + the 0x50000 bytes], u8 0,
                            u8 detail, u8 used, u8 colour, u32 subject, u32 size), 12 order bytes
                            (album position -> record, 0xFF unused), u8 count
"""
import struct
import zlib

GC_W, GC_H = 152, 104
GC_TEX_SIZE = 0x1EE0
HD_W, HD_H = 800, 450
HD_DATA_SIZE = 0x50000
ALBUM_SIZE = 12
GX_TF_I4, GX_TF_I8 = 0, 1          # capture formats of the black-and-white Picto Box


def _rgb565(v):
    r, g, b = v >> 11 & 31, v >> 5 & 63, v & 31
    return (r << 3 | r >> 2, g << 2 | g >> 4, b << 3 | b >> 2)


def decode_cmpr(data, width=GC_W, height=GC_H):
    """GameCube CMPR texture -> list of rows of (r, g, b)."""
    img = [[(0, 0, 0)] * width for _ in range(height)]
    p = 0
    for by in range(0, height, 8):
        for bx in range(0, width, 8):
            for sy in (0, 4):
                for sx in (0, 4):
                    c0, c1 = struct.unpack(">HH", data[p:p + 4])
                    bits = struct.unpack(">I", data[p + 4:p + 8])[0]
                    p += 8
                    a, b = _rgb565(c0), _rgb565(c1)
                    if c0 > c1:
                        pal = [a, b, tuple((2 * a[i] + b[i]) // 3 for i in range(3)),
                               tuple((a[i] + 2 * b[i]) // 3 for i in range(3))]
                    else:
                        pal = [a, b, tuple((a[i] + b[i]) // 2 for i in range(3)), (0, 0, 0)]
                    for j in range(16):
                        x, y = bx + sx + j % 4, by + sy + j // 4
                        if x < width and y < height:
                            img[y][x] = pal[bits >> (30 - 2 * j) & 3]
    return img


class GcPicture:
    def __init__(self, block):
        self.image = decode_cmpr(block[:GC_TEX_SIZE])
        self.subject = struct.unpack(">I", block[0x1EE0:0x1EE4])[0]
        self.detail = block[0x1EE4]
        self.capture_format = block[0x1EE5]

    @property
    def colour(self):
        return self.capture_format not in (GX_TF_I4, GX_TF_I8)


def to_png(img):
    """Rows of (r, g, b) -> PNG bytes (for inspection)."""
    h, w = len(img), len(img[0])
    raw = b"".join(b"\0" + bytes(c for px in row for c in px) for row in img)

    def chunk(tag, body):
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


# --- baseline JPEG encoder (4:2:0, standard tables), as the HD game's own pictures are stored ----------

_ZIGZAG = [0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5, 12, 19, 26, 33, 40, 48, 41, 34, 27, 20,
           13, 6, 7, 14, 21, 28, 35, 42, 49, 56, 57, 50, 43, 36, 29, 22, 15, 23, 30, 37, 44, 51, 58, 59, 52,
           45, 38, 31, 39, 46, 53, 60, 61, 54, 47, 55, 62, 63]
_QY = [16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55, 14, 13, 16, 24, 40, 57, 69, 56, 14, 17,
       22, 29, 51, 87, 80, 62, 18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92, 49, 64, 78,
       87, 103, 121, 120, 101, 72, 92, 95, 98, 112, 100, 103, 99]
_QC = [17, 18, 24, 47, 99, 99, 99, 99, 18, 21, 26, 66, 99, 99, 99, 99, 24, 26, 56, 99, 99, 99, 99, 99, 47, 66,
       99, 99, 99, 99, 99, 99] + [99] * 32
_DC_Y = ([0, 1, 5, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0], list(range(12)))
_DC_C = ([0, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0], list(range(12)))
_AC_Y = ([0, 2, 1, 3, 3, 2, 4, 3, 5, 5, 4, 4, 0, 0, 1, 0x7D], [
    0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06, 0x13, 0x51, 0x61, 0x07, 0x22, 0x71,
    0x14, 0x32, 0x81, 0x91, 0xA1, 0x08, 0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
    0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x34, 0x35, 0x36, 0x37,
    0x38, 0x39, 0x3A, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
    0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78, 0x79, 0x7A, 0x83,
    0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
    0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6, 0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3,
    0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9, 0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
    0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA])
_AC_C = ([0, 2, 1, 2, 4, 4, 3, 4, 7, 5, 4, 4, 0, 1, 2, 0x77], [
    0x00, 0x01, 0x02, 0x03, 0x11, 0x04, 0x05, 0x21, 0x31, 0x06, 0x12, 0x41, 0x51, 0x07, 0x61, 0x71, 0x13, 0x22,
    0x32, 0x81, 0x08, 0x14, 0x42, 0x91, 0xA1, 0xB1, 0xC1, 0x09, 0x23, 0x33, 0x52, 0xF0, 0x15, 0x62, 0x72, 0xD1,
    0x0A, 0x16, 0x24, 0x34, 0xE1, 0x25, 0xF1, 0x17, 0x18, 0x19, 0x1A, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x35, 0x36,
    0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58,
    0x59, 0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78, 0x79, 0x7A,
    0x82, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A,
    0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6, 0xB7, 0xB8, 0xB9, 0xBA,
    0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9, 0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA,
    0xE2, 0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA])


def _huff_codes(table):
    counts, symbols = table
    codes, code, k = {}, 0, 0
    for length in range(1, 17):
        for _ in range(counts[length - 1]):
            codes[symbols[k]] = (code, length)
            code += 1
            k += 1
        code <<= 1
    return codes


def _scaled(q, quality):
    s = 5000 // quality if quality < 50 else 200 - 2 * quality
    return [min(255, max(1, (v * s + 50) // 100)) for v in q]


def encode_jpeg(img, quality=85):
    """Rows of (r, g, b) (width and height multiples of 2) -> baseline JFIF, 4:2:0."""
    import math
    h, w = len(img), len(img[0])
    qy, qc = _scaled(_QY, quality), _scaled(_QC, quality)
    cos = [[math.cos((2 * x + 1) * u * math.pi / 16) * (math.sqrt(0.125) if u == 0 else 0.5) for x in range(8)]
           for u in range(8)]
    # colour conversion into planes padded to whole 16x16 units
    W, H = (w + 15) // 16 * 16, (h + 15) // 16 * 16
    Y = [[0.0] * W for _ in range(H)]
    Cb = [[0.0] * (W // 2) for _ in range(H // 2)]
    Cr = [[0.0] * (W // 2) for _ in range(H // 2)]
    for y in range(H):
        row = img[min(y, h - 1)]
        yr = Y[y]
        cbr, crr = Cb[y // 2], Cr[y // 2]
        for x in range(W):
            r, g, b = row[min(x, w - 1)]
            yr[x] = 0.299 * r + 0.587 * g + 0.114 * b - 128
            cbr[x // 2] += (-0.168736 * r - 0.331264 * g + 0.5 * b) / 4
            crr[x // 2] += (0.5 * r - 0.418688 * g - 0.081312 * b) / 4

    def block(plane, bx, by, q):
        rows = [plane[by + i][bx:bx + 8] for i in range(8)]
        tmp = [[sum(rows[i][x] * cos[u][x] for x in range(8)) for u in range(8)] for i in range(8)]
        out = [0] * 64
        for v in range(8):
            cv = cos[v]
            for u in range(8):
                val = sum(tmp[i][u] * cv[i] for i in range(8))
                out[v * 8 + u] = int(round(val / q[v * 8 + u]))
        return [out[z] for z in _ZIGZAG]

    bits, nbits, out = 0, 0, bytearray()

    def put(code, length):
        nonlocal bits, nbits
        bits = bits << length | code
        nbits += length
        while nbits >= 8:
            byte = bits >> (nbits - 8) & 0xFF
            out.append(byte)
            if byte == 0xFF:
                out.append(0)
            nbits -= 8
        bits &= (1 << nbits) - 1

    def emit(coefs, dc_prev, dc_codes, ac_codes):
        diff = coefs[0] - dc_prev
        size = abs(diff).bit_length()
        put(*dc_codes[size])
        if size:
            put(diff if diff > 0 else diff + (1 << size) - 1, size)
        run = 0
        last = max((i for i in range(1, 64) if coefs[i]), default=0)
        for i in range(1, last + 1):
            v = coefs[i]
            if v == 0:
                run += 1
                continue
            while run > 15:
                put(*ac_codes[0xF0])
                run -= 16
            size = abs(v).bit_length()
            put(*ac_codes[run << 4 | size])
            put(v if v > 0 else v + (1 << size) - 1, size)
            run = 0
        if last < 63:
            put(*ac_codes[0])
        return coefs[0]

    dcy, dcc, acy, acc = (_huff_codes(t) for t in (_DC_Y, _DC_C, _AC_Y, _AC_C))
    py = pcb = pcr = 0
    for my in range(0, H, 16):
        for mx in range(0, W, 16):
            for oy, ox in ((0, 0), (0, 8), (8, 0), (8, 8)):
                py = emit(block(Y, mx + ox, my + oy, qy), py, dcy, acy)
            pcb = emit(block(Cb, mx // 2, my // 2, qc), pcb, dcc, acc)
            pcr = emit(block(Cr, mx // 2, my // 2, qc), pcr, dcc, acc)
    if nbits:
        put((1 << (8 - nbits)) - 1, 8 - nbits)

    def seg(marker, body):
        return bytes([0xFF, marker]) + struct.pack(">H", len(body) + 2) + body

    def dqt(i, q):
        return seg(0xDB, bytes([i]) + bytes(q[z] for z in _ZIGZAG))

    def dht(cls, i, table):
        return seg(0xC4, bytes([cls << 4 | i]) + bytes(table[0]) + bytes(table[1]))

    head = (b"\xFF\xD8" + seg(0xE0, b"JFIF\0\x01\x01\x00\x00\x01\x00\x01\x00\x00") + dqt(0, qy) + dqt(1, qc) +
            seg(0xC0, struct.pack(">BHHB", 8, h, w, 3) + bytes([1, 0x22, 0, 2, 0x11, 1, 3, 0x11, 1])) +
            dht(0, 0, _DC_Y) + dht(1, 0, _AC_Y) + dht(0, 1, _DC_C) + dht(1, 1, _AC_C) +
            seg(0xDA, bytes([3, 1, 0x00, 2, 0x11, 3, 0x11, 0, 63, 0])))
    return head + bytes(out) + b"\xFF\xD9"


def to_hd_frame(img):
    """A 152x104 picture centred in an 800x450 frame (bilinear, black bars left and right)."""
    h, w = len(img), len(img[0])
    scale = HD_H / h
    out_w = int(round(w * scale)) // 2 * 2
    left = (HD_W - out_w) // 2
    frame = []
    for y in range(HD_H):
        fy = min(h - 1.0, max(0.0, (y + 0.5) / scale - 0.5))
        y0 = int(fy)
        y1 = min(h - 1, y0 + 1)
        wy = fy - y0
        row = [(0, 0, 0)] * HD_W
        r0, r1 = img[y0], img[y1]
        for x in range(out_w):
            fx = min(w - 1.0, max(0.0, (x + 0.5) / scale - 0.5))
            x0 = int(fx)
            x1 = min(w - 1, x0 + 1)
            wx = fx - x0
            a, b, c, d = r0[x0], r0[x1], r1[x0], r1[x1]
            row[left + x] = tuple(int(round((a[i] * (1 - wx) + b[i] * wx) * (1 - wy) +
                                            (c[i] * (1 - wx) + d[i] * wx) * wy)) for i in range(3))
        frame.append(row)
    return frame


def record_checksum(size, data):
    return zlib.crc32(struct.pack(">I", size) + data) & 0xFFFFFFFF


def build_album(blocks):
    """GameCube picture blocks of one file -> {file name suffix: bytes} for one HD Quest Log:
    "pic_<i>" x 12 and "order"."""
    files, records, order = {}, [], []
    for i in range(ALBUM_SIZE):
        if i < len(blocks):
            pic = GcPicture(blocks[i])
            jpeg = encode_jpeg(to_hd_frame(pic.image))
            if len(jpeg) > HD_DATA_SIZE:
                raise ValueError("picture too large")
            data = jpeg.ljust(HD_DATA_SIZE, b"\0")
            records.append(struct.pack(">IBBBBII", record_checksum(len(jpeg), data), 0, pic.detail, 1,
                                       1 if pic.colour else 0, pic.subject, len(jpeg)))
            order.append(i)
        else:
            data = bytes(HD_DATA_SIZE)
            records.append(struct.pack(">I", record_checksum(0, data)) + bytes(12))
        files["pic_%d" % i] = data
    files["order"] = b"".join(records) + bytes(order + [0xFF] * (ALBUM_SIZE - len(order))) + bytes([len(order)])
    return files


def parse_order(raw):
    """cking_pic_order<S>.sav -> ([(checksum, detail, used, colour, subject, size)], order, count)."""
    recs = [struct.unpack(">IBBBBII", raw[i * 16:(i + 1) * 16]) for i in range(ALBUM_SIZE)]
    return [(r[0], r[2], r[3], r[4], r[5], r[6]) for r in recs], list(raw[192:204]), raw[204]
