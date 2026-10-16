---
name: short-form-platform-specs
description: Cross-platform specs for content posted to BOTH Instagram (Reels, carousels) and TikTok (video, photo mode) — canvas sizes, UI safe zones, cover/grid crops, export settings, audio loudness, caption and hashtag limits, and cross-posting rules. Load this whenever planning, editing, designing, or exporting short-form content, and before giving any size, safe-zone, or export number. The talking-head-editing and carousel-editing skills depend on it.
---

# Short-form platform specs (Instagram + TikTok)

> **Hard rule from the user:** captions and on-screen text must *never* touch the app interface (handle, caption, buttons, search bar) on either platform. A render that fails the safe-zone check is not done. Fix it before showing it to the user.

Every piece of content gets posted to **both** IG and TikTok. The rule is: **design once for the stricter platform in every dimension**, so one master file works on both without re-editing.

Platforms change their UI often. If a number here looks off against what the user sees in-app, trust the app, then update this file.

## 1. Vertical video canvas (Reels / TikTok)

| Setting | Value |
|---|---|
| Aspect / resolution | 9:16, **1080×1920** |
| Frame rate | Keep source fps (30 is the default; 24/25/60 are fine). Never convert 30→24. |
| Length sweet spot | 20–60 s. Both platforms allow longer, but keep under 90 s unless the content earns it. |

### Combined safe zone (union of both apps' UI overlays)

Keep **all text, faces, and key visuals** inside this box on a 1080×1920 frame:

```
x: 80 → 880   (left 80px — tall phones crop ~50px off each side; right 200px — avatar and button column)
y: 260 → 1400 (top 260px — tabs, or the search bar on search results; bottom 520px — handle, caption, audio, promo/chip rows)
```

- The bottom 520px is the most dangerous zone: the caption expands upward on both apps, and TikTok adds rows above the handle (promote banner, location or effect chips).
- The right 200px holds the avatar and the like/comment/save/share buttons. On TikTok the column starts at about x 900.
- Backgrounds and B-roll can and should fill the full frame. Only *information* has to stay inside the box.

**Every text element counts:** titles, captions, credits and series tags ("@handle · series") all stay inside the box above. Measured from the user's own TikTok screenshot (2026-10-16): the handle sits at y ≈ 1540, the button column at x ≥ 900, and the search bar reaches y ≈ 250. TikTok puts the handle at about y 1540–1620 and the caption just below it. Text placed at 77–88% of the frame height lands directly on it. This happened to the user on 2026-10-16.

**QA check (required before export):** `python3 scripts/safe_zone_check.py final.mp4 zones.png` shades the UI zones in cyan on sampled frames. Look at the image. No text and no face may sit in cyan.

### Cover / grid crop

Both profile grids show a **3:4 center crop** (1080×1440 from the 1920 frame, so y 240 → 1680).
Cover text must sit inside **y 300 → 1400**, so it reads on the grid AND in the feed.

## 2. Carousel / photo-post canvas

The two platforms prefer different ratios:
- Instagram carousel: 4:5 (1080×1350) is the default; 3:4 (1080×1440) is also supported.
- TikTok photo mode: 9:16 (1080×1920) fills the screen. Anything shorter gets letterboxed or blurred.

**Master approach: design 1080×1920 with all content inside a centered 4:5 band.**

```
Canvas:            1080×1920 (TikTok export as-is)
4:5 content band:  y 285 → 1635 (1080×1350; crop this for the IG export)
Text-safe area:    x 80 → 880, y 330 → 1400
```

- The 285px above and below the band is background only: a solid fill, gradient, or extended image.
- The text-safe area keeps text clear of TikTok's right-side buttons and bottom caption (photo mode shows the same interface), and inside IG's 4:5 crop.
- Export **two files per slide**: `slide-01_tiktok.png` (full 1080×1920) and `slide-01_ig.png` (center crop, 1080×1350).
- Slide count: aim for **5–10 slides**. That's well under the limits (IG 20, TikTok 35).
- Format: PNG for text-heavy graphics, high-quality JPG (≥90) for photos. Use sRGB.

## 3. Export settings (video)

| Setting | Value |
|---|---|
| Container / codec | MP4, H.264 (High profile), yuv420p |
| Bitrate | 12–20 Mbps VBR at 1080p30 (scale up for 60fps) |
| Audio | AAC, 48 kHz, 256–320 kbps, stereo |
| Loudness | **−14 LUFS integrated, true peak ≤ −1 dBTP** |
| Moov atom | `+faststart` |

Reference ffmpeg export:

```bash
ffmpeg -i master.mov \
  -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2" \
  -c:v libx264 -profile:v high -pix_fmt yuv420p -preset slow -crf 18 -maxrate 20M -bufsize 40M \
  -af "loudnorm=I=-14:TP=-1:LRA=11" -c:a aac -b:a 320k -ar 48000 \
  -movflags +faststart out_1080x1920.mp4
```

## 4. Cross-posting rules (both platforms)

1. **Never repost a file downloaded from the other app.** IG down-ranks visible TikTok watermarks, and re-encoding twice degrades quality. Always upload the clean master export to each app separately.
2. **Burn in captions yourself.** Don't depend on either app's auto-captions for the main text, and turn auto-captions off if you've burned them in, so you don't get double captions.
3. **Music:** trending sounds don't carry across platforms. Either
   - export with **voice only** and add a platform-native sound in each app at low volume (better for reach), or
   - bake in licensed or royalty-free music at −20 to −25 dB under the voice.
   Default to voice-only unless the music is part of the edit's rhythm.
4. **In-app text and stickers** (polls, links) are platform-specific. Add them after upload, never in the master.
5. **No platform names, logos, or "link in bio" pointing at the other platform** in the master file.

## 5. Captions, hashtags and copy limits

| | Instagram | TikTok | Write for both |
|---|---|---|---|
| Caption length | 2,200 chars | 4,000 chars | **≤ 300 chars**, hook in the first 125 |
| Hashtags | capped at a handful | no hard cap in practice | **3–5** specific tags |
| Visible before "more" | ~125 chars | ~1–2 lines | First line = hook or keyword |

Write captions with **searchable keywords** in the first sentence. Both apps index caption text for search.
