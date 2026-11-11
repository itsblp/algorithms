#!/usr/bin/env python3
"""Cut a video down to the kept pieces (segments.txt from story_cut.py or tighten.py), in order,
with 10 ms audio fades at every join so cuts never pop.

Usage: apply_cuts.py INPUT.mp4 segments.txt OUTPUT.mp4

- Piece boundaries are snapped to the 30 fps frame grid, so picture and sound stay in sync.
- Video: each piece is rendered on its own (input seeking, exact frame count), then joined.
  This keeps memory low on 4K/60 phone files.
- Audio: cut and joined in ONE pass from the source. Encoding audio per piece would add an
  encoder lead-in of silence at every join, which brings back the pauses we just removed.
Output: 1080x1920, 30 fps, H.264 + AAC 48 kHz (phone rotation is applied automatically).
"""
import os
import subprocess
import sys
import tempfile

FPS = 30
inp, seg_path, out = sys.argv[1:4]
raw = [tuple(map(float, l.split())) for l in open(seg_path) if l.strip()]
segs = []
for s, e in raw:
    fs, fe = round(s * FPS), round(e * FPS)
    if fe > fs:
        segs.append((fs, fe))
tmp = tempfile.mkdtemp(prefix="cuts_")

# video pieces, exact frame counts
parts = []
for i, (fs, fe) in enumerate(segs):
    p = os.path.join(tmp, f"{i:03d}.mp4")
    subprocess.run([
        "ffmpeg", "-loglevel", "error", "-y", "-ss", f"{fs / FPS:.4f}", "-i", inp, "-an",
        "-vf", f"fps={FPS},scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
        "-frames:v", str(fe - fs), "-c:v", "libx264", "-crf", "16", "-preset", "fast",
        "-pix_fmt", "yuv420p", "-threads", "2", p], check=True)
    parts.append(p)
lst = os.path.join(tmp, "list.txt")
with open(lst, "w") as f:
    f.write("".join(f"file '{p}'\n" for p in parts))
video = os.path.join(tmp, "video.mp4")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                "-c", "copy", video], check=True)

# audio in one pass, same frame-snapped boundaries
graph = []
for i, (fs, fe) in enumerate(segs):
    s, e = fs / FPS, fe / FPS
    graph.append(f"[0:a]atrim={s:.4f}:{e:.4f},asetpts=PTS-STARTPTS,"
                 f"afade=t=in:d=0.01,afade=t=out:st={max(e - s - 0.01, 0):.4f}:d=0.01[a{i}];")
graph.append("".join(f"[a{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=0:a=1[a]")
gpath = os.path.join(tmp, "audio.filter")
open(gpath, "w").write("".join(graph))
audio = os.path.join(tmp, "audio.wav")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", inp, "-vn", "-filter_complex_script", gpath,
                "-map", "[a]", "-ar", "48000", "-ac", "2", audio], check=True)

subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", video, "-i", audio, "-map", "0:v", "-map", "1:a",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-shortest", "-movflags", "+faststart", out],
               check=True)
for f in parts + [lst, video, gpath, audio]:
    os.remove(f)
os.rmdir(tmp)
print(out)
