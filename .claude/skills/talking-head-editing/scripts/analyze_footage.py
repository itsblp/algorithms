#!/usr/bin/env python3
"""Look at the footage and recommend a talking-head style (see ../styles/), or hand off to the
separate voiceover-montage format when the footage is narration + many short clips.

Usage: analyze_footage.py FILE_OR_DIR [...]   (prints a JSON report + a recommendation)

Per video: duration, orientation, how often a face is visible, how big the face is
(selfie close-up vs. medium shot), whether there is speech-level audio, camera motion,
and how bright the caption bands are (top y 260-420, middle y 900-1100 on 1080x1920),
so captions can be anchored where they stay readable. Audio-only files (.m4a/.mp3/.wav)
count as a voiceover.
"""
import json
import os
import subprocess
import sys

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "..", "models", "blaze_face_short_range.tflite")
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv"}
AUDIO_EXT = {".m4a", ".mp3", ".wav", ".aac"}


def mean_volume(path):
    out = subprocess.run(["ffmpeg", "-i", path, "-vn", "-af", "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    for line in out.splitlines():
        if "mean_volume" in line:
            return float(line.split(":")[1].split()[0])
    return None


def analyze_video(path, det):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    dur = n / fps if n else 0
    samples = max(6, min(24, int(dur)))
    faces, sizes, top_l, mid_l, motion = 0, [], [], [], []
    prev = None
    for i in range(samples):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i * n / samples))
        ok, f = cap.read()
        if not ok:
            continue
        f = cv2.resize(f, (540, int(540 * H / W)))
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        h = g.shape[0]
        top_l.append(float(g[int(h * 260 / 1920):int(h * 420 / 1920)].mean()))
        mid_l.append(float(g[int(h * 900 / 1920):int(h * 1100 / 1920)].mean()))
        if prev is not None:
            motion.append(float(np.abs(g.astype(int) - prev.astype(int)).mean()))
        prev = g
        r = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(f, cv2.COLOR_BGR2RGB)))
        if r.detections:
            faces += 1
            sizes.append(r.detections[0].bounding_box.height / h)
    vol = mean_volume(path)
    face_h = float(np.median(sizes)) if sizes else 0.0
    return {
        "file": os.path.basename(path), "duration_s": round(dur, 1), "size": f"{W}x{H}",
        "vertical": H > W, "face_visible": round(faces / samples, 2),
        "face_height": round(face_h, 2),
        "framing": "selfie close-up" if face_h >= 0.22 else ("medium shot" if face_h >= 0.09 else
                                                                ("wide / no face" if face_h else "no face")),
        "speech_audio": vol is not None and vol > -35, "mean_volume_db": vol,
        "camera_motion": round(float(np.mean(motion)), 1) if motion else 0.0,
        "top_band_luma": round(float(np.mean(top_l)), 0) if top_l else None,
        "mid_band_luma": round(float(np.mean(mid_l)), 0) if mid_l else None,
        "low_res": min(W, H) < 1000,
    }


def recommend(videos, audio_files):
    talk = [v for v in videos if v["face_visible"] >= 0.6 and v["speech_audio"]]
    short = [v for v in videos if v["duration_s"] < 8]
    reasons = []
    if audio_files or (len(videos) >= 4 and len(short) >= len(videos) * 0.6):
        style = "voiceover-montage (separate format: use the voiceover-montage skill)"
        reasons.append("a voiceover file and/or many short candid clips" if audio_files else "many short candid clips")
    elif len(talk) == 1 and talk[0]["framing"] == "selfie close-up" and len(videos) - len(talk) <= 1:
        style = "quiet-take"
        reasons.append("one continuous selfie take with little or no B-roll")
    else:
        style = "story-cut"
        reasons.append(f"{len(talk)} talking take(s) plus {len(videos) - len(talk)} other clip(s)")
        if talk and talk[0]["framing"] == "medium shot":
            reasons.append("medium shot leaves room for punch-ins and above-head overlays")
    ref = talk[0] if talk else (videos[0] if videos else None)
    caption_anchor = None
    if ref:
        if style == "quiet-take":
            caption_anchor = "top" if (ref["top_band_luma"] or 0) < 185 else "top + stronger shadow (bright wall)"
        else:
            caption_anchor = "middle" if (ref["mid_band_luma"] or 0) < 200 else "middle + stronger shadow"
    warnings = []
    if any(v["low_res"] for v in videos):
        warnings.append("some clips are below 1080p (likely app downloads); ask for the camera originals")
    if any(not v["vertical"] for v in videos):
        warnings.append("horizontal clips will be center-cropped to 9:16")
    return {"style": style, "why": "; ".join(reasons), "caption_anchor": caption_anchor, "warnings": warnings}


def main(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            files += [os.path.join(p, f) for f in sorted(os.listdir(p))]
        else:
            files.append(p)
    det = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
        base_options=BaseOptions(model_asset_path=MODEL)))
    videos = [analyze_video(f, det) for f in files if os.path.splitext(f)[1].lower() in VIDEO_EXT]
    audio = [os.path.basename(f) for f in files if os.path.splitext(f)[1].lower() in AUDIO_EXT]
    det.close()
    print(json.dumps({"videos": videos, "voiceover_files": audio,
                      "recommendation": recommend(videos, audio)}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
