#!/usr/bin/env python3
"""Overlapping-lines audio style (the TikTok voiceover trend): each new line starts ~0.25 s before
the previous line finishes, both at full volume, so the speech is one continuous, fast stream
with no dead air (an L-cut on every sentence boundary). This gives voiceover-style
momentum with no air between lines.

Usage: overlap_lines.py tight.mp4 words_tight.json OUTDIR [--overlap 0.25]

Run it AFTER tighten.py and apply_cuts.py (on the tightened video). Lines are sentences, found from
the punctuation at the end of words (. ? !). Per boundary:
  - audio: the next line starts `overlap` seconds before the previous one ends; BOTH play at
    full volume through the overlap (no fade; a limiter stops the doubled audio clipping);
  - video: cuts to the next line exactly when its audio starts, so its lip-sync is perfect; the
    previous line's tail plays over the new shot (L-cut).
Only sentence boundaries overlap, never cuts inside a sentence.

Writes OUTDIR/overlap.mp4 and OUTDIR/words_overlap.json (caption timings on the new timeline).
"""
import argparse
import json
import os
import re
import subprocess
import tempfile

import numpy as np

p = argparse.ArgumentParser()
p.add_argument("video")
p.add_argument("words")
p.add_argument("outdir")
p.add_argument("--overlap", type=float, default=0.25)
a = p.parse_args()

words = json.load(open(a.words))
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                     "-of", "csv=p=0", a.video]).strip())
# Line boundaries come from the AUDIO, not Whisper's timing (Whisper ends words early, which
# clipped "lucky"): after each sentence-ending word, the line ends where its sound actually stops,
# i.e. the first 30 ms of non-speech before the next line's audio begins.
pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", a.video, "-vn", "-ac", "1", "-ar", "16000",
                      "-f", "f32le", "-"], capture_output=True, check=True).stdout
x = np.frombuffer(pcm, np.float32)
nf = len(x) // 160
db = 20 * np.log10(np.sqrt((x[:nf * 160].reshape(nf, 160) ** 2).mean(axis=1) + 1e-12))
thr = np.percentile(db, 90) - 18


def next_onset(t_next):
    """Where the next line's sound actually begins: walk back from just after Whisper's start of
    the next word while it's still speech; the onset is the first loud frame after the last quiet
    one. Everything before it, including the full tail of the previous word, stays with the
    previous line (silences inside words, like the "c" in "lucky", can't fool this)."""
    k = min(int((t_next + 0.08) * 100), nf - 1)
    while k > 0 and db[k] >= thr:
        k -= 1
    return (k + 1) / 100


cuts = [0.0]
for w, nxt in zip(words, words[1:]):
    if re.search(r"[.?!][\"')]*$", w["word"].strip()):
        cuts.append(max(next_onset(nxt["start"]) - 0.01, w["end"]))
cuts.append(dur)
lines = [(s, e) for s, e in zip(cuts, cuts[1:]) if e - s > a.overlap * 2]
ov = a.overlap
n = len(lines)

# timeline offsets: each line starts `ov` before the previous one ends
offsets, t = [], 0.0
for s, e in lines:
    offsets.append(t)
    t += (e - s) - ov
total = t + ov

g = []
for i, (s, e) in enumerate(lines):
    vlen = (e - s) - (ov if i < n - 1 else 0)  # picture leaves line i when line i+1 starts
    g.append(f"[0:v]trim={s:.3f}:{s + vlen:.3f},setpts=PTS-STARTPTS[v{i}];")
    # no fade: both lines stay at full volume through the overlap (the user's spec); 10 ms edge
    # ramps only, so the cut itself never clicks
    fade = f",afade=t=out:st={max((e - s) - 0.01, 0):.3f}:d=0.01"
    g.append(f"[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01{fade},"
             f"adelay={int(offsets[i] * 1000)}:all=1[a{i}];")
g.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v];")
g.append("".join(f"[a{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0:duration=longest,alimiter=limit=0.95:level=disabled[a]")
fpath = tempfile.mktemp(suffix=".filter")
open(fpath, "w").write("".join(g))
os.makedirs(a.outdir, exist_ok=True)
out = os.path.join(a.outdir, "overlap.mp4")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a.video, "-filter_complex_script", fpath,
                "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}", "-c:v", "libx264", "-crf", "16",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", "-ar", "48000", out], check=True)
os.remove(fpath)


def remap(x):
    for i, (s, e) in enumerate(lines):
        if s <= x <= e:
            return round(offsets[i] + (x - s), 3)
    return round(x, 3)


json.dump([{**w, "start": remap(w["start"]), "end": remap(w["end"])} for w in words],
          open(os.path.join(a.outdir, "words_overlap.json"), "w"), indent=1)
print(f"{n} lines, {n - 1} overlaps of {ov:.2f} s: {dur:.1f} s -> {total:.1f} s")
print(out)
