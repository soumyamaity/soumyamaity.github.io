/* ===== portfolio.js — homepage interactions ===== */
(function () {
  'use strict';

  /* --- Mobile nav toggle --- */
  var toggle = document.querySelector('.pf-nav-toggle');
  var links  = document.querySelector('.pf-nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', function () { links.classList.toggle('open'); });
    links.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { links.classList.remove('open'); });
    });
  }

  /* --------------------------------------------------------------- */
  /*  Scroll-triggered .reveal fade-up                               */
  /* --------------------------------------------------------------- */
  var reveals = document.querySelectorAll('.reveal');
  if (reveals.length) {
    var revealObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add('visible');
          revealObs.unobserve(e.target);
        }
      });
    }, { threshold: 0.12 });
    reveals.forEach(function (el) { revealObs.observe(el); });
  }

  /* --------------------------------------------------------------- */
  /*  Animated metric counters                                       */
  /* --------------------------------------------------------------- */
  var counters = document.querySelectorAll('[data-count]');
  if (counters.length) {
    var counted = new Set();
    var counterObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting || counted.has(e.target)) return;
        counted.add(e.target);
        animateCounter(e.target);
        counterObs.unobserve(e.target);
      });
    }, { threshold: 0.3 });
    counters.forEach(function (el) { counterObs.observe(el); });
  }

  function animateCounter(el) {
    var target = parseInt(el.getAttribute('data-count'), 10);
    var duration = 1400;
    var start = performance.now();

    function step(now) {
      var t = Math.min((now - start) / duration, 1);
      // ease-out cubic
      var ease = 1 - Math.pow(1 - t, 3);
      var current = Math.round(ease * target);
      el.textContent = current.toLocaleString();
      if (t < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  /* --------------------------------------------------------------- */
  /*  Active nav highlighting on scroll                              */
  /* --------------------------------------------------------------- */
  var sections = document.querySelectorAll('[data-nav]');
  var navLinks = document.querySelectorAll('.pf-nav-links a[href^="#"]');

  if (sections.length && navLinks.length) {
    var navObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          var id = e.target.getAttribute('id');
          navLinks.forEach(function (a) {
            a.classList.toggle('active', a.getAttribute('href') === '#' + id);
          });
        }
      });
    }, { threshold: 0.25, rootMargin: '-64px 0px -40% 0px' });
    sections.forEach(function (s) { navObs.observe(s); });
  }

})();
