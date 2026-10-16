# Carousel house style

These are the user's preferences. Claude reads this file on every carousel, and it **overrides**
the defaults in `SKILL.md`. Values marked `# default` haven't been confirmed yet.

Shared brand settings (niche, audience, voice, creative references, banned phrases) live in
`../talking-head-editing/preferences.md`, so both formats sound and look like the same person.
Read that file's **Brand** and **Creative references** sections first. Only carousel-specific settings go here.

## Structure
```yaml
default_slide_count: 7        # default — cover + 5 body + CTA
default_format: story         # default — this audience responds to personal story → business insight; listicle as second choice
swipe_cue_on_cover: true      # default — subtle "→", not a big "SWIPE"
slide_numbers: true           # default — small "2/7"
continuity_cue: false         # default
handle_on_slides: true        # default
handle: "@"                   # TODO: fill in
```

## Look
Natural, editorial and uncluttered. Think brand book, not infographic. Real photos of spaces,
objects and the user beat graphics. Use lots of negative space.

```yaml
headline_font: "Inter Bold"   # clean modern sans, same family as video captions
body_font: "Inter Regular"
headline_size_px: 80          # default
body_size_px: 42              # default
headline_case: Sentence
text_align: left              # default
background: "#F4F1EC"         # default — warm off-white (natural, "not beige-boring": pair with real photography)
text: "#111111"               # default — near-black
accent: none                  # default — plain type, matching the captions; emphasis via weight and size
photo_text_color: "#FFFFFF"   # white text with a soft dark scrim when text sits on a photo
cover_style: "full-bleed real photo (space, object, or the user) + short headline"   # default
```

## CTA
```yaml
cta_action: comment-keyword
cta_text: "Comment \"KEYWORD\" and I'll send you ___"   # Claude picks a one-word keyword tied to the topic
```

## Notes from past carousels
<!-- Claude appends dated one-line learnings here when the user gives feedback. -->
