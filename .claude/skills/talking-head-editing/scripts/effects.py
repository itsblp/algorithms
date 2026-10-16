#!/usr/bin/env python3
"""Apply talking-head effects in one pass: punch-ins, text behind the head, photo overlays.

Usage: effects.py INPUT.mp4 effects.json OUTPUT.mp4

effects.json (all times in seconds on INPUT's timeline; every list is optional):
{
  "punch_ins": [{"start": 2.0, "end": 4.5, "scale": 1.18, "ease": 0}],
      # zoom anchored on the face. ease 0 = hard cut (default); ease 0.3 = smooth 0.3 s push-in

  "text_behind": [
    {"start": 5.0, "end": 8.0, "style": "marquee",
     "text": "\"you had it so good at Google. why would you leave?\""},
      # DEFAULT style. One line scrolls right -> left at eye level and passes BEHIND the head
      # (person mask). Use it for a quoted voice: what someone said to you, the critic, the inner
      # monologue. Optional: color (default "#F5D547"), size (104), font, y (baseline px; default eyes)
    {"start": 0, "end": 2.4, "style": "block", "lines": [{"text": "FREEDOM", "size": 300}],
     "y": 380, "color": "#FBF4D6", "anim": "rise"}
      # big static word(s) behind the head. y = top of block. anim: rise | fade | none
  ],

  "photos": [
    {"start": 9.0, "end": 10.2, "path": "photos/mom.jpg"},
    {"start": 12.0, "end": 13.5, "paths": ["photos/team1.jpg", "photos/team2.jpg"]}
      # DEFAULT style "plain": a clean rectangle (no border, tilt, shadow) that cuts in just above
      # the head, centered on the face. "paths" flips through several photos in the same spot.
      # Optional: width (430), anim (cut | fade | pop), style "card" (white border, tilt, shadow),
      # placement "above_head" (default) | "auto" (largest free band above/below the face),
      # or x / y (top-left px) to place manually.
  ]
}

Order per frame: punch-in -> text behind person -> photo overlays. Burn captions AFTER this
script, and leave caption gaps where a marquee runs (the reference style hides captions then).
Audio is copied from INPUT unchanged.
"""
import json
import os
import subprocess
import sys

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(HERE, "..", "models")
FONT_DIR = "/usr/share/fonts/opentype/inter"
BLOCK_FONT = os.path.join(FONT_DIR, "InterDisplay-SemiBold.otf")
MARQUEE_FONT = os.path.join(FONT_DIR, "InterDisplay-Bold.otf")
SAFE_TOP, SAFE_BOTTOM = 220, 1440  # combined IG/TikTok safe zone on 1080x1920


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ease_out(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def active(effects, t):
    return [e for e in effects if e["start"] <= t < e["end"]]


def to_float(img):
    return np.array(img).astype(np.float32) / 255.0


# ---------- text layers (rendered once per effect) ----------

def render_block(e, W, H):
    """Full-frame RGBA layer with stacked static lines."""
    font_path = e.get("font", BLOCK_FONT)
    tracking, leading = e.get("tracking", -0.04), e.get("leading", 0.9)
    color = hex_rgb(e.get("color", "#FBF4D6")) + (255,)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y = e.get("y", 560)
    for i, ln in enumerate(e["lines"]):
        size = ln["size"]
        font = ImageFont.truetype(font_path, size)
        width = font.getlength(ln["text"]) + tracking * size * (len(ln["text"]) - 1)
        while width > W - 60 and size > 40:  # keep inside the frame
            size -= 4
            font = ImageFont.truetype(font_path, size)
            width = font.getlength(ln["text"]) + tracking * size * (len(ln["text"]) - 1)
        y += size * (0.8 if i == 0 else leading)
        x = (W - width) / 2 if e.get("x", "center") == "center" else e["x"]
        for j, ch in enumerate(ln["text"]):
            d.text((x + font.getlength(ln["text"][:j]) + tracking * size * j, y), ch,
                   font=font, fill=color, anchor="ls")
    return to_float(layer)


def render_marquee(e):
    """One-line RGBA strip (wider than the frame) with a thin dark edge for legibility."""
    size = e.get("size", 104)
    font = ImageFont.truetype(e.get("font", MARQUEE_FONT), size)
    text = e["text"]
    pad = 12
    w = int(font.getlength(text)) + 2 * pad
    h = int(size * 1.35) + 2 * pad
    strip = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    base = pad + int(size * 1.0)
    ImageDraw.Draw(shadow).text((pad + 2, base + 4), text, font=font, fill=(0, 0, 0, 120), anchor="ls")
    strip = Image.alpha_composite(strip, shadow.filter(ImageFilter.GaussianBlur(5)))
    ImageDraw.Draw(strip).text((pad, base), text, font=font, fill=hex_rgb(e.get("color", "#F5D547")) + (255,),
                               anchor="ls", stroke_width=max(2, size // 40), stroke_fill=(40, 30, 0, 200))
    return to_float(strip), base


# ---------- photos (rendered once per image) ----------

def render_photo(path, e):
    img = Image.open(path).convert("RGB")
    w = e.get("width", 430)
    img = img.resize((w, round(img.height * w / img.width)), Image.LANCZOS).convert("RGBA")
    if e.get("style", "plain") == "plain":
        return np.array(img)
    b = e.get("border", 14)  # "card" style
    card = Image.new("RGBA", (img.width + 2 * b, img.height + 2 * b), (255, 255, 255, 255))
    card.paste(img, (b, b))
    pad = 40
    out = Image.new("RGBA", (card.width + 2 * pad, card.height + 2 * pad), (0, 0, 0, 0))
    shadow = Image.new("RGBA", out.size, (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 110), (pad + 6, pad + 12, pad + 6 + card.width, pad + 12 + card.height))
    out = Image.alpha_composite(out, shadow.filter(ImageFilter.GaussianBlur(14)))
    out.alpha_composite(card, (pad, pad))
    return np.array(out.rotate(e.get("rotate", -3), resample=Image.BICUBIC, expand=True))


def blend(frame, rgba, x, y):
    """Alpha-blend an RGBA (float 0-1 or uint8) image onto a BGR uint8 frame at (x, y)."""
    H, W = frame.shape[:2]
    h, w = rgba.shape[:2]
    x, y = int(x), int(y)
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1:
        return frame
    src = rgba[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32)
    if src.max() > 1.0:
        src /= 255.0
    a = src[..., 3:4]
    roi = frame[y0:y1, x0:x1].astype(np.float32) / 255.0
    frame[y0:y1, x0:x1] = ((src[..., 2::-1] * a + roi * (1 - a)) * 255).astype(np.uint8)
    return frame


def place_photo(e, img, face, W):
    """Return (img, top_left_x, top_left_y)."""
    h, w = img.shape[:2]
    if "x" in e or "y" in e:
        return img, int(e.get("x", (W - w) // 2)), int(e.get("y", SAFE_TOP))
    if face is None:
        return img, (W - w) // 2, SAFE_TOP
    fx, fy, fw, fh = face
    if e.get("placement", "above_head") == "above_head":
        head_top = fy - 0.45 * fh                   # face box starts at the brows; add hair
        bottom = head_top + 0.12 * fh               # overlap the hairline slightly, like the reference
        if bottom - h < SAFE_TOP:                   # not enough room: shrink to fit the band
            s = max(bottom - SAFE_TOP, 260) / h
            img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
            h, w = img.shape[:2]
        x = min(max(fx + fw / 2 - w / 2, 30), W - w - 30)
        return img, int(x), int(max(bottom - h, SAFE_TOP))
    # "auto": the larger free band above or below the face
    fy0, fy1 = fy - 0.25 * fh, fy + fh * 1.05
    above = (SAFE_TOP, max(SAFE_TOP, fy0 - 20))
    below = (min(SAFE_BOTTOM, fy1 + 20), SAFE_BOTTOM)
    top, bot = max([above, below], key=lambda b: b[1] - b[0])
    if bot - top < h:
        s = max(bot - top, 380) / h
        img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        h, w = img.shape[:2]
    return img, (W - w) // 2, int((top + bot) / 2 - h / 2)


def main(inp, fx_path, out):
    fx = json.load(open(fx_path))
    punches, texts, photos = fx.get("punch_ins", []), fx.get("text_behind", []), fx.get("photos", [])

    cap = cv2.VideoCapture(inp)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
        base_options=BaseOptions(model_asset_path=os.path.join(MODELS, "selfie_segmenter.tflite")),
        running_mode=vision.RunningMode.VIDEO, output_confidence_masks=True))
    faces = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
        base_options=BaseOptions(model_asset_path=os.path.join(MODELS, "blaze_face_short_range.tflite")),
        running_mode=vision.RunningMode.VIDEO))

    layers = []
    for e in texts:
        if e.get("style", "marquee") == "marquee":
            layers.append(render_marquee(e))
        else:
            layers.append((render_block(e, W, H), None))
    photo_imgs = [[render_photo(p, e) for p in e.get("paths", [e.get("path")])] for e in photos]

    enc = subprocess.Popen([
        "ffmpeg", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", f"{fps}", "-i", "-",
        "-i", inp, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
        "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", out], stdin=subprocess.PIPE)

    face_c = (W / 2, H * 0.38)
    face_cache = {}

    def detect_face(frame, ts_ms):
        """Face box (x, y, w, h) for this frame, or None. Cached: VIDEO mode needs increasing timestamps."""
        if ts_ms not in face_cache:
            face_cache.clear()
            rgb = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            det = faces.detect_for_video(rgb, ts_ms).detections
            bb = det[0].bounding_box if det else None
            face_cache[ts_ms] = (bb.origin_x, bb.origin_y, bb.width, bb.height) if bb else None
        return face_cache[ts_ms]

    marquee_y = {}
    placements = {}
    prev_mask = None
    n = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        t = n / fps
        ts_ms = int(t * 1000)

        # --- punch-in, anchored on a smoothed face center ---
        p = active(punches, t)
        if p:
            e = p[0]
            if n % 3 == 0:
                bb = detect_face(frame, ts_ms)
                if bb:
                    c = (bb[0] + bb[2] / 2, bb[1] + bb[3] / 2)
                    face_c = (0.8 * face_c[0] + 0.2 * c[0], 0.8 * face_c[1] + 0.2 * c[1])
            ease = e.get("ease", 0)
            k = ease_out((t - e["start"]) / ease) if ease else 1.0
            s = 1 + (e.get("scale", 1.18) - 1) * k
            cw, ch = W / s, H / s
            x0 = min(max(face_c[0] - cw / 2, 0), W - cw)
            y0 = min(max(face_c[1] - ch * 0.42, 0), H - ch)  # keep eyes in the upper-middle
            frame = cv2.resize(frame[int(y0):int(y0 + ch), int(x0):int(x0 + cw)], (W, H),
                               interpolation=cv2.INTER_CUBIC)

        # --- text behind the person ---
        tb = [(i, e) for i, e in enumerate(texts) if e["start"] <= t < e["end"]]
        if tb:
            rgb = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            m = seg.segment_for_video(rgb, ts_ms).confidence_masks[0].numpy_view()[..., 0].copy()
            m = cv2.GaussianBlur(np.clip((m - 0.35) / 0.3, 0, 1), (7, 7), 0)  # firm, soft-edged matte
            if prev_mask is not None:
                m = 0.6 * m + 0.4 * prev_mask  # temporal smoothing against flicker
            prev_mask = m
            person = frame.copy()
            for i, e in tb:
                layer, base = layers[i]
                if base is not None:  # marquee: linear scroll from off-right to off-left
                    if i not in marquee_y:
                        bb = detect_face(frame, ts_ms)
                        eyes = bb[1] + 0.42 * bb[3] if bb else H * 0.36
                        marquee_y[i] = e.get("y", eyes + e.get("size", 104) * 0.35) - base
                    k = (t - e["start"]) / (e["end"] - e["start"])
                    x = W - k * (W + layer.shape[1])
                    frame = blend(frame, layer, x, marquee_y[i])
                else:
                    age, left = t - e["start"], e["end"] - t
                    anim = e.get("anim", "rise")
                    alpha = ease_out(min(age, left) / 0.2) if anim != "none" else 1.0
                    dy = int((1 - ease_out(age / 0.3)) * 60) if anim == "rise" else 0
                    lay = layer.copy()
                    lay[..., 3] *= alpha
                    frame = blend(frame, lay, 0, dy)
            m3 = m[..., None]
            frame = (person * m3 + frame * (1 - m3)).astype(np.uint8)
        else:
            prev_mask = None

        # --- photo overlays (on top of everything) ---
        for i, (e, imgs) in enumerate(zip(photos, photo_imgs)):
            if not (e["start"] <= t < e["end"]):
                continue
            span = (e["end"] - e["start"]) / len(imgs)
            j = min(int((t - e["start"]) / span), len(imgs) - 1)
            if (i, j) not in placements:
                placements[(i, j)] = place_photo(e, imgs[j], detect_face(frame, ts_ms), W)
            img, x, y = placements[(i, j)]
            anim = e.get("anim", "cut")
            age, left = t - e["start"] - j * span, e["end"] - t
            if anim in ("fade", "pop"):
                img = img.astype(np.float32)
                img[..., 3] *= ease_out(min(age, left) / 0.12)
            if anim == "pop" and age < 0.18:
                s = 0.85 + 0.15 * ease_out(age / 0.18)
                big = img
                img = cv2.resize(big, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
                x, y = x + (big.shape[1] - img.shape[1]) // 2, y + (big.shape[0] - img.shape[0]) // 2
            frame = blend(frame, img, x, y)

        enc.stdin.write(frame.tobytes())
        n += 1

    enc.stdin.close()
    enc.wait()
    seg.close()
    faces.close()


if __name__ == "__main__":
    main(*sys.argv[1:4])
