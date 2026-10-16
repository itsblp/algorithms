#!/usr/bin/env python3
"""Render a photo-cover carousel slide: full-bleed photo + stacked mixed-size type.

Usage: render_slide.py slide.json [more.json ...]

Writes <out_dir>/tiktok/<name>.png (1080x1920) and <out_dir>/ig/<name>.png
(1080x1350 center crop, y 285-1635). Spec keys (defaults in DEFAULTS):

  photo        path to the image (cover-fit; "focus_y" 0-1 picks the crop height)
  name         output file stem, e.g. "01"
  lines        [{"text": "...", "size": 190, "gap_before": 0}, ...]
               lines wider than the text-safe width are shrunk to fit
  bottom       y of the text block's last baseline (default sits low in the 4:5 band)
  background   hex color used when there is no photo
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
IG_TOP, IG_H = 285, 1350
DEFAULTS = {
    "out_dir": ".",
    "font": "/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf",
    "color": "#FBF4D6",
    "tracking": -0.055,   # fraction of font size between letters
    "leading": 0.93,      # baseline-to-baseline as fraction of the next line's size
    "x": 80,
    "max_width": 800,     # text-safe x 80 -> 880
    "bottom": 1380,       # last baseline; descenders must stay above y 1400
    "focus_y": 0.4,
    "gradient": 0.3,      # max bottom darkening (0 = none); keeps cream type legible
    "shadow": 0.25,       # soft drop-shadow opacity
    "weight_boost": 0.0,  # faux-bolder stroke as fraction of font size (e.g. 0.012 makes a Regular look Medium)
    "background": "#F4F1EC",
}


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def cover(img, focus_y):
    s = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    left = (img.width - W) // 2
    top = round((img.height - H) * focus_y)
    return img.crop((left, top, left + W, top + H))


def line_width(font, text, size, tracking):
    return font.getlength(text) + tracking * size * (len(text) - 1)


def draw_tracked(draw, x, y, text, font, size, tracking, fill, stroke=0):
    for i, ch in enumerate(text):
        cx = x + font.getlength(text[:i]) + tracking * size * i
        draw.text((cx, y), ch, font=font, fill=fill, anchor="ls", stroke_width=stroke, stroke_fill=fill)


def render(spec):
    no_photo = {} if spec.get("photo") else {"color": "#111111", "gradient": 0, "shadow": 0}
    c = {**DEFAULTS, **no_photo, **spec}
    if c.get("photo"):
        base = cover(Image.open(c["photo"]).convert("RGB"), c["focus_y"])
    else:
        base = Image.new("RGB", (W, H), hex_rgb(c["background"]))
    base = base.convert("RGBA")

    if c["gradient"]:
        grad = Image.new("L", (1, H))
        start = 800
        for y in range(H):
            grad.putpixel((0, y), 0 if y < start else round(255 * c["gradient"] * (y - start) / (H - start)))
        shade = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        shade.putalpha(grad.resize((W, H)))
        base = Image.alpha_composite(base, shade)

    lines = []
    for ln in c["lines"]:
        size = ln["size"]
        font = ImageFont.truetype(c["font"], size)
        while line_width(font, ln["text"], size, c["tracking"]) > c["max_width"] and size > 24:
            size -= 2
            font = ImageFont.truetype(c["font"], size)
        lines.append((ln["text"], size, font, ln.get("gap_before", 0)))

    baselines, y = [], 0
    for i, (_, size, _, gap) in enumerate(lines):
        y += (size * 0.75 if i == 0 else size * c["leading"]) + gap
        baselines.append(y)
    offset = c["bottom"] - baselines[-1]

    text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td, sd = ImageDraw.Draw(text_layer), ImageDraw.Draw(shadow_layer)
    for (text, size, font, _), b in zip(lines, baselines):
        stroke = round(size * c["weight_boost"])
        draw_tracked(td, c["x"], b + offset, text, font, size, c["tracking"], hex_rgb(c["color"]), stroke)
        if c["shadow"]:
            draw_tracked(sd, c["x"] + 2, b + offset + 3, text, font, size, c["tracking"],
                         (0, 0, 0, round(255 * c["shadow"])), stroke)
    if c["shadow"]:
        from PIL import ImageFilter
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(6))
        base = Image.alpha_composite(base, shadow_layer)
    base = Image.alpha_composite(base, text_layer).convert("RGB")

    for d in ("tiktok", "ig"):
        os.makedirs(os.path.join(c["out_dir"], d), exist_ok=True)
    base.save(os.path.join(c["out_dir"], "tiktok", f"{c['name']}.png"))
    base.crop((0, IG_TOP, W, IG_TOP + IG_H)).save(os.path.join(c["out_dir"], "ig", f"{c['name']}.png"))


for path in sys.argv[1:]:
    render(json.load(open(path)))
