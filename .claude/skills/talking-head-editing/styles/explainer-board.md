# Explainer Board

**Reference:** @markynv "how to edit tips" reel (user's screen recording, 2026-10-23). The talking head shrinks into a card at the top of a white canvas, and hand-drawn notes write themselves on below it, then get circled.

## Fits when
- The content is a **framework, list, equation or step-by-step**. This is decided from the transcript or the Notion card (Recipe: Freedom math, Skateboard → car, Open the door; Hook pattern: Coined concept or Dichotomy), not from the footage alone.
- Any talking take works, as long as the face isn't so close that a card crop cuts off the chin. Medium shots or a relaxed selfie are best.
- The user wants the video to be *saved*: boards read like a mini lesson.

## Edit
1. **Cuts:** jump cuts on dead air and filler, as in Story Cut, but no punch-ins (the card is already a tight frame).
2. **Board plan:** list 2–4 "board moments", each a short handwritten note (≤ 4 words per line, ≤ 2 lines) timed to when the idea is said. Add a `circle` or `underline` on the key term, and `clear` between points.
3. **Handwriting:**
   - **Default:** the user's own drawings. iPad or paper PNGs in the post's Drive folder `drawings/`; a white paper background is keyed out automatically.
   - **Fallback:** Caveat Bold (bundled). Say in the delivery note when the fallback was used.
4. **Render:** `scripts/explainer_board.py cut.mp4 board.json board.mp4`. It runs full frame for the hook (`shrink_at` ≈ 1–1.5 s), then the shrink into the card, then the notes. The board is white (`#FFFFFF`), or the brand off-white `#F4F1EC` when the user prefers warmer.
5. **Captions:** inside the card. `kinetic_captions.py --mode pop --baseline <card y + h − 80>` (e.g. 850), with the signature accent word. Burn them after the board render.
6. **QA:** safe-zone check. Notes and captions must clear the cyan; only the video card may extend into the side and top bands.

## Watch for
- **Too much text:** a board is not a slide. If a note needs more than 2 lines, it belongs in a carousel.
- **The card crop:** make sure gestures that matter (hands showing a number) stay inside the card.
