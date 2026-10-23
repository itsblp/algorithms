#!/usr/bin/env python3
"""Render carousel slides in the user's named styles, as both TikTok (9:16) and IG (4:5) PNGs.

Usage: render_slide.py slide.json [more.json ...]

Writes <out_dir>/tiktok/<name>.png (1080x1920) and <out_dir>/ig/<name>.png (1080x1350 center
crop, y 285-1635). Every style keeps text inside the text-safe area x 80-880, y 330-1400.

Signature accent (all styles): wrap ONE word or short phrase per slide in *asterisks*
("I spent *$40k* on my") -> Instrument Serif Italic in butter yellow (#F5D547). On light
backgrounds it becomes ink-colored serif italic on a butter-yellow highlighter swipe.

Styles ("style" key; see ../styles/):
  photo_stack  (default when "photo" is set) full-bleed photo + stacked mixed-size cream type
               low-left.  Keys: photo, focus_y, lines [{text, size, gap_before}], bottom, gradient
  thesis       solid background, one big statement.  Keys: kicker (small caps label, optional),
               lines [{text, size, gap_before}], body (small paragraph, optional),
               theme "light" (#F4F1EC, ink) | "dark" (#111111, off-white)
  notes        paper background + handwritten list.  Keys: title, items [str], circle (item
               index to loop), drawing (PNG of the user's own handwriting/sketch, optional),
               theme "light" | "white"
Common: name, out_dir.
"""
import json
import math
import os
import random
import re
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
IG_TOP, IG_H = 285, 1350
SAFE_L, SAFE_R, SAFE_T, SAFE_B = 80, 880, 330, 1400
INTER = "/usr/share/fonts/opentype/inter/"
HERE = os.path.dirname(os.path.abspath(__file__))
BRAND = os.path.join(HERE, "..", "..", "short-form-platform-specs", "fonts")
ACCENT_FONT = os.path.join(BRAND, "InstrumentSerif-Italic.ttf")
HAND_FONT = os.path.join(BRAND, "Caveat-Bold.ttf")
ACCENT = "#F5D547"
CREAM, OFFWHITE, INK = "#FBF4D6", "#F4F1EC", "#111111"


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ---------- text with the signature accent ----------

def segments(text):
    """'I spent *$40k* on' -> [('I spent ', False), ('$40k', True), (' on', False)]"""
    return [(s, i % 2 == 1) for i, s in enumerate(re.split(r"\*", text)) if s]


def seg_font(base_font, size, is_acc):
    return ImageFont.truetype(ACCENT_FONT if is_acc else base_font, int(size * (1.14 if is_acc else 1)))


def line_width(text, base_font, size, tracking):
    w = 0
    for s, acc in segments(text):
        f = seg_font(base_font, size, acc)
        tr = 0 if acc else tracking * size
        w += sum(f.getlength(c) for c in s) + tr * len(s)
    return w


def draw_line(draw, x, base, text, base_font, size, tracking, color, accent_mode, shadow_draw=None):
    """accent_mode: 'color' (accent text in butter yellow) | 'highlight' (ink text on a yellow swipe)."""
    for s, acc in segments(text):
        f = seg_font(base_font, size, acc)
        tr = 0 if acc else tracking * size
        seg_w = sum(f.getlength(c) for c in s) + tr * len(s)
        if acc and accent_mode == "highlight":
            draw.rectangle([x - 6, base - size * 0.42, x + seg_w + 2, base + size * 0.08], fill=rgb(ACCENT) + (255,))
        fill = (rgb(ACCENT) if acc and accent_mode == "color" else rgb(color)) + (255,)
        for c in s:
            if shadow_draw is not None:
                shadow_draw.text((x + 2, base + 3), c, font=f, fill=(0, 0, 0, 70), anchor="ls")
            draw.text((x, base), c, font=f, fill=fill, anchor="ls")
            x += f.getlength(c) + tr
    return x


def fit(lines, base_font, tracking, max_w):
    out = []
    for ln in lines:
        size = ln["size"]
        while line_width(ln["text"], base_font, size, tracking) > max_w and size > 24:
            size -= 2
        out.append({**ln, "size": size})
    return out


# ---------- styles ----------

