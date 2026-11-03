#!/usr/bin/env python3
"""Extract every inline <script> block from index.html into /tmp and list them."""
import re, pathlib

html = pathlib.Path("/home/z/my-project/deploy/index.html").read_text(encoding="utf-8")
blocks = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, flags=re.S)
out = pathlib.Path("/tmp/jscheck")
out.mkdir(exist_ok=True)
for i, b in enumerate(blocks):
    p = out / f"block{i}.js"
    p.write_text(b, encoding="utf-8")
    print(f"block{i}.js: {len(b)} chars")
print(f"total inline script blocks: {len(blocks)}")
