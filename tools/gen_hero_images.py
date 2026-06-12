#!/usr/bin/env python3
"""
gen_hero_images.py — give every blog post a hero image.

    python tools/gen_hero_images.py

For each content/blog/*.md whose `hero:` doesn't point to an existing file,
generate a branded SVG into content/blog/images/<slug>.svg (the default hero
location) and set `hero: images/<slug>.svg` in the post's frontmatter.

- Posts whose hero already resolves (e.g. a hand-made PNG in images/) are
  left untouched, so the tool is safe to re-run after adding new posts.
- Artwork is deterministic per slug: re-running never churns existing files.
- Stdlib only.
"""
import hashlib
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "content" / "blog"
IMAGES = BLOG / "images"

W, H = 1200, 630
NAVY = "#0c1c33"      # site contact-band navy
ACCENT = "#155eb8"    # site accent blue
LIGHT = "#3f8ad1"
PALE = "#9cc4ec"


def beams(rng):
    """Parallel translucent diagonal bands."""
    angle = rng.uniform(18, 34)
    parts = []
    for _ in range(rng.randint(4, 6)):
        x = rng.uniform(-150, W)
        w = rng.uniform(80, 260)
        color = rng.choice([ACCENT, LIGHT, PALE])
        parts.append(
            f'<rect x="{x:.0f}" y="-300" width="{w:.0f}" height="{H + 600}" '
            f'fill="{color}" opacity="{rng.uniform(0.06, 0.16):.2f}" '
            f'transform="rotate({angle:.0f} {W / 2:.0f} {H / 2:.0f})"/>')
    return "".join(parts)


def nodes(rng):
    """Network graph: dots joined when close enough."""
    pts = [(rng.uniform(60, W - 60), rng.uniform(60, H - 60))
           for _ in range(rng.randint(9, 13))]
    parts = []
    for i, (x1, y1) in enumerate(pts):
        for x2, y2 in pts[i + 1:]:
            if (x1 - x2) ** 2 + (y1 - y2) ** 2 < 340 ** 2:
                parts.append(
                    f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
                    f'stroke="{PALE}" stroke-width="1.5" opacity="0.25"/>')
    for x, y in pts:
        parts.append(
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rng.uniform(4, 9):.1f}" '
            f'fill="{rng.choice([ACCENT, LIGHT, PALE])}" opacity="0.85"/>')
    return "".join(parts)


def rings(rng):
    """Concentric circles radiating from an off-centre point."""
    cx = rng.uniform(W * 0.6, W * 0.9)
    cy = rng.uniform(H * 0.2, H * 0.8)
    parts = [f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="10" fill="{ACCENT}"/>']
    r = rng.uniform(50, 90)
    for _ in range(rng.randint(5, 7)):
        parts.append(
            f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="none" '
            f'stroke="{rng.choice([ACCENT, LIGHT, PALE])}" '
            f'stroke-width="{rng.uniform(1.5, 3):.1f}" '
            f'opacity="{rng.uniform(0.18, 0.5):.2f}"/>')
        r += rng.uniform(45, 90)
    return "".join(parts)


def grid(rng):
    """Dot matrix with a few accent dots lit up."""
    step = rng.choice([70, 84, 96])
    parts = []
    for gx in range(60, W, step):
        for gy in range(50, H, step):
            if rng.random() < 0.08:
                parts.append(f'<circle cx="{gx}" cy="{gy}" '
                             f'r="{rng.uniform(5, 9):.1f}" fill="{ACCENT}" opacity="0.9"/>')
            else:
                parts.append(f'<circle cx="{gx}" cy="{gy}" r="2.2" fill="{PALE}" opacity="0.35"/>')
    return "".join(parts)


def make_svg(slug: str) -> str:
    seed = int.from_bytes(hashlib.md5(slug.encode("utf-8")).digest()[:8], "big")
    rng = random.Random(seed)
    pattern = rng.choice([beams, nodes, rings, grid])
    top = rng.choice(["#11294a", "#0e2240", "#132f55"])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img">\n'
        f'  <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">\n'
        f'    <stop offset="0" stop-color="{top}"/>'
        f'<stop offset="1" stop-color="{NAVY}"/>\n'
        f'  </linearGradient></defs>\n'
        f'  <rect width="{W}" height="{H}" fill="url(#bg)"/>\n'
        f'  {pattern(rng)}\n'
        f'  <rect y="{H - 6}" width="{W}" height="6" fill="{ACCENT}"/>\n'
        f'</svg>\n')


def set_hero(text: str, value: str) -> str:
    """Set/replace the hero: key inside the frontmatter block."""
    m = re.match(r"^---\s*\r?\n(.*?)(\r?\n)---", text, re.DOTALL)
    if not m:
        return text
    block, nl = m.group(1), m.group(2)
    if re.search(r"(?m)^hero:", block):
        block = re.sub(r"(?m)^hero:.*$", lambda _: "hero: " + value, block, count=1)
    else:
        block = block + nl + "hero: " + value
    return text[:m.start(1)] + block + text[m.end(1):]


def main() -> int:
    IMAGES.mkdir(exist_ok=True)
    generated = kept = 0
    for md in sorted(BLOG.glob("*.md")):
        if md.name.startswith("_"):
            continue
        text = md.read_text(encoding="utf-8")
        cur = re.search(r"(?m)^hero:\s*(\S+)", text)
        if cur and (BLOG / cur.group(1)).is_file():
            kept += 1
            continue
        rel = f"images/{md.stem}.svg"
        (BLOG / rel).write_text(make_svg(md.stem), encoding="utf-8")
        md.write_text(set_hero(text, rel), encoding="utf-8")
        generated += 1
        print(f"  {md.name} -> {rel}")
    print(f"{generated} hero(s) generated, {kept} existing kept.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