def cover(img, focus_y):
    s = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    left = (img.width - W) // 2
    top = round((img.height - H) * focus_y)
    return img.crop((left, top, left + W, top + H))


def photo_stack(c):
    base = cover(Image.open(c["photo"]).convert("RGB"), c.get("focus_y", 0.4)).convert("RGBA")
    g = c.get("gradient", 0.3)
    if g:
        grad = Image.new("L", (1, H))
        for y in range(H):
            grad.putpixel((0, y), 0 if y < 800 else round(255 * g * (y - 800) / (H - 800)))
        shade = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        shade.putalpha(grad.resize((W, H)))
        base = Image.alpha_composite(base, shade)
    font, tracking = c.get("font", INTER + "InterDisplay-Medium.otf"), c.get("tracking", -0.055)
    lines = fit(c["lines"], font, tracking, SAFE_R - SAFE_L)
    y, bases = 0, []
    for i, ln in enumerate(lines):
        y += (ln["size"] * 0.75 if i == 0 else ln["size"] * c.get("leading", 0.93)) + ln.get("gap_before", 0)
        bases.append(y)
    off = c.get("bottom", 1380) - bases[-1]
    layer, sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)), Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d, sd = ImageDraw.Draw(layer), ImageDraw.Draw(sh)
    for ln, b in zip(lines, bases):
        draw_line(d, SAFE_L, b + off, ln["text"], font, ln["size"], tracking, c.get("color", CREAM), "color", sd)
    base = Image.alpha_composite(base, sh.filter(ImageFilter.GaussianBlur(6)))
    return Image.alpha_composite(base, layer)


def thesis(c):
    dark = c.get("theme", "light") == "dark"
    bg, ink = (INK, OFFWHITE) if dark else (OFFWHITE, INK)
    img = Image.new("RGBA", (W, H), rgb(bg) + (255,))
    d = ImageDraw.Draw(img)
    font, tracking = INTER + "InterDisplay-SemiBold.otf", -0.045
    y = SAFE_T + 120
    if c.get("kicker"):
        kf = ImageFont.truetype(INTER + "InterDisplay-Medium.otf", 34)
        d.text((SAFE_L, y), c["kicker"].upper(), font=kf, fill=rgb(ink) + (170,), anchor="ls")
        y += 90
    lines = fit(c["lines"], font, tracking, SAFE_R - SAFE_L)
    for i, ln in enumerate(lines):
        y += (ln["size"] * 0.8 if i == 0 else ln["size"] * 1.0) + ln.get("gap_before", 0)
        draw_line(d, SAFE_L, y, ln["text"], font, ln["size"], tracking, ink, "color" if dark else "highlight")
    if c.get("body"):
        bf = ImageFont.truetype(INTER + "InterDisplay-Regular.otf", 42)
        words, cur, y = c["body"].split(), "", y + 90
        for w_ in words:
            if bf.getlength(f"{cur} {w_}".strip()) > SAFE_R - SAFE_L:
                d.text((SAFE_L, y), cur, font=bf, fill=rgb(ink) + (220,), anchor="ls")
                cur, y = w_, y + 58
            else:
                cur = f"{cur} {w_}".strip()
        d.text((SAFE_L, y), cur, font=bf, fill=rgb(ink) + (220,), anchor="ls")
    if y > SAFE_B:
        raise SystemExit(f"{c['name']}: text runs past y {SAFE_B}; shorten it or reduce sizes")
    return img


def loop(d, box, color, seed):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx = min((x1 - x0) / 2 + 36, cx - SAFE_L + 4, SAFE_R - cx)   # stay inside the text-safe area
    ry = (y1 - y0) / 2 + 30
    start = rnd.uniform(-0.6, -0.2)                               # pen starts at the upper right
    pts = [(cx + rx * (1 + .03 * math.sin(k / 7)) * math.cos(start + 2 * math.pi * 1.1 * k / 119),
            cy + ry * (1 + .03 * math.sin(k / 7)) * math.sin(start + 2 * math.pi * 1.1 * k / 119) + k * .06)
           for k in range(120)]
    d.line(pts, fill=rgb(color) + (255,), width=7, joint="curve")


