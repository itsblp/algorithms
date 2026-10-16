# Carousel house style — EDIT ME

These are the user's preferences. Claude reads this file on every carousel, and it **overrides**
the defaults in `SKILL.md`. Values marked `# default` haven't been confirmed yet.
Change them freely, and delete the `# default` tag once a value is yours.

Shared brand settings (niche, audience, voice, banned phrases) live in
`../talking-head-editing/preferences.md` so both formats sound like the same person.
Only carousel-specific overrides go here.

## Structure
```yaml
default_slide_count: 7        # default — cover + 5 body + CTA
default_format: listicle      # default — listicle | steps | myth-fact | story | framework
swipe_cue_on_cover: true      # default
slide_numbers: true           # default — "2/7" style counter
continuity_cue: false         # default — element that crosses slide edges / progress bar
handle_on_slides: true        # default — small @handle on each slide
handle: "@"                   # default — fill in
```

## Typography
```yaml
headline_font: "Montserrat ExtraBold"  # default
body_font: "Inter Medium"              # default
headline_size_px: 84          # default
body_size_px: 44              # default
headline_case: Sentence       # default — UPPER | Sentence | Title
text_align: left              # default — left reads faster than centered for body copy
```

## Color
```yaml
background: "#0F0F0F"         # default — near-black
text: "#FFFFFF"               # default
accent: "#FFE500"             # default — matches talking-head caption accent for brand consistency
cover_style: "big headline on solid background"   # default — or "photo of me + headline"
```

## CTA
```yaml
cta_action: save              # default — save | follow | comment-keyword | share
cta_text: "Save this for later"   # default
```

## Notes from past carousels
<!-- Claude appends dated one-line learnings here when the user gives feedback. -->
