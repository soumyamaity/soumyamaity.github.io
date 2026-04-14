/* ===== main.js ===== */
(function () {
  'use strict';

  /* --- Mobile nav toggle --- */
  const navToggle = document.querySelector('.nav-toggle');
  const navLinks = document.querySelector('.nav-links');
  if (navToggle) {
    navToggle.addEventListener('click', () => {
      navLinks.classList.toggle('open');
    });
    // Close on link click
    navLinks.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => navLinks.classList.remove('open'));
    });
  }

  /* --- Typing animation (index.html hero) --- */
  const typingEl = document.getElementById('typing-text');
  if (typingEl) {
    const phrases = [
      'An InfoSec Expert',
      'A DevSecOps Evangelist',
      'AI/ML Enthusiast',
      'Security Development Lifecycle Coach',
      'Researcher | Author | Thought Leader'
    ];
    let phraseIdx = 0;
    let charIdx = 0;
    let deleting = false;
    let pauseTime = 0;

    function typeLoop() {
      const current = phrases[phraseIdx];
      if (!deleting) {
        typingEl.textContent = current.substring(0, charIdx + 1);
        charIdx++;
        if (charIdx === current.length) {
          deleting = true;
          pauseTime = 2000;
        } else {
          pauseTime = 60;
        }
      } else {
        typingEl.textContent = current.substring(0, charIdx - 1);
        charIdx--;
        if (charIdx === 0) {
          deleting = false;
          phraseIdx = (phraseIdx + 1) % phrases.length;
          pauseTime = 400;
        } else {
          pauseTime = 30;
        }
      }
      setTimeout(typeLoop, pauseTime);
    }
    typeLoop();
  }

  /* --- Animate skill bars on scroll --- */
  const skillBars = document.querySelectorAll('.skill-bar-fill');
  if (skillBars.length) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.width = entry.target.dataset.width + '%';
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });
    skillBars.forEach(bar => observer.observe(bar));
  }

  /* --- Blog preview on index.html --- */
  const blogPreview = document.getElementById('blog-preview');
  if (blogPreview) {
    fetch('posts/index.json')
      .then(r => r.json())
      .then(posts => {
        const recent = posts.slice(0, 6);
        blogPreview.innerHTML = recent.map(p => `
          <a class="blog-card" href="post.html?slug=${encodeURIComponent(p.slug)}">
            <div class="blog-card-date">${p.date}</div>
            <div class="blog-card-title">${esc(p.title)}</div>
            <div class="blog-card-desc">${esc(p.description)}</div>
            <div class="blog-card-tags">${p.tags.slice(0, 4).map(t => `<span class="tag">${esc(t)}</span>`).join('')}</div>
          </a>
        `).join('');
      })
      .catch(() => {
        blogPreview.innerHTML = '<p class="no-results">Could not load posts.</p>';
      });
  }

  /* --- Blog listing page (blog.html) --- */
  const blogList = document.getElementById('blog-list');
  const searchInput = document.getElementById('search-input');
  const tagFiltersEl = document.getElementById('tag-filters');

  if (blogList && searchInput) {
    let allPosts = [];
    let activeTag = null;

    fetch('posts/index.json')
      .then(r => r.json())
      .then(posts => {
        allPosts = posts;
        buildTagFilters(posts);
        renderPosts(posts);

        searchInput.addEventListener('input', () => filterPosts());
      })
      .catch(() => {
        blogList.innerHTML = '<p class="no-results">Could not load posts.</p>';
      });

    function buildTagFilters(posts) {
      const tagCount = {};
      posts.forEach(p => p.tags.forEach(t => {
        const tl = t.toLowerCase();
        tagCount[tl] = (tagCount[tl] || 0) + 1;
      }));
      // Show top 15 tags by frequency
      const topTags = Object.entries(tagCount)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 15);

      tagFiltersEl.innerHTML = `<span class="tag active" data-tag="">All</span>` +
        topTags.map(([t]) => `<span class="tag" data-tag="${esc(t)}">${esc(t)}</span>`).join('');

      tagFiltersEl.addEventListener('click', e => {
        if (e.target.classList.contains('tag')) {
          tagFiltersEl.querySelectorAll('.tag').forEach(el => el.classList.remove('active'));
          e.target.classList.add('active');
          activeTag = e.target.dataset.tag || null;
          filterPosts();
        }
      });
    }

    function filterPosts() {
      const q = searchInput.value.toLowerCase().trim();
      let filtered = allPosts;

      if (activeTag) {
        filtered = filtered.filter(p =>
          p.tags.some(t => t.toLowerCase() === activeTag)
        );
      }

      if (q) {
        filtered = filtered.filter(p =>
          p.title.toLowerCase().includes(q) ||
          p.description.toLowerCase().includes(q) ||
          p.tags.some(t => t.toLowerCase().includes(q))
        );
      }

      renderPosts(filtered);
    }

    function renderPosts(posts) {
      if (posts.length === 0) {
        blogList.innerHTML = '<p class="no-results">No posts found.</p>';
        return;
      }
      blogList.innerHTML = posts.map(p => `
        <a class="blog-list-item" href="post.html?slug=${encodeURIComponent(p.slug)}">
          <div class="blog-list-item-header">
            <div class="blog-list-item-title">${esc(p.title)}</div>
            <div class="blog-list-item-date">${p.date}</div>
          </div>
          <div class="blog-list-item-desc">${esc(p.description)}</div>
        </a>
      `).join('');
    }
  }

  /* --- Single post page (post.html) --- */
  const postContent = document.getElementById('post-content');
  const postTitle = document.getElementById('post-title');
  const postMeta = document.getElementById('post-meta');
  const postTags = document.getElementById('post-tags');

  if (postContent && postTitle) {
    const params = new URLSearchParams(window.location.search);
    const slug = params.get('slug');

    if (!slug) {
      postTitle.textContent = 'No post specified';
      postContent.innerHTML = '<p>Please select a post from the <a href="blog.html">blog listing</a>.</p>';
    } else {
      fetch(`posts/${slug}.md`)
        .then(r => {
          if (!r.ok) throw new Error('Not found');
          return r.text();
        })
        .then(md => {
          // Parse frontmatter
          let body = md;
          let fm = {};
          const fmMatch = md.match(/^---\s*\n([\s\S]*?)\n---\s*\n/);
          if (fmMatch) {
            body = md.slice(fmMatch[0].length);
            fm = parseFrontmatter(fmMatch[1]);
          }

          const title = fm.title || slug.replace(/-/g, ' ');
          postTitle.textContent = title;
          document.title = title + ' | Dr. Soumyo Maity';

          if (fm.date) {
            postMeta.textContent = fm.date.substring(0, 10);
          }

          if (fm.tags && postTags) {
            postTags.innerHTML = fm.tags.map(t =>
              `<span class="tag">${esc(t)}</span>`
            ).join('');
          }

          // Render markdown
          if (typeof marked !== 'undefined') {
            marked.setOptions({
              breaks: true,
              gfm: true
            });
            postContent.innerHTML = marked.parse(body);
          } else {
            // Fallback: show raw markdown
            postContent.innerHTML = '<pre>' + esc(body) + '</pre>';
          }
        })
        .catch(() => {
          postTitle.textContent = 'Post not found';
          postContent.innerHTML = '<p>The requested post could not be loaded. <a href="blog.html">Back to blog</a>.</p>';
        });
    }
  }

  /* --- Helpers --- */
  function esc(str) {
    const el = document.createElement('span');
    el.textContent = str;
    return el.innerHTML;
  }

  function parseFrontmatter(text) {
    const result = {};
    let currentKey = null;
    let inList = false;

    text.split('\n').forEach(line => {
      const trimmed = line.trim();

      // List item
      if (inList && trimmed.startsWith('- ')) {
        if (!result[currentKey]) result[currentKey] = [];
        result[currentKey].push(trimmed.slice(2).trim().replace(/^['"]|['"]$/g, ''));
        return;
      }

      // Key: value
      const kv = line.match(/^(\w[\w-]*)\s*:\s*(.*)$/);
      if (kv) {
        currentKey = kv[1];
        const val = kv[2].trim();
        if (val === '' || val === '|') {
          inList = true;
          result[currentKey] = [];
        } else {
          inList = false;
          result[currentKey] = val.replace(/^['"]|['"]$/g, '');
        }
        return;
      }

      // Nested/indented list item for current key
      if (currentKey && trimmed.startsWith('- ')) {
        if (!Array.isArray(result[currentKey])) result[currentKey] = [];
        result[currentKey].push(trimmed.slice(2).trim().replace(/^['"]|['"]$/g, ''));
      } else if (trimmed === '') {
        inList = false;
      }
    });

    return result;
  }

})();
