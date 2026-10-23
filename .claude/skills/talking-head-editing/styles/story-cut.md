# Story Cut

**References:** the scrolling-quote and above-head-photo reel (2026-10-16); Jun Yuh / Alexis Barber pacing from the brand brief.

## Fits when
- There are one or more talking takes in a **medium shot** (room to punch in, room above the head for photos).
- There's a story with named people, places or "before" moments that photos can show, and/or a quote worth scrolling.
- The goal is high retention and energy.

## Edit
- The full workflow in `../SKILL.md` (steps 1–8): hook moved to the front, jump cuts every 1.5–2 s, punch-ins, B-roll weave.
- **Effects** (`effects.py`): punch-ins, a scrolling quote behind the head when someone else is being quoted, and plain photos above the head when a person or place is named. Counts are in `../preferences.md` under **Effects**.
- **Captions:** `kinetic_captions.py --mode pop` (bold, mid-frame, words pop in), with the signature accent word.
- **Callouts, i.e. captions as layout** (`effects.py` `callouts`): 1–2 per video, on the most quotable line. A 2–3 line stack hugs the head on the roomier side, and the last line is in the accent (serif italic, butter yellow, underlined). If there isn't room beside the head, it stacks above it. Leave those words out of the regular captions.
- **Reaction image** (`effects.py` photo with `"placement": "reaction"`): a small image pops in lower-left for about 1 s on a punchline. Use the user's own photos or screenshots. No copyrighted memes unless the user supplies them.

## Watch for
- **Not enough room above the head** (the top of the head is near y 300–400): photos come out small. Use `placement: auto` (chest) instead.
- **Effects are punctuation, not wallpaper.** If the transcript has no quote and no named people or places, skip that effect.
