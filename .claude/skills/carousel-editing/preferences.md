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
swipe_cue_on_cover: parenthetical   # a small last line like "(here's everything I did)", no arrows or "SWIPE"
slide_numbers: false          # IG and TikTok both show their own "1/7" counter, so don't design one
continuity_cue: false         # default
handle_on_slides: false       # the reference style has no handle; keeps the photo clean
handle: "@"                   # TODO: fill in
```

## Look: "photo + stacked type" (from the user's reference, 2026-10-16)

The user's chosen carousel style. Every slide uses it unless the user asks otherwise.

- **Full-bleed real photo** on every slide: the user, a space, an object. It's candid and warm, with natural light. No graphics, boxes, borders, stickers or icons.
- **Type sits directly on the photo,** with no box, no outline and no visible scrim. Legibility comes from choosing photos with calm, mid-to-dark areas behind the text, plus an almost invisible bottom shade and soft shadow.
- **Stacked, left-aligned type block in the lower half** of the 4:5 area, set in mixed sizes to create rhythm:
  1. **Lead-in** (medium, ~120–130 px): "I spent"
  2. **The number and the payoff** (huge, ~190–200 px, 1–2 lines): "$5,000 on a / 5 day glow up"
  3. **Context** (medium, ~110–120 px): "in South Korea"
  4. **Parenthetical swipe cue** (small, ~70 px, extra space above): "(here's everything I did)"
- **Font:** neo-grotesque sans at a *medium* weight, not bold. Tracking is very tight and line spacing is tight, so it reads like one solid editorial block. Sentence case, with the dollar amount written as digits.
- **Color:** warm cream text, not pure white.
- **Headline formula:** personal + a specific dollar amount or number + a specific place or time → payoff, then a parenthetical promise. For example: "I spent $40k building out my first studio (here's what I'd never do again)".
- **Body slides:** same treatment, with a different photo per slide. A short headline (1–2 big lines) plus 1–2 smaller lines of detail at most. Keep the type block in the same position on every slide.
- **CTA slide:** same treatment, with the comment keyword in the huge size.

```yaml
font: "Inter Display Medium"  # chosen by the user 2026-10-16 over Helvetica clones (Nimbus Sans, TeX Gyre Heros) after a side-by-side test. Preinstalled: /usr/share/fonts/opentype/inter/InterDisplay-Medium.otf
tracking: -0.055              # ≈ -55 in Canva/Figma letter-spacing units (-5.5%)
line_height: 0.93
text_color: "#FBF4D6"         # warm cream
size_scale: {lead: 125, hero: 195, context: 115, note: 72}   # px on the 1080-wide canvas; shrink a line only if it overflows
text_align: left
text_block_bottom_y: 1380     # on the 1080×1920 master (≈ y 1095 in the 4:5 IG crop); TikTok photo mode shows the handle below this
bottom_shade: 0.3             # bottom gradient opacity
text_shadow: 0.25             # soft, blurred, barely visible
accent: none
fallback_background: "#F4F1EC"   # only when there's no photo
```

**Photo requirements:** vertical originals (9:16 or taller) so the TikTok version isn't over-cropped. The subject's face goes in the upper half (y 300–900 on the master), leaving the lower half for type.

## CTA
```yaml
cta_action: comment-keyword
cta_text: "Comment \"KEYWORD\" and I'll send you ___"   # Claude picks a one-word keyword tied to the topic
```

## Notes from past carousels
<!-- Claude appends dated one-line learnings here when the user gives feedback. -->
