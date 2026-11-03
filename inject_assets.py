#!/usr/bin/env python3
"""Injects base64 assets (logo, fonts, sql-wasm) into deploy/index.html placeholders.
Run ONLY as the final build step. Placeholders: __SQL_WASM_B64__, __FONT_REG_B64__, __FONT_BOLD_B64__, __LOGO_B64__"""
import pathlib

D = pathlib.Path("/home/z/my-project/deploy")
html = (D / "index.html").read_text(encoding="utf-8")

repl = {
    "__SQL_WASM_B64__": (D / "_assets/sql-wasm-b64.txt").read_text().strip(),
    "__FONT_REG_B64__": (D / "_assets/font-regular.b64").read_text().strip(),
    "__FONT_BOLD_B64__": (D / "_assets/font-bold.b64").read_text().strip(),
    "__LOGO_B64__": (D / "_assets/logo.b64").read_text().strip(),
}

for k, v in repl.items():
    if k not in html:
        print(f"WARNING: placeholder {k} not found in index.html")
        continue
    html = html.replace(k, v)
    print(f"injected {k} ({len(v)} chars)")

leftover = [k for k in repl if k in html]
if leftover:
    raise SystemExit("ERROR: leftover placeholders: " + str(leftover))

(D / "index.html").write_text(html, encoding="utf-8")
print("INJECT OK — final size:", len(html.encode('utf-8')), "bytes")
