#!/usr/bin/env python3
"""Transcribe a video/audio file to word-level timestamps.

Usage: transcribe.py INPUT [--model small] > words.json
Output: JSON list of {"word", "start", "end"} in seconds.
Requires: pip install faster-whisper
"""
import argparse
import json
import sys

from faster_whisper import WhisperModel

p = argparse.ArgumentParser()
p.add_argument("input")
p.add_argument("--model", default="small")
p.add_argument("--language", default="en")
a = p.parse_args()

model = WhisperModel(a.model, device="cpu", compute_type="int8")
segments, _ = model.transcribe(a.input, language=a.language, word_timestamps=True, vad_filter=True)
words = [
    {"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)}
    for s in segments
    for w in s.words
    if w.word.strip()
]
json.dump(words, sys.stdout, indent=1)
