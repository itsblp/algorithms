#!/usr/bin/env python3
"""Overlapping-lines audio style: each new line starts while the last ~0.25 s of the previous line
is still fading out underneath it (an L-cut on every sentence boundary). This gives voiceover-style
momentum with no air between lines.

Usage: overlap_lines.py tight.mp4 words_tight.json OUTDIR [--overlap 0.25]

Run it AFTER tighten.py and apply_cuts.py (on the tightened video). Lines are sentences, found from
the punctuation at the end of words (. ? !). Per boundary:
  - audio: the next line starts `overlap` seconds before the previous one ends, at full volume;
    the previous line's tail fades out under it;
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

p = argparse.ArgumentParser()
p.add_argument("video")
p.add_argument("words")
p.add_argument("outdir")
p.add_argument("--overlap", type=float, default=0.25)
a = p.parse_args()

words = json.load(open(a.words))
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                     "-of", "csv=p=0", a.video]).strip())
# cut points between lines: midway through the (already tiny) gap after a sentence-ending word
cuts = [0.0]
for w, nxt in zip(words, words[1:]):
    if re.search(r"[.?!][\"')]*$", w["word"].strip()):
        cuts.append((w["end"] + nxt["start"]) / 2)
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
    fade = f",afade=t=out:st={(e - s) - ov:.3f}:d={ov:.3f}:curve=qsin" if i < n - 1 else ""
    g.append(f"[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01{fade},"
             f"adelay={int(offsets[i] * 1000)}:all=1[a{i}];")
g.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v];")
g.append("".join(f"[a{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0:duration=longest[a]")
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
