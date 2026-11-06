"""Pre-launch checks on dist/: broken internal links, missing assets, duplicate IDs,
heading structure, image alt text, titles/descriptions. Run after build:  python3 tools/check_site.py"""
import re, sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
DIST = Path(__file__).resolve().parent.parent / "dist"
problems = []; titles = {}; descs = {}

class P(HTMLParser):
    def __init__(s): super().__init__(); s.ids=[]; s.links=[]; s.h=[]; s.imgs=[]; s.title=""; s.in_title=False; s.desc=None; s.labels=set(); s.inputs=[]
    def handle_starttag(s, t, a):
        a = dict(a)
        if "id" in a: s.ids.append(a["id"])
        for k in ("href", "src"):
            if k in a and t != "a" or (t == "a" and k == "href" and "href" in a): s.links.append(a.get(k)) if a.get(k) else None
        if re.fullmatch(r"h[1-6]", t): s.h.append(int(t[1]))
        if t == "img" and "alt" not in a: s.imgs.append(a.get("src"))
        if t == "title" and not s.title: s.in_title = True
        if t == "meta" and a.get("name") == "description": s.desc = a.get("content")
        if t == "label" and a.get("for"): s.labels.add(a["for"])
        if t in ("input","select","textarea") and a.get("type") not in ("hidden",) and a.get("name") != "bot-field": s.inputs.append(a.get("id"))
    def handle_endtag(s, t):
        if t == "title": s.in_title = False
    def handle_data(s, d):
        if s.in_title: s.title += d

for f in sorted(DIST.rglob("*.html")):
    rel = f.relative_to(DIST); p = P(); p.feed(f.read_text())
    dup = {i for i in p.ids if p.ids.count(i) > 1}
    if dup: problems.append(f"{rel}: duplicate ids {dup}")
    if p.h.count(1) != 1: problems.append(f"{rel}: {p.h.count(1)} h1 elements")
    for a, b in zip(p.h, p.h[1:]):
        if b > a + 1: problems.append(f"{rel}: heading jumps h{a} -> h{b}")
    if p.imgs: problems.append(f"{rel}: images without alt {p.imgs}")
    for i in p.inputs:
        if i not in p.labels: problems.append(f"{rel}: form control #{i} has no <label for>")
    if f.name != "404.html":
        titles.setdefault(p.title, []).append(str(rel)); descs.setdefault(p.desc, []).append(str(rel))
    for link in p.links:
        u = urlparse(link)
        if u.scheme or link.startswith(("mailto:", "tel:", "#", "data:")): continue
        path = u.path
        target = (DIST / path.lstrip("/")) if path.startswith("/") else (f.parent / path)
        if path == "" : continue
        target = target.resolve()
        if target.is_dir(): target = target / "index.html"
        if not target.exists(): problems.append(f"{rel}: broken link {link}")
        if u.fragment and target.suffix == ".html":
            if f'id="{u.fragment}"' not in target.read_text(): problems.append(f"{rel}: missing anchor {link}")
for t, fs in titles.items():
    if len(fs) > 1: problems.append(f"duplicate title on {fs}")
    if len(t) > 70: problems.append(f"long title ({len(t)}): {t}")
for d, fs in descs.items():
    if not d: problems.append(f"missing description {fs}")
    elif len(fs) > 1: problems.append(f"duplicate description on {fs}")
print("\n".join(problems) if problems else "All checks passed.")
sys.exit(1 if problems else 0)
