#!/usr/bin/env python3
"""
import_linkedin.py — turn a LinkedIn post or article into a blog post here.

    python tools/import_linkedin.py <linkedin-url>

The post is fetched, converted to markdown, and saved in content/blog/
with the ORIGINAL publication timestamp (decoded from the LinkedIn
activity ID, accurate to the millisecond) and `source:` pointing back
to LinkedIn. Manifests are regenerated automatically.

LinkedIn sometimes blocks anonymous fetches. If that happens, open the
post in your browser, save the page (Ctrl+S, "Webpage, HTML Only"),
then run:

    python tools/import_linkedin.py <linkedin-url> --file saved.html

Options:
    --file PATH    read a saved HTML file instead of fetching the URL
    --title TEXT   override the generated title
    --tags a,b,c   extra tags (hashtags in the post are picked up too)
    --dry-run      print the markdown instead of writing the file
"""
import argparse
import html as htmllib
import json
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IST = timezone(timedelta(hours=5, minutes=30))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


# ---------------------------------------------------------------- timestamp

def activity_id_from(text: str):
    """Find a 19-digit LinkedIn activity/ugcPost ID in a URL or page."""
    m = re.search(r"(?:activity|ugcPost|share)[:%-](\d{19})", text)
    return int(m.group(1)) if m else None


def timestamp_from_activity_id(activity_id: int) -> datetime:
    """The top 41 bits of a LinkedIn activity ID are the epoch millis."""
    ms = activity_id >> 22
    return datetime.fromtimestamp(ms / 1000, tz=IST)


# ---------------------------------------------------------------- HTML → MD

