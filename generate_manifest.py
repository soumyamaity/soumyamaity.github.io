#!/usr/bin/env python3
"""Scan posts/*.md, extract YAML frontmatter, produce posts/index.json."""
import os, json, re, glob

posts_dir = os.path.join(os.path.dirname(__file__), "posts")
manifest = []

for md_path in sorted(glob.glob(os.path.join(posts_dir, "*.md"))):
    slug = os.path.splitext(os.path.basename(md_path))[0]
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract YAML frontmatter between --- markers
    m = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not m:
        continue
    fm_text = m.group(1)

    # Simple YAML parsing (no dependency needed)
    title = ""
    date = ""
    description = ""
    tags = []

    for line in fm_text.split("\n"):
        line = line.strip()
        if line.startswith("title:"):
            title = line[6:].strip().strip('"').strip("'")
        elif line.startswith("date:"):
            date = line[5:].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            description = line[12:].strip().strip('"').strip("'")

    # Parse tags list
    in_tags = False
    for line in fm_text.split("\n"):
        stripped = line.strip()
        if stripped == "tags:" or stripped.startswith("tags:"):
            if stripped == "tags:":
                in_tags = True
            else:
                # inline tags
                inline = stripped[5:].strip()
                if inline.startswith("["):
                    tags = [t.strip().strip('"').strip("'") for t in inline.strip("[]").split(",")]
                    in_tags = False
            continue
        if in_tags:
            if stripped.startswith("- "):
                tags.append(stripped[2:].strip().strip('"').strip("'"))
            elif stripped.startswith("-"):
                tags.append(stripped[1:].strip().strip('"').strip("'"))
            else:
                in_tags = False

    # Normalize date to YYYY-MM-DD
    date_short = date[:10] if len(date) >= 10 else date

    manifest.append({
        "slug": slug,
        "title": title or slug.replace("-", " ").title(),
        "date": date_short,
        "description": description,
        "tags": [t for t in tags if t]
    })

# Sort by date descending
manifest.sort(key=lambda x: x["date"], reverse=True)

out_path = os.path.join(posts_dir, "index.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

print(f"Generated {out_path} with {len(manifest)} posts")
