/* ============================================================
   smaity.co.in — site engine ("The Monograph" edition)
   Renders every page from markdown files in content/.
   Pages are selected by <body data-page="home|blog|post|learning">.
   ============================================================ */

(function () {
  'use strict';

  /* ---------------- utilities ---------------- */

  async function fetchText(path) {
    const res = await fetch(path, { cache: 'no-cache' });
    if (!res.ok) throw new Error(path + ' → HTTP ' + res.status);
    return res.text();
  }

  async function fetchJSON(path) {
    const res = await fetch(path, { cache: 'no-cache' });
    if (!res.ok) throw new Error(path + ' → HTTP ' + res.status);
    return res.json();
  }

  /* Parse YAML-ish frontmatter: top-level `key: value` pairs and
     `key:` followed by `- item` lists. Nested maps are ignored. */
  function parseFrontmatter(text) {
    const m = text.match(/^---\s*\r?\n([\s\S]*?)\r?\n---\s*\r?\n?([\s\S]*)$/);
    if (!m) return { fm: {}, body: text.trim() };
    const fm = {};
    const lines = m[1].split(/\r?\n/);
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (/^\s/.test(line)) continue;           // nested / indented → skip
      const kv = line.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
      if (!kv) continue;
      const key = kv[1];
      let val = kv[2].trim().replace(/^["']|["']$/g, '');
      if (val === '') {
        const list = [];
        let j = i + 1;
        while (j < lines.length && /^\s*-\s+/.test(lines[j])) {
          list.push(lines[j].replace(/^\s*-\s+/, '').trim().replace(/^["']|["']$/g, ''));
          j++;
        }
        if (list.length) { fm[key] = list; i = j - 1; continue; }
      }
      if (val.startsWith('[') && val.endsWith(']')) {
        fm[key] = val.slice(1, -1).split(',').map(s => s.trim().replace(/^["']|["']$/g, '')).filter(Boolean);
      } else {
        fm[key] = val;
      }
    }
    return { fm, body: m[2].trim() };
  }

  function stripComments(s) {
    return s.replace(/<!--[\s\S]*?-->/g, '').trim();
  }

  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function mdInline(s) { return marked.parseInline(s); }
  function md(s) { return marked.parse(s); }

  const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];

  function fmtDate(iso) {
    if (!iso) return '';
    const m = String(iso).match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (!m) return String(iso);
    return parseInt(m[3], 10) + ' ' + MONTHS[parseInt(m[2], 10) - 1].slice(0, 3) + ' ' + m[1];
  }

  function monthKey(iso) {
    const m = String(iso).match(/^(\d{4})-(\d{2})/);
    if (!m) return '';
    return MONTHS[parseInt(m[2], 10) - 1] + ' ' + m[1];
  }

  function yearKey(iso) {
    const m = String(iso).match(/^(\d{4})/);
    return m ? m[1] : '';
  }

  function safeSlug(s) {
    if (!s) return '';
    return s.replace(/[\\/]|\.\./g, '');
  }

  /* Non-comment, non-empty body lines */
  function bodyLines(body) {
    return stripComments(body).split(/\r?\n/).map(l => l.trim()).filter(Boolean);
  }

  /* Parse "### Title" card blocks: { title, desc[], pills[] } */
  function parseCards(body) {
    const cards = [];
    let cur = null;
    for (const line of bodyLines(body)) {
      if (line.startsWith('### ')) {
        cur = { title: line.slice(4).trim(), desc: [], pills: [] };
        cards.push(cur);
      } else if (!cur) {
        continue;
      } else if (/^Tags:/i.test(line)) {
        cur.pills = line.replace(/^Tags:\s*/i, '').split('|').map(s => s.trim()).filter(Boolean);
      } else if (/^\[[^\]]+\]/.test(line) && /\]$/.test(line)) {
        const found = line.match(/\[([^\]]+)\]/g) || [];
        cur.pills = found.map(p => p.slice(1, -1));
      } else {
        cur.desc.push(line);
      }
    }
    return cards;
  }

  function paragraphs(body) {
    return stripComments(body).split(/\r?\n\s*\r?\n/).filter(p => p.trim())
      .map(p => '<p>' + mdInline(p.replace(/\r?\n/g, ' ')) + '</p>').join('');
  }

  /* ---------------- shared chrome ---------------- */

  function initNav() {
    const toggle = document.querySelector('.nav-toggle');
    const links = document.getElementById('nav-links');
    if (toggle && links) {
      toggle.addEventListener('click', () => links.classList.toggle('open'));
      links.addEventListener('click', e => {
        if (e.target.tagName === 'A') links.classList.remove('open');
      });
    }
  }

  function initReveal() {
    const obs = new IntersectionObserver(entries => {
      entries.forEach(en => {
        if (en.isIntersecting) { en.target.classList.add('visible'); obs.unobserve(en.target); }
      });
    }, { threshold: 0.06 });
    document.querySelectorAll('.reveal').forEach(el => obs.observe(el));
  }

  function initCounters() {
    const obs = new IntersectionObserver(entries => {
      entries.forEach(en => {
        if (!en.isIntersecting) return;
        obs.unobserve(en.target);
        const el = en.target;
        const target = parseInt(el.dataset.count, 10) || 0;
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
          el.textContent = target;
          return;
        }
        const dur = 1400, t0 = performance.now();
        (function tick(t) {
          const p = Math.min((t - t0) / dur, 1);
          el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
          if (p < 1) requestAnimationFrame(tick);
        })(t0);
      });
    }, { threshold: 0.4 });
    document.querySelectorAll('[data-count]').forEach(el => obs.observe(el));
  }

  async function loadFooter() {
    try {
      const { fm } = parseFrontmatter(await fetchText('content/site.md'));
      if (fm.footer) {
        document.querySelectorAll('#footer-text').forEach(el => { el.innerHTML = mdInline(fm.footer); });
      }
      const dom = document.getElementById('footer-domain');
      if (dom && fm.domain) dom.textContent = fm.domain;
    } catch (e) { /* fall back to static footer */ }
  }

  function tags(list) {
    return (list || []).map(t => '<span class="tag">' + mdInline(t) + '</span>').join('');
  }

  /* ============================================================
     HOME PAGE
     ============================================================ */

  /* "01 — Current focus" → kicker "Current focus"; the big number
     comes from a CSS counter, so chapters renumber automatically. */
  function chapterHead(fm) {
    const kicker = String(fm.label || '').split('—').pop().trim();
    return '<div class="chapter-rail"><div class="chapter-marker">' +
             '<span class="chapter-kicker kicker">' + mdInline(kicker) + '</span>' +
           '</div></div>' +
           '<div class="chapter-body"><h2 class="chapter-title">' + mdInline(fm.title || '') + '</h2>';
  }

  async function renderHero() {
    const { fm, body } = parseFrontmatter(await fetchText('content/profile/hero.md'));
    const paras = stripComments(body).split(/\r?\n\s*\r?\n/).filter(p => p.trim());
    let metrics = '';
    for (let i = 1; i <= 8; i++) {
      if (!fm['m' + i + '_label']) continue;
      metrics +=
        '<div class="metric"><div class="metric-value"><span data-count="' + esc(fm['m' + i + '_count'] || 0) + '">0</span>' +
        '<span class="suffix">' + esc(fm['m' + i + '_suffix'] || '') + '</span></div>' +
        '<div class="metric-label">' + mdInline(fm['m' + i + '_label']) + '</div></div>';
    }

    // social-proof strip: venues pulled from the speaking section
    let proof = '';
    try {
      const sp = parseFrontmatter(await fetchText('content/profile/speaking.md'));
      const line = bodyLines(sp.body).find(l => l.includes('|')) || '';
      const venues = line.split('|').map(s => s.trim()).filter(Boolean);
      if (venues.length) {
        proof =
          '<div class="proof-strip cover-anim cover-anim-5">' +
            '<div class="proof-label">Speaker &amp; contributor at</div>' +
            '<div class="proof-names">' + venues.map(v => '<span>' + mdInline(v) + '</span>').join('') + '</div>' +
          '</div>';
      }
    } catch (e) { /* optional */ }

    document.getElementById('mount-hero').innerHTML =
      '<div class="hero-grid">' +
        '<div>' +
          (fm.eyebrow ? '<div class="cover-anim cover-anim-1"><span class="hero-eyebrow">' + mdInline(fm.eyebrow) + '</span></div>' : '') +
          '<h1 class="hero-name cover-anim cover-anim-2">' + mdInline(fm.headline || '') + '</h1>' +
          (fm.tagline ? '<p class="hero-tagline cover-anim cover-anim-2">' + mdInline(fm.tagline) + '</p>' : '') +
          '<div class="lede cover-anim cover-anim-3">' + paras.map(p => '<p>' + mdInline(p.replace(/\r?\n/g, ' ')) + '</p>').join('') + '</div>' +
          (Array.isArray(fm.expertise) && fm.expertise.length
            ? '<div class="expertise cover-anim cover-anim-3">' + fm.expertise.map(x => '<span class="chip">' + mdInline(x) + '</span>').join('') + '</div>'
            : '') +
          '<div class="cover-actions cover-anim cover-anim-4">' +
            '<a href="#contact" class="btn btn-fill">Get in touch</a>' +
            (fm.cv_href ? '<a href="' + esc(fm.cv_href) + '" class="btn" target="_blank" rel="noopener">Printable Profile</a>' : '') +
            '<a href="blog.html" class="btn">Read my writing</a>' +
          '</div>' +
        '</div>' +
        (fm.photo ? '<div class="hero-photo-wrap cover-anim cover-anim-3"><img class="hero-photo" src="' + esc(fm.photo) + '" alt="' + esc(fm.headline || 'Portrait') + '"></div>' : '') +
      '</div>' +
      (metrics ? '<div class="colophon cover-anim cover-anim-5"><div class="colophon-inner">' + metrics + '</div></div>' : '') +
      proof;
    initCounters();
  }

  async function renderWork() {
    const head = parseFrontmatter(await fetchText('content/projects/_index.md')).fm;
    let cards = [];
    try {
      const manifest = await fetchJSON('content/projects/index.json');
      cards = await Promise.all(manifest.map(async p => {
        const { fm, body } = parseFrontmatter(await fetchText('content/projects/' + safeSlug(p.slug) + '.md'));
        return { fm, body };
      }));
    } catch (e) { /* no projects yet */ }
    const html = cards.map(c =>
      '<li class="now-item' + (String(c.fm.featured) === 'true' ? ' featured' : '') + '">' +
        '<div class="now-side"><span class="kicker">' + mdInline(c.fm.label || '') + '</span></div>' +
        '<div><div class="now-title">' + mdInline(c.fm.title || '') + '</div>' +
        '<div class="now-body">' + paragraphs(c.body) + '</div></div>' +
      '</li>'
    ).join('');
    document.getElementById('mount-work').innerHTML =
      chapterHead(head) + '<ul class="now-list">' + html + '</ul></div>';
  }

  async function renderWriting() {
    const { fm, body } = parseFrontmatter(await fetchText('content/profile/writing.md'));
    let latest = [];
    let total = 0;
    try {
      const manifest = await fetchJSON('content/blog/index.json');
      latest = manifest.slice(0, parseInt(fm.latest_posts, 10) || 3);
      total = manifest.length;
    } catch (e) { /* manifest missing */ }
    const upcoming = parseCards(body);

    const cards = latest.map(p =>
      '<a class="wcard" href="post.html?slug=' + encodeURIComponent(p.slug) + '">' +
        '<div class="wcard-date">' + fmtDate(p.date) + '</div>' +
        '<div class="wcard-title">' + esc(p.title) + '</div>' +
        (p.description ? '<div class="wcard-desc">' + esc(p.description) + '</div>' : '') +
        ((p.tags || []).length ? '<div class="ledger-tags">' + tags(p.tags.slice(0, 3)) + '</div>' : '') +
        '<span class="wcard-more">Read &rarr;</span>' +
      '</a>').join('');

    const pipeline = upcoming.map(c => {
      const tg = c.pills.filter(p => p.toLowerCase() !== 'coming-soon');
      return '<li class="pipeline-item">' +
        '<span class="tag-soon">Coming soon</span>' +
        '<div><span class="pipeline-title">' + mdInline(c.title) + '</span>' +
        (tg.length ? '<span class="pipeline-tags">' + tags(tg) + '</span>' : '') + '</div></li>';
    }).join('');

    document.getElementById('mount-writing').innerHTML =
      chapterHead(fm) +
      '<div class="writing-grid">' + cards + '</div>' +
      (pipeline ? '<div class="pipeline"><div class="pipeline-label">In the pipeline</div><ul>' + pipeline + '</ul></div>' : '') +
      '<div class="chapter-cta"><a href="blog.html" class="btn">View all ' + (total ? total + ' ' : '') + 'posts &rarr;</a></div></div>';
  }

  async function renderResearch() {
    const { fm, body } = parseFrontmatter(await fetchText('content/profile/research.md'));
    const cols = [];
    let cur = null;
    for (const line of bodyLines(body)) {
      if (line.startsWith('## ')) { cur = { title: line.slice(3).trim(), items: [], note: '' }; cols.push(cur); }
      else if (!cur) continue;
      else if (line.startsWith('- ')) cur.items.push(line.slice(2).trim());
      else if (/^\*.+\*$/.test(line)) cur.note = line.replace(/^\*|\*$/g, '');
    }
    const html = cols.map(c =>
      '<div class="research-col"><h3>' + mdInline(c.title) + '</h3>' +
      '<ul class="research-list">' + c.items.map(i => '<li>' + mdInline(i) + '</li>').join('') + '</ul>' +
      (c.note ? '<div class="research-more">' + mdInline(c.note) + '</div>' : '') + '</div>'
    ).join('');
    document.getElementById('mount-research').innerHTML =
      chapterHead(fm) + '<div class="research-grid">' + html + '</div></div>';
  }

  async function renderSpeaking() {
    const { fm, body } = parseFrontmatter(await fetchText('content/profile/speaking.md'));
    const venueLine = bodyLines(body).find(l => l.includes('|')) || '';
    const venues = venueLine.split('|').map(s => s.trim()).filter(Boolean);
    document.getElementById('mount-speaking').innerHTML =
      chapterHead(fm) +
      '<div class="speaking-grid">' +
        '<div class="speaking-stat">' +
          '<div class="speaking-figure">' +
            '<span class="speaking-number">' + esc(fm.count || '') + '</span>' +
            '<span class="speaking-label">' + mdInline(fm.count_label || '') + '</span>' +
          '</div>' +
          (fm.note ? '<p class="speaking-note">' + mdInline(fm.note) + '</p>' : '') +
          '<div class="speaking-cta"><a href="#contact" class="btn btn-fill">Invite me to speak</a></div>' +
        '</div>' +
        '<div><div class="venue-head">Venues &amp; forums</div>' +
        '<div class="venue-index">' + venues.map(v => '<div class="venue">' + mdInline(v) + '</div>').join('') + '</div></div>' +
      '</div></div>';
  }

  async function renderCommunity() {
    const { fm, body } = parseFrontmatter(await fetchText('content/profile/community.md'));
    const cards = parseCards(body);
    const html = cards.map(c =>
      '<li class="community-item">' +
        '<div class="community-name">' + mdInline(c.title) + '</div>' +
        '<div><div class="community-body">' + mdInline(c.desc.join(' ')) + '</div>' +
        '<div class="community-tags">' + tags(c.pills) + '</div></div>' +
      '</li>'
    ).join('');
    document.getElementById('mount-community').innerHTML =
      chapterHead(fm) + '<ul class="community-list">' + html + '</ul></div>';
  }

  /* Recognition + Education side by side — credentials at a glance */
  async function renderCredentials() {
    const rec = parseFrontmatter(await fetchText('content/profile/recognition.md'));
    const edu = parseFrontmatter(await fetchText('content/profile/education.md'));

    const recRows = bodyLines(rec.body).map(line => {
      const parts = line.split('|').map(s => s.trim());
      if (parts.length < 3) return '';
      const latest = (parts[3] || '').toUpperCase() === 'LATEST';
      return '<li class="cred-row"><span class="cred-year">' + esc(parts[0]) + '</span><div>' +
        '<div class="cred-name">' + mdInline(parts[1]) + (latest ? '<span class="badge-latest">Latest</span>' : '') + '</div>' +
        '<div class="cred-sub">' + mdInline(parts[2]) + '</div>' +
        '</div></li>';
    }).join('');

    const eduRows = bodyLines(edu.body).map(line => {
      const parts = line.split('|').map(s => s.trim());
      if (parts.length < 3) return '';
      return '<li class="cred-row"><span class="cred-year">' + esc(parts[0]) + '</span><div>' +
        '<div class="cred-name">' + mdInline(parts[1]) + '</div>' +
        '<div class="cred-sub">' + mdInline(parts[2]) + '</div>' +
        (parts[3] ? '<div class="cred-detail">' + mdInline(parts[3]) + '</div>' : '') +
        '</div></li>';
    }).join('');

    const head = {
      label: (rec.fm.label || 'Recognition') + ' & Education',
      title: (rec.fm.title || 'Recognition') + ' &amp; ' + (edu.fm.title || 'Education')
    };
    document.getElementById('mount-credentials').innerHTML =
      chapterHead(head) +
      '<div class="cred-grid">' +
        '<div class="cred-col"><h3>' + mdInline(rec.fm.title || 'Recognition') + '</h3><ul>' + recRows + '</ul></div>' +
        '<div class="cred-col"><h3>' + mdInline(edu.fm.title || 'Education') + '</h3><ul>' + eduRows + '</ul></div>' +
      '</div></div>';
  }

  async function renderContact() {
    const { fm, body } = parseFrontmatter(await fetchText('content/profile/contact.md'));
    const links = bodyLines(body).map(line => {
      const parts = line.split('|').map(s => s.trim());
      if (parts.length < 3) return '';
      const ext = /^https?:/.test(parts[2]);
      return '<li><a class="contact-link" href="' + esc(parts[2]) + '"' + (ext ? ' target="_blank" rel="noopener"' : '') + '>' +
        '<span class="contact-type">' + esc(parts[0]) + '</span>' +
        '<span class="contact-value">' + esc(parts[1]) + '</span>' +
        '<span class="contact-arrow">&rarr;</span></a></li>';
    }).join('');
    document.getElementById('mount-contact').innerHTML =
      '<div class="chapter-rail"><div class="chapter-marker">' +
        '<span class="chapter-kicker kicker">Contact</span></div></div>' +
      '<div class="chapter-body">' +
        '<h2 class="contact-head">' + mdInline(fm.headline || '') + '</h2>' +
        '<p class="contact-sub">' + mdInline(fm.subtext || '') + '</p>' +
        '<ul class="contact-links">' + links + '</ul></div>';
  }

  async function pageHome() {
    const jobs = [
      renderHero(), renderWork(), renderWriting(), renderResearch(),
      renderSpeaking(), renderCommunity(), renderCredentials(),
      renderContact(), loadFooter()
    ];
    const results = await Promise.allSettled(jobs);
    results.forEach(r => { if (r.status === 'rejected') console.error(r.reason); });
    initReveal();
    // honour deep links (#research etc.) now that the sections exist
    if (location.hash) {
      const target = document.querySelector(location.hash);
      if (target) target.scrollIntoView();
    }
  }

  /* ============================================================
     THE LEDGER  (blog.html)
     ============================================================ */

  async function pageBlog() {
    loadFooter();
    const listEl = document.getElementById('post-list');
    const countEl = document.getElementById('result-count');
    const tagsEl = document.getElementById('tag-filters');
    const searchEl = document.getElementById('search-input');

    let posts = [];
    try {
      posts = await fetchJSON('content/blog/index.json');
    } catch (e) {
      listEl.innerHTML = '<li class="loading">Could not load posts (run the local server, not file://)</li>';
      return;
    }
    // entry numbers: oldest = № 001, newest = № <total>
    posts.forEach((p, i) => { p.no = posts.length - i; });

    // tag cloud — case-insensitive dedupe, most frequent first
    const tagCount = new Map();
    posts.forEach(p => (p.tags || []).forEach(t => {
      const k = t.toLowerCase();
      const e = tagCount.get(k) || { label: t, n: 0 };
      e.n++; tagCount.set(k, e);
    }));
    const topTags = [...tagCount.entries()].sort((a, b) => b[1].n - a[1].n).slice(0, 14);

    let activeTag = null;
    let query = '';

    tagsEl.innerHTML = '<button class="tag-filter active" data-tag="">All</button>' +
      topTags.map(([k, e]) => '<button class="tag-filter" data-tag="' + esc(k) + '">' + esc(e.label) + '</button>').join('');

    tagsEl.addEventListener('click', e => {
      const btn = e.target.closest('.tag-filter');
      if (!btn) return;
      activeTag = btn.dataset.tag || null;
      tagsEl.querySelectorAll('.tag-filter').forEach(b => b.classList.toggle('active', b === btn));
      render();
    });

    searchEl.addEventListener('input', () => { query = searchEl.value.trim().toLowerCase(); render(); });

    function matches(p) {
      if (activeTag && !(p.tags || []).some(t => t.toLowerCase() === activeTag)) return false;
      if (!query) return true;
      const hay = (p.title + ' ' + (p.description || '') + ' ' + (p.tags || []).join(' ')).toLowerCase();
      return query.split(/\s+/).every(w => hay.includes(w));
    }

    function pad3(n) { return String(n).padStart(3, '0'); }

    function render() {
      const shown = posts.filter(matches);
      countEl.textContent = shown.length + ' of ' + posts.length + ' entries';
      let html = '';
      let lastYear = '';
      for (const p of shown) {
        const y = yearKey(p.date);
        if (y && y !== lastYear) {
          html += '<li class="ledger-year-head"><span class="year-figure">' + esc(y) + '</span></li>';
          lastYear = y;
        }
        html +=
          '<li class="ledger-row">' +
            '<span class="ledger-date"><span class="ledger-no">&#8470; ' + pad3(p.no) + '</span><br>' + fmtDate(p.date) + '</span>' +
            '<div><a class="ledger-link" href="post.html?slug=' + encodeURIComponent(p.slug) + '"></a>' +
              '<div class="ledger-title">' + esc(p.title) + '</div>' +
              (p.description && p.description.toLowerCase() !== p.title.toLowerCase()
                ? '<div class="ledger-desc">' + esc(p.description) + '</div>' : '') +
              ((p.tags || []).length ? '<div class="ledger-tags">' + tags(p.tags.slice(0, 5)) + '</div>' : '') +
            '</div><span class="ledger-arrow">&rarr;</span></li>';
      }
      listEl.innerHTML = html || '<li class="loading">Nothing in the ledger matches</li>';
    }
    render();
  }

  /* ============================================================
     READING PAGE  (post.html)
     ============================================================ */

  async function pagePost() {
    loadFooter();
    const params = new URLSearchParams(location.search);
    const slug = safeSlug(params.get('slug') || '');
    const from = params.get('from') === 'learning' ? 'learning' : 'blog';
    const titleEl = document.getElementById('post-title');
    const metaEl = document.getElementById('post-meta');
    const tagsEl = document.getElementById('post-tags');
    const contentEl = document.getElementById('post-content');
    const backEl = document.getElementById('back-link');

    if (from === 'learning') { backEl.href = 'learning.html'; backEl.innerHTML = '&larr; All learning notes'; }

    if (!slug) { titleEl.textContent = 'Post not found'; contentEl.innerHTML = ''; return; }

    try {
      const raw = await fetchText('content/' + from + '/' + encodeURIComponent(slug) + '.md');
      const { fm, body } = parseFrontmatter(raw);
      const title = fm.title || slug.replace(/-/g, ' ');
      document.title = title + ' | Dr. Soumya Maity';
      titleEl.textContent = title;

      const words = body.split(/\s+/).length;
      let meta = '<span>' + fmtDate(fm.date) + '</span><span>' + Math.max(1, Math.round(words / 200)) + ' min read</span>';
      if (fm.source) meta += '<a href="' + esc(fm.source) + '" target="_blank" rel="noopener">Originally on ' + esc(fm.source_name || 'LinkedIn') + ' &rarr;</a>';
      metaEl.innerHTML = meta;

      const tagList = Array.isArray(fm.tags) ? fm.tags : (fm.tags ? [fm.tags] : []);
      tagsEl.innerHTML = tags(tagList);

      const heroEl = document.getElementById('post-hero');
      if (heroEl && fm.hero) {
        // bare paths (e.g. images/slug.svg) are relative to the post's folder
        const src = /^(https?:)?\//.test(fm.hero) || fm.hero.startsWith('assets/')
          ? fm.hero : 'content/' + from + '/' + fm.hero;
        heroEl.src = src;
        heroEl.alt = title;
        heroEl.hidden = false;
        heroEl.onerror = () => { heroEl.hidden = true; };
      }

      contentEl.innerHTML = md(body);
    } catch (e) {
      titleEl.textContent = 'Post not found';
      contentEl.innerHTML = '<p class="loading">Could not load this post</p>';
      console.error(e);
    }
  }

  /* ============================================================
     FIELD NOTES  (learning.html)
     ============================================================ */

  async function pageLearning() {
    loadFooter();
    const listEl = document.getElementById('learn-list');
    const moreBtn = document.getElementById('load-more');
    const PAGE = 20;
    let notes = [];
    let shown = 0;

    try {
      notes = await fetchJSON('content/learning/index.json');
    } catch (e) {
      listEl.innerHTML = '<div class="loading">Could not load notes (run the local server, not file://)</div>';
      return;
    }
    if (!notes.length) {
      listEl.innerHTML = '<div class="loading">No notes yet</div>';
      return;
    }
    listEl.innerHTML = '';

    async function showNext() {
      const batch = notes.slice(shown, shown + PAGE);
      const loaded = await Promise.all(batch.map(async n => {
        try {
          const { fm, body } = parseFrontmatter(await fetchText('content/learning/' + safeSlug(n.slug) + '.md'));
          return { n, fm, body };
        } catch (e) { return null; }
      }));
      let lastMonth = shown > 0 ? monthKey(notes[shown - 1].date) : '';
      for (const item of loaded) {
        if (!item) continue;
        const mk = monthKey(item.n.date);
        if (mk && mk !== lastMonth) {
          listEl.insertAdjacentHTML('beforeend',
            '<div class="note-month"><span class="year-figure">' + esc(mk) + '</span></div>');
          lastMonth = mk;
        }
        const tagList = Array.isArray(item.fm.tags) ? item.fm.tags : [];
        listEl.insertAdjacentHTML('beforeend',
          '<div class="note">' +
            '<div class="note-date">' + fmtDate(item.n.date) + '</div>' +
            '<div><div class="note-title">' + esc(item.n.title) + '</div>' +
            '<div class="prose">' + md(item.body) + '</div>' +
            (tagList.length ? '<div class="note-tags">' + tags(tagList) + '</div>' : '') +
          '</div></div>');
      }
      shown += batch.length;
      moreBtn.style.display = shown < notes.length ? 'inline-block' : 'none';
    }

    moreBtn.addEventListener('click', showNext);
    await showNext();
  }

  /* ---------------- boot ---------------- */

  document.addEventListener('DOMContentLoaded', () => {
    initNav();
    const page = document.body.dataset.page;
    if (page === 'home') pageHome();
    else if (page === 'blog') pageBlog();
    else if (page === 'post') pagePost();
    else if (page === 'learning') pageLearning();
  });
})();
