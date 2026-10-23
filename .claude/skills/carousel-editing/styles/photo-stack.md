# Photo Stack

**Reference:** the user's "I spent $5,000 on a 5 day glow up" carousel (2026-10-16).

- Full-bleed real photo on every slide, cream type (#FBF4D6) in Inter Display Medium, tight tracking, mixed sizes stacked low-left, ending in a line in parentheses that makes people swipe.
- Accent: one `*word*` per slide, ideally the number or the named thing (`*$40k*`). It renders in butter yellow.
- Photos: vertical originals ≥ 1000 px, face in the upper half, a calm or darker lower half. `analyze_photos.py` checks this.
- Render: `render_slide.py` with `"photo": ...` (the style is implied). Keys: `lines`, `focus_y`, `bottom`, `gradient`.
