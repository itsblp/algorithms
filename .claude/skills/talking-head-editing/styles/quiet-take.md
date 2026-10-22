# Quiet Take

**Reference:** a "How I avoid burnout" skincare-routine reply (user's screen recording, 2026-10-22).

## Fits when
- There's one continuous take, front camera, with the face filling much of the frame (`framing: selfie close-up`).
- The speaker is doing something real while talking: skincare, coffee, getting ready, a walk.
- The video answers a follower question, or the content is reflective and intimate.
- There are no photos or B-roll (or they'd break the mood).

## Edit
- **Cuts:** only dead air, false starts and filler. It must still feel like one take. No punch-ins, no zooms.
- **Hook:** a title at the top for about 1.8 s (`--title`). If it answers a real comment, add a comment bubble (`comment_card.py`, real comment only) as a sticker at x 80, y ≈ 1040 for the same 1.8 s.
- **Captions:** `kinetic_captions.py --mode build --anchor top --title "…" --title-end 1.8`. Small plain white text that builds up at the top (y 280).
- **Effects:** none.
- **Audio:** natural room sound and voice. Add music in-app if wanted.

## Watch for
- **A bright wall behind the top captions** (`top_band_luma` ≥ 185): keep the shadow on. If it's still hard to read, switch to the middle anchor.
- **The comment bubble must stay inside the safe zone** (the reference covered its own handle).
