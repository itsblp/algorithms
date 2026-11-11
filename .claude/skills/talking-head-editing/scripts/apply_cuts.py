#!/usr/bin/env python3
"""Cut a video down to the kept pieces (segments.txt from story_cut.py), in order, with 10 ms
audio fades at every join so cuts never pop.

Usage: apply_cuts.py INPUT.mp4 segments.txt OUTPUT.mp4

Each piece is rendered on its own (seeking straight to it), then the pieces are joined. That keeps
memory low on big 4K/60 phone files, where one filter graph trimming many pieces runs out of memory.
Output: 1080x1920, 30 fps, H.264 + AAC (phone rotation is applied automatically).
"""
import os
import subprocess
import sys
import tempfile

inp, seg_path, out = sys.argv[1:4]
segs = [tuple(map(float, l.split())) for l in open(seg_path) if l.strip()]
tmp = tempfile.mkdtemp(prefix="cuts_")
parts = []
for i, (s, e) in enumerate(segs):
    d = e - s
    p = os.path.join(tmp, f"{i:03d}.mp4")
    subprocess.run([
        "ffmpeg", "-loglevel", "error", "-y", "-ss", f"{s:.3f}", "-i", inp, "-t", f"{d:.3f}",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30",
        "-af", f"afade=t=in:d=0.01,afade=t=out:st={max(d - 0.01, 0):.3f}:d=0.01,aresample=48000",
        "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p", "-threads", "2",
        "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-ac", "2", p], check=True)
    parts.append(p)
lst = os.path.join(tmp, "list.txt")
with open(lst, "w") as f:
    f.write("".join(f"file '{p}'\n" for p in parts))
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                "-c", "copy", "-movflags", "+faststart", out], check=True)
for p in parts:
    os.remove(p)
os.remove(lst)
os.rmdir(tmp)
print(out)
