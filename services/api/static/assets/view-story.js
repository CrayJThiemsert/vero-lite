/* ============================================================
   Story mode — PLAN-0033 Phase C, C0 vertical slice (aquaculture).

   An ADDITIVE presentation overlay (SD-C) that the app.js router
   launches and that coexists with Views A–E — it never replaces the
   working console (AC-14). The C0 slice de-risks the whole technique
   on ONE vertical:
     • the lifecycle teardown contract (AC-13) — one Motion scope per
       open; close() -> scope.kill() -> zero leaked timers/anims/listeners;
     • a branching-DAG pipeline overview (AC-2) with 5 node states +
       3 edge types, hand-placed SVG (no graph-layout lib);
     • the LLM-compose-vs-deterministic-rule-fail-safe reroute (AC-3,
       ADR-010 IN-4) — the moat beat: even an LLM fault still passes the
       human approve-gate + records audit;
     • a two-axis layout (AC-4) — ALL task details on the LEFT with an
       active-task blink, the DAG overview + transport on the RIGHT;
     • a scene-6 control surface (AC-5/AC-6) — persistent action-inbox
       rail + Proposed→Approved→Executed kanban lanes + a reasoning-trace
       "why" toggle reusing the rule/llm/query colour legend;
     • a static reduced-motion floor from day 1 (AC-10) — every state
       reads as colour + icon + label, never motion-only.

   Synthetic Tier-1 mirror data only (ADR-0015 D1). No new backend.
   ============================================================ */
