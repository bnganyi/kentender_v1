#!/usr/bin/env python3
"""Build review.html: every captured page, before and after the DS-REV-002 restyle, at 1440 and 1024 px (HOME6-0109)."""
import os, html
here = os.path.dirname(os.path.abspath(__file__))
names = sorted({f.rsplit("-", 1)[0] for f in os.listdir(os.path.join(here, "before")) if f.endswith(".png")})
rows = []
for name in names:
    for width in ("1440", "1024"):
        b, a = f"before/{name}-{width}.png", f"after/{name}-{width}.png"
        if not (os.path.exists(os.path.join(here, b)) and os.path.exists(os.path.join(here, a))):
            continue
        rows.append(f'<section><h2>{html.escape(name)} <small>{width} px</small></h2><div class="pair"><figure><figcaption>Before</figcaption><img loading="lazy" src="{b}"></figure><figure><figcaption>After</figcaption><img loading="lazy" src="{a}"></figure></div></section>')
page = """<!doctype html><meta charset="utf-8"><title>Industry restyle: before and after</title>
<style>body{font:15px/1.5 system-ui,sans-serif;margin:24px;background:#f8f8f8;color:#222}h1{margin:0 0 4px}p{max-width:70ch}section{margin:32px 0}h2{font-size:18px;margin:0 0 8px}small{color:#666;font-weight:400}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0}figcaption{font-weight:600;margin-bottom:4px}img{width:100%;border:1px solid #ddd;background:#fff}</style>
<h1>Industry restyle: before and after</h1>
<p>HOME-CHG-001 v0.6 Phase 1B: every Industry page on the new design system (KT-STD-001 v1.22, DS-REV-002). Each pair is the same page, same person, same data, on the test site; the left is the previous stylesheet, the right the new one.</p>
""" + "\n".join(rows)
open(os.path.join(here, "review.html"), "w").write(page)
print(len(rows), "pairs")
