# Talking-head house style

These are the user's preferences. Claude reads this file on every talking-head edit,
and it **overrides** the defaults in `SKILL.md`. Values marked `# default` haven't been
confirmed by the user yet. Everything else comes from the user's brief (2026-10-16).

## Brand
```yaml
niche: "building a business with taste — brand world-building, aesthetics, physical spaces, run with operator rigor"
audience: >
  creator entrepreneurs, aspiring founders still in corporate, operators, creatives
  and investors. They can run a P&L and tolerate KPIs and spreadsheets, but live for
  taste, aesthetics, physical spaces and brand world-building, and refuse to let what
  they build be beige.
voice: "smart, grounded, culturally fluent; numbers-literate but never dry; first-person and specific"
banned_phrases: ["hey guys", "in this video", "don't forget to like and subscribe", "game changer", "hustle"]  # "game changer"/"hustle" are defaults — too generic for this audience
```

## Creative references
- **Alexis Barber:** cool-girl cultural commentary, effortless B-roll that feels lived-in, not staged.
- **Jun Yuh:** grounded autobiographical storytelling, cinematic pacing.
- **Jaclyn Johnson:** founder/entrepreneur perspective.

How that translates to the edit:
- **Look:** natural. Use the true-to-life color of the footage, no heavy filters, LUTs, glitch transitions, emoji, or meme zooms. Hard cuts only, plus an occasional quick crossfade (≤ 6 frames) between B-roll shots.
- **Story:** open on a personal, specific moment or opinion ("I almost signed a lease on…") rather than a generic tip. Land on the business insight.
- **Typography:** clean modern sans-serif, plain and legible. Nothing decorative.

## Workflow
```yaml
editor: claude                # Claude does the full edit: transcribe, cut, B-roll, captions, export. No CapCut handoff.
transcriber: faster-whisper   # pip install faster-whisper; word_timestamps=True
```

## Pacing
```yaml
target_length_sec: 30-45
max_pause_ms: 200             # default — tight, to support the fast cut rate
energy: high
visual_change_every_sec: 1.5-2    # every 1.5–2 s: a cut, punch-in, or B-roll switch
punch_in_scale: 112           # default — subtle; this style avoids aggressive zooms
broll_ratio: 0.4-0.5          # default — share of runtime covered by B-roll; talking head stays the anchor
broll_style: "real footage the user shot — hands, spaces, objects, walking, workspace, city; no stock unless asked"
```

## Captions
```yaml
caption_font: "Inter"         # bold weight; clean modern sans, installed in the cloud container. Fallback: Helvetica Neue Bold
caption_size_px: 72           # default (on 1080×1920)
caption_case: Sentence        # default — plain and natural rather than ALL CAPS
caption_color: "#FFFFFF"      # plain white
caption_accent: none          # plain white only; emphasis comes from motion, not color
caption_outline_px: 4         # thin black outline for legibility on any B-roll
caption_shadow_px: 0          # default
caption_words_per_chunk: 2-3
caption_animation: kinetic    # word-by-word reveal timed to speech, with a quick pop-in on each word
caption_position_y: 1250      # default — baseline; keep between 1100 and 1400
emoji_in_captions: false
punctuation_in_captions: false    # default — drop commas/periods; keep ? and !
```

## Hook overlay
```yaml
hook_overlay: true            # default
hook_style: "plain white Inter Bold text, thin outline, no box — same family as the captions"  # default
hook_max_words: 7
```

## Audio
```yaml
master_music: none            # default — add a platform-native sound in each app
music_level_db: -24           # default, if baked
sfx: off                      # default — keeps the natural, uncluttered feel
```

## Ending
```yaml
ending: cta
cta_action: comment-keyword
cta_text: "Comment \"KEYWORD\" and I'll send you ___"   # Claude picks a one-word keyword tied to the video's topic and states it out loud + on screen
```

## Notes from past edits
<!-- Claude appends dated one-line learnings here when the user gives feedback. -->
