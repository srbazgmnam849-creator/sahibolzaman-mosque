#!/usr/bin/env python3
"""A1: replace external sql.js <script src> with inline content; add WASM_B64 const."""
import pathlib

D = pathlib.Path("/home/z/my-project/deploy")
f = D / "index.html"
html = f.read_text(encoding="utf-8")
wasm_js = (D / "_assets/sql-wasm-inline.js").read_text(encoding="utf-8")

assert "</script>" not in wasm_js, "wasm js contains </script> — unsafe to inline"

TAG = '<script src="https://cdn.jsdelivr.net/npm/sql.js@1.10.3/dist/sql-wasm.js"></script>'
assert html.count(TAG) == 1, f"expected 1 sql.js tag, found {html.count(TAG)}"
html = html.replace(TAG, "<script>\n" + wasm_js + "\n</script>")
print("A1: sql.js inlined as local <script> block")

ANCHOR = "'use strict';"
assert html.count(ANCHOR) == 1, f"expected 1 anchor, found {html.count(ANCHOR)}"
CONST = "const WASM_B64='__SQL_WASM_B64__';"
html = html.replace(ANCHOR, ANCHOR + "\n\n/* base64 sql.js WASM binary (injected at build time) — fully offline */\n" + CONST, 1)
print("A1b: WASM_B64 placeholder added before boot")

f.write_text(html, encoding="utf-8")
print("OK, new size:", len(html.encode('utf-8')))
