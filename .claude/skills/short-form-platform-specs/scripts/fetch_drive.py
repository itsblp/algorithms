#!/usr/bin/env python3
"""Download a large file (raw footage) from a Google Drive share link.

Usage: fetch_drive.py "<drive share link>" OUT_PATH

The file must be shared "Anyone with the link: Viewer" (chat uploads are capped at 30 MB, so
this is how full-size clips get in). Works for multi-GB files: it skips Drive's
"can't scan for viruses" page. Afterwards, remind the user they can set the link back to
Restricted.
"""
import re
import subprocess
import sys

link, out = sys.argv[1], sys.argv[2]
m = re.search(r"/d/([\w-]{20,})", link) or re.search(r"[?&]id=([\w-]{20,})", link)
if not m:
    sys.exit("could not find a Drive file id in that link")
url = f"https://drive.usercontent.google.com/download?id={m.group(1)}&export=download&confirm=t"
subprocess.run(["curl", "-L", "--fail", "--retry", "3", "-o", out, url], check=True)
head = open(out, "rb").read(512)
if b"<html" in head.lower():
    sys.exit("Drive returned a web page instead of the file: the link is probably not set to "
             "'Anyone with the link', or the file is still processing. Ask the user to check sharing.")
print(out)
