# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal portfolio and blog of Dr. Soumya Maity (smaity.co.in). Pure static
HTML/CSS/JS, **fully markdown-driven**: every piece of content lives in
`content/` and is fetched + rendered client-side with marked.js (CDN).
The owner only ever edits markdown — never HTML/CSS/JS — to update the site.

Design: professional personal-brand theme modeled on the genre standard for
security experts/speakers (Schneier, Troy Hunt, Keren Elazari): light/white,
Inter type, deep-blue accent `#155eb8`, navy contact band `#0c1c33`.
First-person hero ("Hi, I'm…") with circular photo (path set via `photo:` in
content/profile/hero.md), metric cards, and a "Speaker & contributor at"
social-proof strip (venues pulled from speaking.md). Card-based sections with
alternating white/`#f5f7fa` backgrounds; year-grouped blog list; "Invite me
to speak" CTA in Speaking. Dense, scannable homepage: expertise chips in the
hero (`expertise:` list in hero.md), latest writing as a 3-card grid plus an
"In the pipeline" box, speaking as stat+venues split, and recognition +
education rendered side-by-side as one "credentials" section
(renderCredentials in site.js reads both md files; #credentials section).
Respect `prefers-reduced-motion`.

## Development

```bash
python local-server/serve.py     # rebuild manifests + serve at :8000
python tools/build.py            # regenerate content/*/index.json manifests only
```

The pages fetch `content/**` via `fetch()`, so they must be viewed through a
server (not `file://`).

## Deployment

- Push to `PreProduction` → `.github/workflows/deploy-site.yaml` runs
  `tools/build.py` (manifests) and publishes the tree to the `main` branch
  via peaceiris/actions-gh-pages → GitHub Pages serves smaity.co.in.
- `archive/`, `tools/`, `local-server/`, `.claude/`, `CLAUDE.md` are excluded
  from the published site.

## Architecture

```
index.html               # homepage shell; <body data-page="home">
blog.html                # blog listing (search + tag filters); data-page="blog"
post.html                # single post viewer (?slug=…&from=blog|learning); data-page="post"
learning.html            # daily-learning log, notes rendered inline; data-page="learning"
assets/css/site.css      # the ONE stylesheet for all pages
                         #   NB: .wrap uses padding-left/right longhands; section
                         #   paddings use padding-top/bottom longhands — don't
                         #   reintroduce shorthand `padding:` on .wrap-combined classes
assets/js/site.js        # the ONE script: frontmatter parser + per-page renderers
content/
  site.md                # footer / domain
  profile/*.md           # one file per homepage section (hero, recognition,
                         #   writing, research, speaking, community, education, contact)
  projects/*.md          # one card each; _index.md holds the section heading
  blog/*.md              # ~96 posts; index.json manifest (generated — do not hand-edit)
  blog/images/           # post hero images; `hero:` frontmatter paths resolve
                         #   relative to content/blog/ (e.g. hero: images/slug.svg)
  learning/*.md          # daily notes; index.json manifest (generated)
tools/build.py           # regenerates the three index.json manifests
tools/new_post.py        # scaffolds blog/learning/project markdown files
tools/gen_hero_images.py # branded SVG hero for any post whose hero: file is
                         #   missing; safe to re-run (deterministic per slug)
tools/import_linkedin.py # LinkedIn post → content/blog/*.md with the original
                         #   timestamp (decoded from activity ID: id >> 22 = epoch ms)
local-server/            # serve.py + start-server.bat for local preview
archive/                 # previous site version (reference only; never deploy/edit)
```

### Content formats site.js expects

- All files: YAML frontmatter (`key: value`, plus `tags:` dash-lists).
- `recognition.md` / `education.md` / `contact.md` bodies: one pipe-separated
  row per line (`year | name | org | LATEST`, etc.).
- `community.md` / `writing.md` bodies: `### Title` blocks with a description
  and a `Tags: a | b` or `[Pill] [Pill]` line.
- `research.md` body: `## Column` headings with `- item` bullets; an
  italic-only line becomes a muted footnote.
- Section headings come from each file's `label:`/`title:` frontmatter.

### Adding a blog post

Create `content/blog/slug.md` with `title/date/description/tags` frontmatter.
Manifests rebuild automatically in CI; locally run `python tools/build.py`.
Optional `hero: images/<file>` shows a hero image on the post page; drop the
file in `content/blog/images/`, or run `python tools/gen_hero_images.py` to
generate a branded SVG for any post without one.

## Conventions

- Keep the site dependency-free: stdlib-only Python tools, CDN-only JS
  (marked.js), no build framework, no npm.
- New content types should follow the same pattern: a folder under
  `content/`, a manifest in `tools/build.py`, a renderer in `site.js`.
- Don't modify anything in `archive/`.
