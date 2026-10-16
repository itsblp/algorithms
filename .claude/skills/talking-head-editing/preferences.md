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
caption_position_y: 1250      # default — baseline; never below 1300 (a 2-line caption must end above y 1400)
emoji_in_captions: false
punctuation_in_captions: false    # default — drop commas/periods; keep ? and !
```

## Hook overlay
```yaml
hook_overlay: true            # default
hook_style: "plain white Inter Bold text, thin outline, no box — same family as the captions"  # default
hook_max_words: 7
```

## Effects (matched to the user's reference screen recording, 2026-10-16)
```yaml
text_behind_head:
  style: marquee   # one quoted line scrolls right -> left at eye level, passing BEHIND the head
  use: when the speaker quotes someone else (a parent, a boss, a critic, the old inner voice), at most 1–2 per video
  text: the quote in double quotes, sentence case, ≤ 12 words; Inter Display Bold ~104 px, yellow "#F5D547"
  duration: ≈ (1080 + text width px) / 1000 s, so it moves at ~1000 px/s (≈ 3 s for 10 words)
  captions: leave a gap in the burned captions while the marquee runs
  alt: style "block" (1–2 big static words behind the head) only if the user asks for it
photo_overlay:
  style: plain     # clean rectangle: no border, tilt or shadow; hard cut in and out
  placement: above_head (centered on the face, overlapping the hairline slightly)
  width: ~430 px (about 40% of the frame)
  use: 1–3 per video, the moment the speaker names a person, place, past self, or "dozens of people"
  sequence: for plurals ("my team", "dozens of people"), flip 2–3 photos in the same spot ("paths")
  duration: 1–1.5 s per photo
  source: the user's own photos from the post's Drive folder or a Story Bank atom's Visual assets
punch_in:
  use: on emphasis lines and to hide jump cuts; hard cut between a medium shot and ~118%
  rule: alternate in/out, never two of the same scale in a row
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
- 2026-10-16: Old TikToks had the title and captions at about 77–88% of the frame height, which collided with the TikTok handle. Keep all text inside x 80–880, y 260–1400 (tightened 2026-10-16 from a TikTok screenshot) and run safe_zone_check before every export.
- 2026-10-16: Typical framing is a medium shot, standing, with a handheld mic near the chin and little headroom (top of head at about y 300–400). Above-head photos come out small (about 300 px). For bigger photos, use `placement: auto` (chest), or ask the user to leave more headroom when filming.
- 2026-10-16: For real edits, ask for the original camera files from Drive, not TikTok downloads. Downloads are 576×1024, recompressed, and already have captions burned in.
