#!/usr/bin/env python3
"""
new_post.py — scaffold a new blog post, learning note, or project card.

    python tools/new_post.py blog "My Post Title"
    python tools/new_post.py learning "Tried the new SLSA verifier"
    python tools/new_post.py project "Confidential Computing Pilot"

Creates the markdown file in the right content/ folder with frontmatter
filled in, then regenerates the manifests. Open the file, write, push.
"""
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def slugify(title: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", title).strip("-")
    return s[:80] or "untitled"


TEMPLATES = {
    "blog": (
        "content/blog/{slug}.md",
        "---\n"
        "title: {title}\n"
        "date: {date}\n"
        "description: \n"
        "tags:\n"
        "  - InfoSec\n"
        "---\n\n"
        "Write your post here in markdown.\n",
    ),
    "learning": (
        "content/learning/{day}-{slug}.md",
        "---\n"
        "title: {title}\n"
        "date: {date}\n"
        "tags:\n"
        "  - til\n"
        "---\n\n"
        "What I learned today…\n",
    ),
    "project": (
        "content/projects/{slug}.md",
        "---\n"
        "label: Area of work\n"
        "title: {title}\n"
        "featured: false\n"
        "order: 10\n"
        "---\n\n"
        "One or two paragraphs describing the project.\n",
    ),
}


def main() -> int:
    if len(sys.argv) < 3 or sys.argv[1] not in TEMPLATES:
        print(__doc__)
        return 1
    kind, title = sys.argv[1], " ".join(sys.argv[2:])
    now = datetime.now().astimezone()
    slug = slugify(title)
    path_tpl, body_tpl = TEMPLATES[kind]
    path = ROOT / path_tpl.format(slug=slug, day=now.strftime("%Y-%m-%d"))
    if path.exists():
        print(f"Refusing to overwrite existing file: {path}")
        return 1
    path.write_text(
        body_tpl.format(title=title, date=now.strftime("%Y-%m-%d %H:%M:%S%z"), slug=slug),
        encoding="utf-8",
    )
    print(f"Created {path.relative_to(ROOT)}")
    subprocess.run([sys.executable, str(ROOT / "tools" / "build.py")], check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
