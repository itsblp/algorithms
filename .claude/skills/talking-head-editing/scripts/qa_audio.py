#!/usr/bin/env python3
"""Final audio QA for a finished edit. It must pass before a video is sent to the user.

Usage: qa_audio.py final.mp4 words_final.json [--names Saelo]

Checks (exit code 1 if any fail):
  1. Stutter / doubled audio: any 80 ms stretch that repeats almost exactly within the next
     60-400 ms (e.g. a consonant replayed at a cut: "c-consider"). Natural speech never repeats
     sample-for-sample, so a near-perfect waveform match means the same source audio played twice.
  2. Script match: Whisper re-transcribes the finished video, and the result is compared
     word-for-word with the intended words. Extra, missing or changed words are listed (brand
     names given with --names are accepted in any spelling or split Whisper picks).
  3. Swallowed words: any word under 60% recognition confidence, except the first word of the
     video (Whisper is always less sure at the very start).
"""
import argparse
import difflib
import json
import re
import subprocess
import sys

import numpy as np

p = argparse.ArgumentParser()
p.add_argument("video")
p.add_argument("words")
p.add_argument("--names", nargs="*", default=[], help="brand/proper names Whisper may misspell")
a = p.parse_args()

sr = 16000
x = np.frombuffer(subprocess.run(["ffmpeg", "-loglevel", "error", "-i", a.video, "-vn", "-ac", "1", "-ar", str(sr),
                                  "-f", "f32le", "-"], capture_output=True, check=True).stdout, np.float32)
fail = False

# 1. doubled audio
win, hop = int(0.08 * sr), int(0.02 * sr)
lo, hi = int(0.06 * sr), int(0.40 * sr)
lvl = np.percentile(np.abs(x), 99)
hits = []
for s in range(0, len(x) - win - hi, hop):
    w = x[s:s + win]
    e = np.sqrt((w ** 2).mean())
    if e < lvl * 0.05:  # skip near-silence
        continue
    seg = x[s + lo:s + hi + win]
    c = np.correlate(seg, w, mode="valid")
    norms = np.sqrt(np.convolve(seg ** 2, np.ones(win), mode="valid")) * np.linalg.norm(w) + 1e-9
    r = c / norms
    k = int(np.argmax(r))
    if r[k] > 0.97:
        hits.append((round(s / sr, 2), round((lo + k) / sr, 3), round(float(r[k]), 3)))
merged = []
for h in hits:
    if not merged or h[0] - merged[-1][0] > 0.2:
        merged.append(h)
print(f"1. doubled audio: {len(merged)} spot(s)" + ("" if not merged else f" -> {merged} (time s, repeat after s, match)"))
fail |= bool(merged)

# 2 + 3. re-transcribe
from faster_whisper import WhisperModel  # noqa: E402

model = WhisperModel("small", device="cpu", compute_type="int8")
segs, _ = model.transcribe(x, language="en", word_timestamps=True, beam_size=5)
heard = [w for s in segs for w in s.words]
norm = lambda t: re.sub(r"[^a-z0-9']", "", t.lower())
names = {norm(n) for n in a.names}
expect = [norm(w["word"]) for w in json.load(open(a.words)) if norm(w["word"])]
gidx = [k for k, w in enumerate(heard) if norm(w.word)]
got = [norm(heard[k].word) for k in gidx]
diffs, name_heard = [], set()
for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=expect, b=got, autojunk=False).get_opcodes():
    if op == "equal":
        continue
    exp, hrd = expect[i1:i2], got[j1:j2]
    if op == "replace" and any(e in names for e in exp) and difflib.SequenceMatcher(
            a="".join(exp), b="".join(hrd)).ratio() > 0.6:
        name_heard.update(gidx[j] for j in range(j1, j2))
        continue  # brand name spelled or split differently (e.g. "Saelo" -> "say hello")
    diffs.append((op, " ".join(exp), " ".join(hrd)))
print(f"2. script match: {len(expect)} words expected, {len(got)} heard, {len(diffs)} difference(s)"
      + ("" if not diffs else f" -> {diffs}"))
fail |= bool(diffs)
low = [(w.word.strip(), round(w.start, 2), round(w.probability, 2)) for k, w in enumerate(heard)
       if k > 0 and w.probability < 0.6 and norm(w.word) not in names and k not in name_heard]
print(f"3. low-confidence words: {low or 'none'}")
fail |= bool(low)
print("RESULT:", "FAIL" if fail else "PASS")
sys.exit(1 if fail else 0)
