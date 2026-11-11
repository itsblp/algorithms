#!/usr/bin/env python3
"""Transcribe a video/audio file to word-level timestamps.

Usage: transcribe.py INPUT [--model small] > words.json
Output: JSON list of {"word", "start", "end"} in seconds.
Requires: pip install faster-whisper
"""
import argparse
import json
import subprocess
import sys

import numpy as np

from faster_whisper import WhisperModel

p = argparse.ArgumentParser()
p.add_argument("input")
p.add_argument("--model", default="small")
p.add_argument("--language", default="en")
a = p.parse_args()

model = WhisperModel(a.model, device="cpu", compute_type="int8")
# decode with ffmpeg (16 kHz mono float) rather than PyAV, which breaks across versions
pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", a.input, "-vn", "-ac", "1", "-ar", "16000",
                      "-f", "f32le", "-"], capture_output=True, check=True).stdout
audio = np.frombuffer(pcm, np.float32)
# the prompt nudges Whisper to keep disfluencies (um, uh, like) so story_cut.py can remove them
segments, _ = model.transcribe(audio, language=a.language, word_timestamps=True, vad_filter=False,
                               initial_prompt="Umm, so, uh, I was like, you know, hmm. Okay, um, here's the thing.")
words = [
    {"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
    for s in segments
    for w in s.words
    if w.word.strip()
]
json.dump(words, sys.stdout, indent=1)