(function () {
  'use strict';
  const O = window.OCT;
  const { h, clear, icon } = O;
  const M = O.Motion;
  const SVGNS = 'http://www.w3.org/2000/svg';

  /* tiny SVG hyperscript (h() builds HTML-namespaced nodes) */
  function s(tag, attrs, children) {
    const el = document.createElementNS(SVGNS, tag);
    if (attrs) for (const k in attrs) {
      const v = attrs[k];
      if (v == null || v === false) continue;
      if (k === 'text') el.textContent = v;
      else if (k === 'style' && typeof v === 'object') Object.assign(el.style, v);
      else el.setAttribute(k, v);
    }
    if (children != null) (Array.isArray(children) ? children : [children]).forEach(c => {
      if (c instanceof Node) el.appendChild(c);
      else if (c != null && c !== false) el.appendChild(document.createTextNode(String(c)));
    });
    return el;
  }

  /* ---- DAG geometry + model (hand-placed; no layout lib — AC-2).
     Overview is HORIZONTAL (locked design §2: overview horizontal, details
     vertical): trunk flows left→right, the branch splits up (LLM) / down (Rule)
     and reconverges at Approve. A short, wide band leaves the vertical room
     below for the scene-6 control surface. ---- */
  const BOX_W = 104, BOX_H = 46, HW = BOX_W / 2, HH = BOX_H / 2;
  const NODES = [
    { id: 'ING', n: '1', name: 'Ingest',         kind: 'query', cx: 62,  cy: 120 },
    { id: 'DET', n: '2', name: 'Detect-trend',   kind: 'rule',  cx: 188, cy: 120 },
    { id: 'VAL', n: '3', name: 'Validate',       kind: 'query', cx: 314, cy: 120 },
    { id: 'REC', n: '4', name: 'Recommend',      kind: 'llm',   cx: 440, cy: 120 },
    { id: 'LLM', n: '5', name: 'LLM-compose',    kind: 'llm',   cx: 566, cy: 58,  branch: true },
    { id: 'RUL', n: '6', name: 'Rule fail-safe', kind: 'rule',  cx: 566, cy: 182, branch: true },
    { id: 'APR', n: '7', name: 'Approve',        sub: 'human gate', cx: 692, cy: 120 },
    { id: 'EXE', n: '8', name: 'Execute',        sub: '+ audit',    cx: 818, cy: 120 }
  ];
  const EDGES = [
    { id: 'e_ing_det', from: 'ING', to: 'DET' },
    { id: 'e_det_val', from: 'DET', to: 'VAL' },
    { id: 'e_val_rec', from: 'VAL', to: 'REC' },
    { id: 'e_rec_llm', from: 'REC', to: 'LLM' },
    { id: 'e_rec_rul', from: 'REC', to: 'RUL' },
    { id: 'e_llm_apr', from: 'LLM', to: 'APR' },
    { id: 'e_rul_apr', from: 'RUL', to: 'APR' },
    { id: 'e_apr_exe', from: 'APR', to: 'EXE' }
  ];
  const TASK_ORDER = ['ING', 'DET', 'VAL', 'REC', 'LLM', 'RUL', 'APR', 'EXE'];
  const TASKS = {
    ING: { rows: [['source', 'GET /objects'], ['streams', 'DO · biomass · aerator']],
           note: 'Live signals for pond P-12 — dissolved-oxygen probe, biomass estimate, aerator state.' },
    DET: { rows: [['DO now', '4.6 mg/L'], ['slope', '−0.16 mg/L·min'], ['ETA to 4.0', '≈70 min']],
           note: 'Caught on the way DOWN, not after the crash: projected to cross the 4.0 action line in ~70 min. Lead time is the point.' },
    VAL: { rows: [['probe-B', '4.7 mg/L'], ['calibration', '6 d'], ['confidence', 'HIGH']],
           note: 'Cross-checked against probe-B (Δ0.1) and a 6-day-old calibration — a real trend, not a flat-line sensor fault or alarm-fatigue noise.' },
    REC: { rows: [['action', 'pre-start Aerator-A'], ['window', 'act now (~70 min lead)']],
           note: 'The engine recommends acting while DO is still 4.6 — before the breach, while it is cheap.' },
    LLM: { rows: [['ramp', '60%'], ['notify', 'shift-lead'], ['confidence', '0.86']],
           note: 'The LLM composes the action and its reasoning. When it is confident, this is the path taken.' },
    RUL: { rows: [['rule', 'SOP-DO-01'], ['output', 'Aerator-A ON 100%']],
           note: 'Deterministic fail-safe: DO < 4.6 mg/L AND trend ↓ ⇒ Aerator-A ON 100%. Always available — no model needed. This is where an LLM error reroutes.' },
    APR: { rows: [['gate', 'human approval'], ['policy', 'no auto-execute']],
           note: 'Nothing runs until a human signs. Approve / hold / reject — and every choice is logged, whichever branch produced it.' },
    EXE: { rows: [['result', 'DO holds ~4.5 mg/L'], ['audit', 'work-order logged'], ['reversible', 'yes']],
           note: 'Aerator-A switched ON via the handler; the work-order is logged and reversible.' }
  };

  /* reasoning traces map to REAL engine kinds (ADR-010 IN-4) — AC-6/AC-9 honesty */
  const TRACE = {
    happy: [
      { kind: 'query', step_id: 'ingest', summary: 'Read DO, biomass and aerator state for pond P-12', detail: { stream: 'do_mg_l', latest: 4.6 } },
      { kind: 'rule', step_id: 'trend-guard', summary: 'DO trend −0.16 mg/L·min over 18 min — projected to cross the 4.0 action line in ~70 min', detail: { action_line: 4.0, eta_min: 70 } },
      { kind: 'query', step_id: 'cross-check', summary: 'Probe-B reads 4.7 mg/L (Δ0.1); calibration 6 d → sensor confidence HIGH', detail: { probe_b: 4.7, calib_days: 6, confidence: 'HIGH' } },
      { kind: 'llm', step_id: 'compose', summary: 'Composed action: pre-start Aerator-A, ramp to 60%, notify shift-lead', detail: { confidence: 0.86, ramp: '60%' } }
    ],
    fault: [
      { kind: 'query', step_id: 'ingest', summary: 'Read DO, biomass and aerator state for pond P-12', detail: { stream: 'do_mg_l', latest: 4.6 } },
      { kind: 'rule', step_id: 'trend-guard', summary: 'DO trend −0.16 mg/L·min over 18 min — projected to cross the 4.0 action line in ~70 min', detail: { action_line: 4.0, eta_min: 70 } },
      { kind: 'query', step_id: 'cross-check', summary: 'Probe-B reads 4.7 mg/L (Δ0.1); calibration 6 d → sensor confidence HIGH', detail: { probe_b: 4.7, calib_days: 6, confidence: 'HIGH' } },
      { kind: 'llm', step_id: 'compose', summary: 'LLM compose returned low confidence (0.41 < 0.70 gate) — not trusted; rerouting to the deterministic fail-safe', detail: { confidence: 0.41, gate: 0.70, decision: 'reroute' } },
      { kind: 'rule', step_id: 'fail-safe', summary: 'Deterministic fail-safe SOP-DO-01: DO<4.6 & trend↓ ⇒ Aerator-A ON 100%', detail: { sop: 'SOP-DO-01', output: 'Aerator-A ON 100%' } }
    ]
  };

  const CAPTIONS = [
    ['Ready — press ▶ to run the pipeline, or ⏭ to step through it.'],
    ['Ingesting live signals for pond P-12 — DO, biomass, aerator state.'],
    ['Trend caught early: DO is falling toward the 4.0 action line, ~70 min out.'],
    ['Cross-checked against probe-B — sensor confidence HIGH, not a false alarm.'],
    ['The engine recommends acting now, while there is still lead time.'],
    ['The LLM composed the action — one proposal is waiting for your approval.',
     'LLM compose was low-confidence → rerouted to the deterministic fail-safe. Still waiting for your approval.']
  ];
  const RUN_STEPS = 5;

  const CHIP = {
    pending: ['s-neutral', 'pending'], active: ['s-info', 'active'],
    done: ['s-ok', 'done'], error: ['s-crit', 'error'], skipped: ['s-neutral', 'skipped']
  };
  const KIND_BADGE = { rule: 's-warn', llm: 's-info', query: 's-ok' };

  /* ---- module state ---- */
  let isOpen = false, scope = null, overlayEl = null, mode = 'happy';
  let nodeEls = {}, edgeEls = {}, taskEls = {}, tokenEl = null, captionEl = null;
  let dotsEl = null, playBtn = null, faultBtn = null, inboxEl = null;
  let lanes = {}, propCard = null;
  let stepIndex = 0, playing = false, playTimer = null;

  function nodeById(id) { return NODES.find(n => n.id === id); }
  // horizontal flow: edges leave the right edge of the source, enter the left edge of the target
  function srcPt(id) { const n = nodeById(id); return { x: n.cx + HW, y: n.cy }; }
  function dstPt(id) { const n = nodeById(id); return { x: n.cx - HW, y: n.cy }; }

  /* ============================================================
     Launcher (mounted by app.js into the header, like LlmControl)
     ============================================================ */
  function mountLauncher(host) {
    if (!host) return;
    host.appendChild(h('button', { class: 'story-launch', onClick: open, title: 'Run the guided story (S)' },
      [icon('play'), 'Story']));
    // persistent launch hotkey 'S' (not in app.js VIEWS A–E, so no collision).
    // App-lifetime listener — intentional, not a teardown-scoped leak.
    window.addEventListener('keydown', (e) => {
      if (isOpen) return;
      const tag = e.target && e.target.tagName;
      if (tag && /input|textarea|select/i.test(tag)) return;
      if (e.key === 's' || e.key === 'S') { e.preventDefault(); open(); }
    });
  }

  /* ============================================================
     Open / close — the lifecycle teardown contract (AC-13)
     ============================================================ */
  function open() {
    if (isOpen) return;
    isOpen = true;
    scope = M.scope('story');
    build();
  }
  function close() {
    if (!isOpen) return;
    isOpen = false;
    pause();
    if (scope) scope.kill();           // kills timers, WAAPI anims, the keydown listener
    scope = null;
    if (overlayEl && overlayEl.parentNode) overlayEl.parentNode.removeChild(overlayEl);
    overlayEl = null; nodeEls = {}; edgeEls = {}; taskEls = {};
    tokenEl = null; captionEl = null; dotsEl = null; playBtn = null; faultBtn = null;
    inboxEl = null; lanes = {}; propCard = null; stepIndex = 0; playing = false; playTimer = null;
  }

  /* ============================================================
     Build the overlay DOM (two-axis layout — AC-4)
     ============================================================ */
  function build() {
    overlayEl = h('div', { class: 'story-overlay', role: 'dialog', 'aria-label': 'OCT story mode — aquaculture' });

    // ---- top bar: identity · progress dots · transport · exit ----
    const top = h('div', { class: 'story-top' }, [
      h('div', { class: 'story-id' }, [
        h('div', { class: 'eyebrow' }, 'Story mode · Aquaculture'),
        h('h2', null, 'A falling oxygen trend becomes a governed action')
      ]),
      h('div', { class: 'flex' })
    ]);
    dotsEl = h('div', { class: 'story-dots' });
    for (let i = 0; i < RUN_STEPS; i++) dotsEl.appendChild(h('span', { class: 'dot', title: 'Step ' + (i + 1) }));
    top.appendChild(dotsEl);
    top.appendChild(buildTransport());
    top.appendChild(h('button', { class: 'iconbtn', onClick: close, title: 'Exit story (Esc)' }, [icon('x'), 'Exit']));
    overlayEl.appendChild(top);

    // ---- body: details LEFT, overview + control RIGHT ----
    const body = h('div', { class: 'story-body' });
    const detail = h('div', { class: 'story-detail' }, [
      h('div', { class: 'col-head' }, [
        h('div', { class: 'eyebrow' }, 'Pipeline tasks · all visible'),
        h('h3', null, 'What the engine did, step by step')
      ])
    ]);
    renderTasks(detail);
    body.appendChild(detail);

    const right = h('div', { class: 'story-right' });
    const stage = h('div', { class: 'story-stage' });
    renderDAG(stage);
    right.appendChild(stage);
    right.appendChild(buildControl());
    body.appendChild(right);
    overlayEl.appendChild(body);

    document.body.appendChild(overlayEl);

    // keyboard in CAPTURE phase so A–E never reach the console behind us (AC-11/AC-14)
    scope.on(window, 'keydown', onKey, true);

    applyStep(0);
    updateDots();
  }

  function buildTransport() {
    const t = h('div', { class: 'story-transport' });
    playBtn = h('button', { class: 'iconbtn', onClick: togglePlay, title: 'Play / pause (Space)' }, [icon('play'), 'Play']);
    t.appendChild(playBtn);
    t.appendChild(h('button', { class: 'iconbtn', onClick: () => { pause(); stepForward(true); }, title: 'Step (→)' }, [icon('chevron'), 'Step']));
    t.appendChild(h('button', { class: 'iconbtn', onClick: restart, title: 'Restart (R)' }, [icon('refresh'), 'Restart']));
    faultBtn = h('button', { class: 'iconbtn', onClick: toggleFault, title: 'Run the LLM-fault scenario (shows the fail-safe reroute)' }, [icon('anomaly'), 'Simulate LLM fault']);
    t.appendChild(faultBtn);
    return t;
  }
  function updatePlayBtn() {
    if (!playBtn) return;
    clear(playBtn);
    playBtn.appendChild(icon('play'));
    playBtn.appendChild(document.createTextNode(playing ? 'Pause' : 'Play'));
  }

  /* ============================================================
     LEFT axis — all task detail cards (active-task blink)
     ============================================================ */
  function renderTasks(host) {
    TASK_ORDER.forEach(id => {
      const n = nodeById(id), meta = TASKS[id];
      const card = h('div', { class: 'task-card state-pending' + (n.branch ? ' is-branch' : ''), dataset: { task: id } });
      card.appendChild(h('div', { class: 'task-top' }, [
        h('span', { class: 'task-n' }, n.n),
        h('span', { class: 'task-name' }, n.name),
        h('span', { class: 'badge task-chip s-neutral' }, 'pending')
      ]));
      if (meta.rows && meta.rows.length) {
        card.appendChild(h('div', { class: 'task-detail' }, meta.rows.map(r =>
          h('div', { class: 'task-row' }, [h('span', { class: 'k' }, r[0]), h('span', { class: 'v' }, r[1])]))));
      }
      if (meta.note) card.appendChild(h('div', { class: 'task-note' }, meta.note));
      card.addEventListener('click', () => focusNode(id));
      taskEls[id] = card;
      host.appendChild(card);
    });
  }

  /* ============================================================
     RIGHT axis — branching DAG (AC-2)
     ============================================================ */
  function renderDAG(host) {
    host.appendChild(legend());
    const svg = s('svg', {
      class: 'dag-svg', viewBox: '0 0 880 240', xmlns: SVGNS, role: 'img',
      'aria-label': 'Branching pipeline: ingest, detect-trend, validate, recommend, then LLM-compose or deterministic rule fail-safe, human approve gate, execute with audit'
    });
    EDGES.forEach(e => {
      const a = srcPt(e.from), b = dstPt(e.to);
      const ln = s('line', { class: 'dag-edge is-idle', 'data-edge': e.id, x1: a.x, y1: a.y, x2: b.x, y2: b.y });
      edgeEls[e.id] = ln; svg.appendChild(ln);
    });
    tokenEl = s('circle', { class: 'dag-token', r: 4.5, cx: 0, cy: 0, style: { opacity: '0' } });
    svg.appendChild(tokenEl);
    NODES.forEach(n => svg.appendChild(renderNode(n)));
    host.appendChild(svg);
    captionEl = h('div', { class: 'story-caption' }, '');
    host.appendChild(captionEl);
  }

  function legend() {
    return h('div', { class: 'dag-legend' }, [
      h('span', { class: 'lg' }, [h('span', { class: 'sw taken' }), 'taken']),
      h('span', { class: 'lg' }, [h('span', { class: 'sw alt' }), 'alt path']),
      h('span', { class: 'lg' }, [h('span', { class: 'sw fail' }), 'fail-safe reroute']),
      h('span', { class: 'lg' }, [h('span', { class: 'nd query' }), 'query']),
      h('span', { class: 'lg' }, [h('span', { class: 'nd llm' }), 'LLM']),
      h('span', { class: 'lg' }, [h('span', { class: 'nd rule' }), 'rule'])
    ]);
  }

  function renderNode(node) {
    const g = s('g', { class: 'dag-node', 'data-node': node.id, 'data-state': 'pending', 'data-kind': node.kind || '', transform: 'translate(' + node.cx + ',' + node.cy + ')' });
    g.appendChild(s('rect', { class: 'node-box', x: -BOX_W / 2, y: -HH, width: BOX_W, height: BOX_H, rx: 9 }));
    g.appendChild(s('text', { class: 'node-label', x: 0, y: -1, 'text-anchor': 'middle' }, node.name));
    if (node.kind) g.appendChild(s('text', { class: 'node-kind ' + node.kind, x: 0, y: 12, 'text-anchor': 'middle' }, node.kind.toUpperCase()));
    else if (node.sub) g.appendChild(s('text', { class: 'node-sub', x: 0, y: 12, 'text-anchor': 'middle' }, node.sub));
    const badge = s('g', { class: 'state-badge', transform: 'translate(' + (BOX_W / 2 - 3) + ',' + (-HH + 3) + ')' });
    g.appendChild(badge);
    g.addEventListener('click', () => focusNode(node.id));
    nodeEls[node.id] = { g: g, badge: badge };
    return g;
  }

  /* state badge: state = colour + ICON + label (the AC-10 static floor) */
  function drawBadge(badge, state) {
    clear(badge);
    if (state === 'done') {
      badge.appendChild(s('circle', { r: 8, cx: 0, cy: 0, style: { fill: 'var(--ok)' } }));
      badge.appendChild(s('path', { d: 'M -3.2 0 l 2.2 2.6 l 4.4 -5.2', style: { fill: 'none', stroke: '#07120c', strokeWidth: '1.7', strokeLinecap: 'round', strokeLinejoin: 'round' } }));
    } else if (state === 'error') {
      badge.appendChild(s('circle', { r: 8, cx: 0, cy: 0, style: { fill: 'var(--crit)' } }));
      badge.appendChild(s('path', { d: 'M -3 -3 l 6 6 M 3 -3 l -6 6', style: { stroke: '#fff', strokeWidth: '1.7', strokeLinecap: 'round' } }));
    } else if (state === 'active') {
      badge.appendChild(s('circle', { r: 7, cx: 0, cy: 0, style: { fill: 'none', stroke: 'var(--accent)', strokeWidth: '2' } }));
      badge.appendChild(s('circle', { r: 2.6, cx: 0, cy: 0, style: { fill: 'var(--accent)' } }));
    } else if (state === 'skipped') {
      badge.appendChild(s('circle', { r: 8, cx: 0, cy: 0, style: { fill: 'var(--bg-3)', stroke: 'var(--line-strong)', strokeWidth: '1' } }));
      badge.appendChild(s('path', { d: 'M -3 -3 l 6 6', style: { stroke: 'var(--tx-3)', strokeWidth: '1.5', strokeLinecap: 'round' } }));
    }
    // pending: empty
  }

  /* ============================================================
     RIGHT bottom — scene-6 control surface (AC-5/AC-6)
     ============================================================ */
  function buildControl() {
    const ctl = h('div', { class: 'story-control' });
    inboxEl = h('div', { class: 'ctl-inbox' }, [h('span', { class: 'led' }), h('span', { class: 'inbox-txt' }, 'watching · no action pending')]);
    ctl.appendChild(h('div', { class: 'ctl-head' }, [h('div', { class: 'eyebrow' }, 'Action control surface'), inboxEl]));
    const kb = h('div', { class: 'kanban' });
    lanes = {};
    [['proposed', 'Proposed'], ['approved', 'Approved'], ['executed', 'Executed']].forEach(pair => {
      const lbody = h('div', { class: 'lane-body' });
      const count = h('span', { class: 'lane-count' }, '0');
      const lane = h('div', { class: 'lane', dataset: { lane: pair[0] } }, [
        h('div', { class: 'lane-head' }, [h('span', null, pair[1]), count]), lbody
      ]);
      lanes[pair[0]] = { lane: lane, body: lbody, count: count };
      kb.appendChild(lane);
    });
    ctl.appendChild(kb);
    return ctl;
  }

  function emitProposal(kind) {
    clearLanes();
    propCard = buildPropCard(kind);
    lanes.proposed.body.appendChild(propCard);
    updateLaneCounts();
    armInbox();
  }
  function buildPropCard(kind) {
    const card = h('div', { class: 'prop-card' });
    const isRule = kind === 'rule';
    card._kind = isRule ? 'rule' : 'llm';
    card._band = h('div', { class: 'pc-band' });
    card.appendChild(card._band);
    card.appendChild(h('div', { class: 'pc-title' }, isRule ? 'Aerator-A ON 100% — SOP-DO-01 (fail-safe)' : 'Pre-start Aerator-A — ramp to 60%'));
    card.appendChild(h('div', { class: 'pc-meta' }, isRule ? 'Aerator-A · pond P-12 · deterministic fail-safe' : 'Aerator-A · pond P-12 · confidence 86%'));
    card._actions = h('div', { class: 'pc-actions' });
    card.appendChild(card._actions);
    const why = h('div', { class: 'pc-why' }, O.reasoningTrace(isRule ? TRACE.fault : TRACE.happy));
    card.appendChild(why);
    setPropPhase(card, 'proposed');
    return card;
  }
  function whyButton(card) {
    const btn = h('button', { class: 'btn ghost sm', onClick: () => {
      const o = card.classList.toggle('why-open');
      btn.textContent = o ? 'Hide why' : 'Why?';
    } }, card.classList.contains('why-open') ? 'Hide why' : 'Why?');
    return btn;
  }
  function setPropPhase(card, phase) {
    card._phase = phase;
    const bandMap = {
      proposed: ['s-crit', 'Proposed — awaiting approval'],
      approved: ['s-info', 'Approved — ready to execute'],
      executed: ['s-ok', 'Executed — handler dispatched'],
      rejected: ['s-neutral', 'Dismissed — no action taken']
    };
    const bm = bandMap[phase];
    clear(card._band);
    card._band.appendChild(h('span', { class: 'badge solid ' + bm[0] }, bm[1]));
    card._band.appendChild(h('span', { class: 'badge ' + KIND_BADGE[card._kind], style: { textTransform: 'none' } }, card._kind));
    clear(card._actions);
    card._actions.appendChild(whyButton(card));
    if (phase === 'proposed') {
      card._actions.appendChild(h('button', { class: 'btn danger sm', onClick: rejectProposal }, [icon('x', { width: 14, height: 14 }), 'Reject']));
      card._actions.appendChild(h('button', { class: 'btn primary sm', onClick: approveProposal }, [icon('check', { width: 14, height: 14 }), 'Approve']));
    } else if (phase === 'approved') {
      card._actions.appendChild(h('button', { class: 'btn ok sm', onClick: executeProposal }, [icon('play', { width: 14, height: 14 }), 'Execute']));
    } else if (phase === 'executed') {
      if (!card.querySelector('.pc-receipt'))
        card.appendChild(h('div', { class: 'pc-receipt' }, [icon('receipt', { width: 13, height: 13 }), 'WO-AQ-7731 · reversible · audit#a3f1 logged']));
    } else if (phase === 'rejected') {
      card._actions.appendChild(h('button', { class: 'btn ghost sm', onClick: () => { setState('APR', 'active'); setState('EXE', 'pending'); setPropPhase(card, 'proposed'); armInbox(); } }, 'Undo'));
    }
  }
  function moveCard(toLane) {
    if (!propCard) return;
    // Synchronous reparent is the load-bearing move; the slide/fade is the
    // animation. View Transitions are an OPTIONAL 1-line enhancement only and
    // never load-bearing (PLAN-0033 technical contract) — so Motion drives it.
    lanes[toLane].body.appendChild(propCard);
    updateLaneCounts();
    // fill:'none' so a stalled timeline never strands the card dimmed/offset —
    // it falls back to the card's resting style (full opacity, no transform).
    if (scope) scope.tween(propCard, [{ opacity: 0.25, transform: 'translateY(6px)' }, { opacity: 1, transform: 'none' }], { duration: 300, fill: 'none' });
  }
  function clearLanes() {
    Object.keys(lanes).forEach(k => { clear(lanes[k].body); lanes[k].count.textContent = '0'; });
    propCard = null;
  }
  function updateLaneCounts() {
    Object.keys(lanes).forEach(k => { lanes[k].count.textContent = String(lanes[k].body.children.length); });
  }
  function armInbox() {
    if (!inboxEl) return;
    inboxEl.classList.add('is-armed');
    inboxEl.querySelector('.inbox-txt').textContent = '1 action awaiting approval';
  }
  function disarmInbox() {
    if (!inboxEl) return;
    inboxEl.classList.remove('is-armed');
    inboxEl.querySelector('.inbox-txt').textContent = 'watching · no action pending';
  }

  /* approve / execute / reject — the actionable "after" phase (AC-5).
     The fail-safe (rule) proposal goes through the SAME gate as the LLM
     one — that is the moat beat (AC-3): error is still governed + reversible. */
  function approveProposal() {
    if (!propCard) return;
    setState('APR', 'done');
    setState('EXE', 'active');
    setEdge('e_apr_exe', 'taken', true);
    setPropPhase(propCard, 'approved');
    moveCard('approved');
    caption('Approved. Nothing ran until you signed.');
  }
  function executeProposal() {
    if (!propCard) return;
    setState('EXE', 'done');
    setPropPhase(propCard, 'executed');
    moveCard('executed');
    disarmInbox();
    caption('Executed and logged — reversible. The whole chain, including who approved it, is on the audit trail.');
  }
  function rejectProposal() {
    if (!propCard) return;
    setState('APR', 'skipped');
    setState('EXE', 'skipped');
    setPropPhase(propCard, 'rejected');
    disarmInbox();
    caption('Dismissed — no action taken. The decision and who made it are still logged.');
  }

  /* ============================================================
     State machine — applyStep(k) is a PURE snapshot of the visual
     state at run-step k, so forward / back / restart all just re-apply.
     ============================================================ */
  function setState(id, state) {
    const ne = nodeEls[id];
    if (ne) { ne.g.setAttribute('data-state', state); drawBadge(ne.badge, state); }
    const te = taskEls[id];
    if (te) {
      te.classList.remove('state-pending', 'state-active', 'state-done', 'state-error', 'state-skipped');
      te.classList.add('state-' + state);
      const chip = te.querySelector('.task-chip');
      if (chip) { const m = CHIP[state]; chip.className = 'badge task-chip ' + m[0]; chip.textContent = m[1]; }
      if (state === 'active' && te.scrollIntoView) te.scrollIntoView({ block: 'nearest' });
    }
  }
  function setEdge(id, type, flow) {
    const e = edgeEls[id];
    if (e) e.setAttribute('class', 'dag-edge type-' + type + (flow && !M.reduced() ? ' flow' : ''));
  }
  function caption(t) { if (captionEl) captionEl.textContent = t; }

  function resetVisual() {
    NODES.forEach(n => setState(n.id, 'pending'));
    EDGES.forEach(e => { if (edgeEls[e.id]) edgeEls[e.id].setAttribute('class', 'dag-edge is-idle'); });
    if (tokenEl) tokenEl.style.opacity = '0';
    clearLanes();
    disarmInbox();
  }

  function applyStep(k) {
    resetVisual();
    const fault = mode === 'fault';
    const lit = (id, current) => setState(id, current ? 'active' : 'done');

    if (k >= 1) lit('ING', k === 1);
    if (k >= 2) { lit('DET', k === 2); setEdge('e_ing_det', 'taken', true); }
    if (k >= 3) { lit('VAL', k === 3); setEdge('e_det_val', 'taken', true); }
    if (k >= 4) { lit('REC', k === 4); setEdge('e_val_rec', 'taken', true); }
    if (k >= 5) {
      setState('REC', 'done');
      if (!fault) {
        setEdge('e_rec_llm', 'taken', true);
        setEdge('e_rec_rul', 'alt', false);
        setState('LLM', 'done');
        setState('RUL', 'skipped');
        setEdge('e_llm_apr', 'taken', true);
      } else {
        setState('LLM', 'error');
        setEdge('e_rec_llm', 'alt', false);
        setEdge('e_rec_rul', 'fail', true);
        setState('RUL', 'done');
        setEdge('e_rul_apr', 'taken', true);
      }
      setState('APR', 'active');          // the gate lights — awaiting a human, NOT auto-advanced
      emitProposal(fault ? 'rule' : 'llm');
    }
    caption(CAPTIONS[k][fault ? 1 : 0] || CAPTIONS[k][0]);
  }

  /* token dot travels the newly-taken edge when stepping forward (AC-2) */
  function tokenForStep(k) {
    if (k === 2) travelToken('ING', 'DET', false);
    else if (k === 3) travelToken('DET', 'VAL', false);
    else if (k === 4) travelToken('VAL', 'REC', false);
    else if (k === 5) travelToken('REC', mode === 'fault' ? 'RUL' : 'LLM', mode === 'fault');
  }
  function travelToken(fromId, toId, fail) {
    if (!tokenEl || !scope) return;
    const a = srcPt(fromId), b = dstPt(toId);
    tokenEl.setAttribute('class', 'dag-token' + (fail ? ' fail' : ''));
    tokenEl.style.opacity = '1';
    scope.travel(tokenEl, a.x, a.y, b.x, b.y, { duration: 680 });
    // hide via a reliable timer, NOT the animation's finish event — a throttled
    // tab may never fire 'finish', which would strand the dot at opacity 1.
    scope.after(M.reduced() ? 60 : 760, () => { if (tokenEl) tokenEl.style.opacity = '0'; });
  }

  /* ============================================================
     Transport: play / pause / step / restart / fault (AC-11)
     ============================================================ */
  function stepForward(animate) {
    if (stepIndex >= RUN_STEPS) return;
    stepIndex++;
    applyStep(stepIndex);
    if (animate) tokenForStep(stepIndex);
    updateDots();
  }
  function stepBack() {
    if (stepIndex <= 0) return;
    pause();
    stepIndex--;
    applyStep(stepIndex);
    updateDots();
  }
  function restart() {
    pause();
    stepIndex = 0;
    applyStep(0);
    updateDots();
  }
  function play() {
    if (playing || stepIndex >= RUN_STEPS) return;
    playing = true; updatePlayBtn(); scheduleNext();
  }
  function scheduleNext() {
    playTimer = scope.after(stepIndex === 0 ? 320 : 1080, () => {
      stepForward(true);
      if (playing && stepIndex < RUN_STEPS) scheduleNext();
      else { playing = false; updatePlayBtn(); }
    });
  }
  function pause() {
    playing = false;
    if (playTimer != null && scope) { scope.cancelTimer(playTimer); playTimer = null; }
    updatePlayBtn();
  }
  function togglePlay() { playing ? pause() : play(); }
  function toggleFault() {
    mode = mode === 'fault' ? 'happy' : 'fault';
    if (faultBtn) faultBtn.classList.toggle('is-on', mode === 'fault');
    restart();
  }

  function updateDots() {
    if (!dotsEl) return;
    Array.prototype.forEach.call(dotsEl.children, (d, i) => {
      d.classList.toggle('done', stepIndex > i + 1);
      d.classList.toggle('active', stepIndex === i + 1);
    });
  }

  /* clicking a node or a task card cross-highlights both (AC-4) */
  function focusNode(id) {
    Object.keys(nodeEls).forEach(k => nodeEls[k].g.classList.toggle('is-focus', k === id));
    Object.keys(taskEls).forEach(k => taskEls[k].classList.toggle('is-focus', k === id));
    const te = taskEls[id];
    if (te && te.scrollIntoView) te.scrollIntoView({ block: 'nearest' });
  }

  /* ---- keyboard (capture phase; A–E swallowed so the console behind us
     doesn't switch tabs — AC-11/AC-14) ---- */
  function onKey(e) {
    if (!isOpen) return;
    const tag = e.target && e.target.tagName;
    if (tag && /input|textarea|select/i.test(tag)) return;
    const k = e.key;
    if (k === ' ' || k === 'Spacebar') { e.preventDefault(); togglePlay(); }
    else if (k === 'ArrowRight') { e.preventDefault(); pause(); stepForward(true); }
    else if (k === 'ArrowLeft') { e.preventDefault(); stepBack(); }
    else if (k === 'r' || k === 'R') { e.preventDefault(); restart(); }
    else if (k === 'Escape') { e.preventDefault(); close(); }
    else if (/^[a-eA-E]$/.test(k)) { e.stopPropagation(); }   // keep the console behind us stable
  }

  window.OCT.ViewStory = {
    mountLauncher: mountLauncher,
    open: open,
    close: close,
    /* verification probe (AC-13 leak check): { open, step, mode, motion:{...,total} } */
    _probe: function () { return { open: isOpen, step: stepIndex, mode: mode, motion: O.Motion.activeCount() }; }
  };
})();
