#!/usr/bin/env python3
"""Apply talking-head effects in one pass: punch-ins, text behind the head, photo overlays.

Usage: effects.py INPUT.mp4 effects.json OUTPUT.mp4

effects.json (all times in seconds on INPUT's timeline; every list is optional):
{
  "punch_ins": [{"start": 2.0, "end": 4.5, "scale": 1.15, "ease": 0}],
      # zoom anchored on the face. ease 0 = hard cut (jump-cut style); ease 0.3 = smooth 0.3 s push-in
  "text_behind": [{"start": 0, "end": 2.5, "lines": [{"text": "FREEDOM", "size": 300}],
                   "y": 560, "color": "#FBF4D6", "anim": "rise"}],
      # big type placed BEHIND the person (uses a person mask). y = top of the text block.
      # anim: rise | fade | none. Optional: font, tracking, leading, x ("center" or px)
  "photos": [{"start": 5, "end": 7.5, "path": "broll/photo.jpg", "width": 640,
              "rotate": -3, "border": 14, "anim": "pop"}]
      # photo card over the frame. Placement defaults to "auto": the card is centered in the larger
      # free band above or below the face (inside the safe zone) and shrunk to fit, so it doesn't
      # cover the face (an extreme close-up may still clip the chin). Pass "y" (card top, px) and/or "x" to place it manually.
      # anim: pop | fade | none
}

Order per frame: punch-in -> text behind person -> photo overlays. Burn captions AFTER this
script (captions sit on top of everything). Audio is copied from INPUT unchanged.
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
DEFAULT_FONT = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ease_out(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def active(effects, t):
    return [e for e in effects if e["start"] <= t < e["end"]]


# ---------- text layer (rendered once per effect, RGBA) ----------

def render_text_layer(e, W, H):
    font_path = e.get("font", DEFAULT_FONT)
    tracking = e.get("tracking", -0.04)
    leading = e.get("leading", 0.9)
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
    return np.array(layer).astype(np.float32) / 255.0


# ---------- photo card (rendered once per effect, RGBA) ----------

def render_photo_card(e):
    img = Image.open(e["path"]).convert("RGB")
    w = e.get("width", 640)
    img = img.resize((w, round(img.height * w / img.width)), Image.LANCZOS)
    b = e.get("border", 14)
    card = Image.new("RGBA", (img.width + 2 * b, img.height + 2 * b), (255, 255, 255, 255))
    card.paste(img, (b, b))
    pad = 40
    out = Image.new("RGBA", (card.width + 2 * pad, card.height + 2 * pad), (0, 0, 0, 0))
    shadow = Image.new("RGBA", out.size, (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 110), (pad + 6, pad + 12, pad + 6 + card.width, pad + 12 + card.height))
    out = Image.alpha_composite(out, shadow.filter(ImageFilter.GaussianBlur(14)))
    out.alpha_composite(card, (pad, pad))
    if e.get("rotate"):
        out = out.rotate(e["rotate"], resample=Image.BICUBIC, expand=True)
    return out


def blend(frame, rgba, x, y):
    """Alpha-blend an RGBA float/uint8 image onto a BGR uint8 frame at (x, y)."""
    H, W = frame.shape[:2]
    h, w = rgba.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1:
        return frame
    src = rgba[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32)
    if src.max() > 1.0:
        src /= 255.0
    a = src[..., 3:4]
    roi = frame[y0:y1, x0:x1].astype(np.float32) / 255.0
    rgb = src[..., 2::-1]  # RGBA -> BGR
    frame[y0:y1, x0:x1] = ((rgb * a + roi * (1 - a)) * 255).astype(np.uint8)
    return frame


SAFE_TOP, SAFE_BOTTOM = 220, 1440  # combined IG/TikTok safe zone on 1080x1920; captions burn on top


def place_card(e, card, face, W):
    """Return (card, center_x, center_y). Auto mode fits the card into the larger free band
    above or below the face so it never covers it."""
    h, w = card.shape[:2]
    cx = W // 2 if e.get("x", "center") == "center" else int(e["x"]) + w // 2
    if "y" in e:
        return card, cx, int(e["y"]) + h // 2
    if face is None:
        top, bottom = SAFE_TOP, SAFE_TOP + h
    else:
        fy0, fy1 = face[1] - 0.25 * face[3], face[1] + face[3] * 1.05  # include hair and chin
        above = (SAFE_TOP, max(SAFE_TOP, fy0 - 20))
        below = (min(SAFE_BOTTOM, fy1 + 20), SAFE_BOTTOM)
        top, bottom = max([above, below], key=lambda b: b[1] - b[0])
    room = bottom - top
    if room < h:
        s = max(room, 380) / h  # never smaller than this; readable beats perfectly clear
        card = cv2.resize(card, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        h = card.shape[0]
    return card, cx, int((top + bottom) / 2)


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

    text_layers = [render_text_layer(e, W, H) for e in texts]
    cards = [np.array(render_photo_card(e)) for e in photos]

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
            s = 1 + (e.get("scale", 1.15) - 1) * k
            cw, ch = W / s, H / s
            x0 = min(max(face_c[0] - cw / 2, 0), W - cw)
            y0 = min(max(face_c[1] - ch * 0.42, 0), H - ch)  # keep eyes in the upper-middle
            frame = cv2.resize(frame[int(y0):int(y0 + ch), int(x0):int(x0 + cw)], (W, H),
                               interpolation=cv2.INTER_CUBIC)

        # --- text behind the person ---
        tb = [(e, L) for e, L in zip(texts, text_layers) if e["start"] <= t < e["end"]]
        if tb:
            rgb = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            m = seg.segment_for_video(rgb, ts_ms).confidence_masks[0].numpy_view()[..., 0].copy()
            m = cv2.GaussianBlur(np.clip((m - 0.35) / 0.3, 0, 1), (7, 7), 0)  # firm, soft-edged matte
            if prev_mask is not None:
                m = 0.6 * m + 0.4 * prev_mask  # temporal smoothing against flicker
            prev_mask = m
            person = frame.copy()
            for e, L in tb:
                age = t - e["start"]
                left = e["end"] - t
                anim = e.get("anim", "rise")
                alpha = ease_out(min(age, left) / 0.2) if anim != "none" else 1.0
                dy = int((1 - ease_out(age / 0.3)) * 60) if anim == "rise" else 0
                layer = L.copy()
                layer[..., 3] *= alpha
                frame = blend(frame, layer, 0, dy)
            m3 = m[..., None]
            frame = (person * m3 + frame * (1 - m3)).astype(np.uint8)
        else:
            prev_mask = None

        # --- photo overlays (on top of everything) ---
        for i, (e, card) in enumerate(zip(photos, cards)):
            if not (e["start"] <= t < e["end"]):
                continue
            if i not in placements:
                placements[i] = place_card(e, card, detect_face(frame, ts_ms), W)
            card, cx, cy = placements[i]
            age, left = t - e["start"], e["end"] - t
            anim = e.get("anim", "pop")
            img = card
            if anim == "pop":
                s = 0.85 + 0.15 * ease_out(age / 0.18) if age < 0.18 else (
                    0.9 + 0.1 * ease_out(left / 0.12) if left < 0.12 else 1.0)
                img = cv2.resize(card, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
            img = img.astype(np.float32)
            if anim in ("pop", "fade"):
                img[..., 3] *= ease_out(min(age, left) / 0.12)
            h, w = img.shape[:2]
            frame = blend(frame, img, cx - w // 2, cy - h // 2)

        enc.stdin.write(frame.tobytes())
        n += 1

    enc.stdin.close()
    enc.wait()
    seg.close()
    faces.close()


if __name__ == "__main__":
    main(*sys.argv[1:4])
