# Talking-head styles

Three named styles. `../SKILL.md` step 0 explains how Claude picks one from the footage. Voiceover montages (narration over many short clips) are a **separate format** with their own skill, `../../voiceover-montage/`. Don't mix them in here.

| Style | Feels like | Footage it needs | Effort |
|---|---|---|---|
| [Quiet Take](quiet-take.md) | A friend telling you something while doing their routine | One continuous selfie take | Low |
| [Explainer Board](explainer-board.md) | A mini lesson: you in a card, handwritten notes writing themselves on below | Any talking take + a framework, list or equation in the script | Medium |
| [Story Cut](story-cut.md) | A tight, high-energy story with visual punctuation | Medium-shot talking take(s), optional photos and B-roll | High |

Add new styles here as `<name>.md`, using the same sections. Then add a rule for them in `scripts/analyze_footage.py`.
