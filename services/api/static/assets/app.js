/* ============================================================
   OCT — Boot, top-bar wiring, router.
   ============================================================ */
(function () {
  'use strict';
  const O = window.OCT;
  const { h, clear, icon } = O;

  // The full ten-tab census. PLAN-0100's tables cite this block, so every entry
  // stays here even when the published profile drops it — the census must remain
  // readable in one place.
  const ALL_VIEWS = {
    A: { key: 'A', label: 'Operational Map', icon: 'map', mod: () => O.ViewMap },
    B: { key: 'B', label: 'Anomaly & Decision', icon: 'anomaly', mod: () => O.ViewAnomaly, dot: true },
    C: { key: 'C', label: 'Ask', icon: 'ask', mod: () => O.ViewAsk },
    D: { key: 'D', label: 'Data → Decision', icon: 'flow', mod: () => O.ViewFlow },
    E: { key: 'E', label: 'Build a Vertical', icon: 'spark', mod: () => O.ViewIntake },
    F: { key: 'F', label: 'Procedures', icon: 'receipt', mod: () => O.ViewProcedures },
    G: { key: 'G', label: 'Governance Moment', icon: 'spark', mod: () => O.ViewHero },
    H: { key: 'H', label: 'Monitor', icon: 'gauge', mod: () => O.ViewMonitor },
    // PLAN-0096 Step 2: the minute-1 capture surface. Built for a phone, not this
    // desk console — it lives here so the pilot has ONE app, but it is the only
    // view whose layout assumes a thumb.
    I: { key: 'I', label: 'Open a Case', icon: 'spark', mod: () => O.ViewCase },
    // The month-end KPI (the export cover, rendered). Last because it is the
    // END of the flow the other tabs walk: a case is opened in I, governed in
    // F/G/H, and lands here as one row of a number a pilot charter is bound to.
    // Read-only, and deliberately NOT a download control (s192).
    J: { key: 'J', label: 'Month-End KPI', icon: 'receipt', mod: () => O.ViewExport }
  };

  // PLAN-0100 Step 3 — tabs whose ENTIRE backend is off the published allowlist.
  //   E  the three intake routes         D5(2)
  //   H  every runs route it calls       default-deny (and SD-1's C-3 disposition
  //      moved its last two allowed routes, GET runs-by-id + gate-resolve, to the
  //      excluded table, so nothing of H's backend survives)
  //   I  the api-cases routes            SD-1(a) — DB-backed
  //   J  the api-exports routes          SD-1(a) — DB-backed
  //
  // Route names above are written WITHOUT a glob on purpose. A slash immediately
  // followed by a star opens a block comment as far as any naive stripper is
  // concerned, and the CSS-class contract test strips comments before scanning
  // for applied classes. Writing the intake route with a trailing glob here
  // silently swallowed everything from that line to the next block-comment close
  // ~150 lines below — including the `strip-msg` class on the status strip — and
  // reddened test_css_class_contract, a test this change never went near.
  // (Written out in words rather than shown as an example, because an example
  // would re-arm the very trap. The first fix removed the globs from the list
  // above but left one inside the sentence explaining them, and the test stayed
  // red — the explanation was still the bug.)
  //
  // Filtered out of VIEWS ITSELF rather than hidden at buildTabs(), so every
  // downstream consumer is correct by construction and no second branch can be
  // forgotten: containers are never built, buildTabs() cannot render the tab,
  // go() already falls back to 'A' for an unknown key (so a deep-linked #E is
  // handled), and the oct:goto listener cannot route into a dead view.
  const PUBLISHED_EXCLUDED_VIEWS = ['E', 'H', 'I', 'J'];

  const VIEWS = O.isPublished()
    ? Object.fromEntries(
        Object.entries(ALL_VIEWS).filter(([k]) => PUBLISHED_EXCLUDED_VIEWS.indexOf(k) === -1)
      )
    : ALL_VIEWS;

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

    // ---- D6 persistent notice (PLAN-0100 Step 5; ADR-0035 D6) ----
    // Published profile only, and NOT dismissable. D6 makes the in-app notice the
    // load-bearing consent-capture point precisely because the vendor gate page is
    // capability this repo cannot verify — a close button would turn a required
    // disclosure into an optional one.
    //
    // Carries all six D6 elements (retained text / 90 days / operator-only reader /
    // Cloudflare processes the email / vendor-edge transit / synthetic, enter nothing
    // real). Wording reviewed against ADR-0032 D5's vocabulary rules; the six are
    // pinned individually by tests/api/test_ui_profile.py, so a reword that drops ONE
    // reddens on that element rather than passing a "is there a banner" check.
    if (O.State.uiProfile === 'published') {
      app.appendChild(h('div', { class: 'd6-notice', role: 'note' }, [
        h('b', null, 'Demo data is synthetic — please do not enter real personal data.'),
        ' ',
        h('span', null,
          'What you type is retained for 90 days and read only by the operator. ' +
          'Access is gated by Cloudflare, which processes your email address, and ' +
          'traffic transits the vendor edge.')
      ]));
    }

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
    // PLAN-0100 Step 3: NOT mounted on the published profile — its two backends
    // (/warm, /sleep) are excluded by D5(2)/P11, and an anonymous visitor must not
    // be handed a control that unloads the model mid-demo.
    if (!O.isPublished() && O.LlmControl && O.LlmControl.mount) O.LlmControl.mount(rightEl);
    // Story-mode launcher (PLAN-0033 C0): additive overlay, coexists with Views A–E.
    if (O.ViewStory && O.ViewStory.mountLauncher) O.ViewStory.mountLauncher(rightEl);
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
      // PLAN-0084: map-node → Monitor jump — pre-mount focus, the same pattern as view B.
      if (d.view === 'H' && d.run && O.ViewMonitor && O.ViewMonitor.focusRun) O.ViewMonitor.focusRun(d.run);
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
