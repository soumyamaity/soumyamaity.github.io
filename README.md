# smaity.co.in — personal site of Dr. Soumya Maity

Markdown-driven portfolio + blog, served by GitHub Pages. **You never edit
code to update the site — every piece of content is a markdown file in
`content/`.** Push to the `PreProduction` branch and GitHub Actions
publishes it to https://smaity.co.in.

## Everyday tasks

### Preview locally

Double-click **`local-server/start-server.bat`** (or run
`python local-server/serve.py`). It opens http://localhost:8000 showing
the site exactly as GitHub Pages will.

### Write a blog post

```bash
python tools/new_post.py blog "My Post Title"
```

…or just create `content/blog/my-post-title.md` by hand:

```markdown
---
title: My Post Title
date: 2026-06-12
description: One-line summary shown in listings.
tags:
  - AI Security
---

Your post, in markdown.
```

Push to `PreProduction`. That's it — the post appears on the blog page
and (if recent) in the homepage Writing section.

### Import a LinkedIn post

```bash
python tools/import_linkedin.py https://www.linkedin.com/posts/soumyam_..."
```

The post text is converted to markdown and saved in `content/blog/` with
the **exact original publication time** (decoded from the LinkedIn
activity ID) and a "Originally on LinkedIn" backlink. If LinkedIn blocks
the fetch, save the post page in your browser (Ctrl+S → "Webpage, HTML
Only") and rerun with `--file saved.html`.

### Add a daily-learning note

```bash
python tools/new_post.py learning "What I tried today"
```

…or create `content/learning/2026-06-12-what-i-tried.md` with the same
frontmatter as a blog post. Notes appear on the **Learning** page,
newest first, grouped by month.

### Add / edit a project ("What I am building now")

One file per card in `content/projects/`:

```markdown
---
label: AI Security          # small teal label
title: My Project           # card heading
featured: true              # highlighted + sorted first
order: 1                    # optional sort
---

One or two paragraphs about the project.
```

### Update profile sections

Each homepage section is one file in `content/profile/` — edit and push:

| File             | Section                                  |
| ---------------- | ---------------------------------------- |
| `hero.md`        | Headline, intro, metrics, CV button      |
| `recognition.md` | Awards (one `year \| name \| org` per line) |
| `writing.md`     | Pinned/upcoming writing items            |
| `research.md`    | Patents & publications columns           |
| `speaking.md`    | Speaking stats and venue pills           |
| `community.md`   | Community & service cards                |
| `education.md`   | Degrees (one per line)                   |
| `contact.md`     | Contact headline and links               |

`content/site.md` holds the footer/domain text.

## How it works

```
index.html / blog.html / post.html / learning.html   ← static shells
assets/css/site.css                                  ← one professional light theme (Inter, blue accent)
assets/js/site.js                                    ← fetches content/*.md, renders client-side (marked.js)
content/                                             ← ALL site content (markdown)
  profile/   homepage sections
  projects/  project cards
  blog/      blog posts (+ index.json manifest)
  learning/  daily notes (+ index.json manifest)
tools/                                               ← build.py, new_post.py, import_linkedin.py
local-server/                                        ← local preview server
archive/                                             ← the previous version of the site (not deployed)
```

The `index.json` manifests are regenerated automatically by the GitHub
Action on every push (and by the local server), so adding a markdown
file is always enough.

**Deploy flow:** push to `PreProduction` → `.github/workflows/deploy-site.yaml`
builds manifests → publishes to the `main` branch → GitHub Pages serves
smaity.co.in (`archive/`, `tools/`, `local-server/` are excluded).

Requirements: Python 3.10+ for the helper tools. The site itself needs
no build — it is plain HTML/CSS/JS with marked.js from a CDN.
