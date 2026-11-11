#!/usr/bin/env python3
"""Render the two-line hook title ("editing made / easy") as a transparent 1080x1920 PNG, with
exact letter and line spacing (libass can't control these precisely).

Usage: title_card.py "serif line" "sans line" OUT.png [--width 680] [--top 300]

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
    return sum(font.getlength(c) for c in text) + track * font.size * (len(text) - 1)


# size the block so the wider line spans --width
s = 100
for _ in range(2):
    fs, fb = ImageFont.truetype(SERIF, s), ImageFont.truetype(SANS, round(s * SANS_RATIO))
    widest = max(width(a.serif_line, fs, SERIF_TRACK), width(a.sans_line, fb, SANS_TRACK) if a.sans_line else 0)
    s = int(s * a.width / widest)
fs, fb = ImageFont.truetype(SERIF, s), ImageFont.truetype(SANS, round(s * SANS_RATIO))

img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(img)


def draw(text, font, track, baseline):
    x = W / 2 - width(text, font, track) / 2
    for c in text:
        d.text((x, baseline), c, font=font, fill=(255, 255, 255, 255), anchor="ls")
        x += font.getlength(c) + track * font.size


b1 = a.top + fs.getbbox("dh", anchor="ls")[1] * -1  # first baseline so the ascenders start at --top
draw(a.serif_line, fs, SERIF_TRACK, b1)
if a.sans_line:
    draw(a.sans_line, fb, SANS_TRACK, b1 + GAP * s)
img.save(a.out)
print(f"{a.out}: serif {s}px, sans {round(s * SANS_RATIO)}px")
