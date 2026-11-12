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
a = p.parse_args()


def width(text, font, track):
    return font.getlength(text) + track * font.size * (len(text) - 1)  # kerned


ser = [t for t in a.serif_line.split("\\n") for t in t.split("\n") if t]
san = [t for t in a.sans_line.split("\\n") for t in t.split("\n") if t] if a.sans_line else []

# size the block so the widest line spans --width
s = 100
for _ in range(3):
    fs, fb = ImageFont.truetype(SERIF, s), ImageFont.truetype(SANS, round(s * SANS_RATIO))
    widest = max([width(t, fs, SERIF_TRACK) for t in ser] + [width(t, fb, SANS_TRACK) for t in san])
    s = int(s * a.width / widest)
fs, fb = ImageFont.truetype(SERIF, s), ImageFont.truetype(SANS, round(s * SANS_RATIO))

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
    b += GAP * s if k == 0 else 0.92 * fb.size
    draw(t, fb, SANS_TRACK, b)
img.save(a.out)
print(f"{a.out}: serif {s}px, sans {round(s * SANS_RATIO)}px, {len(ser) + len(san)} lines, last baseline y {round(b)}")
