#!/usr/bin/env python3
"""Render a comment-reply bubble (the "answering a follower's comment" hook) as a transparent PNG.

Usage: comment_card.py "the comment text" out.png [--handle @name] [--width 620]

Overlay it with effects.py: {"photos": [{"start": 0, "end": 2.0, "path": "card.png",
"style": "sticker", "x": 80, "y": 1040}]}. effects.py clamps it inside the safe zone.
Use the follower's real comment (with permission or anonymized), never an invented one.
"""
import argparse

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf"

p = argparse.ArgumentParser()
p.add_argument("text")
p.add_argument("out")
p.add_argument("--handle", default="")
p.add_argument("--width", type=int, default=620)
p.add_argument("--size", type=int, default=38)
a = p.parse_args()

font = ImageFont.truetype(FONT, a.size)
small = ImageFont.truetype(FONT, int(a.size * 0.72))
pad, radius = 30, 30
inner = a.width - 2 * pad

lines, cur = [], ""
for word in a.text.split():
    trial = f"{cur} {word}".strip()
    if font.getlength(trial) <= inner:
        cur = trial
    else:
        lines.append(cur)
        cur = word
lines.append(cur)

line_h = int(a.size * 1.22)
head_h = int(a.size * 1.1) if a.handle else 0
h = pad * 2 + head_h + line_h * len(lines)
shadow_pad = 24
img = Image.new("RGBA", (a.width + 2 * shadow_pad, h + 2 * shadow_pad), (0, 0, 0, 0))
sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
ImageDraw.Draw(sh).rounded_rectangle([shadow_pad, shadow_pad + 6, shadow_pad + a.width, shadow_pad + 6 + h],
                                     radius, fill=(0, 0, 0, 70))
img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(10)))
d = ImageDraw.Draw(img)
d.rounded_rectangle([shadow_pad, shadow_pad, shadow_pad + a.width, shadow_pad + h], radius, fill=(255, 255, 255, 245))
y = shadow_pad + pad
if a.handle:
    d.text((shadow_pad + pad, y), f"Reply to {a.handle}'s comment", font=small, fill=(120, 120, 120, 255))
    y += head_h
for ln in lines:
    d.text((shadow_pad + pad, y), ln, font=font, fill=(17, 17, 17, 255))
    y += line_h
img.save(a.out)
print(a.out)
