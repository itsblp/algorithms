---
name: talking-head-editing
description: Edit talking-head (person-speaking-to-camera) short-form videos for Instagram Reels and TikTok in the user's house style, automatically choosing a style (Quiet Take, Diary Voiceover, Story Cut) from the footage. Use when the user shares a talking-head clip, transcript, or script, or asks to cut, tighten, caption, add B-roll or zooms to, plan, review, or export a talking-head/face-cam/vlog-style video, voiceover diary, Reel, or TikTok. Produces a hook rewrite, cut list, burned-in caption file, zoom/B-roll plan, ffmpeg commands, and post copy.
---

# Talking-head video editing

Before doing anything, load these:
1. `../short-form-platform-specs/SKILL.md` — sizes, safe zones, export and cross-posting rules. Every output must be valid on **both** IG Reels and TikTok.
2. `preferences.md` (this folder) — the user's house style. **Preferences override the defaults in this file.** If the user states a new preference during a session, offer to save it to `preferences.md`.

3. If the video has a card in the Notion Founder Content Database, read its linked **Story atoms** (see `../content-strategist/SKILL.md`). Scripts, hooks, captions and on-screen text may only state facts those Verified atoms support. After transcribing, hand the transcript to the content-strategist's **Mine** loop, so new stories become Proposed atoms.

## Step 0 — Choose the style (always, before editing)

There are three named styles in `styles/`: **Quiet Take**, **Diary Voiceover** and **Story Cut**. The user doesn't have to pick one. Claude chooses from the footage:

1. Run `python3 scripts/analyze_footage.py <files or folder>`. It reports the framing (selfie close-up / medium / no face), speech, clip lengths, voiceover files, camera motion, caption-band brightness and low-res warnings, plus a recommended style.
2. Sanity-check the recommendation against the content and the Notion card:
   - An answer to a follower question or a reflective routine → Quiet Take.
   - An emotional or episodic story told over many clips → Diary Voiceover.
   - A story with named people or places or quotes → Story Cut.
3. Tell the user the choice in **one line** with the reason (e.g. "Quiet Take: one selfie take while you do skincare, so a calm top-caption edit"). Then proceed without waiting. If the user names a style, use it.
4. Follow that style's file for hook, cuts, captions and effects. Everything else in this file (safe zones, audio, QA, export, post copy) applies to all styles.

If the footage fits no style well (e.g. a dark, low-res clip), say what's missing and what would fix it (more light, the camera original, a voice note) instead of forcing a style.

## Inputs you might get

