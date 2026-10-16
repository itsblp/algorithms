#!/usr/bin/env python3
"""Visual QA: shade the IG + TikTok UI zones on sampled frames of a vertical video.

Usage: safe_zone_check.py VIDEO.mp4 OUT.png [--frames 8]

Cyan = covered by app UI on at least one platform (bottom 520 px: handle, caption, audio, chips;
right 200 px: avatar + buttons; top 260 px: tabs/search; sides: tall-phone crop), scaled from 1080x1920.
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
    "drawbox=x=0:y=1400:w=1080:h=520:color=cyan@0.40:t=fill",   # bottom: handle + caption + audio + chips
    "drawbox=x=880:y=260:w=200:h=1140:color=cyan@0.40:t=fill",  # right: avatar + engagement buttons
    "drawbox=x=0:y=260:w=80:h=1140:color=cyan@0.40:t=fill",    # left: tall phones crop the sides
    "drawbox=x=0:y=0:w=1080:h=260:color=cyan@0.40:t=fill",      # top: tabs / search bar
    "drawbox=x=0:y=1400:w=1080:h=3:color=cyan:t=fill",
])
cols = min(a.frames, 4)
rows = -(-a.frames // cols)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a.video, "-vf",
                f"fps={fps:.5f},{zones},scale=270:-1,tile={cols}x{rows}", "-frames:v", "1", a.out], check=True)
print(a.out)