def notes(c):
    bg = "#FFFFFF" if c.get("theme") == "white" else OFFWHITE
    img = Image.new("RGBA", (W, H), rgb(bg) + (255,))
    d = ImageDraw.Draw(img)
    y = SAFE_T + 110
    if c.get("title"):
        font = INTER + "InterDisplay-SemiBold.otf"
        t = fit([{"text": c["title"], "size": 84}], font, -0.045, SAFE_R - SAFE_L)[0]
        draw_line(d, SAFE_L, y, t["text"], font, t["size"], -0.045, INK, "highlight")
        y += 70
    items = [f"{i + 1}. {it}" for i, it in enumerate(c.get("items", []))]
    size = c.get("hand_size", 92)
    while items and size > 48 and max(ImageFont.truetype(HAND_FONT, size).getlength(l) for l in items) > SAFE_R - SAFE_L - 80:
        size -= 4                                  # one size for every item, so the list reads evenly
    hf = ImageFont.truetype(HAND_FONT, size)
    for i, label in enumerate(items):
        y += int(hf.size * (1.25 + (0.3 if c.get("circle") in (i, i - 1) else 0)))  # room for the loop
        d.text((SAFE_L + 40, y), label, font=hf, fill=rgb(INK) + (255,), anchor="ls")
        if c.get("circle") == i:
            loop(d, (SAFE_L + 40, y - hf.size * 0.74, SAFE_L + 40 + hf.getlength(label), y + hf.size * 0.24), INK, i)
    if c.get("drawing"):
        dr = Image.open(c["drawing"]).convert("RGBA")
        room_h = SAFE_B - (y + 60)
        s = min((SAFE_R - SAFE_L) / dr.width, room_h / dr.height, 1.0)
        if s > 0.2:
            dr = dr.resize((int(dr.width * s), int(dr.height * s)), Image.LANCZOS)
            px = dr.load()
            if all(px[x, y_][3] > 250 for x, y_ in [(0, 0), (dr.width - 1, 0), (0, dr.height - 1)]):
                g = dr.convert("L").point(lambda v: max(0, min(255, int((235 - v) * 2.2))))
                dr.putalpha(g)  # key out white paper / iPad background
            img.alpha_composite(dr, ((SAFE_L + SAFE_R - dr.width) // 2, y + 60))
            y += 60 + dr.height
    if y > SAFE_B:
        raise SystemExit(f"{c['name']}: notes run past y {SAFE_B}; fewer items or smaller hand_size")
    return img


def center_block(img, bg, target_cy=880):
    """Move the drawn content so its vertical center sits at target_cy (optically centered in the
    IG 4:5 crop and the TikTok frame), staying inside y 330-1400."""
    diff = Image.new("RGBA", img.size, rgb(bg) + (255,))
    from PIL import ImageChops
    box = ImageChops.difference(img.convert("RGB"), diff.convert("RGB")).getbbox()
    if not box:
        return img
    top, bot = box[1], box[3]
    shift = int(target_cy - (top + bot) / 2)
    shift = max(SAFE_T - top, min(shift, SAFE_B - bot))
    out = Image.new("RGBA", img.size, rgb(bg) + (255,))
    out.alpha_composite(img.crop((0, max(0, -shift), W, H - max(0, shift))), (0, max(0, shift)))
    return out


def render(spec):
    style = spec.get("style", "photo_stack" if spec.get("photo") else "thesis")
    img = {"photo_stack": photo_stack, "thesis": thesis, "notes": notes}[style](spec)
    if style == "thesis":
        img = center_block(img, INK if spec.get("theme") == "dark" else OFFWHITE, spec.get("center_y", 880))
    elif style == "notes":
        img = center_block(img, "#FFFFFF" if spec.get("theme") == "white" else OFFWHITE, spec.get("center_y", 880))
    img = img.convert("RGB")
    out = spec.get("out_dir", ".")
    for d in ("tiktok", "ig"):
        os.makedirs(os.path.join(out, d), exist_ok=True)
    img.save(os.path.join(out, "tiktok", f"{spec['name']}.png"))
    img.crop((0, IG_TOP, W, IG_TOP + IG_H)).save(os.path.join(out, "ig", f"{spec['name']}.png"))


for path in sys.argv[1:]:
    render(json.load(open(path)))