| Input | What to do |
|---|---|
| Raw talking-head take(s) + B-roll clips | Probe everything with `ffprobe`. Transcribe with `scripts/transcribe.py` (run `pip install faster-whisper` first if it's missing), then run the full workflow and the **Full pipeline** at the bottom. Claude does the whole edit; there's no CapCut handoff unless the user asks for one. |
| Transcript (with or without timestamps) | Run the full workflow and output a cut list and captions. |
| Script / idea, not yet filmed | Run steps 1–2 only. Return a tightened script with hook options, plus filming notes (framing, eyeline, safe zone). |
| Finished edit to review | Run the QA checklist (step 7) and return specific timestamped fixes. |

## Workflow

### 1. Hook (first 1–3 seconds)
- Find the strongest line in the whole take. If it isn't in the first 3 s, **move it to the front** (a cold-open cut).
- Give 3 hook options in different styles: **bold claim**, **question / curiosity gap**, and **"you're doing X wrong" / pattern interrupt**. If the preferences' creative references lean toward storytelling, swap one of these for a **personal-moment opener** ("Last year I almost…"). Recommend one.
- Hook text overlay: ≤ 7 words, on screen from frame 1 to about 2.5 s, placed in the upper-middle of the safe zone (y ≈ 300–600) so it doesn't collide with captions.

### 2. Structure
Hook → context in one line → payoff (2–4 tight beats) → CTA or loop-back. Cut anything that doesn't serve the payoff. Target length comes from `preferences.md`.

### 3. Cut list (jump cuts)
Produce a cut list as a table: `#, in, out, keep/cut, reason`.
- Remove filler words (um, uh, like, so, you know, basically), false starts, repeated takes (keep the **last** clean take unless an earlier one has better energy), breaths between sentences, and dead air longer than the `max_pause` preference.
- Keep about 2–4 frames of handle on each side of a cut so words don't clip.
- Never cut mid-word. Use word timestamps to snap.
- If the cut list will be applied with ffmpeg, also emit a `select`/`aselect` filter or a concat list (see "Applying cuts" below).

### 4. Punch-ins, B-roll weave and visual rhythm
- Hide jump cuts by alternating framing: **100% → `punch_in_scale`** on emphasis lines, back out on the next cut. Don't zoom twice in a row on the same scale.
- Add a visual change (cut, punch-in, or B-roll switch) at the `visual_change_every_sec` rate from preferences. Talking heads without changes lose people.
- **Weave B-roll over the voice:** the audio stays continuous from the talking head while the picture cuts to B-roll for `broll_ratio` of the runtime.
  - Match each B-roll shot to the noun or feeling in the line being spoken (literal first, then atmospheric).
  - Keep each B-roll shot 1–2 s and run 1–3 shots in a row, then return to the face for the next claim or punchline. The face is the anchor: the hook, the turn, and the CTA are always on camera.
  - Pick the strongest 1–2 s inside each clip: motion that's already happening, not the start of a pan.
  - Fill 9:16 from horizontal B-roll with a center crop (`crop=ih*9/16:ih,scale=1080:1920`), never letterbox.
  - Cut B-roll on the beat of speech (at word boundaries), not mid-word.
  - Grade nothing beyond matching exposure between shots. Keep the natural look.
  - Write the plan as an EDL table: `#, timeline in, timeline out, source (A-roll / clip name), source in, scale, note`.
- Face stays inside the safe zone at every zoom level: eyes around y ≈ 650–800, never behind the right-side buttons.
- For each B-roll / graphic suggestion, give: timestamp, what to show, and why (it illustrates the noun the speaker just said).

### 5. Captions (burned in)
If `caption_animation: kinetic`, generate captions with `scripts/kinetic_captions.py` from word timestamps of the **cut** video (re-transcribe `cut.mp4` so timings match). It reveals each word as it's spoken, with a quick pop-in, inside a stable 2–3-word line. Fix transcription errors in `words.json` before generating. The static template below is for non-kinetic styles.

Otherwise, generate an `.ass` subtitle file (preferred: supports styling and word highlight) and an `.srt` fallback.
- Style comes from `preferences.md` (`caption_*` keys).
- **1–2 lines, max ~4 words per line, ~2–3 words visible per chunk** for high-energy edits.
- Position: centered, baseline around **y ≈ 1250** on 1080×1920 (above both apps' bottom UI, below the face). In ASS: `PlayResX: 1080`, `PlayResY: 1920`, `Alignment: 2`, `MarginV: 670`.
- Highlight the key word in each chunk with the accent color.
- Fix transcription errors, brand names and numbers by hand. Write numbers as digits ("3 tips", not "three tips").
- No captions over the hook overlay's time range if they would overlap. Shift one or the other.

ASS style template (fill from preferences):

```
[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Montserrat,78,&H00FFFFFF,&H0000E5FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,6,2,2,200,200,670,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:00.80,Caption,,0,0,0,,THIS IS {\c&H0000E5FF&}HOW{\c&H00FFFFFF&}
```
(ASS colors are `&HAABBGGRR`, so the hex `#FFE500` becomes `&H0000E5FF`. Margins of 200 on both sides keep captions centered and clear of TikTok's button column, which starts at about x 900, and of the side crop on tall phones.)

### 6. Audio
- Light cleanup: high-pass at ~80 Hz, gentle de-ess, and noise reduction only if there's audible hiss (`afftdn` lightly; heavy settings sound robotic).
- Normalize to −14 LUFS / −1 dBTP (see the specs skill).
- Music follows the cross-posting rule in the specs skill. The default is voice-only master.
- Optional SFX (whoosh on punch-ins, pop on text) only if `sfx: on` in preferences.

### 7. QA checklist (run before calling an edit done)
- [ ] Hook lands in < 3 s, and the hook overlay is readable in < 2 s
- [ ] All text and the face are inside x 80–880, y 260–1400, and captions are inside x 200–880. Run `../short-form-platform-specs/scripts/safe_zone_check.py` on `final.mp4` and look at the sheet. A series or credit tag goes at the top (y ≈ 260–320), never under the captions.
- [ ] Captions match the audio word for word, with no typos, and digits for numbers
- [ ] No double captions (if burned in, app auto-captions are off)
- [ ] Visual change at least every 4 s
- [ ] No clipped words at cuts, no audio pops (add 10 ms fades at cut points if needed)
- [ ] −14 LUFS ±1, peaks ≤ −1 dBTP
- [ ] 1080×1920, H.264, `+faststart`, no watermark
- [ ] Cover frame chosen, with cover text inside y 300–1400
- [ ] Ending loops cleanly or ends on a CTA (per preferences)

### 8. Post copy
Output one block that works on both apps:
- **Caption:** hook line with a search keyword → 1–2 lines of value → CTA. ≤ 300 chars.
- **Hashtags:** 3–5, specific to the niche (no #fyp / #viral filler).
- **Cover text:** ≤ 5 words.
- **On-screen keyword:** say the main keyword out loud in the first 5 s and put it in the overlay too. Both apps use speech and on-screen text for search.

## Applying cuts with ffmpeg

For a keep-list of `(start, end)` segments in seconds, build a filter script rather than a giant command line:

```bash
# segments.txt -> one "start end" per line; generates trim+concat filtergraph
python3 - <<'PY' segments.txt > cuts.filter
import sys
segs=[tuple(map(float,l.split())) for l in open(sys.argv[1]) if l.strip()]
parts=[]
for i,(s,e) in enumerate(segs):
    parts.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[v{i}];")
    parts.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={e-s-0.01:.3f}:d=0.01[a{i}];")
parts.append("".join(f"[v{i}][a{i}]" for i in range(len(segs)))+f"concat=n={len(segs)}:v=1:a=1[v][a]")
print("".join(parts))
PY
ffmpeg -i raw.mp4 -filter_complex_script cuts.filter -map "[v]" -map "[a]" -c:v libx264 -crf 16 -c:a aac -b:a 320k cut.mp4
```

Then burn captions and do the final export (settings from the specs skill):

```bash
ffmpeg -i cut.mp4 -vf "ass=captions.ass" -c:v libx264 -profile:v high -pix_fmt yuv420p -crf 18 \
  -af "loudnorm=I=-14:TP=-1:LRA=11" -c:a aac -b:a 320k -ar 48000 -movflags +faststart final.mp4
```

If the user edits in CapCut / Premiere / DaVinci instead, deliver the cut list as a timecoded table plus the `.srt`, and describe punch-ins as "scale 115% at 00:04.20". Don't push ffmpeg on someone who doesn't want it.

## Full pipeline (Claude does the edit)

Work in `content/<video-slug>/` with the raw A-roll and a `broll/` folder.

1. `python3 scripts/transcribe.py raw.mp4 > words_raw.json`. Write the hook, structure and cut list from it (steps 1–3).
2. Apply the cuts → `cut.mp4` (see "Applying cuts" above).
3. **Signature effects** with `scripts/effects.py cut.mp4 effects.json fx.mp4`. The effects JSON schema is in the script's docstring. It does three things in one pass:
   - **Punch-ins** anchored on the face. These are hard cuts by default, with `ease` available for a smooth push.
   - **Text behind the head:** big type placed behind the person using a person mask (MediaPipe selfie segmenter, bundled in `models/`).
   - **Photo overlays:** a bordered, slightly tilted card that pops in, placed automatically in the free space above or below the face.

   Use the counts and rules in `preferences.md` under **Effects**. After rendering, check stills at each effect for clean edges around the hair and to confirm the face isn't covered.
   Setup in a fresh container: `apt-get install -y libegl1 libgles2 && pip install mediapipe opencv-python-headless`.
4. Build the B-roll overlay from the EDL (step 4) on `fx.mp4`. For each B-roll shot, trim and crop it to 1080×1920 and `overlay` it on `fx.mp4` with `enable='between(t,IN,OUT)'`, keeping its audio (punch-ins are already done by `effects.py`). Use `-filter_complex_script` to keep the filter graph in a file.
5. `python3 scripts/transcribe.py cut.mp4 > words.json`, fix any wrong words, then `python3 scripts/kinetic_captions.py words.json > captions.ass` (pass `--size`, `--outline`, `--words` from preferences).
6. Final export: burn captions plus the hook overlay (a second ASS style, or `drawtext` with Inter Bold), loudnorm, and the export settings from the specs skill → `final.mp4`.
7. Extract 3 cover-frame candidates (`-ss` at strong expressions), run the QA checklist on `final.mp4`, and grab stills at about 6 points to visually check the safe zones and captions.

## Deliverables summary
Unless the user asks for less, end with: chosen hook, cut list, `captions.ass` + `captions.srt`, zoom/B-roll plan, export command(s), QA results, and post copy. Save files next to the source video or in a `content/<video-slug>/` folder.
