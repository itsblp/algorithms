#!/usr/bin/env python3
"""Story editing for talking heads: find the story arc, cut what doesn't drive it, and
remove ums, false starts and dead air, automatically.

Two steps:
  1) story_cut.py analyze words.json > sentences.json
       Splits the transcript into numbered sentences, and auto-flags fillers (um, uh, erm, hmm),
       pauses longer than --max-pause, and retakes (a sentence restarted with the same opening
       words; the last take is kept). Claude reads the printed sentence list and writes arc.json.
  2) story_cut.py apply words.json sentences.json arc.json OUTDIR
       Writes OUTDIR/segments.txt ("start end" per kept piece, for the cut filter),
       OUTDIR/words_cut.json (word timings re-mapped onto the cut timeline, for captions, so there's
       no second transcription) and OUTDIR/arc_report.md (the story map to show the user).

arc.json (written by Claude, never by the user):
{
  "order": [10, 1, 3, 4, 5, 6, 8, 9, 10],    # sentence ids in final order; a repeat = loop ending
  "roles": {"10": "hook", "1": "context", "3": "tension", "6": "turn", "8": "insight", "9": "payoff"},
  "cut": {"2": "aside: credit moves to the post caption", "7": "repeats sentence 9"},
  "trim": {"15": {"from": "our very first bulk order got"}}   # optional: drop an in-sentence restart
}
Roles: hook, context, tension, turn, insight, payoff, cta. Every sentence is either in "order" or
in "cut" with a reason.
"""
import argparse
import json
import os
import re

FILLERS = {"um", "umm", "uh", "uhh", "erm", "er", "hmm", "mm", "ah"}


def norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower())


def analyze(words, max_pause):
    sents, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r"[.?!]$", w["word"].strip()):
            sents.append(cur)
            cur = []
    if cur:
        sents.append(cur)
    out = []
    for i, s in enumerate(sents, 1):
        fill = [k for k, w in enumerate(s) if norm(w["word"]) in FILLERS]
        pauses = [round(s[k + 1]["start"] - s[k]["end"], 2) for k in range(len(s) - 1)
                  if s[k + 1]["start"] - s[k]["end"] > max_pause]
        out.append({"id": i, "start": s[0]["start"], "end": s[-1]["end"],
                    "text": " ".join(w["word"].strip() for w in s), "fillers": len(fill),
                    "long_pauses": pauses, "words": s})
    for a, b in zip(out, out[1:]):  # retake: next sentence restarts with the same opening words
        ha = [norm(w["word"]) for w in a["words"][:4]]
        hb = [norm(w["word"]) for w in b["words"][:4]]
        if len(ha) >= 3 and ha[:3] == hb[:3]:
            a["retake_of_next"] = True
    return out


