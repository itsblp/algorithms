#!/usr/bin/env python3
"""Visual QA: shade the IG + TikTok UI zones on sampled frames of a vertical video.

Usage: safe_zone_check.py VIDEO.mp4 OUT.png [--frames 8]

Cyan = covered by app UI on at least one platform (bottom 480 px: handle, caption, audio;
right 150 px: like/comment/share; top 220 px: tabs/header), scaled from 1080x1920.
Any caption, title, or face inside cyan will collide with the UI on TikTok or IG.
"""
import argparse
import subprocess

p = argparse.ArgumentParser()
p.add_argument("video")
p.add_argument("out")
p.add_argument("--frames", type=int, default=8)
a = p.parse_args()

dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                     "-of", "csv=p=0", a.video]).strip())
fps = a.frames / dur
zones = ",".join([
    "scale=1080:1920",
    "drawbox=x=0:y=1440:w=1080:h=480:color=cyan@0.40:t=fill",   # bottom: handle + caption + audio
    "drawbox=x=930:y=220:w=150:h=1220:color=cyan@0.40:t=fill",  # right: engagement buttons
    "drawbox=x=0:y=0:w=1080:h=220:color=cyan@0.40:t=fill",      # top: tabs / header
    "drawbox=x=0:y=1440:w=1080:h=3:color=cyan:t=fill",
])
cols = min(a.frames, 4)
rows = -(-a.frames // cols)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a.video, "-vf",
                f"fps={fps:.5f},{zones},scale=270:-1,tile={cols}x{rows}", "-frames:v", "1", a.out], check=True)
print(a.out)
