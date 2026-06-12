#!/usr/bin/env python3
"""
build.py  —  Compile all markdown content into a single SPA index.html

Usage:
    python build.py

Reads:
    content/            ← all section markdown files
    posts/upcoming.md   ← upcoming writing items
    posts/*.md          ← blog post frontmatter (for manifest)
    css/portfolio.css   ← base styles (inlined into output)

Writes:
    index.html          ← compiled SPA (overwritten each run)
    posts/index.json    ← blog manifest (also updated)
"""

import glob
import json
import os
import re
from pathlib import Path

BASE = Path(__file__).parent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_fm(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter + body. Handles key:val and key:\\n  - list."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", text, re.DOTALL)
    if not m:
        return {}, text.strip()
    fm_raw, body = m.group(1), m.group(2).strip()

    fm: dict = {}
    lines = fm_raw.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if ":" in stripped and not stripped.startswith("-") and not stripped.startswith(" "):
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val == "":
                # collect list items that follow
                lst = []
                i += 1
                while i < len(lines) and re.match(r"^\s*-\s+", lines[i]):
                    lst.append(re.sub(r"^\s*-\s+", "", lines[i]).strip().strip('"').strip("'"))
                    i += 1
                fm[key] = lst
                continue
            else:
                fm[key] = val
        i += 1

    return fm, body


