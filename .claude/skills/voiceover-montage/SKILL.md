---
name: voiceover-montage
description: Make voiceover montage videos (personal "diary" episodes) for Instagram Reels and TikTok, where the user's narration plays over a sequence of short candid clips from her life. This is a separate format from talking-head videos and from carousels. Use when the user shares a voice note or narration plus several short clips, asks for a diary, montage, vlog-style voiceover, or "Founder Diaries"-type episode, or when talking-head-editing's footage analysis hands off here.
---

# Voiceover montage (its own format)

**This is not a talking-head video and not a carousel.** Don't mix its look (fast candid clips, big-word opener, bold middle captions) into the other two formats, and don't add talking-head effects (scrolling quote, photos above the head, punch-ins) here.

Before doing anything, load these:
1. `../short-form-platform-specs/SKILL.md`: safe zones (hard rule: no text touching the app interface), export, cross-posting.
2. `preferences.md` (this folder), plus the brand voice and **signature caption look** in `../talking-head-editing/preferences.md`. The caption font and accent color are shared across formats so all of them are recognizably the user's.
3. The Story Bank (`../content-strategist/SKILL.md`): narration and captions may only state facts supported by Verified atoms.

Shared tools live in `../talking-head-editing/scripts/` (`transcribe.py`, `kinetic_captions.py`, `analyze_footage.py`). `scripts/montage.py` (this folder) assembles the clips under the narration.

**Reference:** a "Founder Diaries Ch. 2" episode (user's screen recording, 2026-10-22). The narration ("I'm out, and I hate admitting it…") plays over raw clips of daily life: desk, car, office, crying in bed, presenting.

## Fits when
- There's a voice note or narration (`voiceover_files`), or one talking take whose audio can carry the story.
- There are **many short candid clips** (most under 8 s): real moments, often not looking at the camera.
- The story is emotional or episodic: struggles, behind the scenes, "chapter" series. This fits the Story Bank's Story and Belief shift atoms and the Exit Interview series.

## Edit
1. **Narration first:** transcribe the voice track, then tighten it to 25–45 s (cut filler and dead air).
2. **Clip plan:** one clip per phrase, changing every 1.5–3 s at phrase boundaries. Match each clip to what's being said, literally first (eczema → close-up of skin), otherwise emotionally. The most vulnerable clip goes on the turn of the story, not at the start.
3. **Assemble:** `scripts/montage.py plan.json montage.mp4`. Clips are center-cropped to 9:16, with clip sound muted or at −24 dB under the voice.
4. **Hook:** the first 1.5–2 s show the opening words **one at a time, huge, at the top** (`--hook-big 1.9`).
5. **Captions:** `../talking-head-editing/scripts/kinetic_captions.py --mode build --anchor middle --chars 20 --hook-big 1.9`. Bold white, 1–3 words building in the middle of the frame, plus the signature accent word (Instrument Serif italic, butter yellow; mark it with `"accent": true`, burn with `fontsdir=../short-form-platform-specs/fonts`).
6. **Series label:** put "Founder Diaries Ch. N"-style naming in the post caption, not on screen. If it's on screen, it goes at the top, never near the handle.
7. **Effects:** none, apart from hard cuts. No punch-ins (the clips change constantly anyway).

## Watch for
- **Vulnerable footage needs explicit user approval** before it's used: crying, health, other people's faces.
- **Bright clips** under the middle captions (`mid_band_luma` ≥ 200): keep the shadow.
