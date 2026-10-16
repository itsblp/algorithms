# Talking-head house style — EDIT ME

These are the user's preferences. Claude reads this file on every talking-head edit,
and it **overrides** the defaults in `SKILL.md`. Values marked `# default` haven't been
confirmed by the user yet. Change them freely, and delete the `# default` tag once a value is yours.

## Brand
```yaml
niche: ""                     # default — e.g. "personal finance for creatives"
audience: ""                  # default — who you're talking to
voice: "direct, warm, no fluff"   # default
banned_phrases: ["hey guys", "in this video", "don't forget to like and subscribe"]  # default
```

## Pacing
```yaml
target_length_sec: 30-45      # default
max_pause_ms: 250             # default — gaps longer than this get cut
energy: high                  # default — high = tight jump cuts; calm = keep breaths, slower cuts
visual_change_every_sec: 3    # default
punch_in_scale: 115           # default — percent
```

## Captions
```yaml
caption_font: "Montserrat ExtraBold"   # default — safe fallbacks: Inter Black, Poppins Bold
caption_size_px: 78           # default (on 1080×1920)
caption_case: UPPER           # default — UPPER | Sentence
caption_color: "#FFFFFF"      # default
caption_accent: "#FFE500"     # default — highlight color for the key word
caption_outline_px: 6         # default — black outline
caption_words_per_chunk: 3    # default
caption_position_y: 1250      # default — baseline; keep between 1100 and 1400
emoji_in_captions: false      # default
```

## Hook overlay
```yaml
hook_overlay: true            # default
hook_style: "white box, black text"   # default
hook_max_words: 7             # default
```

## Audio
```yaml
master_music: none            # default — none (add native sound in-app) | baked
music_level_db: -22           # default, if baked
sfx: off                      # default — on | off
```

## Ending
```yaml
ending: loop                  # default — loop (last line flows into first) | cta
cta_text: ""                  # default — e.g. "Follow for part 2"
```

## Notes from past edits
<!-- Claude appends dated one-line learnings here when the user gives feedback, e.g.
- 2026-10-16: user prefers cutting the intro "so" even when it sounds natural -->
