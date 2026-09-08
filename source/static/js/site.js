/* Moonshine site behaviour: header, menu, hero motion, ResDiary loader,
   form stubs, map consent, booking date note. No frameworks. */
(function () {
  'use strict';

  // Header goes solid once you scroll off the hero
  var header = document.querySelector('.site-header');
  function onScroll() { header.classList.toggle('is-scrolled', window.scrollY > 40); }
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  // Full-screen menu
  var burger = document.querySelector('.burger');
  var menu = document.getElementById('menu');
  var closeBtn = menu && menu.querySelector('.menu__close');
  // Everything behind the open menu is made inert so focus cannot escape it
  var behind = ['main', '.site-header', '.site-footer', '.sticky-book']
    .map(function (s) { return document.querySelector(s); }).filter(Boolean);
  function setInert(on) { behind.forEach(function (el) { on ? el.setAttribute('inert', '') : el.removeAttribute('inert'); }); }
  function openMenu() {
    menu.hidden = false;
    burger.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
    setInert(true);
    (closeBtn || menu.querySelector('a')).focus();
  }
  function closeMenu(keepFocus) {
    menu.hidden = true;
    burger.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
    setInert(false);
    if (!keepFocus) burger.focus();
  }
  if (burger && menu) {
    burger.addEventListener('click', function () { menu.hidden ? openMenu() : closeMenu(); });
    closeBtn && closeBtn.addEventListener('click', function () { closeMenu(); });
    menu.querySelectorAll('a').forEach(function (a) { a.addEventListener('click', function () { closeMenu(true); }); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !menu.hidden) closeMenu(); });
    menu.addEventListener('keydown', function (e) {
      if (e.key !== 'Tab') return;
      var f = menu.querySelectorAll('a[href], button:not([disabled])');
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });
  }

  // Hero video respects reduced motion
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var video = document.querySelector('.hero video');
  if (video) {
    if (reduce) { video.removeAttribute('autoplay'); video.pause(); }
    else { var p = video.play(); if (p && p.catch) p.catch(function () {}); }
  }
  // Pause control for the moving hero
  var pauseBtn = document.querySelector('[data-pause]');
  if (pauseBtn && video) {
    var setPaused = function (paused) {
      pauseBtn.textContent = paused ? 'Play' : 'Pause';
      pauseBtn.setAttribute('aria-label', paused ? 'Play video' : 'Pause video');
      pauseBtn.setAttribute('aria-pressed', paused ? 'true' : 'false');
    };
    pauseBtn.addEventListener('click', function () {
      if (video.paused) { video.play(); setPaused(false); } else { video.pause(); setPaused(true); }
    });
    if (reduce) setPaused(true);
  }

  // ResDiary booking calendar, loaded when it comes near the viewport.
  // The hosted widget page is framed in: it shows the full inline calendar on
  // any domain. On the live domain the script embed from the old site can be
  // swapped back in if preferred (WidgetV2Loader.js + #rdwidgeturl).
  var rdBoxes = document.querySelectorAll('[data-resdiary]');
  function loadResDiary(box) {
    if (box.dataset.loaded) return;
    box.dataset.loaded = '1';
    var f = document.createElement('iframe');
    f.src = box.dataset.resdiary;
    f.title = 'Book a table at Moonshine';
    f.setAttribute('allow', 'payment');
    f.addEventListener('load', function () { box.dataset.ready = '1'; });
    f.addEventListener('error', function () { delete box.dataset.loaded; });
    box.appendChild(f);
  }
  rdBoxes.forEach(function (box) {
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) { if (en.isIntersecting) { loadResDiary(box); io.disconnect(); } });
      }, { rootMargin: '700px' });
      io.observe(box);
      var io2 = new IntersectionObserver(function (entries) {
        document.body.classList.toggle('rd-visible', entries.some(function (en) { return en.isIntersecting; }));
      });
      io2.observe(box);
    } else {
      loadResDiary(box);
    }
  });

  // Forms are not wired to a backend yet: validate, then show the success copy.
  document.querySelectorAll('form[data-stub]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!form.checkValidity()) { form.reportValidity(); return; }
      var fields = form.querySelector('.form__fields');
      var msg = form.querySelector('.form__msg');
      if (fields) fields.hidden = true;
      if (msg) { msg.hidden = false; msg.focus(); }
    });
  });

  // Map loads only when asked for
  document.querySelectorAll('[data-map]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var wrap = btn.closest('.map');
      var f = document.createElement('iframe');
      f.src = btn.dataset.map;
      f.title = 'Map showing Moonshine, 91 High Street, Leicester';
      f.loading = 'lazy';
      f.referrerPolicy = 'no-referrer-when-downgrade';
      f.setAttribute('allowfullscreen', '');
      wrap.innerHTML = '';
      wrap.appendChild(f);
    });
  });

  // Private hire: a room's Enquire button pre-selects that room in the form
  document.querySelectorAll('[data-pick-room]').forEach(function (a) {
    a.addEventListener('click', function () {
      var sel = document.querySelector('select[name="room"]');
      if (sel) sel.value = a.dataset.pickRoom;
    });
  });

  // Carry the event date from a "Book a Table" click into the ResDiary
  // calendar (its hosted page accepts ?date=YYYY-MM-DD, ISO only) and say so.
  var d = new URLSearchParams(window.location.search).get('date');
  if (d && /^\d{4}-\d{2}-\d{2}$/.test(d)) {
    rdBoxes.forEach(function (box) {
      var base = box.dataset.resdiary;
      box.dataset.resdiary = base + (base.indexOf('?') > -1 ? '&' : '?') + 'date=' + d;
    });
    var note = document.querySelector('[data-book-date]');
    if (note) {
      var dt = new Date(d + 'T12:00:00');
      note.textContent = 'Booking for ' + dt.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }) + '. The calendar below has that date selected.';
      note.hidden = false;
    }
  }
})();
