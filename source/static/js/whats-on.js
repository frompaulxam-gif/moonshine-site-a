/* What's On: filters, search, month jump, paging and grid/list view.
   Every event is already in the HTML for search engines; this only
   shows and hides. Filters sync to the URL so a filtered view can be shared. */
(function () {
  'use strict';
  var grid = document.querySelector('[data-events]');
  if (!grid) return;

  var cards = Array.prototype.slice.call(grid.querySelectorAll('[data-event]'));
  var heads = Array.prototype.slice.call(grid.querySelectorAll('[data-month-head]'));
  var chips = document.querySelectorAll('[data-filter-type]');
  var roomSel = document.querySelector('[data-filter-room]');
  var monthSel = document.querySelector('[data-filter-month]');
  var q = document.querySelector('[data-filter-q]');
  var more = document.querySelector('[data-more]');
  var empty = document.querySelector('[data-empty]');
  var count = document.querySelector('[data-count]');
  var viewBtns = document.querySelectorAll('[data-view]');
  var PAGE = 12;
  var state = { type: 'all', room: 'all', month: 'all', q: '', shown: PAGE };

  function matches(c) {
    var tags = ' ' + (c.dataset.tags || c.dataset.type) + ' ';
    return (state.type === 'all' || tags.indexOf(' ' + state.type + ' ') !== -1)
      && (state.room === 'all' || c.dataset.room === state.room)
      && (state.month === 'all' || c.dataset.month === state.month)
      && (!state.q || c.dataset.search.indexOf(state.q) !== -1);
  }

  function apply() {
    var visible = 0, total = 0, months = {};
    cards.forEach(function (c) {
      var ok = matches(c);
      if (ok) total++;
      var show = ok && visible < state.shown;
      if (show) { visible++; months[c.dataset.month] = true; }
      c.hidden = !show;
    });
    heads.forEach(function (h) { h.hidden = !months[h.dataset.monthHead]; });
    if (empty) empty.hidden = total > 0;
    if (more) more.hidden = total <= visible;
    if (count) count.textContent = total === 1 ? '1 night' : total + ' nights';
    syncUrl();
  }

  function syncUrl() {
    var p = new URLSearchParams();
    if (state.type !== 'all') p.set('type', state.type);
    if (state.room !== 'all') p.set('room', state.room);
    if (state.month !== 'all') p.set('month', state.month);
    if (state.q) p.set('q', state.q);
    var s = p.toString();
    history.replaceState(null, '', window.location.pathname + (s ? '?' + s : '') + window.location.hash);
  }

  chips.forEach(function (b) {
    b.addEventListener('click', function () {
      chips.forEach(function (x) { x.setAttribute('aria-pressed', 'false'); });
      b.setAttribute('aria-pressed', 'true');
      state.type = b.dataset.filterType;
      state.shown = PAGE;
      apply();
    });
  });
  if (roomSel) roomSel.addEventListener('change', function () { state.room = roomSel.value; state.shown = PAGE; apply(); });
  if (monthSel) monthSel.addEventListener('change', function () { state.month = monthSel.value; state.shown = PAGE; apply(); });
  var timer;
  if (q) q.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(function () { state.q = q.value.trim().toLowerCase(); state.shown = PAGE; apply(); }, 120);
  });
  if (more) more.addEventListener('click', function () { state.shown += PAGE; apply(); });
  viewBtns.forEach(function (b) {
    b.addEventListener('click', function () {
      viewBtns.forEach(function (x) { x.setAttribute('aria-pressed', 'false'); });
      b.setAttribute('aria-pressed', 'true');
      grid.classList.toggle('events--list', b.dataset.view === 'list');
    });
  });

  // Start from whatever is in the URL
  var init = new URLSearchParams(window.location.search);
  if (init.get('type')) {
    state.type = init.get('type');
    chips.forEach(function (x) { x.setAttribute('aria-pressed', x.dataset.filterType === state.type ? 'true' : 'false'); });
  }
  if (init.get('room') && roomSel) { roomSel.value = init.get('room'); state.room = roomSel.value || 'all'; }
  if (init.get('month') && monthSel) { monthSel.value = init.get('month'); state.month = monthSel.value || 'all'; }
  if (init.get('q') && q) { q.value = init.get('q'); state.q = q.value.trim().toLowerCase(); }
  apply();
})();
