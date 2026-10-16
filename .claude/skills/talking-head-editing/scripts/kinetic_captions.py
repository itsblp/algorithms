#!/usr/bin/env python3
"""Build kinetic (word-by-word, timed-to-speech) ASS captions from words.json.

Each chunk of 2-3 words is laid out in full from the start, so the line never
shifts, but every word stays invisible until it is spoken, then pops in.

Usage: kinetic_captions.py words.json > captions.ass
       [--font Inter] [--size 72] [--outline 4] [--words 3]
       [--baseline 1250] [--upper] [--keep-punct]
"""
import argparse
import json
import re

p = argparse.ArgumentParser()
p.add_argument("words")
p.add_argument("--font", default="Inter")
p.add_argument("--size", type=int, default=72)
p.add_argument("--outline", type=int, default=4)
p.add_argument("--words", dest="per_chunk", type=int, default=3, help="max words per chunk")
p.add_argument("--baseline", type=int, default=1250, help="caption baseline y on 1080x1920")
p.add_argument("--upper", action="store_true")
p.add_argument("--keep-punct", action="store_true")
p.add_argument("--pop-ms", type=int, default=90)
p.add_argument("--gap", type=float, default=0.35, help="silence (s) that forces a new chunk")
a = p.parse_args()

words = json.load(open(a.words))


def clean(w):
    if not a.keep_punct:
        w = re.sub(r"[^\w'’?!%$&-]", "", w)
    return w.upper() if a.upper else w


def ts(t):
    t = max(t, 0)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


chunks, cur = [], []
for w in words:
    if cur and (len(cur) >= a.per_chunk or w["start"] - cur[-1]["end"] > a.gap
                or re.search(r"[.?!,]$", cur[-1]["word"])):
        chunks.append(cur)
        cur = []
    cur.append(w)
if cur:
    chunks.append(cur)

print(f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{a.font},{a.size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,{a.outline},0,2,80,170,{1920 - a.baseline},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text""")

for i, c in enumerate(chunks):
    start = c[0]["start"]
    end = c[-1]["end"] + 0.15
    if i + 1 < len(chunks):
        nxt = chunks[i + 1][0]["start"]
        end = nxt if nxt - c[-1]["end"] < 0.6 else end  # hold until next chunk if the gap is short
    parts = []
    for w in c:
        text = clean(w["word"])
        if not text:
            continue
        t0 = int((w["start"] - start) * 1000)
        parts.append(
            f"{{\\alpha&HFF&\\fscx88\\fscy88\\t({t0},{t0 + 1},\\alpha&H00&)"
            f"\\t({t0},{t0 + a.pop_ms},\\fscx100\\fscy100)}}{text}"
        )
    if parts:
        print(f"Dialogue: 0,{ts(start)},{ts(end)},Caption,,0,0,0,,{' '.join(parts)}")
