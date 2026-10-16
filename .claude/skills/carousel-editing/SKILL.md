---
name: carousel-editing
description: Plan, write, design and review swipeable carousel posts (Instagram carousels and TikTok photo mode) in the user's house style. Use when the user wants to turn an idea, script, thread, blog post, or video into slides, or asks to write, edit, tighten, lay out, design, review or export a carousel, slideshow, slide post, or photo-mode post. Produces slide-by-slide copy, a layout spec, dual-ratio export guidance, and post copy that works on both platforms.
---

# Carousel editing

Before doing anything, load these:
1. `../short-form-platform-specs/SKILL.md`, section 2 (the carousel canvas). Every slide is designed **1080×1920 with content inside the centered 4:5 band**, so one design exports to both TikTok (9:16) and IG (4:5).
2. `preferences.md` (this folder) — the user's house style. **Preferences override the defaults in this file.** If the user states a new preference, offer to save it there.

3. If the carousel has a card in the Notion Founder Content Database, build it from the card's linked **Story atoms** and **Recipe** (see `../content-strategist/SKILL.md`). Slide copy may only state facts those Verified atoms support. Use the atoms' "Visual assets" Drive folders for photos.

## Inputs you might get

| Input | What to do |
|---|---|
| A topic or idea | Run the full workflow from step 1. |
| Long-form source (script, transcript, blog, thread) | Pull out the single most useful idea, then follow the workflow. Don't try to fit everything; offer a part 2. |
| Draft slide copy | Run step 3 (tighten) and step 5 (QA). |
| Finished slide images | Check them against the QA checklist and the safe zones, and return per-slide fixes. |

## Workflow

### 1. Pick the format
Choose one structure and say which:
- **Listicle:** "5 X that Y". One item per slide.
- **Step-by-step:** a process in order, numbered.
- **Myth vs. fact / mistake → fix:** pairs, one pair per slide.
- **Before → after / story:** a narrative arc across slides.
- **Framework:** a named model (acronym or matrix) explained piece by piece.

### 2. Slide plan
Target slide count comes from `preferences.md` (default 7: cover + 5 body + CTA).

| Slide | Job | Rules |
|---|---|---|
| 1 — Cover | Stop the scroll | ≤ 8 words in the largest type size, plus supporting lines in smaller sizes. Promise a specific outcome, number, or tension. Must read at thumbnail size. Use a swipe cue (→ or "swipe") unless preferences say otherwise. |
| 2 — Setup | Earn the swipe | Why this matters / the problem in 1–2 lines. Some formats skip it and go straight to item 1. |
| Body slides | Deliver | **One idea per slide.** Headline ≤ 8 words + body ≤ 25 words. Number them if it's a list. |
| Second-to-last | Payoff | The best or most surprising point goes here, or on slide 2. Never bury it in the middle. |
| Last — CTA | Convert | One action only (save / follow / comment a keyword / share). Restate the value in one line. |

TikTok photo posts can auto-advance and play with a sound, so every slide should be readable in about 3 s.

### 3. Write and tighten the copy
- Cut every word that doesn't change the meaning. Prefer verbs, numbers and concrete nouns.
- Use the same grammatical form across list items (all start with verbs, or all nouns).
- Write numbers as digits. No walls of text: if a body runs over 25 words, split the slide.
- Use the voice and banned phrases from `preferences.md`.
- Give 3 cover headline options (specific number / curiosity / contrarian) and recommend one.

Output the copy as a table: `slide #, headline, body, visual note`.

### 4. Layout spec
If `preferences.md` defines a named **Look** (sizes, placement, font), it replaces the generic geometry and type sizes below. Keep only the safe-area limits.

Use the 1080×1920 master (see the specs skill):

```
Text-safe area:     x 80 → 880, y 330 → 1400
Headline zone:      top of the text-safe area (starting at y ≈ 360)
Slide counter / handle: inside the band, e.g. bottom-left at y ≈ 1560 — small, 50% opacity
Background:         full-bleed 1080×1920 (bleeds past the 4:5 crop on purpose)
```

Typography and colors come from `preferences.md`. General rules:
- Headline 72–96 px, body 40–48 px, line height 1.15–1.3. Never smaller than 36 px.
- At most 2 typefaces and 1 accent color. Use the accent only on the key word or number.
- Text contrast should be at least WCAG AA (4.5:1). On photos, use a scrim or solid text box.
- Keep a consistent grid across slides: same margins, same headline position. Swiping should feel like turning pages, not jumping around.
- Give a visual continuity cue (an element that crosses the slide edge, or a running progress bar) if `continuity_cue` is on.

### 5. QA checklist
- [ ] Cover headline readable at thumbnail size (≈ 25% scale), ≤ 8 words
- [ ] One idea per slide, body ≤ 25 words
- [ ] All text inside x 80–880 / y 330–1400 on the 1080×1920 master
- [ ] IG export is a 1080×1350 center crop (y 285–1635) and nothing important is cut
- [ ] Consistent margins, fonts and headline position across all slides
- [ ] Contrast at least 4.5:1, no text over busy image areas without a scrim
- [ ] Spelling and numbers checked, parallel list grammar
- [ ] Exactly one CTA, on the last slide
- [ ] Files named `NN_tiktok.png` (1080×1920) and `NN_ig.png` (1080×1350), sRGB

### 6. Render and export
**Photo + stacked type slides (the user's default style):** write one JSON spec per slide and render with `scripts/render_slide.py`. It cover-fits the photo, applies the shade and shadow, sets tracked mixed-size type, and writes both `tiktok/NN.png` (1080×1920) and `ig/NN.png` (the 4:5 crop) in one go:

```json
{"photo": "photos/studio.jpg", "name": "01", "out_dir": "content/<slug>", "focus_y": 0.3,
 "lines": [{"text": "I spent", "size": 125},
           {"text": "$40k on my", "size": 195}, {"text": "first studio", "size": 195},
           {"text": "(here's what I'd never do again)", "size": 72, "gap_before": 30}]}
```

```bash
python3 scripts/render_slide.py content/<slug>/specs/*.json
```

Spec keys and defaults are listed at the top of the script. Override `color`, `font`, `tracking`, `bottom` and the others per slide only when preferences say to. After rendering, **look at every `ig/NN.png`** to check legibility against the photo: adjust `focus_y`, raise `gradient`, or pick another photo if any word sits on a busy or bright patch.

For other layouts, with a 1080×1920 master per slide, create the IG version by center-cropping:

```bash
mkdir -p ig && for f in tiktok/*.png; do
  ffmpeg -loglevel error -y -i "$f" -vf "crop=1080:1350:0:285" "ig/$(basename "$f")"
done
```

If the user builds in **Canva**: document size 1080×1920, a guide box at y 285–1635 and text-safe guides at x 80/880 and y 330/1400. Download as PNG for TikTok, then use Resize → 1080×1350 (or the crop command above) for IG. If the Canva connector is available in the session, offer to generate or fill the design directly.

### 7. Post copy (same for both apps)
- **Caption:** the cover promise restated with a search keyword → a 1-line teaser of the best slide → CTA. ≤ 300 chars.
- **Hashtags:** 3–5 niche-specific tags.
- **TikTok extras:** suggest adding a trending sound in-app at low volume. Photo posts with sound get more distribution there. The IG upload can use music too, but pick it in-app.
- **Alt text** (IG): one sentence summarizing the carousel.

## Deliverables summary
Unless the user asks for less, end with: format choice, cover options, slide copy table, layout notes, QA results and post copy. Save to `content/<carousel-slug>/` when producing files.
