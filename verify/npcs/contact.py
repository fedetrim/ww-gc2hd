#!/usr/bin/env python3
"""contact.py SHOTS_DIR OUT.png [COLS]

Contact sheet of the screenshots of a run, in time order, numbered (the frame numbers the reports quote).

Inputs:  a folder of .png screenshots (WWHD_SCREENSHOT_DIR of a run)
Output:  OUT.png. Needs the Python package Pillow.
Run:     python3 verify/npcs/contact.py research/out/verify/npcs/NAME/shots research/out/verify/npcs/NAME/contact.png 4
"""
import os, sys
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 4
fs = sorted(f for f in os.listdir(d) if f.endswith(".png"))
w, h = 480, 270
rows = (len(fs) + cols - 1) // cols
sheet = Image.new("RGB", (cols * w, rows * h))
for i, f in enumerate(fs):
    im = Image.open(os.path.join(d, f)).convert("RGB").resize((w, h))
    ImageDraw.Draw(im).text((4, 4), "%d %s" % (i + 1, f[-12:-4]), fill=(255, 255, 0))
    sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(out)
