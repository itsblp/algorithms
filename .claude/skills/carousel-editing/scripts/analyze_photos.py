#!/usr/bin/env python3
"""Look at the user's photos for a carousel and recommend a style (see ../styles/).

Usage: analyze_photos.py FILE_OR_DIR [...]   (prints JSON: per-photo report + recommendation)

Per photo: size, orientation, whether a face is present and where, and how calm and dark the
text zone is (y 900-1400 after a 9:16 cover crop): busy or bright zones make the cream
photo_stack type hard to read. A photo "works for photo_stack" when it's at least 1000 px on its
short side, roughly vertical, and has a readable text zone.
"""
import json
import os
import sys

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

HERE = os.path.dirname(os.path.abspath(__file__))
FACE_MODEL = os.path.join(HERE, "..", "..", "talking-head-editing", "models", "blaze_face_short_range.tflite")
EXT = {".jpg", ".jpeg", ".png", ".heic", ".webp"}


def cover_916(img):
    h, w = img.shape[:2]
    s = max(1080 / w, 1920 / h)
    img = cv2.resize(img, (round(w * s), round(h * s)))
    y0, x0 = int((img.shape[0] - 1920) * 0.4), (img.shape[1] - 1080) // 2
    return img[y0:y0 + 1920, x0:x0 + 1080]


def analyze(path, det):
    img = cv2.imread(path)
    if img is None:
        return {"file": os.path.basename(path), "error": "unreadable (HEIC? export as JPG)"}
    h, w = img.shape[:2]
    c = cover_916(img)
    zone = cv2.cvtColor(c[900:1400, 80:880], cv2.COLOR_BGR2GRAY)
    luma = float(zone.mean())
    busy = float(cv2.Laplacian(zone, cv2.CV_64F).var())
    r = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(c, cv2.COLOR_BGR2RGB)))
    face = None
    if r.detections:
        bb = r.detections[0].bounding_box
        face = {"center_y": round((bb.origin_y + bb.height / 2) / 1920, 2), "height": round(bb.height / 1920, 2)}
    readable = luma < 150 and busy < 900
    return {
        "file": os.path.basename(path), "size": f"{w}x{h}", "vertical": h >= w * 1.1,
        "short_side_ok": min(w, h) >= 1000, "face": face,
        "text_zone_luma": round(luma), "text_zone_busyness": round(busy),
        "text_zone_readable": readable,
        "photo_stack_ok": min(w, h) >= 1000 and readable and (face is None or face["center_y"] < 0.5),
    }


def main(paths):
    files = []
    for p in paths:
        files += [os.path.join(p, f) for f in sorted(os.listdir(p))] if os.path.isdir(p) else [p]
    files = [f for f in files if os.path.splitext(f)[1].lower() in EXT]
    det = vision.FaceDetector.create_from_options(
        vision.FaceDetectorOptions(base_options=BaseOptions(model_asset_path=FACE_MODEL)))
    photos = [analyze(f, det) for f in files]
    det.close()
    good = [p for p in photos if p.get("photo_stack_ok")]
    if len(good) >= 4:
        rec = {"style": "photo_stack", "why": f"{len(good)} photos have a readable lower text zone"}
    elif good:
        rec = {"style": "thesis (photo_stack cover)",
               "why": f"only {len(good)} strong photo(s): use the best one as the cover, thesis cards inside"}
    else:
        lowres = sum(1 for p in photos if not p.get("short_side_ok", True))
        busy = sum(1 for p in photos if p.get("short_side_ok") and not p.get("text_zone_readable"))
        why = []
        if lowres:
            why.append(f"{lowres} photo(s) under 1000 px (ask for originals, not app downloads or frames)")
        if busy:
            why.append(f"{busy} photo(s) too bright or busy where the type goes")
        rec = {"style": "thesis", "why": "; ".join(why) or "no photos supplied"}
    rec["note"] = ("content overrides: lists, steps and frameworks -> notes; "
                   "one-line coined concepts or dichotomies -> thesis")
    print(json.dumps({"photos": photos, "recommendation": rec}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