def esc(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def md_inline(text: str) -> str:
    """Convert inline markdown and common typographic shortcuts to HTML."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    text = text.replace(" — ", " &mdash; ").replace("—", "&mdash;")
    text = text.replace("·", "&middot;").replace("×", "&times;")
    return text


def md_to_html(text: str) -> str:
    """Convert basic block markdown (headings, lists, paragraphs) to HTML."""
    lines = text.split("\n")
    out: list[str] = []
    in_ul = False
    in_ol = False
    para_buf: list[str] = []

    def flush_para() -> None:
        nonlocal para_buf
        if not para_buf:
            return
        joined = " ".join(para_buf).strip()
        para_buf = []
        if not joined:
            return
        # italic-only paragraph → muted footnote
        if re.match(r"^\*.+\*$", joined):
            out.append(f'<p class="pf-research-more">{md_inline(joined)}</p>')
        else:
            out.append(f"<p>{md_inline(joined)}</p>")

    def close_list() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    for line in lines:
        s = line.strip()
        if s.startswith("### "):
            flush_para(); close_list()
            out.append(f"<h3>{md_inline(s[4:])}</h3>")
        elif s.startswith("## "):
            flush_para(); close_list()
            out.append(f"<h2>{md_inline(s[3:])}</h2>")
        elif s.startswith("# "):
            flush_para(); close_list()
            out.append(f"<h1>{md_inline(s[2:])}</h1>")
        elif re.match(r"^\d+\.\s", s):
            flush_para()
            if not in_ol:
                close_list()
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{md_inline(re.sub(r'^\\d+\\.\\s+', '', s))}</li>")
        elif s.startswith("- ") or s.startswith("* "):
            flush_para()
            if not in_ul:
                close_list()
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{md_inline(s[2:])}</li>")
        elif s == "" or re.match(r"^-{3,}$", s):
            flush_para(); close_list()
        else:
            close_list()
            # skip HTML-comment lines
            if not s.startswith("<!--"):
                para_buf.append(s)

    flush_para(); close_list()
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def build_hero() -> str:
    fm, body = parse_fm(read(BASE / "content/hero.md"))

    headline = re.sub(r"\*(.+?)\*", r"<em>\1</em>", fm.get("headline", ""))

    # Sub-text: join paragraphs, convert inline markdown
    paras = [p.strip() for p in body.split("\n\n") if p.strip()]
    sub_html = " ".join(md_inline(p) for p in paras)

    # Metrics (m1_count … m4_count)
    metrics_html = ""
    for n in range(1, 5):
        count = esc(fm.get(f"m{n}_count", "0"))
        suffix = esc(fm.get(f"m{n}_suffix", ""))
        label = esc(fm.get(f"m{n}_label", ""))
        metrics_html += f"""    <div class="pf-metric">
      <div class="pf-metric-value"><span data-count="{count}">0</span><span class="counter-suffix">{suffix}</span></div>
      <div class="pf-metric-label">{label}</div>
    </div>\n"""

    eyebrow = esc(fm.get("eyebrow", ""))
    cv_href = esc(fm.get("cv_href", "files/SMAITY_short_CV.pdf"))

    return f"""<header class="pf-hero pf-wrap" id="hero" data-nav>
  <div class="pf-hero-eyebrow hero-anim hero-anim-1">{eyebrow}</div>
  <h1 class="pf-hero-headline hero-anim hero-anim-2">{headline}</h1>
  <p class="pf-hero-sub hero-anim hero-anim-3">{sub_html}</p>
  <div class="pf-hero-buttons hero-anim hero-anim-4">
    <a href="{cv_href}" class="pf-btn pf-btn-fill" target="_blank" rel="noopener">Download CV</a>
    <a href="#writing" class="pf-btn pf-btn-ghost">Read my writing</a>
    <a href="#contact" class="pf-btn pf-btn-ghost">Get in touch</a>
  </div>
  <div class="pf-metrics hero-anim hero-anim-5">
{metrics_html}  </div>
</header>"""


def build_work() -> str:
    idx_fm, _ = parse_fm(read(BASE / "content/work/_index.md"))
    label = esc(idx_fm.get("label", "01 &mdash; Current focus"))
    title = esc(idx_fm.get("title", "What I am building now"))

    cards = []
    for path in sorted(glob.glob(str(BASE / "content/work/*.md"))):
        if "_index" in path:
            continue
        fm, body = parse_fm(read(Path(path)))
        featured = fm.get("featured", "false").lower() == "true"
        cls = "pf-work-card featured" if featured else "pf-work-card"
        # Strip HTML comments from body
        body_clean = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL).strip()
        cards.append(f"""    <div class="{cls}">
      <div class="pf-work-card-label">{esc(fm.get("label", ""))}</div>
      <h3>{esc(fm.get("title", ""))}</h3>
      <p>{md_inline(body_clean)}</p>
    </div>""")

    return f"""<section class="pf-section pf-wrap reveal" id="work" data-nav>
  <div class="pf-section-label">{label}</div>
  <h2 class="pf-section-title">{title}</h2>
  <div class="pf-work-grid">
{chr(10).join(cards)}
  </div>
</section>"""


def build_recognition() -> str:
    fm, body = parse_fm(read(BASE / "content/recognition.md"))
    label = fm.get("label", "02 &mdash; Recognition")
    title = fm.get("title", "Recognition")

    items_html = ""
    for line in body.split("\n"):
        line = line.strip()
        if not line or line.startswith("<!--"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue
        year = esc(parts[0])
        name = esc(parts[1])
        org = esc(parts[2])
        latest = len(parts) > 3 and parts[3].upper() == "LATEST"
        badge = ' <span class="pf-badge-latest">Latest</span>' if latest else ""
        items_html += f"""    <li class="pf-recog-item">
      <span class="pf-recog-year">{year}</span>
      <span class="pf-recog-name">{name}{badge}</span>
      <span class="pf-recog-org">{org}</span>
    </li>\n"""

    return f"""<section class="pf-section pf-wrap reveal" id="recognition" data-nav>
  <div class="pf-section-label">{esc(label)}</div>
  <h2 class="pf-section-title">{esc(title)}</h2>
  <ul class="pf-recog-list">
{items_html}  </ul>
</section>"""


def parse_upcoming() -> str:
    """Parse posts/upcoming.md → writing list HTML."""
    path = BASE / "posts/upcoming.md"
    if not path.exists():
        return ""

    _, body = parse_fm(read(path))
    # Remove HTML comments
    body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL).strip()

    items_html = ""
    num = 0
    blocks = re.split(r"^###\s+", body, flags=re.MULTILINE)

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        num += 1
        lines = block.split("\n")
        title = lines[0].strip()

        desc_lines = []
        tag_line = ""
        for ln in lines[1:]:
            ln = ln.strip()
            if not ln:
                continue
            if re.match(r"^\[.+?\]", ln):
                tag_line = ln
            else:
                desc_lines.append(ln)

        desc = " ".join(desc_lines)
        tags = re.findall(r"\[(.+?)\]", tag_line)

        pills_html = ""
        for tag in tags:
            if tag.lower() in ("coming-soon", "coming soon"):
                pills_html += '<span class="pf-pill pf-pill-soon">Coming soon</span>'
            else:
                pills_html += f'<span class="pf-pill">{esc(tag)}</span>'

        items_html += f"""    <li class="pf-writing-item">
      <span class="pf-writing-num">{num:02d}</span>
      <div>
        <div class="pf-writing-title">{md_inline(title)}</div>
        <div class="pf-writing-desc">{md_inline(desc)}</div>
        <div class="pf-writing-pills">{pills_html}</div>
      </div>
      <span class="pf-writing-arrow">&nearr;</span>
    </li>\n"""

    return items_html


def build_writing() -> str:
    upcoming_html = parse_upcoming()
    return f"""<section class="pf-section pf-wrap reveal" id="writing" data-nav>
  <div class="pf-section-label">03 &mdash; Writing</div>
  <h2 class="pf-section-title">Writing</h2>
  <ul class="pf-writing-list">
{upcoming_html}  </ul>
  <div style="margin-top:2rem;text-align:center">
    <a href="#blog" class="pf-btn pf-btn-ghost" id="view-all-blog">View all blog posts &rarr;</a>
  </div>
</section>"""


def build_research() -> str:
    cols_html = ""
    for path in sorted(glob.glob(str(BASE / "content/research/*.md"))):
        if "_index" in path:
            continue
        fm, body = parse_fm(read(Path(path)))
        col_title = esc(fm.get("column_title", ""))
        body_clean = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL).strip()
        inner = md_to_html(body_clean)
        inner = inner.replace("<ul>", '<ul class="pf-research-list">')
        cols_html += f"""    <div class="pf-research-col">
      <h3>{col_title}</h3>
{inner}
    </div>\n"""

    return f"""<section class="pf-section pf-wrap reveal" id="research" data-nav>
  <div class="pf-section-label">04 &mdash; Research &amp; Patents</div>
  <h2 class="pf-section-title">Research &amp; Patents</h2>
  <div class="pf-research-grid">
{cols_html}  </div>
</section>"""


def build_speaking() -> str:
    fm, body = parse_fm(read(BASE / "content/speaking/_index.md"))
    title = esc(fm.get("title", "Speaking"))
    count = esc(fm.get("count", "100+"))
    count_label = esc(fm.get("count_label", "global security forums and conferences"))
    note = md_inline(fm.get("note", ""))

    body_clean = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL).strip()
    venues = [v.strip() for v in body_clean.split("|") if v.strip()]
    venues_html = "".join(f'<span class="pf-tag-pill">{esc(v)}</span>' for v in venues)

    return f"""<section class="pf-section pf-wrap reveal" id="speaking" data-nav>
  <div class="pf-section-label">05 &mdash; Speaking</div>
  <h2 class="pf-section-title">{title}</h2>
  <div class="pf-speaking-number">{count}</div>
  <div class="pf-speaking-label">{count_label}</div>
  <div class="pf-tag-cloud">
    {venues_html}
  </div>
  <p class="pf-speaking-note">{note}</p>
</section>"""


def build_community() -> str:
    fm, body = parse_fm(read(BASE / "content/community.md"))
    title = esc(fm.get("title", "Community & Service"))

    body_clean = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL).strip()
    cards_html = ""
    blocks = re.split(r"^###\s+", body_clean, flags=re.MULTILINE)

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n")
        card_title = lines[0].strip()
        desc_lines = []
        tags: list[str] = []
        for ln in lines[1:]:
            ln = ln.strip()
            if not ln:
                continue
            if ln.startswith("Tags:"):
                tags = [t.strip() for t in ln[5:].split("|") if t.strip()]
            else:
                desc_lines.append(ln)
        desc = " ".join(desc_lines)
        tags_html = "".join(f'<span class="pf-community-tag">{esc(t)}</span>' for t in tags)
        cards_html += f"""    <div class="pf-community-card">
      <h3>{md_inline(card_title)}</h3>
      <p>{md_inline(desc)}</p>
      <div class="pf-community-tags">{tags_html}</div>
    </div>\n"""

    return f"""<section class="pf-section pf-wrap reveal" id="community" data-nav>
  <div class="pf-section-label">06 &mdash; Community &amp; Service</div>
  <h2 class="pf-section-title">{title}</h2>
  <div class="pf-community-grid">
{cards_html}  </div>
</section>"""


def build_education() -> str:
    fm, body = parse_fm(read(BASE / "content/education.md"))
    title = esc(fm.get("title", "Education"))

    items_html = ""
    for line in body.split("\n"):
        line = line.strip()
        if not line or line.startswith("<!--"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue
        # normalise dashes in year range
        year = esc(parts[0]).replace("–", "&ndash;").replace("-", "&ndash;")
        degree = esc(parts[1])
        school = esc(parts[2])
        detail = (
            f'\n        <div class="pf-edu-detail">{esc(parts[3])}</div>'
            if len(parts) > 3
            else ""
        )
        items_html += f"""    <li class="pf-edu-item">
      <span class="pf-edu-year">{year}</span>
      <div>
        <div class="pf-edu-degree">{degree}</div>
        <div class="pf-edu-school">{school}</div>{detail}
      </div>
    </li>\n"""

    return f"""<section class="pf-section pf-wrap reveal" id="education" data-nav>
  <div class="pf-section-label">07 &mdash; Education</div>
  <h2 class="pf-section-title">{title}</h2>
  <ul class="pf-edu-list">
{items_html}  </ul>
</section>"""


def build_contact() -> str:
    fm, body = parse_fm(read(BASE / "content/contact.md"))
    headline = md_inline(fm.get("headline", "Let&rsquo;s build something secure together"))
    subtext = esc(fm.get("subtext", ""))

    links_html = ""
    for line in body.split("\n"):
        line = line.strip()
        if not line or line.startswith("<!--"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue
        label = esc(parts[0])
        display = esc(parts[1])
        href = parts[2]
        extra = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
        links_html += f"""      <li>
        <a class="pf-contact-link" href="{href}"{extra}>
          <span class="pf-contact-type">{label}</span>
          <span class="pf-contact-value">{display}</span>
          <span class="pf-contact-arrow">&nearr;</span>
        </a>
      </li>\n"""

    return f"""<section class="pf-contact pf-wrap reveal" id="contact" data-nav>
  <div class="pf-contact-grid">
    <div>
      <h2 class="pf-contact-headline">{headline}</h2>
      <p class="pf-contact-sub">{subtext}</p>
    </div>
    <ul class="pf-contact-links">
{links_html}    </ul>
  </div>
</section>"""


# ---------------------------------------------------------------------------
# Blog manifest
# ---------------------------------------------------------------------------

def build_manifest() -> list[dict]:
    manifest = []
    for md_path in sorted(glob.glob(str(BASE / "posts/*.md"))):
        slug = Path(md_path).stem
        if slug == "upcoming":
            continue
        text = read(Path(md_path))
        fm, _ = parse_fm(text)
        if not fm:
            continue

        tags_raw = fm.get("tags", [])
        if isinstance(tags_raw, str):
            tags_raw = [
                t.strip().strip('"').strip("'")
                for t in tags_raw.strip("[]").split(",")
            ]
        tags = [t for t in tags_raw if t]

        manifest.append(
            {
                "slug": slug,
                "title": fm.get("title", slug.replace("-", " ").title()),
                "date": fm.get("date", "")[:10],
                "description": fm.get("description", ""),
                "tags": tags,
            }
        )

    manifest.sort(key=lambda x: x["date"], reverse=True)
    return manifest


# ---------------------------------------------------------------------------
# Extra CSS (blog/post views, SPA view toggling)
# ---------------------------------------------------------------------------

EXTRA_CSS = """
/* ── SPA view management — JS controls via style.display ── */
#blog-view, #post-view { display: none; }

/* ── Blog listing ── */
.pf-blog-header { padding: 6rem 0 2rem; }
.pf-blog-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(2rem,4vw,3rem); font-weight:500; color:#e8ecf1;
  margin-bottom:.5rem;
}
.pf-blog-back, .pf-post-back {
  display:inline-flex; align-items:center; gap:.4rem;
  font-family:'IBM Plex Mono',monospace;
  font-size:.75rem; color:#64ffda; letter-spacing:.5px;
  margin-bottom:2rem; transition:opacity .2s; cursor:pointer;
  text-decoration:none;
}
.pf-blog-back:hover, .pf-post-back:hover { opacity:.7; }
.pf-blog-search-row { display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:1.5rem; }
.pf-blog-search {
  flex:1; min-width:200px;
  background:rgba(255,255,255,.04); border:1px solid rgba(100,255,218,.12);
  border-radius:4px; padding:.55rem 1rem;
  color:#e8ecf1; font-family:'IBM Plex Sans',sans-serif; font-size:.9rem;
  outline:none; transition:border-color .2s;
}
.pf-blog-search::placeholder { color:#6a7384; }
.pf-blog-search:focus { border-color:rgba(100,255,218,.35); }
.pf-blog-filter-row { display:flex; gap:.4rem; flex-wrap:wrap; margin-bottom:2rem; }
.pf-blog-tag {
  font-family:'IBM Plex Mono',monospace;
  font-size:.68rem; padding:.25rem .7rem;
  border:1px solid rgba(100,255,218,.15); border-radius:20px;
  color:#8892a4; cursor:pointer; transition:all .18s; background:none;
}
.pf-blog-tag:hover, .pf-blog-tag.active { border-color:#64ffda; color:#64ffda; }
.pf-blog-grid {
  display:grid; grid-template-columns:1fr 1fr; gap:1px;
  background:rgba(100,255,218,.06);
  border:1px solid rgba(100,255,218,.06);
  border-radius:6px; overflow:hidden; margin-bottom:4rem;
}
.pf-blog-card {
  background:#0c1018; padding:1.6rem 1.6rem;
  transition:background .2s; cursor:pointer;
  display:flex; flex-direction:column; gap:.5rem;
}
.pf-blog-card:hover { background:#111620; }
.pf-blog-card-date {
  font-family:'IBM Plex Mono',monospace;
  font-size:.7rem; color:#6a7384;
}
.pf-blog-card-title {
  font-family:'Cormorant Garamond',serif;
  font-size:1.1rem; font-weight:500; color:#e8ecf1; line-height:1.3;
}
.pf-blog-card-desc { font-size:.82rem; color:#8892a4; line-height:1.6; flex:1; }
.pf-blog-card-tags { display:flex; flex-wrap:wrap; gap:.3rem; margin-top:.3rem; }
.pf-blog-card-tag {
  font-family:'IBM Plex Mono',monospace;
  font-size:.64rem; padding:.15rem .45rem; border-radius:3px;
  background:rgba(100,255,218,.06); color:#6a7384;
}
.pf-blog-empty {
  grid-column:1/-1; padding:3rem;
  text-align:center; color:#6a7384; font-size:.9rem;
}

/* ── Post view ── */
.pf-post-header { padding:6rem 0 2rem; }
.pf-post-meta { display:flex; gap:1rem; align-items:center; margin-bottom:1.2rem; flex-wrap:wrap; }
.pf-post-date { font-family:'IBM Plex Mono',monospace; font-size:.75rem; color:#6a7384; }
.pf-post-tags { display:flex; gap:.35rem; flex-wrap:wrap; }
.pf-post-tag {
  font-family:'IBM Plex Mono',monospace;
  font-size:.66rem; padding:.15rem .5rem; border-radius:3px;
  background:rgba(100,255,218,.06); color:#8892a4;
}
.pf-post-title {
  font-family:'Cormorant Garamond',serif;
  font-size:clamp(1.8rem,3.5vw,2.8rem);
  font-weight:500; color:#e8ecf1; line-height:1.2; margin-bottom:2.5rem;
}
.pf-post-content {
  max-width:720px;
  font-size:.95rem; line-height:1.78; color:#9aa0b0; margin-bottom:4rem;
}
.pf-post-content h1,.pf-post-content h2,.pf-post-content h3 {
  font-family:'Cormorant Garamond',serif; color:#e8ecf1;
  margin:2rem 0 .8rem; font-weight:500;
}
.pf-post-content h2 { font-size:1.5rem; }
.pf-post-content h3 { font-size:1.2rem; }
.pf-post-content p { margin-bottom:1.1rem; }
.pf-post-content ul,.pf-post-content ol { margin:0 0 1.1rem 1.4rem; }
.pf-post-content li { margin-bottom:.4rem; }
.pf-post-content strong { color:#cdd3df; }
.pf-post-content code {
  font-family:'IBM Plex Mono',monospace; font-size:.85em;
  background:rgba(100,255,218,.06); padding:.15rem .4rem;
  border-radius:3px; color:#64ffda;
}
.pf-post-content pre {
  background:rgba(0,0,0,.3); border:1px solid rgba(100,255,218,.08);
  border-radius:6px; padding:1.2rem 1.4rem; overflow-x:auto; margin-bottom:1.2rem;
}
.pf-post-content pre code { background:none; padding:0; border-radius:0; color:#9aa0b0; }
.pf-post-content blockquote {
  border-left:2px solid #64ffda; padding-left:1rem;
  color:#6a7384; font-style:italic; margin:1.2rem 0;
}
.pf-post-content a { color:#64ffda; }
.pf-post-content hr { border:none; border-top:1px solid rgba(100,255,218,.1); margin:2rem 0; }
.pf-post-loading {
  text-align:center; padding:3rem; color:#6a7384;
  font-family:'IBM Plex Mono',monospace; font-size:.85rem;
}

@media (max-width:768px) {
  .pf-blog-grid { grid-template-columns:1fr; }
}
"""


# ---------------------------------------------------------------------------
# Inline JS
# ---------------------------------------------------------------------------

def build_js(manifest: list[dict]) -> str:
    manifest_json = json.dumps(manifest, ensure_ascii=False)
    return f"""
// ── Blog manifest (embedded at build time) ──────────────────────────────────
const BLOG = {manifest_json};

// ── Utility ─────────────────────────────────────────────────────────────────
function escHtml(s) {{
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}}

// ── Nav toggle ───────────────────────────────────────────────────────────────
const navToggle = document.querySelector('.pf-nav-toggle');
const navLinks  = document.querySelector('.pf-nav-links');
navToggle?.addEventListener('click', () => navLinks.classList.toggle('open'));
document.querySelectorAll('.pf-nav-links a').forEach(a =>
  a.addEventListener('click', () => navLinks.classList.remove('open')));

// ── Scroll-reveal ────────────────────────────────────────────────────────────
const revealObs = new IntersectionObserver(
  entries => entries.forEach(e => {{ if (e.isIntersecting) e.target.classList.add('visible'); }}),
  {{ threshold: .08 }}
);
document.querySelectorAll('.reveal').forEach(el => revealObs.observe(el));

// ── Counter animation ────────────────────────────────────────────────────────
function animateCounter(el) {{
  const target = +el.dataset.count;
  const dur = 1400;
  const start = performance.now();
  const step = now => {{
    const p = Math.min((now - start) / dur, 1);
    el.textContent = Math.floor(p * p * (3 - 2 * p) * target);
    if (p < 1) requestAnimationFrame(step); else el.textContent = target;
  }};
  requestAnimationFrame(step);
}}
const ctrObs = new IntersectionObserver(entries => {{
  entries.forEach(e => {{
    if (e.isIntersecting) {{
      e.target.querySelectorAll('[data-count]').forEach(animateCounter);
      ctrObs.unobserve(e.target);
    }}
  }});
}}, {{ threshold: .3 }});
const metricsEl = document.querySelector('.pf-metrics');
if (metricsEl) ctrObs.observe(metricsEl);

// ── Active nav highlight ─────────────────────────────────────────────────────
const navAnchors = document.querySelectorAll('.pf-nav-links a');
const activeObs  = new IntersectionObserver(entries => {{
  entries.forEach(e => {{
    if (!e.isIntersecting) return;
    navAnchors.forEach(a => a.classList.remove('active'));
    const a = document.querySelector(`.pf-nav-links a[href="#${{e.target.id}}"]`);
    if (a) a.classList.add('active');
  }});
}}, {{ rootMargin: '-40% 0px -55% 0px' }});
document.querySelectorAll('[data-nav]').forEach(s => activeObs.observe(s));

// ── SPA router ───────────────────────────────────────────────────────────────
const VIEW_HOME = document.getElementById('home-view');
const VIEW_BLOG = document.getElementById('blog-view');
const VIEW_POST = document.getElementById('post-view');

function showView(name) {{
  VIEW_HOME.style.display = name === 'home' ? '' : 'none';
  VIEW_BLOG.style.display = name === 'blog' ? '' : 'none';
  VIEW_POST.style.display = name === 'post' ? '' : 'none';
  window.scrollTo(0, 0);
}}

function route() {{
  const h = location.hash;
  if (h.startsWith('#blog/')) {{
    showView('post');
    loadPost(h.slice(6));
  }} else if (h === '#blog') {{
    showView('blog');
    renderBlog();
  }} else {{
    showView('home');
    if (h && h !== '#') {{
      setTimeout(() => {{
        const el = document.querySelector(h);
        if (el) el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      }}, 50);
    }}
  }}
}}

window.addEventListener('hashchange', route);
document.addEventListener('DOMContentLoaded', route);

// Intercept "View all blog posts" without changing to a separate page
document.getElementById('view-all-blog')?.addEventListener('click', e => {{
  e.preventDefault();
  history.pushState(null, '', '#blog');
  route();
}});

// ── Blog listing ─────────────────────────────────────────────────────────────
let activeTag = null;
let searchQ   = '';

function renderBlog() {{
  const tagRow   = document.getElementById('blog-tag-row');
  const cards    = document.getElementById('blog-cards');
  if (!cards) return;

  if (tagRow && !tagRow.dataset.built) {{
    tagRow.dataset.built = '1';
    const tags = [...new Set(BLOG.flatMap(p => p.tags || []))].sort();
    tags.forEach(tag => {{
      const btn = document.createElement('button');
      btn.className = 'pf-blog-tag';
      btn.textContent = tag;
      btn.addEventListener('click', () => {{
        activeTag = activeTag === tag ? null : tag;
        tagRow.querySelectorAll('.pf-blog-tag').forEach(b => b.classList.remove('active'));
        if (activeTag) btn.classList.add('active');
        renderCards();
      }});
      tagRow.appendChild(btn);
    }});
  }}
  renderCards();
}}

function renderCards() {{
  const cards = document.getElementById('blog-cards');
  if (!cards) return;

  let posts = BLOG;
  if (activeTag) posts = posts.filter(p => (p.tags || []).includes(activeTag));
  if (searchQ)   posts = posts.filter(p =>
    p.title.toLowerCase().includes(searchQ) ||
    (p.description || '').toLowerCase().includes(searchQ)
  );

  if (!posts.length) {{
    cards.innerHTML = '<div class="pf-blog-empty">No posts match your search.</div>';
    return;
  }}

  cards.innerHTML = posts.map(p => {{
    const d = p.date ? new Date(p.date + 'T00:00:00').toLocaleDateString('en-US', {{
      year: 'numeric', month: 'short', day: 'numeric'
    }}) : '';
    const tagPills = (p.tags || []).slice(0, 4)
      .map(t => `<span class="pf-blog-card-tag">${{escHtml(t)}}</span>`).join('');
    return `<div class="pf-blog-card" onclick="location.hash='#blog/${{encodeURIComponent(p.slug)}}'">
      <div class="pf-blog-card-date">${{d}}</div>
      <div class="pf-blog-card-title">${{escHtml(p.title)}}</div>
      <div class="pf-blog-card-desc">${{escHtml(p.description || '')}}</div>
      <div class="pf-blog-card-tags">${{tagPills}}</div>
    </div>`;
  }}).join('');
}}

document.getElementById('blog-search')?.addEventListener('input', e => {{
  searchQ = e.target.value.trim().toLowerCase();
  renderCards();
}});

document.getElementById('blog-back')?.addEventListener('click', e => {{
  e.preventDefault();
  history.pushState(null, '', '#blog');
  route();
}});

// ── Post viewer ───────────────────────────────────────────────────────────────
async function loadPost(slug) {{
  const slug_dec = decodeURIComponent(slug);
  const titleEl   = document.getElementById('post-title');
  const dateEl    = document.getElementById('post-date');
  const tagsEl    = document.getElementById('post-tags');
  const contentEl = document.getElementById('post-content');

  if (titleEl)   titleEl.textContent = '';
  if (contentEl) contentEl.innerHTML = '<div class="pf-post-loading">Loading&hellip;</div>';

  const meta = BLOG.find(p => p.slug === slug_dec);
  if (meta) {{
    if (titleEl) titleEl.textContent = meta.title;
    if (dateEl)  dateEl.textContent = meta.date
      ? new Date(meta.date + 'T00:00:00').toLocaleDateString('en-US', {{
          year: 'numeric', month: 'long', day: 'numeric'
        }})
      : '';
    if (tagsEl) tagsEl.innerHTML = (meta.tags || [])
      .map(t => `<span class="pf-post-tag">${{escHtml(t)}}</span>`).join('');
  }}

  try {{
    const res = await fetch(`posts/${{slug_dec}}.md`);
    if (!res.ok) throw new Error('fetch failed');
    let md = await res.text();
    md = md.replace(/^---[\\s\\S]*?---\\n?/, '');
    contentEl.innerHTML = typeof marked !== 'undefined'
      ? marked.parse(md)
      : `<pre>${{escHtml(md)}}</pre>`;
  }} catch (_) {{
    contentEl.innerHTML = '<p style="color:#6a7384">Could not load this post.</p>';
  }}
}}

document.getElementById('post-back')?.addEventListener('click', e => {{
  e.preventDefault();
  history.pushState(null, '', '#blog');
  route();
}});
"""


# ---------------------------------------------------------------------------
# Main assembler
# ---------------------------------------------------------------------------

def build() -> None:
    site_fm, _ = parse_fm(read(BASE / "content/site.md"))

    css = read(BASE / "css/portfolio.css")
    manifest = build_manifest()

    # Write updated posts/index.json
    (BASE / "posts/index.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    hero_html      = build_hero()
    work_html      = build_work()
    recog_html     = build_recognition()
    writing_html   = build_writing()
    research_html  = build_research()
    speaking_html  = build_speaking()
    community_html = build_community()
    education_html = build_education()
    contact_html   = build_contact()
    js             = build_js(manifest)

    # Site metadata
    title    = esc(site_fm.get("title", "Dr. Soumya Maity"))
    desc     = esc(site_fm.get("description", ""))
    og_title = esc(site_fm.get("og_title", ""))
    og_desc  = esc(site_fm.get("og_description", ""))
    og_image = esc(site_fm.get("og_image", "assets/images/author/maity.png"))
    og_url   = esc(site_fm.get("og_url", "https://smaity.co.in"))
    domain   = esc(site_fm.get("domain", "smaity.co.in"))
    favicon  = esc(site_fm.get("favicon", "assets/images/site/favicon.png"))
    footer_t = esc(site_fm.get("footer", "© 2025 Dr. Soumya Maity · Bengaluru, India"))
    footer_t = footer_t.replace("&amp;middot;", "&middot;")

    footer_html = f"""<footer class="pf-footer pf-wrap">
  <span>{footer_t}</span>
  <span class="pf-footer-domain">{domain}</span>
</footer>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <meta property="og:title" content="{og_title}">
  <meta property="og:type" content="website">
  <meta property="og:description" content="{og_desc}">
  <meta property="og:image" content="{og_image}">
  <meta property="og:url" content="{og_url}">
  <link rel="icon" href="{favicon}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=IBM+Plex+Sans:wght@300;400;500&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
{css}
{EXTRA_CSS}
  </style>
</head>
<body>

<nav class="pf-nav">
  <a href="#" class="pf-nav-brand">Dr. Soumya <span class="accent">Maity</span></a>
  <button class="pf-nav-toggle" aria-label="Toggle navigation">&#9776;</button>
  <ul class="pf-nav-links">
    <li><a href="#work">Work</a></li>
    <li><a href="#writing">Writing</a></li>
    <li><a href="#research">Research</a></li>
    <li><a href="#speaking">Speaking</a></li>
    <li><a href="#blog">Blog</a></li>
    <li><a href="#contact" class="nav-contact">Contact</a></li>
  </ul>
</nav>

<!-- ═══════════════════════════════════════════════════════════
     HOME VIEW  (default — all sections scroll normally)
═══════════════════════════════════════════════════════════ -->
<div id="home-view" class="spa-view">

{hero_html}

{work_html}

{recog_html}

{writing_html}

{research_html}

{speaking_html}

{community_html}

{education_html}

{contact_html}

{footer_html}
</div>

<!-- ═══════════════════════════════════════════════════════════
     BLOG VIEW  (#blog)
═══════════════════════════════════════════════════════════ -->
<div id="blog-view" class="spa-view">
  <div class="pf-wrap">
    <div class="pf-blog-header">
      <a href="#" id="blog-back" class="pf-blog-back">&larr; Back to home</a>
      <h1 class="pf-blog-title">All Writing</h1>
      <div class="pf-blog-search-row">
        <input id="blog-search" class="pf-blog-search" type="search"
               placeholder="Search {len(manifest)} posts&hellip;" autocomplete="off">
      </div>
      <div id="blog-tag-row" class="pf-blog-filter-row"></div>
    </div>
    <div id="blog-cards" class="pf-blog-grid"></div>
  </div>
  {footer_html}
</div>

<!-- ═══════════════════════════════════════════════════════════
     POST VIEW  (#blog/<slug>)
═══════════════════════════════════════════════════════════ -->
<div id="post-view" class="spa-view">
  <div class="pf-wrap">
    <div class="pf-post-header">
      <a href="#" id="post-back" class="pf-post-back">&larr; All posts</a>
      <div class="pf-post-meta">
        <span id="post-date" class="pf-post-date"></span>
        <div id="post-tags" class="pf-post-tags"></div>
      </div>
      <h1 id="post-title" class="pf-post-title"></h1>
    </div>
    <div id="post-content" class="pf-post-content"></div>
  </div>
  {footer_html}
</div>

<script>
{js}
</script>
</body>
</html>"""

    out = BASE / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"✓  Built {out}  ({len(html):,} bytes, {len(manifest)} blog posts)")


if __name__ == "__main__":
    build()
