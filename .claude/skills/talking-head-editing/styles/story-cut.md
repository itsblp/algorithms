# Story Cut

**References:** the scrolling-quote and above-head-photo reel (2026-10-16); Jun Yuh / Alexis Barber pacing from the brand brief.

## Fits when
- There are one or more talking takes in a **medium shot** (room to punch in, room above the head for photos).
- There's a story with named people, places or "before" moments that photos can show, and/or a quote worth scrolling.
- The goal is high retention and energy.

## Edit
- The full workflow in `../SKILL.md` (steps 1–8): hook moved to the front, jump cuts every 1.5–2 s, punch-ins, B-roll weave.
- **Effects** (`effects.py`): punch-ins, a scrolling quote behind the head when someone else is being quoted, and plain photos above the head when a person or place is named. Counts are in `../preferences.md` under **Effects**.
- **Captions:** `kinetic_captions.py --mode pop` (bold, mid-frame, words pop in).

## Watch for
- **Not enough room above the head** (the top of the head is near y 300–400): photos come out small. Use `placement: auto` (chest) instead.
- **Effects are punctuation, not wallpaper.** If the transcript has no quote and no named people or places, skip that effect.
