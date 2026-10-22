# Diary Voiceover

**Reference:** a "Founder Diaries Ch. 2" episode (user's screen recording, 2026-10-22). The narration ("I'm out, and I hate admitting it…") plays over raw clips of daily life: desk, car, office, crying in bed, presenting.

## Fits when
- There's a voice note or narration (`voiceover_files`), or one talking take whose audio can carry the story.
- There are **many short candid clips** (most under 8 s): real moments, often not looking at the camera.
- The story is emotional or episodic: struggles, behind the scenes, "chapter" series. This fits the Story Bank's Story and Belief shift atoms and the Exit Interview series.

## Edit
1. **Narration first:** transcribe the voice track, then tighten it to 25–45 s (cut filler and dead air).
2. **Clip plan:** one clip per phrase, changing every 1.5–3 s at phrase boundaries. Match each clip to what's being said, literally first (eczema → close-up of skin), otherwise emotionally. The most vulnerable clip goes on the turn of the story, not at the start.
3. **Assemble:** `montage.py plan.json montage.mp4`. Clips are center-cropped to 9:16, with clip sound muted or at −24 dB under the voice.
4. **Hook:** the first 1.5–2 s show the opening words **one at a time, huge, at the top** (`--hook-big 1.9`).
5. **Captions:** `kinetic_captions.py --mode build --anchor middle --chars 20 --hook-big 1.9`. Bold white, 1–3 words building in the middle of the frame.
6. **Series label:** put "Founder Diaries Ch. N"-style naming in the post caption, not on screen. If it's on screen, it goes at the top, never near the handle.
7. **Effects:** none, apart from hard cuts. No punch-ins (the clips change constantly anyway).

## Watch for
- **Vulnerable footage needs explicit user approval** before it's used: crying, health, other people's faces.
- **Bright clips** under the middle captions (`mid_band_luma` ≥ 200): keep the shadow.
