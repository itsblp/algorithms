#!/usr/bin/env python3
"""Cut a video down to the kept pieces (segments.txt from story_cut.py), in order, with 10 ms
audio fades at every join so cuts never pop.

Usage: apply_cuts.py INPUT.mp4 segments.txt OUTPUT.mp4
"""
import os
import subprocess
import sys
import tempfile

inp, seg_path, out = sys.argv[1:4]
segs = [tuple(map(float, l.split())) for l in open(seg_path) if l.strip()]
parts = []
for i, (s, e) in enumerate(segs):
    d = e - s
    parts.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=increase,"
                 f"crop=1080:1920,setsar=1,fps=30[v{i}];")
    parts.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={d - 0.01:.3f}:d=0.01[a{i}];")
parts.append("".join(f"[v{i}][a{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=1[v][a]")
with tempfile.NamedTemporaryFile("w", suffix=".filter", delete=False) as f:
    f.write("".join(parts))
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", inp, "-filter_complex_script", f.name,
                "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "16", "-c:a", "aac", "-b:a", "320k", out],
               check=True)
os.unlink(f.name)
print(out)
