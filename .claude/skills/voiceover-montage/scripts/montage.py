#!/usr/bin/env python3
"""Assemble a voiceover montage: one voice track over a sequence of candid clips.

Usage: montage.py plan.json out.mp4

plan.json:
{
  "vo": "voice.m4a",          # the narration (a voice memo, or a talking clip's audio)
  "vo_in": 0.0,                # optional: where the narration starts in that file
  "clips": [                   # in order; each fills its "dur" seconds of the timeline
    {"path": "clips/desk.mov", "in": 3.2, "dur": 1.8},
    {"path": "clips/car.mov",  "in": 0.0, "dur": 2.4, "speed": 1.0}
  ],
  "ambient_db": -24            # clip sound under the narration (null = mute clips)
}
Clips are center-cropped to 9:16 and scaled to 1080x1920 at 30 fps. Cut points should land
on phrase boundaries of the narration (use its word timestamps), so plan "dur" from them.
"""
import json
import subprocess
import sys

plan = json.load(open(sys.argv[1]))
out = sys.argv[2]
clips = plan["clips"]
amb = plan.get("ambient_db", -24)

args = ["ffmpeg", "-loglevel", "error", "-y"]
for c in clips:
    args += ["-ss", str(c.get("in", 0)), "-t", str(c["dur"] * c.get("speed", 1.0)), "-i", c["path"]]
args += ["-ss", str(plan.get("vo_in", 0)), "-i", plan["vo"]]
total = sum(c["dur"] for c in clips)

f = []
for i, c in enumerate(clips):
    sp = c.get("speed", 1.0)
    f.append(f"[{i}:v]crop='min(iw,ih*9/16)':'min(ih,iw*16/9)',scale=1080:1920,setsar=1,fps=30,"
             f"setpts=(PTS-STARTPTS)/{sp},trim=duration={c['dur']}[v{i}]")
    if amb is not None:
        f.append(f"[{i}:a]atrim=duration={c['dur'] * sp},asetpts=PTS-STARTPTS,atempo={sp},"
                 f"apad=whole_dur={c['dur']},atrim=duration={c['dur']},volume={amb}dB[a{i}]")
f.append("".join(f"[v{i}]" for i in range(len(clips))) + f"concat=n={len(clips)}:v=1:a=0[v]")
vo = len(clips)
f.append(f"[{vo}:a]atrim=duration={total},asetpts=PTS-STARTPTS[vo]")
if amb is not None:
    f.append("".join(f"[a{i}]" for i in range(len(clips))) + f"concat=n={len(clips)}:v=0:a=1[amb]")
    f.append("[vo][amb]amix=inputs=2:duration=first:normalize=0[a]")
else:
    f.append("[vo]anull[a]")
args += ["-filter_complex", ";".join(f), "-map", "[v]", "-map", "[a]", "-t", str(total),
         "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", out]
subprocess.run(args, check=True)
print(out)
