#!/usr/bin/env python3
"""Explainer Board: the talking head shrinks into a card at the top of a clean canvas, and
hand-drawn notes write themselves on below it.

Usage: explainer_board.py INPUT.mp4 board.json OUTPUT.mp4

board.json (times in seconds on INPUT's timeline):
{
  "canvas": "#FFFFFF",               # board color (or the brand off-white "#F4F1EC")
  "ink": "#111111",                  # handwriting / drawing color
  "shrink_at": 1.2,                  # full-frame talking head until here, then shrinks into the card
                                     # over 0.45 s (omit: card from the start)
  "card": {"y": 170, "w": 860, "h": 760},
  "notes": [
    {"start": 2.0, "text": "HOW TO\\nEDIT TIPS", "reveal": 1.0, "size": 140},
        # handwriting fallback (Caveat Bold). Prefer the user's own drawings:
    {"start": 5.0, "path": "drawings/skateboard.png", "reveal": 0.8, "width": 640},
        # PNG from her iPad/paper. A white background is keyed out automatically.
    {"start": 3.4, "circle": 0, "reveal": 0.6},   # hand-drawn loop around note #0
    {"start": 3.9, "underline": 0, "reveal": 0.4},
    {"start": 8.0, "clear": true}                 # wipe the board for the next point
  ]
}
Notes sit centered in the board area under the card, inside the safe zone (x 80-880,
bottom y 1400). Optional "y" (top px) per note. Burn captions AFTER this script, inside the card
(e.g. kinetic_captions.py --baseline <card y + h - 80>). Audio is copied from INPUT.
"""
import json
import math
import os
import random
import subprocess
import sys

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(HERE, "..", "models")
HAND_FONT = os.path.join(HERE, "..", "..", "short-form-platform-specs", "fonts", "Caveat-Bold.ttf")
SAFE_LEFT, SAFE_RIGHT, SAFE_BOTTOM = 80, 880, 1400
W, H = 1080, 1920


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def render_text(note, ink):
    font = ImageFont.truetype(HAND_FONT, note.get("size", 140))
    lines = note["text"].split("\n")
    lh = int(font.size * 1.05)
    wmax = int(max(font.getlength(l) for l in lines)) + 20
    img = Image.new("RGBA", (wmax, lh * len(lines) + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rows = []
    for i, l in enumerate(lines):
        lw = font.getlength(l)
        x0 = (wmax - lw) / 2
        d.text((x0, 10 + i * lh), l, font=font, fill=hex_rgb(ink) + (255,))
        rows.append((10 + i * lh, 10 + (i + 1) * lh, int(x0), int(x0 + lw)))
    return np.array(img), rows


def render_drawing(note):
    img = Image.open(note["path"]).convert("RGBA")
    w = note.get("width", 640)
    img = img.resize((w, round(img.height * w / img.width)), Image.LANCZOS)
    a = np.array(img).astype(np.float32)
    if a[..., 3].min() > 250:  # no transparency: key out a light paper/white background
        lum = a[..., :3].mean(axis=2)
        a[..., 3] = np.clip((235 - lum) / 120, 0, 1) * 255
    return a.astype(np.uint8), [(0, a.shape[0], 0, a.shape[1])]


def reveal_mask(shape, rows, p):
    """Write-on: rows are revealed one after another, each left to right, with a soft edge."""
    m = np.zeros(shape[:2], np.float32)
    n = len(rows)
    for i, (y0, y1, x0, x1) in enumerate(rows):
        q = min(max(p * n - i, 0), 1)
        if q <= 0:
            continue
        edge = x0 + q * (x1 - x0 + 40)
        xs = np.arange(shape[1])
        m[y0:y1, :] = np.clip((edge - xs) / 40, 0, 1)[None, :]
    return m


def loop_points(box, seed, overshoot=1.12):
    """A slightly wobbly hand-drawn ellipse around box (x0, y0, x1, y1), as a point list."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 + 50, (y1 - y0) / 2 + 40
    pts, start = [], rnd.uniform(-2.4, -1.8)
    for k in range(120):
        a = start + 2 * math.pi * overshoot * k / 119
        wob = 1 + 0.03 * math.sin(k / 7 + rnd.random())
        pts.append((cx + rx * wob * math.cos(a), cy + ry * wob * math.sin(a) + k * 0.15))
    return pts


def blend(frame, rgba, x, y, alpha=None):
    h, w = rgba.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1:
        return
    src = rgba[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32) / 255.0
    a = src[..., 3:4] if alpha is None else src[..., 3:4] * alpha[y0 - y:y1 - y, x0 - x:x1 - x, None]
    roi = frame[y0:y1, x0:x1].astype(np.float32) / 255.0
    frame[y0:y1, x0:x1] = ((src[..., 2::-1] * a + roi * (1 - a)) * 255).astype(np.uint8)


def main(inp, board_path, out):
    b = json.load(open(board_path))
    canvas = np.array(hex_rgb(b.get("canvas", "#FFFFFF"))[::-1], np.uint8)
    ink = b.get("ink", "#111111")
    card = {"y": 170, "w": 860, "h": 760, **b.get("card", {})}
    card_rect = ((W - card["w"]) // 2, card["y"], card["w"], card["h"])
    shrink_at = b.get("shrink_at")
    notes = b.get("notes", [])
    board_top = card["y"] + card["h"] + 40

    rendered, placed = {}, {}
    for i, nt in enumerate(notes):
        if "text" in nt:
            rendered[i] = render_text(nt, ink)
        elif "path" in nt:
            rendered[i] = render_drawing(nt)
    ytop = board_top
    for i, nt in enumerate(notes):
        if nt.get("clear"):
            ytop = board_top
        if i in rendered:
            img, rows = rendered[i]
            room = SAFE_BOTTOM - board_top
            if img.shape[0] > room or img.shape[1] > SAFE_RIGHT - SAFE_LEFT:
                s = min(room / img.shape[0], (SAFE_RIGHT - SAFE_LEFT) / img.shape[1])
                img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
                rows = [(int(a * s), int(c * s), int(d * s), int(e * s)) for a, c, d, e in rows]
                rendered[i] = (img, rows)
            x = (SAFE_LEFT + SAFE_RIGHT - img.shape[1]) // 2
            y = nt.get("y", ytop)
            y = min(y, SAFE_BOTTOM - img.shape[0])
            placed[i] = (x, y)
            ytop = y + img.shape[0] + 20

    cap = cv2.VideoCapture(inp)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    det = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
        base_options=BaseOptions(model_asset_path=os.path.join(MODELS, "blaze_face_short_range.tflite")),
        running_mode=vision.RunningMode.VIDEO))
    enc = subprocess.Popen([
        "ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
        "-r", f"{fps}", "-i", "-", "-i", inp, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-crf", "16",
        "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", out], stdin=subprocess.PIPE)

    face_c = None
    n = 0
    while True:
        ok, src = cap.read()
        if not ok:
            break
        if src.shape[1] != W or src.shape[0] != H:
            src = cv2.resize(src, (W, H), interpolation=cv2.INTER_CUBIC)
        t = n / fps
        if n % 5 == 0:
            r = det.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,
                                              data=cv2.cvtColor(src, cv2.COLOR_BGR2RGB)), int(t * 1000))
            if r.detections:
                bb = r.detections[0].bounding_box
                c = (bb.origin_x + bb.width / 2, bb.origin_y + bb.height / 2)
                face_c = c if face_c is None else (0.8 * face_c[0] + 0.2 * c[0], 0.8 * face_c[1] + 0.2 * c[1])
        fc = face_c or (W / 2, H * 0.38)

        # where the talking head sits right now (full frame -> card)
        k = 1.0 if shrink_at is None else ease((t - shrink_at) / 0.45)
        rx = int(card_rect[0] * k)
        ry = int(card_rect[1] * k)
        rw = int(W + (card_rect[2] - W) * k)
        rh = int(H + (card_rect[3] - H) * k)
        # crop the source to the rect's aspect, centered on the face (face in upper-middle)
        ch = H
        cw = int(ch * rw / rh)
        if cw > W:
            cw, ch = W, int(W * rh / rw)
        cx0 = int(min(max(fc[0] - cw / 2, 0), W - cw))
        cy0 = int(min(max(fc[1] - ch * 0.4, 0), H - ch))
        view = cv2.resize(src[cy0:cy0 + ch, cx0:cx0 + cw], (rw, rh), interpolation=cv2.INTER_AREA)
        frame = np.empty((H, W, 3), np.uint8)
        frame[:] = canvas
        frame[ry:ry + rh, rx:rx + rw] = view

        # notes (only once the card is in place)
        visible = []
        for i, nt in enumerate(notes):
            if nt["start"] > t:
                break
            if nt.get("clear"):
                visible = [] if t - nt["start"] > 0.25 else [(j, 1 - (t - nt["start"]) / 0.25) for j, _ in visible]
                continue
            visible.append((i, 1.0))
        for i, fade in visible:
            nt = notes[i]
            p = ease((t - nt["start"]) / nt.get("reveal", 0.8))
            if i in rendered:
                img, rows = rendered[i]
                x, y = placed[i]
                blend(frame, img, x, y, reveal_mask(img.shape, rows, p) * fade)
            elif "circle" in nt or "underline" in nt:
                tgt = nt.get("circle", nt.get("underline"))
                if tgt not in placed:
                    continue
                img = rendered[tgt][0]
                x, y = placed[tgt]
                box = (x, y, x + img.shape[1], y + img.shape[0])
                if "circle" in nt:
                    pts = loop_points(box, seed=i)
                else:
                    pts = [(box[0] + (box[2] - box[0]) * q / 40, box[3] + 6 + 4 * math.sin(q / 6)) for q in range(41)]
                m = max(2, int(len(pts) * p))
                layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ImageDraw.Draw(layer).line(pts[:m], fill=hex_rgb(ink) + (int(255 * fade),), width=8, joint="curve")
                blend(frame, np.array(layer), 0, 0)

        enc.stdin.write(frame.tobytes())
        n += 1
    enc.stdin.close()
    enc.wait()
    det.close()


if __name__ == "__main__":
    main(*sys.argv[1:4])
