/* ============================================================
   OCT — Boot, top-bar wiring, router.
   ============================================================ */
(function () {
  'use strict';
  const O = window.OCT;
  const { h, clear, icon } = O;

  const VIEWS = {
    A: { key: 'A', label: 'Operational Map', icon: 'map', mod: () => O.ViewMap },
    B: { key: 'B', label: 'Anomaly & Decision', icon: 'anomaly', mod: () => O.ViewAnomaly, dot: true },
    C: { key: 'C', label: 'Ask', icon: 'ask', mod: () => O.ViewAsk },
    D: { key: 'D', label: 'Data → Decision', icon: 'flow', mod: () => O.ViewFlow },
    E: { key: 'E', label: 'Build a Vertical', icon: 'spark', mod: () => O.ViewIntake }
  };

  let stripEl, metaChipsEl, tabsEl, containers = {};
  let current = null;

  function boot() {
    const app = document.getElementById('app');

    // ---- classification / connection strip ----
    stripEl = h('div', { class: 'strip' }, [
      h('span', { class: 'dot' }),
      h('span', { class: 'strip-msg' }, 'CONNECTING…'),
      h('span', { class: 'sep' }, '·'),
      h('span', null, 'UNCLASSIFIED · NOTIONAL DATA')
    ]);
    app.appendChild(stripEl);

    // ---- header ----
    const header = h('div', { class: 'header' });
    header.appendChild(h('div', { class: 'brand' }, [
      h('div', { class: 'mark' }, icon('grid', { width: 16, height: 16 })),
      h('div', { class: 'wordmark' }, [h('b', null, 'OCT'), h('span', null, 'Control Tower')])
    ]));
    metaChipsEl = h('div', { class: 'meta-chips' });
    header.appendChild(metaChipsEl);
    tabsEl = h('div', { class: 'tabs' });
    header.appendChild(tabsEl);
    header.appendChild(h('div', { class: 'spacer' }));
    const rightEl = h('div', { class: 'right' });
    // MS-S1 LLM control (PLAN-0018): residency indicator + warm/sleep, before Refresh.
    if (O.LlmControl && O.LlmControl.mount) O.LlmControl.mount(rightEl);
    rightEl.appendChild(
      h('button', { class: 'iconbtn', id: 'globalRefresh', onClick: globalRefresh }, [icon('refresh'), 'Refresh'])
    );
    header.appendChild(rightEl);
    app.appendChild(header);

    // ---- main / view containers ----
    const main = h('div', { class: 'main' });
    Object.keys(VIEWS).forEach(k => {
      const c = h('div', { class: 'view', dataset: { view: k }, 'data-screen-label': 'View ' + k });
      containers[k] = c; main.appendChild(c);
    });
    app.appendChild(main);

    buildTabs();
    wireConnection();
    wireEvents();

    // boot sequence: load meta, then land on default view
    initMeta();
  }

  function buildTabs() {
    clear(tabsEl);
    Object.values(VIEWS).forEach(v => {
      const tab = h('button', { class: 'tab', dataset: { view: v.key }, onClick: () => go(v.key) }, [
        h('span', { class: 'key' }, v.key),
        h('span', null, v.label),
        v.dot ? h('span', { class: 'badge-dot', id: 'anomDot' }) : null
      ]);
      tabsEl.appendChild(tab);
    });
  }

  function setActiveTab(k) {
    tabsEl.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.view === k));
  }

  async function initMeta() {
    try {
      await O.loadMeta();
      renderMetaChips();
      // The connection listener only fires on a CHANGE, and the app starts
      // 'live', so the happy path never repaints the strip off "CONNECTING…".
      // Paint it explicitly after the first successful load (the mock fallback
      // flips to 'degraded' on its own via setConnection).
      if (!O.State.usingMock) stripState('live', 'LIVE · SAME-ORIGIN');
    } catch (e) {
      stripState('down', 'BACKEND UNREACHABLE');
    }
    // pick default from hash or fall back to A
    const hash = (location.hash || '').replace('#', '').toUpperCase();
    go(VIEWS[hash] ? hash : 'A');
  }

  function renderMetaChips() {
    const m = O.State.meta; if (!m) return;
    clear(metaChipsEl);
    metaChipsEl.appendChild(h('span', { class: 'chip' }, [h('span', { class: 'lbl' }, 'Vertical'), h('b', null, m.vertical || '—')]));
    if (m.namespace) metaChipsEl.appendChild(h('span', { class: 'chip mono' }, [h('span', { class: 'lbl' }, 'NS'), h('b', null, m.namespace)]));
    if (m.version != null) metaChipsEl.appendChild(h('span', { class: 'chip mono' }, [h('span', { class: 'lbl' }, 'v'), h('b', null, m.version)]));
  }

  async function go(k) {
    if (!VIEWS[k]) k = 'A';
    current = k;
    location.hash = k;
    setActiveTab(k);
    Object.keys(containers).forEach(x => containers[x].classList.toggle('active', x === k));
    const mod = VIEWS[k].mod();
    if (mod && mod.mount) await mod.mount(containers[k]);
  }

  function globalRefresh() {
    const btn = document.getElementById('globalRefresh');
    btn.classList.add('spin');
    // clear caches so views refetch
    O.State.objects = {}; O.State.recommendations = [];
    go(current).finally(() => setTimeout(() => btn.classList.remove('spin'), 500));
  }

  /* ---- connection strip ---- */
  function wireConnection() {
    O.onConnection((c) => {
      if (c === 'live') stripState('live', 'LIVE · SAME-ORIGIN');
      else if (c === 'degraded') stripState('degraded', 'DEGRADED · SERVING EMBEDDED DEMO DATA');
      else stripState('down', 'BACKEND UNREACHABLE');
    });
  }
  function stripState(cls, msg) {
    stripEl.className = 'strip' + (cls === 'degraded' ? ' is-degraded' : cls === 'down' ? ' is-down' : '');
    stripEl.querySelector('.strip-msg').textContent = msg;
  }

  /* ---- cross-view events ---- */
  function wireEvents() {
    // jump to a view, optionally focusing an action or seeding a question
    document.addEventListener('oct:goto', (e) => {
      const d = e.detail || {};
      if (d.view === 'B' && d.action && O.ViewAnomaly) O.ViewAnomaly.setFocus(d.action);
      go(d.view).then(() => {
        if (d.view === 'C' && d.ask && O.ViewAsk) setTimeout(() => O.ViewAsk.ask(d.ask), 120);
      });
    });
    // navigate to an object's record (open Map focused on it)
    document.addEventListener('oct:navobj', (e) => {
      const d = e.detail || {};
      go('A').then(() => { if (O.ViewMap && O.ViewMap.focusObject) O.ViewMap.focusObject(d.type, d.id); });
    });
    window.addEventListener('keydown', (e) => {
      if (e.target && /input|textarea/i.test(e.target.tagName)) return;
      const k = e.key.toUpperCase();
      if (VIEWS[k]) { go(k); }
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
