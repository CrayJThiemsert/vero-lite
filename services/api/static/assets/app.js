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

  // PLAN-0103 Step 2 — which tabs the published profile renders is DECLARED BY
  // THE SERVER, per system, and arrives on <meta name="ui-views"> before the
  // first paint (O.State.publishedViews).
  //
  // It used to be PUBLISHED_EXCLUDED_VIEWS, a list here naming the five tabs
  // energy drops. That constant encoded N=1: a second published system with a
  // different tab set had nowhere to say so except a per-vertical branch in the
  // browser. Each system now declares its own set in its own published.env, and
  // the rationale for a given set lives with that system's profile — which is
  // also where the per-tab reasoning for energy's five went.
  //
  // Route names are written WITHOUT a glob anywhere in this file on purpose. A
  // slash immediately followed by a star opens a block comment as far as any
  // naive stripper is concerned, and the CSS-class contract test strips comments
  // before scanning for applied classes. Writing a route with a trailing glob
  // here once silently swallowed everything from that line to the next
  // block-comment close ~150 lines below — including the `strip-msg` class on
  // the status strip — and reddened test_css_class_contract, a test that change
  // never went near. (Written out in words rather than shown as an example,
  // because an example would re-arm the very trap. The first fix removed the
  // globs from the list but left one inside the sentence explaining them, and
  // the test stayed red — the explanation was still the bug.)

  // The published profile's ordered view keys, or null to mean "render the full
  // census". Called exactly once, below, to build VIEWS.
  //
  // The server validated every key it sent against the same ten-tab census, so a
  // NON-EMPTY declared set is already trustworthy. What this function decides is
  // the one case the server cannot: the tag did not arrive at all, and
  // O.State.publishedViews is empty — a rewrite that failed, a cached pre-Step-2
  // index, an offline bundle. See the fallback discussion in the PR.
  function publishedViewKeys() {
    const declared = O.State.publishedViews;
    if (declared.length) return declared;
    // Nothing declared on a page that knows it is published (Cray, typed, s219).
    // Both meta tags come from ONE substitution in main.py, so arriving here
    // means a premise broke that this code cannot name — and every way of
    // GUESSING is wrong in its own direction: the full census renders controls
    // whose backends the allowlist 404s, and a hardcoded set is a guess about
    // WHICH system this is, wrong on procurement (G,F) and fleet.
    //
    // So: refuse, visibly. An empty set is turned into an explicit panel by
    // boot(), not into an empty header — a page that merely looks broken costs
    // the operator the diagnosis, which is the whole reason this branch exists.
    return [];
  }

  // Filtered into VIEWS ITSELF rather than hidden at buildTabs(), so every
  // downstream consumer is correct by construction and no second branch can be
  // forgotten: containers are never built, buildTabs() cannot render the tab,
  // go() falls back to the default key for an unknown one (so a deep-linked #E
  // is handled), and the oct:goto listener cannot route into a dead view.
  //
  // Built by MAPPING the declared keys rather than filtering ALL_VIEWS, because
  // the declared list is ORDERED and that order is the tab order — procurement
  // lands on G, not A. A filter would silently re-impose census order.
  const DECLARED = O.isPublished() ? publishedViewKeys() : null;
  const VIEWS = DECLARED
    ? Object.fromEntries(DECLARED.filter(k => ALL_VIEWS[k]).map(k => [k, ALL_VIEWS[k]]))
    : ALL_VIEWS;

  // The system's default landing tab: the first declared key. Energy declares A
  // and is unchanged; procurement must land on G because its Tab A is
  // structurally blank (its adapter's stream_events is an empty iterator by
  // design), which the old hardcoded 'A' fallback could not express.
  const DEFAULT_VIEW = Object.keys(VIEWS)[0] || 'A';

  let stripEl, metaChipsEl, tabsEl, containers = {};
  let current = null;

  // The published profile declared nothing renderable. Two audiences, two
  // channels, deliberately:
  //
  //   * the VISITOR gets an honest, calm page and no internals. Naming the meta
  //     tag or the env var to an anonymous visitor is a stack trace on a public
  //     surface — it reads as amateurish and tells them nothing they can act on.
  //   * the OPERATOR gets the actual diagnosis on the console, where it is
  //     addressed to someone who can fix it.
  //
  // No D6 notice on this path (ADR-0035 D6): the notice's obligations are about
  // what a visitor TYPES, and this page offers no input at all.
  function renderUnconfigured(app) {
    console.error(
      'OCT: ui_profile is "published" but no <meta name="ui-views"> reached this ' +
      'document, so no tab set could be built. Both tags are emitted by one ' +
      'substitution (services/api/main.py _profiled_index) — check that the ' +
      'server rewrote this index and that UI_PUBLISHED_VIEWS is set for this system.'
    );
    app.appendChild(h('div', { class: 'state' }, h('div', { class: 'box' }, [
      h('h3', null, 'This system isn’t configured yet'),
      h('p', null,
        'The server didn’t declare which parts of the console this deployment ' +
        'publishes, so none are being shown.'),
      h('p', { class: 'muted', style: { marginTop: '12px' } },
        'vero-lite is an operational control tower — it maps assets from an ' +
        'operator’s own data, explains why something was flagged, and routes ' +
        'the fix to a person to approve, keeping a reasoning trace and an audit ' +
        'record behind every decision.'),
      h('p', { class: 'muted', style: { marginTop: '10px' } },
        'Which is why this page is empty rather than improvised: what it may ' +
        'show is declared by the server, never guessed by the browser.')
    ])));
  }

  function boot() {
    const app = document.getElementById('app');

    // Refuse before anything else is built. Rendering the header first would
    // paint a tabless console for a moment, which is the "looks broken, says
    // nothing" outcome this branch exists to avoid.
    if (O.isPublished() && !Object.keys(VIEWS).length) { renderUnconfigured(app); return; }

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

    // ---- D2.4 case-persistence line, BESIDE the D6 notice (PLAN-0106) ----
    // 🔴 BESIDE, never INSIDE. SD-3 ruled (a): correct by SCOPING in a new element,
    // leaving D6's shared string byte-identical — it is TRUE of the prompt log on
    // every system, and editing it to fix one profile reopens what ADR-0037 D3
    // refused. AC-3 pins that the block above is untouched.
    //
    // Why a second element at all, when Tab I already carries the load-bearing
    // notice: case text is READ on Tabs H and J by visitors who never open Tab I,
    // and this persistent region is where a reading visitor's expectations are set.
    // The D6 sentence directly above says "read only by the operator" — true of the
    // prompt log, false of case text — so on THIS profile the correction has to sit
    // where that sentence is read.
    //
    // Gated on SERVER-DECLARED state, never a browser guess and never a vertical
    // name: the disclosure is true exactly where the system publishes the
    // case-WRITING surface, so the gate is "Tab I is in the declared view set".
    // On dev this is unreachable (not published); on a published system without
    // Tab I — procurement's ruled G,F — there is no case dataset and the claim
    // would be false.
    if (O.State.uiProfile === 'published' && Object.prototype.hasOwnProperty.call(VIEWS, 'I')) {
      app.appendChild(h('div', { class: 'case-persist-notice', role: 'note' }, [
        h('span', null,
          'ข้อความและรูปในใบแจ้งซ่อมถูกเก็บในฐานข้อมูลของระบบนี้ ลบภายใน 90 วัน ' +
          'และผู้เข้าชมทุกคนของระบบนี้อ่านข้อความนั้นได้')
      ]));
    }

    // ---- header ----
    const header = h('div', { class: 'header' });
    header.appendChild(h('div', { class: 'brand' }, [
      // The brand mark is a shipped raster, not an inline icon, so the file has to
      // exist at this exact string or the header renders a broken image — a seam
      // nothing else in the suite reads. tests/api/test_brand_mark_contract.py is
      // that reader: it parses this src and GETs it through the real static mount.
      h('div', { class: 'mark' }, h('img', {
        src: 'assets/brand/cray-j.png', alt: 'Cray.J', width: 24, height: 17
      })),
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
    // pick default from hash or fall back to this system's default landing tab
    const hash = (location.hash || '').replace('#', '').toUpperCase();
    go(VIEWS[hash] ? hash : DEFAULT_VIEW);
  }

  function renderMetaChips() {
    const m = O.State.meta; if (!m) return;
    clear(metaChipsEl);
    metaChipsEl.appendChild(h('span', { class: 'chip' }, [h('span', { class: 'lbl' }, 'Vertical'), h('b', null, m.vertical || '—')]));
    if (m.namespace) metaChipsEl.appendChild(h('span', { class: 'chip mono' }, [h('span', { class: 'lbl' }, 'NS'), h('b', null, m.namespace)]));
    if (m.version != null) metaChipsEl.appendChild(h('span', { class: 'chip mono' }, [h('span', { class: 'lbl' }, 'v'), h('b', null, m.version)]));
  }

  async function go(k) {
    if (!VIEWS[k]) k = DEFAULT_VIEW;
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
