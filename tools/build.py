#!/usr/bin/env python3
"""
build.py — regenerate the index.json manifests the site reads.

    python tools/build.py

Scans:
    content/blog/*.md      -> content/blog/index.json
    content/learning/*.md  -> content/learning/index.json
    content/projects/*.md  -> content/projects/index.json

You normally never need to run this by hand: the GitHub Action runs it
on every push, and local-server/start-server runs it before serving.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"

# Old imported posts have sentence-like tags split into words; drop the noise.
TAG_STOPWORDS = {"and", "or", "of", "the", "a", "an", "in", "for", "to", "on", "with", "is"}


def parse_frontmatter(text: str) -> dict:
    """Top-level key: value pairs plus simple `- item` lists."""
    m = re.match(r"^---\s*\r?\n(.*?)\r?\n---", text, re.DOTALL)
    if not m:
        return {}
    fm: dict = {}
    lines = m.group(1).split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line or line.startswith("#") or line[0].isspace():
            i += 1
            continue
        kv = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not kv:
            i += 1
            continue
        key, val = kv.group(1), kv.group(2).strip().strip('"').strip("'")
        if val == "":
            lst = []
            j = i + 1
            while j < len(lines) and re.match(r"^\s*-\s+", lines[j]):
                lst.append(re.sub(r"^\s*-\s+", "", lines[j]).strip().strip('"').strip("'"))
                j += 1
            if lst:
                fm[key] = lst
                i = j
                continue
            fm[key] = ""
        elif val.startswith("[") and val.endswith("]"):
            fm[key] = [t.strip().strip('"').strip("'") for t in val[1:-1].split(",") if t.strip()]
        else:
            fm[key] = val
        i += 1
    return fm


def build_posts_manifest(folder: Path) -> int:
    """Manifest for date-ordered collections (blog, learning)."""
    entries = []
    for md in sorted(folder.glob("*.md")):
        if md.name.startswith("_"):
            continue
        fm = parse_frontmatter(md.read_text(encoding="utf-8"))
        date = str(fm.get("date", ""))
        tags = fm.get("tags", [])
        if isinstance(tags, str):
            tags = [tags] if tags else []
        entries.append({
            "slug": md.stem,
            "title": fm.get("title") or md.stem.replace("-", " ").title(),
            "date": date[:10],
            "description": fm.get("description", ""),
            "tags": [t for t in tags if t and t.lower() not in TAG_STOPWORDS],
        })
    entries.sort(key=lambda e: e["date"], reverse=True)
    out = folder / "index.json"
    out.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  {out.relative_to(ROOT)}  ({len(entries)} entries)")
    return len(entries)


def build_projects_manifest(folder: Path) -> int:
    entries = []
    for md in sorted(folder.glob("*.md")):
        if md.name.startswith("_"):
            continue
        fm = parse_frontmatter(md.read_text(encoding="utf-8"))
        entries.append({
            "slug": md.stem,
            "label": fm.get("label", ""),
            "title": fm.get("title", md.stem),
            "featured": str(fm.get("featured", "false")).lower() == "true",
            "order": int(fm.get("order", 999)) if str(fm.get("order", "")).isdigit() else 999,
        })
    # featured cards first, then explicit order, then filename
    entries.sort(key=lambda e: (not e["featured"], e["order"], e["slug"]))
    out = folder / "index.json"
    out.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  {out.relative_to(ROOT)}  ({len(entries)} entries)")
    return len(entries)


def main() -> int:
    print("Building manifests:")
    build_posts_manifest(CONTENT / "blog")
    build_posts_manifest(CONTENT / "learning")
    build_projects_manifest(CONTENT / "projects")
    return 0


if __name__ == "__main__":
    sys.exit(main())
