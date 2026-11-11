#!/usr/bin/env python3
"""Remove breaths and dead air from an already story-cut video, using the audio itself.

Usage: tighten.py cut.mp4 words_cut.json OUTDIR [--gap 0.14] [--keep 0.05] [--below 18]

Whisper's word timings often run into the breath after a word, so transcript-based cutting
leaves breaths and short pauses. This measures the speaker's level (90th percentile of
10 ms RMS frames), treats anything more than --below dB under it as non-speech (breaths, room
tone, mouth clicks), and shortens every non-speech run longer than --gap to --keep seconds
(split evenly before and after the cut), so speech flows with no audible gasps.

Writes OUTDIR/tight_segments.txt (for apply_cuts.py on cut.mp4) and OUTDIR/words_tight.json
(caption timings re-mapped onto the tightened timeline), then prints how much was removed.
"""
import argparse
import json
import os
import subprocess

import numpy as np

p = argparse.ArgumentParser()
p.add_argument("video")
p.add_argument("words")
p.add_argument("outdir")
p.add_argument("--gap", type=float, default=0.14, help="non-speech runs longer than this get shortened")
p.add_argument("--keep", type=float, default=0.05, help="seconds of each run that stay")
p.add_argument("--below", type=float, default=18, help="dB under speech level that counts as non-speech")
a = p.parse_args()

sr, hop = 16000, 160  # 10 ms frames
pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", a.video, "-vn", "-ac", "1", "-ar", str(sr),
                      "-f", "f32le", "-"], capture_output=True, check=True).stdout
x = np.frombuffer(pcm, np.float32)
n = len(x) // hop
rms = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(axis=1) + 1e-12)
db = 20 * np.log10(rms)
db = np.convolve(db, np.ones(3) / 3, mode="same")  # light smoothing
speech_level = np.percentile(db, 90)
thr = speech_level - a.below
quiet = db < thr
dur = n * hop / sr

# non-speech runs -> removal intervals (keep a.keep/2 at each edge so word onsets/tails survive)
removed = []
k = 0
while k < n:
    if quiet[k]:
        j = k
        while j < n and quiet[j]:
            j += 1
        s, e = k * hop / sr, j * hop / sr
        if e - s > a.gap:
            removed.append((s + a.keep / 2, e - a.keep / 2, float(db[k:j].mean())))
        k = j
    else:
        k += 1

# never cut inside a transcribed word's core (guards quiet consonants like "f", "s", "th")
words = json.load(open(a.words))
cores = [(w["start"] + 0.04, w["end"] - 0.04) for w in words if w["end"] - w["start"] > 0.1]
safe = []
for s, e, level in removed:
    # Only short, not-too-quiet runs could be a quiet consonant inside a word; breaths and real
    # silence are longer or deeper, so Whisper's stretched word timings don't protect them.
    maybe_consonant = level > thr - 12 and (e - s) < 0.2
    for cs, ce in (cores if maybe_consonant else []):
        if s < ce and e > cs:  # overlap: shrink the cut away from the word core
            if cs - s >= a.gap / 2:
                e = min(e, cs)
            else:
                s = max(s, ce)
    if e - s > 0.04:
        safe.append((s, e))

keep, t = [], 0.0
for s, e in safe:
    if s > t:
        keep.append((t, s))
    t = e
if t < dur:
    keep.append((t, dur))


def remap(x):
    gone = sum(min(e, x) - s for s, e in safe if s < x)
    return round(x - gone, 3)


os.makedirs(a.outdir, exist_ok=True)
with open(os.path.join(a.outdir, "tight_segments.txt"), "w") as f:
    f.write("".join(f"{s:.3f} {e:.3f}\n" for s, e in keep))
json.dump([{**w, "start": remap(w["start"]), "end": remap(w["end"])} for w in words],
          open(os.path.join(a.outdir, "words_tight.json"), "w"), indent=1)
cut = sum(e - s for s, e in safe)
print(f"speech level {speech_level:.1f} dB, non-speech below {thr:.1f} dB")
print(f"removed {len(safe)} breaths/pauses, {cut:.1f} s: {dur:.1f} s -> {dur - cut:.1f} s")
