#!/usr/bin/env python3
"""Build timed-to-speech ASS captions from words.json.

Two modes:
  pop   (default, "produced" talking heads): chunks of 2-3 bold words laid out in full,
        each word invisible until spoken, then pops in. Middle of the frame (--baseline).
  build (Quiet Take; also used by the separate voiceover-montage skill): text that builds up word by word as it's spoken,
        then clears. --anchor top (Quiet Take: small, plain) or middle (voiceover montage:
        bold Inter Display 84 px, 1-3 words at a time; pass --chars 20).
        Optional --title shows a hook title at the top first; captions wait until it ends.
        Optional --hook-big SEC: words spoken before SEC appear one at a time, huge, at the
        top (the voiceover-montage cold open); normal captions take over after.

Signature accent: mark 1 key word per caption line (about one every 3-5 s) with "accent": true
in words.json. It renders in the accent font (Instrument Serif Italic) and color (#F5D547).
Burn with: ffmpeg ... -vf "ass=captions.ass:fontsdir=../../short-form-platform-specs/fonts"

Usage: kinetic_captions.py words.json > captions.ass
       [--mode pop|build] [--font Inter] [--size 72] [--outline 4] [--words 3]
       [--baseline 1250] [--top 280] [--title "How I avoid burnout" --title-end 1.8]
       [--upper] [--keep-punct]
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
p.add_argument("--mode", choices=["pop", "build"], default="pop")
p.add_argument("--top", type=int, default=280, help="build mode: top edge of the caption block (y)")
p.add_argument("--chars", type=int, default=48, help="build mode: max characters before the block clears")
p.add_argument("--title", default="", help="hook title shown at the top before captions start")
p.add_argument("--title-end", type=float, default=1.8)
p.add_argument("--anchor", choices=["top", "middle"], default="top", help="build mode position")
p.add_argument("--mid-y", type=int, default=1000, help="build mode, middle anchor: baseline y")
p.add_argument("--hook-big", type=float, default=0.0, help="seconds of one-big-word-at-a-time opener")
p.add_argument("--accent-color", default="#F5D547", help="signature accent color for words marked \"accent\": true")
p.add_argument("--accent-font", default="Instrument Serif", help="signature accent font (italic)")
p.add_argument("--accent-scale", type=int, default=128, help="accent word size, %% of caption size")
a = p.parse_args()
if a.mode == "build" and a.anchor == "top":
    a.size = 54 if a.size == 72 else a.size
    a.font = "Inter Display Medium" if a.font == "Inter" else a.font
elif a.mode == "build":  # middle anchor: bold diary captions
    a.size = 84 if a.size == 72 else a.size
    a.font = "Inter Display" if a.font == "Inter" else a.font
if not 600 <= a.baseline <= 1300:
    p.error("--baseline must be 600-1300 so captions stay clear of the TikTok/IG interface (safe zone ends at y 1400)")
if not 1000 <= a.mid_y <= 1300 and a.anchor == "middle":
    p.error("--mid-y must be 1000-1300 (safe zone)")
if not 270 <= a.top <= 420:
    p.error("--top must be 270-420: above that the IG header / TikTok tabs and search bar cover it")

words = json.load(open(a.words))


def clean(w):
    if not a.keep_punct:
        w = re.sub(r"[^\w'’?!%$&-]", "", w)
    return w.upper() if a.upper else w


def bgr(hexcolor):
    h = hexcolor.lstrip("#")
    return f"&H00{h[4:6]}{h[2:4]}{h[0:2]}&"



def accent(text, w):
    """Signature look: words marked "accent": true in words.json render in the accent font + color."""
    if not w.get("accent"):
        return text
    return (f"{{\\fn{a.accent_font}\\i1\\fscx{a.accent_scale}\\fscy{a.accent_scale}"
            f"\\c{bgr(a.accent_color)}}}{text}{{\\r}}")


def ts(t):
    t = max(t, 0)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def build_mode():
    """Pages of up to --chars characters; each word adds itself to the visible text."""
    pages, cur, n = [], [], 0
    for w in words:
        t = clean(w["word"])
        if not t:
            continue
        if cur and (n + len(t) + 1 > a.chars or w["start"] - cur[-1]["end"] > 0.8
                    or re.search(r"[.?!]$", cur[-1]["word"])):
            pages.append(cur)
            cur, n = [], 0
        cur.append(w)
        n += len(t) + 1
    if cur:
        pages.append(cur)
    out = []
    for i, pg in enumerate(pages):
        page_end = pg[-1]["end"] + 0.3
        if i + 1 < len(pages):
            page_end = min(page_end, pages[i + 1][0]["start"])
        for k, w in enumerate(pg):
            start = max(w["start"], a.title_end if a.title else 0, a.hook_big)
            end = pg[k + 1]["start"] if k + 1 < len(pg) else page_end
            if end - start < 0.04:
                continue
            text = " ".join(accent(clean(x["word"]), x) for x in pg[:k + 1])
            out.append(f"Dialogue: 0,{ts(start)},{ts(end)},Build,,0,0,0,,{text}")
    hook = [w for w in words if w["start"] < a.hook_big and clean(w["word"])]
    for k, w in enumerate(hook):
        end = hook[k + 1]["start"] if k + 1 < len(hook) else a.hook_big
        out.append(f"Dialogue: 1,{ts(w['start'])},{ts(end)},Big,,0,0,0,,{clean(w['word'])}")
    return out


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
Style: Caption,{a.font},{a.size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,{a.outline},0,2,200,200,{1920 - a.baseline},1
Style: Build,{a.font},{a.size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,{-1 if a.anchor == "middle" else 0},0,0,0,100,100,0,0,1,0,2,{8 if a.anchor == "top" else 2},200,200,{a.top if a.anchor == "top" else 1920 - a.mid_y},1
Style: Big,Inter Display,128,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,-1,0,0,0,100,100,-2,0,1,0,3,8,80,200,{a.top},1
Style: Title,Inter Display SemiBold,84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,-1,0,1,0,3,7,80,200,{a.top},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text""")

if a.title:
    print(f"Dialogue: 1,{ts(0)},{ts(a.title_end)},Title,,0,0,0,,{a.title}")
if a.mode == "build":
    print("\n".join(build_mode()))
    raise SystemExit

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
        full = a.accent_scale if w.get("accent") else 100
        look = f"\\fn{a.accent_font}\\i1\\b0\\c{bgr(a.accent_color)}" if w.get("accent") else ""
        parts.append(
            f"{{{look}\\alpha&HFF&\\fscx{int(full * .88)}\\fscy{int(full * .88)}\\t({t0},{t0 + 1},\\alpha&H00&)"
            f"\\t({t0},{t0 + a.pop_ms},\\fscx{full}\\fscy{full})}}{text}{{\\r}}"
        )
    if parts:
        print(f"Dialogue: 0,{ts(start)},{ts(end)},Caption,,0,0,0,,{' '.join(parts)}")