class HTML2MD(HTMLParser):
    SKIP = {"script", "style", "noscript", "head"}
    BLOCK = {"p", "div", "section", "article", "br", "tr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip_depth = 0
        self.href = None

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag in ("strong", "b"):
            self.out.append("**")
        elif tag in ("em", "i"):
            self.out.append("*")
        elif tag == "a":
            self.href = dict(attrs).get("href", "")
            self.out.append("[")
        elif tag == "li":
            self.out.append("\n- ")
        elif re.fullmatch(r"h[1-6]", tag):
            self.out.append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag == "code":
            self.out.append("`")
        elif tag in self.BLOCK:
            self.out.append("\n\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
            return
        if tag in ("strong", "b"):
            self.out.append("**")
        elif tag in ("em", "i"):
            self.out.append("*")
        elif tag == "a":
            self.out.append("](" + (self.href or "") + ")")
            self.href = None
        elif tag == "code":
            self.out.append("`")
        elif re.fullmatch(r"h[1-6]", tag) or tag in ("p", "ul", "ol"):
            self.out.append("\n\n")

    def handle_data(self, data):
        if not self.skip_depth:
            self.out.append(data)

    def markdown(self) -> str:
        text = "".join(self.out)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" ?\n ?", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def html_to_md(fragment: str) -> str:
    p = HTML2MD()
    p.feed(fragment)
    return p.markdown()


# ---------------------------------------------------------------- extraction

def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def json_ld_blocks(page: str):
    for m in re.finditer(
            r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            page, re.DOTALL | re.IGNORECASE):
        try:
            data = json.loads(htmllib.unescape(m.group(1)))
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict):
                yield item


def meta_content(page: str, *names):
    for name in names:
        m = re.search(
            r'<meta[^>]+(?:property|name)=["\']' + re.escape(name) +
            r'["\'][^>]+content=["\'](.*?)["\']', page, re.IGNORECASE | re.DOTALL)
        if m:
            return htmllib.unescape(m.group(1)).strip()
    return ""


def voyager_commentary(page: str) -> str:
    """Public post pages embed the full post text in voyager JSON."""
    best = ""
    for m in re.finditer(r'"commentary"\s*:\s*\{', page):
        chunk = page[m.end() - 1: m.end() + 20000]
        t = re.search(r'"text"\s*:\s*"((?:[^"\\]|\\.)*)"', chunk)
        if t:
            try:
                text = json.loads('"' + t.group(1) + '"')
            except json.JSONDecodeError:
                continue
            if len(text) > len(best):
                best = text
    return best


def extract(page: str, url: str):
    """Return (title, body_markdown, date_iso_or_None)."""
    title, body, date_pub = "", "", None

    # 1. JSON-LD (LinkedIn articles / pulse posts)
    for item in json_ld_blocks(page):
        t = item.get("headline") or item.get("name") or ""
        b = item.get("articleBody") or ""
        d = item.get("datePublished") or item.get("dateCreated")
        if b and len(b) > len(body):
            title, body, date_pub = t or title, b, d or date_pub
        elif d and not date_pub:
            date_pub = d

    # 2. voyager JSON commentary (feed posts)
    if len(body) < 200:
        v = voyager_commentary(page)
        if len(v) > len(body):
            body = v

    # 3. og: meta fallback (often truncated, but better than nothing)
    og_title = meta_content(page, "og:title", "twitter:title")
    og_desc = meta_content(page, "og:description", "description")
    if not body and og_desc:
        body = og_desc
    if not title and og_title:
        title = og_title

    # If body looks like HTML, convert it; otherwise keep as text
    if "<" in body and re.search(r"</?\w+", body):
        body = html_to_md(body)
    body = body.replace("\\n", "\n")
    # LinkedIn renders hashtags as "hashtag#word" in scraped text
    body = re.sub(r"hashtag#(\w)", r"#\1", body)
    # collapse single newlines into paragraphs
    body = re.sub(r"\r\n", "\n", body).strip()

    # Clean LinkedIn boilerplate from og titles: "Name on LinkedIn: text"
    title = re.sub(r"\s*\|\s*LinkedIn\s*$", "", title)
    m = re.match(r".{0,60}? on LinkedIn:?\s*(.+)", title)
    if m:
        title = m.group(1).strip()
    title = title.strip().strip('"')

    return title, body, date_pub


def hashtags(text: str):
    return list(dict.fromkeys(re.findall(r"#(\w[\w-]{1,40})", text)))


def slugify(title: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", title).strip("-")
    return s[:80] or "linkedin-post"


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description="Import a LinkedIn post as a blog entry.")
    ap.add_argument("url", help="LinkedIn post / article URL")
    ap.add_argument("--file", help="saved HTML file (when LinkedIn blocks fetching)")
    ap.add_argument("--title", help="override the title")
    ap.add_argument("--tags", default="", help="extra comma-separated tags")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.file:
        page = Path(args.file).read_text(encoding="utf-8", errors="replace")
    else:
        try:
            page = fetch(args.url)
        except Exception as e:
            print(f"Could not fetch the page ({e}).")
            print("LinkedIn often blocks anonymous requests. Open the post in your")
            print('browser, save it with Ctrl+S ("Webpage, HTML Only"), then run:')
            print(f'  python tools/import_linkedin.py "{args.url}" --file saved.html')
            return 1

    if "authwall" in page[:4000].lower() and not args.file:
        print("LinkedIn returned its login wall instead of the post.")
        print('Save the post page from your browser (Ctrl+S, "Webpage, HTML Only") and rerun with --file saved.html')
        return 1

    title, body, date_pub = extract(page, args.url)

    # Exact original timestamp: decoded from the activity ID when present
    aid = activity_id_from(args.url) or activity_id_from(page)
    if aid:
        when = timestamp_from_activity_id(aid)
    elif date_pub:
        try:
            when = datetime.fromisoformat(date_pub.replace("Z", "+00:00")).astimezone(IST)
        except ValueError:
            when = datetime.now(IST)
    else:
        when = datetime.now(IST)
        print("Warning: could not determine the original post time; using now.")

    if args.title:
        title = args.title
    if not title:
        first = re.split(r"[.\n!?]", body.strip(), 1)[0]
        title = (first[:77] + "…") if len(first) > 78 else first or "LinkedIn post"

    if not body:
        print("Could not extract any post text. Try saving the page and using --file.")
        return 1

    tags = ["LinkedIn"] + hashtags(body) + [t.strip() for t in args.tags.split(",") if t.strip()]
    tags = list(dict.fromkeys(tags))
    description = re.sub(r"\s+", " ", re.sub(r"[#*`\[\]]", "", body))[:160].strip()

    fm_lines = [
        "---",
        f"title: {title}",
        f"date: {when.strftime('%Y-%m-%d %H:%M:%S%z')}",
        f"description: {description}",
        "tags:",
        *[f"  - {t}" for t in tags],
        f"source: {args.url}",
        "source_name: LinkedIn",
        "---",
        "",
        body,
        "",
    ]
    doc = "\n".join(fm_lines)

    if args.dry_run:
        print(doc)
        return 0

    out = ROOT / "content" / "blog" / f"{when.strftime('%Y-%m-%d')}-{slugify(title)}.md"
    if out.exists():
        print(f"Refusing to overwrite existing file: {out}")
        return 1
    out.write_text(doc, encoding="utf-8")
    print(f"Created {out.relative_to(ROOT)}")
    print(f"Original post time: {when.isoformat()}")
    subprocess.run([sys.executable, str(ROOT / "tools" / "build.py")], check=False)
    print("Done — review the file, then push to PreProduction to publish.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