def apply(words, sents, arc, outdir, max_pause, pad_pre, pad_post):
    by_id = {s["id"]: s for s in sents}
    missing = [s["id"] for s in sents if s["id"] not in arc["order"] and str(s["id"]) not in arc.get("cut", {})]
    if missing:
        raise SystemExit(f"arc.json must place or cut every sentence; unhandled: {missing}")
    pieces = []  # (src_start, src_end, [words]) in final order
    def trimmed(sid):
        """Optional "trim": {"15": {"from": "our very first bulk order got", "to": "..."}} keeps only
        the clean part of a sentence (drops an in-sentence stumble or restart). Phrases match the
        LAST occurrence for "from" and the first for "to"."""
        ws = by_id[sid]["words"]
        t = arc.get("trim", {}).get(str(sid))
        if not t:
            return ws
        toks = [norm(w["word"]) for w in ws]
        if t.get("from"):
            ph = [norm(x) for x in t["from"].split()]
            hits = [k for k in range(len(toks)) if toks[k:k + len(ph)] == ph]
            if not hits:
                raise SystemExit(f"trim 'from' phrase not found in sentence {sid}: {t['from']}")
            ws, toks = ws[hits[-1]:], toks[hits[-1]:]
        if t.get("to"):
            ph = [norm(x) for x in t["to"].split()]
            hits = [k for k in range(len(toks)) if toks[k:k + len(ph)] == ph]
            if not hits:
                raise SystemExit(f"trim 'to' phrase not found in sentence {sid}: {t['to']}")
            ws = ws[:hits[0] + len(ph)]
        return ws

    for sid in arc["order"]:
        ws = [w for w in trimmed(sid) if norm(w["word"]) not in FILLERS]
        if not ws:
            continue
        run = [ws[0]]
        for w in ws[1:]:
            if w["start"] - run[-1]["end"] > max_pause:  # tighten dead air inside the sentence
                pieces.append(run)
                run = []
            run.append(w)
        pieces.append(run)
    # Whisper often ends a word ~0.1 s before the sound actually stops, so pieces get generous
    # margins (tighten.py removes the extra silence later), but never reach into a neighbouring
    # word of the original take.
    key = lambda w: (round(w["start"], 3), round(w["end"], 3), w["word"])
    order = {key(w): k for k, w in enumerate(words)}
    segs, cut_words, t = [], [], 0.0
    for run in pieces:
        i0, i1 = order.get(key(run[0])), order.get(key(run[-1]))
        lo = words[i0 - 1]["end"] + 0.02 if i0 else 0.0
        hi = words[i1 + 1]["start"] - 0.02 if i1 is not None and i1 + 1 < len(words) else run[-1]["end"] + pad_post
        s0 = max(run[0]["start"] - pad_pre, lo, 0)
        s1 = max(min(run[-1]["end"] + pad_post, hi), run[-1]["end"])
        segs.append((round(s0, 3), round(s1, 3)))
        for w in run:
            cut_words.append({**w, "start": round(t + w["start"] - s0, 3), "end": round(t + w["end"] - s0, 3)})
        t += s1 - s0
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "segments.txt"), "w") as f:
        f.write("".join(f"{a} {b}\n" for a, b in segs))
    json.dump(cut_words, open(os.path.join(outdir, "words_cut.json"), "w"), indent=1)
    raw = sents[-1]["end"] - sents[0]["start"]
    rep = [f"# Story map\n\nRaw {raw:.1f} s → cut {t:.1f} s ({100 * (1 - t / raw):.0f}% removed).\n",
           "| # | Role | Line |", "|---|---|---|"]
    seen = set()
    for sid in arc["order"]:
        role = arc.get("roles", {}).get(str(sid), "")
        line = " ".join(w["word"].strip() for w in trimmed(sid))
        rep.append(f"| {sid}{' (again)' if sid in seen else ''} | {role} | {line}{' ✂' if str(sid) in arc.get('trim', {}) else ''} |")
        seen.add(sid)
    rep.append("\n**Cut:**\n")
    rep += [f"- {sid}: {why} (\"{by_id[int(sid)]['text'][:70]}…\")" for sid, why in arc.get("cut", {}).items()]
    fills = sum(s["fillers"] for s in sents)
    rep.append(f"\nAlso removed: {fills} filler word(s) and every pause over {max_pause:.2f} s.")
    open(os.path.join(outdir, "arc_report.md"), "w").write("\n".join(rep) + "\n")
    print("\n".join(rep))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["analyze", "apply"])
    p.add_argument("files", nargs="+")
    p.add_argument("--max-pause", type=float, default=0.25)
    p.add_argument("--pad-pre", type=float, default=0.15, help="max seconds kept before each piece")
    p.add_argument("--pad-post", type=float, default=0.30, help="max seconds kept after each piece (word tails)")
    a = p.parse_args()
    words = json.load(open(a.files[0]))
    if a.cmd == "analyze":
        sents = analyze(words, a.max_pause)
        json.dump(sents, open(1, "w"), indent=1)
        for s in sents:
            flags = [f"{s['fillers']} filler"] if s["fillers"] else []
            flags += [f"pauses {s['long_pauses']}"] if s["long_pauses"] else []
            flags += ["RETAKE (next is a redo)"] if s.get("retake_of_next") else []
            print(f"[{s['id']}] {s['start']:.1f}-{s['end']:.1f}s  {s['text']}  {'; '.join(flags)}",
                  file=__import__("sys").stderr)
    else:
        apply(words, json.load(open(a.files[1])), json.load(open(a.files[2])), a.files[3], a.max_pause, a.pad_pre, a.pad_post)
