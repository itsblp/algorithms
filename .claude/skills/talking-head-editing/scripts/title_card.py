#!/usr/bin/env python3
"""Render the two-line hook title ("editing made / easy") as a transparent 1080x1920 PNG, with
exact letter and line spacing (libass can't control these precisely).

Usage: title_card.py "serif line" "sans line" OUT.png [--width 680] [--top 300]
       Use "\n" inside either argument for more lines, e.g.
       title_card.py "Entrepreneur canon\nexperience:" "running out of inventory\n& scrambling" title.png

Look (the user's pick, 2026-11-11): line one in Cormorant Garamond Medium Italic, tracked -4.5%;
line two in Inter Tight SemiBold at 93% of the serif size, tracked -5.8%. The baseline gap is
0.77x the serif size, so the lines sit tight. Both are white, centered on the frame, with NO
shadow or outline. The block is sized so the wider line spans --width px (default 680, i.e.
x 200-880, inside the safe zone).

Overlay it for the first ~3 s:
  ffmpeg -i video.mp4 -i title.png -filter_complex "[0][1]overlay=enable='between(t,0,3)'" ...
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "..", "short-form-platform-specs", "fonts")
SERIF = os.path.join(FONTS, "CormorantGaramond-MediumItalic.ttf")
SANS = os.path.join(FONTS, "InterTight-SemiBold.ttf")
W, H = 1080, 1920
SERIF_TRACK, SANS_TRACK, SANS_RATIO, GAP = -0.045, -0.058, 0.93, 0.77

p = argparse.ArgumentParser()
p.add_argument("serif_line")
p.add_argument("sans_line")
p.add_argument("out")
p.add_argument("--width", type=int, default=680)
p.add_argument("--top", type=int, default=300, help="top of the title block (safe zone starts at 260)")
p.add_argument("--lead-ratio", type=float, default=None,
               help="make the serif line a small lead-in: serif size = this x the sans size (e.g. 0.69); "
                    "the block is then sized so the widest SANS line spans --width")
p.add_argument("--shade", type=float, default=0,
               help="soft dark gradient baked into the PNG behind the title (0-1 at the top, fading to 0 "
                    "~200 px below the block), for legibility on bright backgrounds. Not a shadow.")
a = p.parse_args()


def width(text, font, track):
    return font.getlength(text) + track * font.size * (len(text) - 1)  # kerned


ser = [t for t in a.serif_line.split("\\n") for t in t.split("\n") if t]
san = [t for t in a.sans_line.split("\\n") for t in t.split("\n") if t] if a.sans_line else []

# size the block so the widest line spans --width
s = 100
if a.lead_ratio:
    sz = 100
    for _ in range(3):
        fb_ = ImageFont.truetype(SANS, sz)
        sz = int(sz * a.width / max(width(t, fb_, SANS_TRACK) for t in san))
    s = round(sz * a.lead_ratio)
for _ in range(3 if not a.lead_ratio else 0):
    fs, fb = ImageFont.truetype(SERIF, s), ImageFont.truetype(SANS, round(s * SANS_RATIO))
    widest = max([width(t, fs, SERIF_TRACK) for t in ser] + [width(t, fb, SANS_TRACK) for t in san])
    s = int(s * a.width / widest)
fs = ImageFont.truetype(SERIF, s)
fb = ImageFont.truetype(SANS, sz if a.lead_ratio else round(s * SANS_RATIO))

img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(img)


def draw(text, font, track, baseline):
    """Centered, with the font's kerning kept: each glyph sits at its kerned prefix width plus tracking."""
    x0 = W / 2 - width(text, font, track) / 2
    for i, c in enumerate(text):
        d.text((x0 + font.getlength(text[:i]) + track * font.size * i, baseline), c, font=font,
               fill=(255, 255, 255, 255), anchor="ls")


b = a.top + fs.getbbox("dh", anchor="ls")[1] * -1  # first baseline so the ascenders start at --top
for k, t in enumerate(ser):
    if k:
        b += 0.86 * s
    draw(t, fs, SERIF_TRACK, b)
for k, t in enumerate(san):
    if k == 0:  # serif baseline -> sans baseline: a small air gap plus the sans cap height
        b += (0.45 * s + 0.73 * fb.size) if a.lead_ratio else GAP * s
    else:
        b += 0.98 * fb.size if a.lead_ratio else 0.92 * fb.size
    draw(t, fb, SANS_TRACK, b)
if a.shade:
    hold = b + 0.25 * fb.size          # full strength down to the bottom of the title block
    end = min(H, hold + 200)           # then a smooth fade over 200 px
    col = Image.new("L", (1, H), 0)
    for y in range(int(end)):
        t_ = 0 if y <= hold else (y - hold) / (end - hold)
        col.putpixel((0, y), round(255 * a.shade * (1 - t_ * t_ * (3 - 2 * t_))))  # smoothstep fade
    scrim = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    scrim.putalpha(col.resize((W, H)))
    img = Image.alpha_composite(scrim, img)
img.save(a.out)
print(f"{a.out}: serif {s}px, sans {fb.size}px, {len(ser) + len(san)} lines, last baseline y {round(b)}")
