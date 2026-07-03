/* ============================================================
   Story mode — PLAN-0033 Phase C.

   C0 (shipped) de-risked the technique on ONE rich scene (the
   branching pipeline). C1 generalises that into a SCENES REGISTRY
   driven by a small generic shell, then layers the pain-first arc
   around the proven pipeline:

     1. Hook      — cold-open on the buyer's OWN pain (DO falling at
                    2 a.m.), predictive not cartoon: the trend is
                    caught on the way down with lead time + $/biomass
                    at stake. Couples straight into scene 2 (SD-A).
     2. จับได้+คุณคุม — detect → approve, governance-as-offense; a hero
                    decision card (re-housing the View-B grammar with
                    shared primitives) + the 🌟 fail-safe SELF-CATCH:
                    when the LLM is unsure it reroutes to the
                    deterministic rule path and STILL waits for your
                    signature (ADR-010 IN-4 → error is still governed).
     3. Pipeline  — the C0 branching-DAG + two-axis layout + scene-6
                    control surface, preserved verbatim as a scene.

   Architecture (the lifecycle teardown contract, AC-13):
     • ONE shell Motion scope per open (owns the capture-phase keyboard
       nav listener), killed on close.
     • ONE scene Motion scope per scene, killed on scene-leave — so
       cycling scenes reclaims every tween/timer/listener deterministically
       and O.Motion.activeCount().total returns to 0.
   Each scene is a factory: create({scope, host, advance}) -> controller
     { title, stepCount, alt?, applyStep(k), enterStep?(k), setAlt?(on) }.
   The shell owns the generic stepper (play/step/back/restart), the scene
   dots, the alt-toggle, and scene nav; scenes stay declarative.

   Additive overlay (SD-C): coexists with Views A–E, never replaces the
   working console (AC-14). Synthetic Tier-1 mirror data only (ADR-0015
   D1). No new backend. Default driver = WAAPI/rAF (offline, AC-12); the
   GSAP seam (Motion.useDriver) is reserved with no scene-code change.
   ============================================================ */
(function () {
  'use strict';
  const O = window.OCT;
  const { h, clear, icon } = O;
  const M = O.Motion;
  const SVGNS = 'http://www.w3.org/2000/svg';

  /* tiny SVG hyperscript (h() builds HTML-namespaced nodes) — shared by
     the pipeline DAG and the Hook sparkline */
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

  /* ============================================================
     Shared scenario reality (single source — the SAME incident every
     scene narrates, so the numbers never contradict each other). The
     reasoning traces map to REAL engine kinds (ADR-010 IN-4) — the
     AC-6/AC-9 honesty anchor reused by scene 2 (card) + scene 3 (DAG).
     ============================================================ */
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
  const PROP = {
    happy: { title: 'Pre-start Aerator-A — ramp to 60%', meta: 'Aerator-A · pond P-12 · confidence 86%', kind: 'llm' },
    fault: { title: 'Aerator-A ON 100% — SOP-DO-01 (fail-safe)', meta: 'Aerator-A · pond P-12 · deterministic fail-safe', kind: 'rule' }
  };
  const KIND_BADGE = { rule: 's-warn', llm: 's-info', query: 's-ok' };
  const POND_ENTITY = { object_type: 'Pond', primary_key: 'P-12', title: 'Pond P-12' };

  /* ============================================================
     SCENE 1 — Hook (NEW). Pain-first cold-open. Leads with THEIR
     problem (DO falling at 2 a.m.), not our mechanism. Predictive:
     the trend is caught on the way DOWN with lead time to the 4.0
     action line — no cartoon crash→snap-back. $/biomass attached.
     ============================================================ */
  function createHookScene(ctx) {
    const scope = ctx.scope, host = ctx.host;

    // sparkline geometry: DO 5.0 → y30, 3.8 → y180 over plot x[60..520]
    const yOf = (doVal) => 30 + (5.0 - doVal) / 1.2 * 150;
    const OBS = [[60, 4.80], [100, 4.76], [140, 4.72], [180, 4.68], [220, 4.64], [260, 4.60], [300, 4.57]];
    const yAction = yOf(4.0);            // the 4.0 danger line
    const etaPt = [470, yAction];        // projection meets 4.0 ≈ 70 min out

    const CAP = [
      '2:30 a.m. The whole farm is asleep — but pond P-12 is not.',
      'Dissolved oxygen is slipping — 4.8 … 4.7 … 4.6 mg/L. No one is watching yet.',
      'Left alone, it crosses the 4.0 danger line in about 70 minutes. That lead time is what you have.',
      'This pond = ~16 t of biomass · about ฿2.3M. Oxygen gone by 3 a.m. — finding out at dawn is too late.',
      'What if something watched it for you — and woke you before the 4.0 line?'
    ];

    const root = h('div', { class: 'scene-hook' });
    const stage = h('div', { class: 'hook-stage' });

    // clock + place
    const clockSvg = s('svg', { class: 'hook-clock-face', viewBox: '0 0 48 48', xmlns: SVGNS, 'aria-hidden': 'true' }, [
      s('circle', { cx: 24, cy: 24, r: 21 }),
      s('line', { class: 'h-hand', x1: 24, y1: 24, x2: 24, y2: 13 }),
      s('line', { class: 'm-hand', x1: 24, y1: 24, x2: 33, y2: 24 })
    ]);
    stage.appendChild(h('div', { class: 'hook-clock' }, [
      clockSvg,
      h('div', null, [
        h('div', { class: 'hook-time mono' }, '02:30'),
        h('div', { class: 'hook-place' }, 'Shrimp farm · pond P-12')
      ])
    ]));

    // the DO sparkline — the hero of the hook
    const chart = s('svg', {
      class: 'hook-chart', viewBox: '0 0 560 210', xmlns: SVGNS, role: 'img',
      'aria-label': 'Dissolved-oxygen falling from 4.8 toward the 4.0 action line, projected to breach in about 70 minutes'
    });
    // axis hint labels
    chart.appendChild(s('text', { class: 'hk-axis', x: 30, y: yOf(5.0) + 3, 'text-anchor': 'end' }, '5.0'));
    chart.appendChild(s('text', { class: 'hk-axis', x: 30, y: yAction + 3, 'text-anchor': 'end' }, '4.0'));
    chart.appendChild(s('text', { class: 'hk-axis-u', x: 30, y: 16 }, 'mg/L'));
    // observed group (shown step 1): the 4.0 action line + the falling DO line + current value
    const gObs = s('g', { class: 'hk-layer', 'data-layer': 'obs' });
    gObs.appendChild(s('line', { class: 'hk-action', x1: 50, y1: yAction, x2: 520, y2: yAction }));
    // label sits BELOW the 4.0 line — the ETA badge lives above it near the breach
    // point, so keeping the two on opposite sides of the line avoids overlap (step 2).
    gObs.appendChild(s('text', { class: 'hk-action-lbl', x: 520, y: yAction + 15, 'text-anchor': 'end' }, 'action line · 4.0 mg/L'));
    gObs.appendChild(s('polyline', { class: 'hk-obs', points: OBS.map(p => p[0] + ',' + yOf(p[1])).join(' ') }));
    const last = OBS[OBS.length - 1];
    gObs.appendChild(s('circle', { class: 'hk-now', cx: last[0], cy: yOf(last[1]), r: 4.5 }));
    gObs.appendChild(s('text', { class: 'hk-now-lbl mono', x: last[0] - 8, y: yOf(last[1]) - 9, 'text-anchor': 'end' }, '4.6 ↓'));
    chart.appendChild(gObs);
    // projection group (shown step 2): dashed continuation + ETA badge
    const gProj = s('g', { class: 'hk-layer', 'data-layer': 'proj' });
    gProj.appendChild(s('line', { class: 'hk-proj', x1: last[0], y1: yOf(last[1]), x2: etaPt[0], y2: etaPt[1] }));
    gProj.appendChild(s('circle', { class: 'hk-breach', cx: etaPt[0], cy: etaPt[1], r: 5 }));
    const etaBadge = s('g', { class: 'hk-eta', transform: 'translate(' + (etaPt[0] + 8) + ',' + (etaPt[1] - 20) + ')' });
    etaBadge.appendChild(s('rect', { x: 0, y: 0, width: 80, height: 18, rx: 5 }));
    etaBadge.appendChild(s('text', { x: 40, y: 13, 'text-anchor': 'middle' }, '~70 min'));
    gProj.appendChild(etaBadge);
    chart.appendChild(gProj);
    stage.appendChild(chart);

    // the stake (shown step 3) — $/biomass attached
    const stake = h('div', { class: 'hook-stake', 'data-layer': 'stake' }, [
      h('div', { class: 'stk' }, [h('span', { class: 'stk-k' }, 'biomass in pond'), h('span', { class: 'stk-v' }, '~16 t')]),
      h('div', { class: 'stk' }, [h('span', { class: 'stk-k' }, 'value at risk'), h('span', { class: 'stk-v crit' }, '≈ ฿2.3M')]),
      h('div', { class: 'stk' }, [h('span', { class: 'stk-k' }, 'found at dawn'), h('span', { class: 'stk-v crit' }, 'too late')])
    ]);
    stage.appendChild(stake);

    // the turn (shown step 4) — couples into scene 2
    const turn = h('div', { class: 'hook-turn', 'data-layer': 'turn' }, [
      icon('anomaly', { width: 15, height: 15 }),
      'Something can watch this for you — and wake you before the 4.0 line'
    ]);
    stage.appendChild(turn);

    root.appendChild(stage);
    const cap = h('div', { class: 'hook-caption' }, CAP[0]);
    root.appendChild(cap);
    host.appendChild(root);

    const layers = { obs: gObs, proj: gProj, stake: stake, turn: turn };
    const shownBy = { 1: 'obs', 2: 'proj', 3: 'stake', 4: 'turn' };

    function applyStep(k) {
      cap.textContent = CAP[k] || CAP[CAP.length - 1];
      // pure snapshot: a layer is shown iff its reveal step <= k
      Object.keys(shownBy).forEach(stepN => {
        layers[shownBy[stepN]].classList.toggle('is-shown', Number(stepN) <= k);
      });
      root.classList.toggle('is-awake', k >= 1);
    }
    function enterStep(k) {
      const el = layers[shownBy[k]];
      if (el && scope) scope.tween(el, [{ opacity: 0, transform: 'translateY(6px)' }, { opacity: 1, transform: 'none' }], { duration: 360, fill: 'none' });
    }

    return { title: '2 a.m. — oxygen is falling in your pond', stepCount: 4, applyStep: applyStep, enterStep: enterStep };
  }

  /* ============================================================
     SCENE 2 — จับได้ + คุณคุม (NEW narrative; rehouses the View-B
     decision-card grammar via the SHARED exported primitives —
     O.reasoningTrace / O.entityChip — with synthetic, self-contained
     approve→execute so story mode stays hermetic + re-runnable, like
     the C0 prop-card (SD-C). View B itself is untouched.

     The 🌟 self-catch (alt-toggle): when the LLM is unsure it reroutes
     to the deterministic rule fail-safe — which STILL passes the human
     approve gate + records audit (AC-3, ADR-010 IN-4). Governance is
     the offense, not a limitation.
     ============================================================ */
  function createGovernScene(ctx) {
    const scope = ctx.scope, host = ctx.host, advance = ctx.advance;
    let mode = 'happy';                                  // 'happy' | 'fault' (self-catch)
    const prop = () => PROP[mode];

    const RAIL = {
      happy: [
        ['Caught it — before the danger line', 'Watching pond P-12 all night'],
        ['Proposes a fix + the reasons', 'DO 4.6, not yet at 4.0'],
        ['Opens the full reasoning', 'query → rule → llm · transparent'],
        ['Nothing runs before YOU sign', 'governance = the strength'],
        ['Sign → run → fully logged', 'who signed is known · reversible']
      ],
      fault: [
        ['Caught it — before the danger line', 'Watching pond P-12 all night'],
        ['Proposes a fix + the reasons', 'DO 4.6, not yet at 4.0'],
        ['🌟 AI unsure → it catches itself', '0.41 < 0.70 → rule fail-safe'],
        ['The rule still waits for you', 'an error is still governed'],
        ['Sign → rule runs → fully logged', 'safe even when the AI slips']
      ]
    };
    const CAP = {
      happy: [
        'Something watched pond P-12 all night. And it just caught something.',
        'Caught while DO is still 4.6 — before the 4.0 line. Not after the shrimp die.',
        'Here is the full reasoning: query → rule → llm. Every step is open to inspect.',
        'But it does nothing until YOU sign. That is the strength, not a limitation.',
        'Signed → the aerator runs → fully logged, who signed is known · reversible.'
      ],
      fault: [
        'Tonight, the AI that composes the action is “unsure”. Watch what the system does.',
        'Caught all the same — DO falling, before the 4.0 line.',
        'The AI is only 0.41 confident (below the 0.70 gate) → the system reroutes to the rule fail-safe on its own. It catches itself.',
        'And even though it is a rule, not the AI — it still waits for your signature. An error is still governed.',
        'Sign → rule SOP-DO-01 runs → fully logged · reversible. Safe even when the AI slips.'
      ]
    };

    const root = h('div', { class: 'scene-govern' });

    // ---- LEFT: the governance narration rail ----
    const railEls = [];
    const rail = h('div', { class: 'govern-rail' }, [
      h('div', { class: 'col-head' }, [
        h('div', { class: 'eyebrow' }, 'Caught it + you stay in control'),
        h('h3', null, 'The system shows its reasoning — then waits for you')
      ])
    ]);
    const railList = h('div', { class: 'rail-list' });
    for (let i = 0; i < 5; i++) {
      const t = h('div', { class: 'rail-t' });
      const sub = h('div', { class: 'rail-sub' });
      const beat = h('div', { class: 'rail-beat', dataset: { i: String(i) } }, [
        h('span', { class: 'rail-n' }, String(i + 1)),
        h('div', null, [t, sub])
      ]);
      railEls.push({ beat: beat, t: t, sub: sub });
      railList.appendChild(beat);
    }
    rail.appendChild(railList);
    rail.appendChild(h('div', { class: 'govern-offense' }, [
      icon('check', { width: 14, height: 14 }),
      h('span', null, 'Nothing runs before you sign · every action is logged · reversible')
    ]));
    root.appendChild(rail);

    // ---- RIGHT: the hero decision card ----
    const band = h('div', { class: 'gc-band' });
    const titleEl = h('h2', { class: 'gc-title' });
    const descEl = h('p', { class: 'gc-desc' });
    const confEl = h('div', { class: 'gc-conf' });
    const entEl = h('div', { class: 'gc-ent' });
    const traceWrap = h('div', { class: 'gc-trace' });
    const actionsEl = h('div', { class: 'gc-actions' });
    const card = h('div', { class: 'gc-card' }, [
      band,
      h('div', { class: 'gc-head' }, [titleEl, descEl, confEl,
        h('div', { class: 'gc-handler' }, [h('span', { class: 'eyebrow' }, 'Handler'), h('span', { class: 'mono' }, 'aerator.set_state')])
      ]),
      h('div', { class: 'gc-sec' }, [h('div', { class: 'eyebrow' }, 'Affected'), entEl]),
      h('div', { class: 'gc-sec' }, [h('div', { class: 'gc-trace-head' }, [h('div', { class: 'eyebrow' }, 'Reasoning trace'), h('span', { class: 'muted' }, 'read top to bottom')]), traceWrap]),
      actionsEl
    ]);
    const cap = h('div', { class: 'govern-caption' }, CAP[mode][0]);
    root.appendChild(h('div', { class: 'govern-stage' }, [card, cap]));
    host.appendChild(root);

    function renderTrace() {
      clear(traceWrap);
      traceWrap.appendChild(O.reasoningTrace(mode === 'fault' ? TRACE.fault : TRACE.happy));
    }
    function renderConf() {
      clear(confEl);
      if (mode === 'fault') {
        confEl.appendChild(h('span', { class: 'badge s-warn', style: { textTransform: 'none' } }, 'AI 0.41 ↓ → rule fail-safe'));
        confEl.appendChild(h('span', { class: 'gc-det mono' }, 'deterministic'));
      } else {
        confEl.appendChild(h('div', { class: 'gc-conf-top' }, [h('span', { class: 'eyebrow' }, 'Confidence'), h('span', { class: 'mono' }, '86%')]));
        confEl.appendChild(h('div', { class: 'meter' }, h('i', { style: { width: '86%' } })));
      }
    }
    function renderEntities() {
      clear(entEl);
      entEl.appendChild(O.entityChip(POND_ENTITY));   // no onClick → no console-nav side effect
    }
    function setBand(phase) {
      const map = {
        proposed: ['s-crit', 'Proposed — awaiting your approval'],
        executed: ['s-ok', 'Executed — handler dispatched · logged']
      };
      const m = map[phase] || map.proposed;
      clear(band);
      band.appendChild(h('span', { class: 'gc-band-icon' }, icon('anomaly', { width: 15, height: 15 })));
      band.appendChild(h('span', { class: 'gc-band-lbl' }, m[1]));
      band.appendChild(h('span', { class: 'badge solid ' + m[0], style: { marginLeft: 'auto' } }, phase));
      band.appendChild(h('span', { class: 'badge ' + KIND_BADGE[prop().kind], style: { textTransform: 'none' } }, prop().kind));
    }
    function renderActions(k) {
      clear(actionsEl);
      if (k >= 4) {
        actionsEl.appendChild(h('div', { class: 'gc-receipt' }, [
          icon('receipt', { width: 14, height: 14 }),
          'WO-AQ-7731 · audit#a3f1 · reversible'
        ]));
      } else if (k === 3) {
        actionsEl.appendChild(h('span', { class: 'gc-hint' }, 'Reject / Hold are fine too — every choice is logged'));
        const wrap = h('div', { class: 'gc-act-btns' }, [
          h('button', { class: 'btn primary', onClick: () => advance() }, [icon('check'), 'Approve']),
          h('button', { class: 'btn danger sm', onClick: () => { cap.textContent = 'Rejected — nothing runs. And the rejection is logged too.'; } }, [icon('x', { width: 14, height: 14 }), 'Reject'])
        ]);
        actionsEl.appendChild(wrap);
      } else {
        actionsEl.appendChild(h('span', { class: 'gc-hint muted' }, 'The system is proposing — nothing has run yet'));
      }
    }
    function setRail(k) {
      railEls.forEach((r, i) => {
        r.beat.classList.toggle('active', i === k);
        r.beat.classList.toggle('done', i < k);
        r.t.textContent = RAIL[mode][i][0];
        r.sub.textContent = RAIL[mode][i][1];
      });
    }

    function applyStep(k) {
      cap.textContent = CAP[mode][k] || CAP[mode][CAP[mode].length - 1];
      setRail(k);
      titleEl.textContent = prop().title;
      descEl.textContent = mode === 'fault'
        ? 'The AI missed the confidence gate → the system uses the predefined rule fail-safe'
        : 'Pre-start aeration before DO hits the 4.0 line — while it is still cheap and in time';
      renderConf();
      setBand(k >= 4 ? 'executed' : 'proposed');
      // entities + trace reveal progressively
      entEl.classList.toggle('is-hidden', k < 1);
      card.classList.toggle('trace-open', k >= 2);
      card.classList.toggle('gate-on', k === 3);
      card.classList.toggle('is-executed', k >= 4);
      renderActions(k);
    }
    function setAlt(on) {
      mode = on ? 'fault' : 'happy';
      renderTrace();              // trace shape differs happy/fault
      // shell calls restart() after setAlt → applyStep(0) reconciles the rest
    }

    renderTrace();
    renderEntities();
    return {
      title: 'Caught it — and you stay in command',
      stepCount: 4,
      alt: { label: 'What if the AI is unsure?', title: 'Show the self-catch: LLM unsure → deterministic rule fail-safe (still needs your signature)' },
      applyStep: applyStep,
      setAlt: setAlt
    };
  }

  /* ============================================================
     SCENE 3 — Branching pipeline (C0, PRESERVED). The de-risked
     vertical slice, now a registered scene: horizontal branching-DAG
     (AC-2) + LLM-compose-vs-rule-fail-safe reroute (AC-3) + two-axis
     layout (AC-4) + scene-6 control surface (AC-5/6) + static
     reduced-motion floor (AC-10). The shell drives play/step/restart;
     this factory owns the DAG, the task column and the kanban lanes.
     ============================================================ */
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

  function createPipelineScene(ctx) {
    const scope = ctx.scope, host = ctx.host;
    let mode = 'happy';
    let nodeEls = {}, edgeEls = {}, taskEls = {}, tokenEl = null, captionEl = null;
    let inboxEl = null, lanes = {}, propCard = null;

    const nodeById = (id) => NODES.find(n => n.id === id);
    const srcPt = (id) => { const n = nodeById(id); return { x: n.cx + HW, y: n.cy }; };
    const dstPt = (id) => { const n = nodeById(id); return { x: n.cx - HW, y: n.cy }; };

    const root = h('div', { class: 'scene-pipeline' });
    const detail = h('div', { class: 'story-detail' }, [
      h('div', { class: 'col-head' }, [
        h('div', { class: 'eyebrow' }, 'Pipeline tasks · all visible'),
        h('h3', null, 'What the engine did, step by step')
      ])
    ]);
    renderTasks(detail);
    root.appendChild(detail);
    const right = h('div', { class: 'story-right' });
    const stage = h('div', { class: 'story-stage' });
    renderDAG(stage);
    right.appendChild(stage);
    right.appendChild(buildControl());
    root.appendChild(right);
    host.appendChild(root);

    function renderTasks(hostEl) {
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
        hostEl.appendChild(card);
      });
    }

    function renderDAG(hostEl) {
      hostEl.appendChild(legend());
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
      hostEl.appendChild(svg);
      captionEl = h('div', { class: 'story-caption' }, '');
      hostEl.appendChild(captionEl);
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
    }

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
      card.appendChild(h('div', { class: 'pc-title' }, isRule ? PROP.fault.title : PROP.happy.title));
      card.appendChild(h('div', { class: 'pc-meta' }, isRule ? PROP.fault.meta : PROP.happy.meta));
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
      lanes[toLane].body.appendChild(propCard);
      updateLaneCounts();
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
    function approveProposal() {
      if (!propCard) return;
      setState('APR', 'done'); setState('EXE', 'active');
      setEdge('e_apr_exe', 'taken', true);
      setPropPhase(propCard, 'approved'); moveCard('approved');
      caption('Approved. Nothing ran until you signed.');
    }
    function executeProposal() {
      if (!propCard) return;
      setState('EXE', 'done');
      setPropPhase(propCard, 'executed'); moveCard('executed'); disarmInbox();
      caption('Executed and logged — reversible. The whole chain, including who approved it, is on the audit trail.');
    }
    function rejectProposal() {
      if (!propCard) return;
      setState('APR', 'skipped'); setState('EXE', 'skipped');
      setPropPhase(propCard, 'rejected'); disarmInbox();
      caption('Dismissed — no action taken. The decision and who made it are still logged.');
    }

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
      clearLanes(); disarmInbox();
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
          setEdge('e_rec_llm', 'taken', true); setEdge('e_rec_rul', 'alt', false);
          setState('LLM', 'done'); setState('RUL', 'skipped'); setEdge('e_llm_apr', 'taken', true);
        } else {
          setState('LLM', 'error'); setEdge('e_rec_llm', 'alt', false); setEdge('e_rec_rul', 'fail', true);
          setState('RUL', 'done'); setEdge('e_rul_apr', 'taken', true);
        }
        setState('APR', 'active');
        emitProposal(fault ? 'rule' : 'llm');
      }
      caption(CAPTIONS[k][fault ? 1 : 0] || CAPTIONS[k][0]);
    }
    function enterStep(k) {
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
      scope.after(M.reduced() ? 60 : 760, () => { if (tokenEl) tokenEl.style.opacity = '0'; });
    }
    function focusNode(id) {
      Object.keys(nodeEls).forEach(k => nodeEls[k].g.classList.toggle('is-focus', k === id));
      Object.keys(taskEls).forEach(k => taskEls[k].classList.toggle('is-focus', k === id));
      const te = taskEls[id];
      if (te && te.scrollIntoView) te.scrollIntoView({ block: 'nearest' });
    }

    return {
      title: 'A falling oxygen trend becomes a governed action',
      stepCount: RUN_STEPS,
      alt: { label: 'Simulate LLM fault', title: 'Run the LLM-fault scenario (shows the fail-safe reroute)' },
      applyStep: applyStep,
      enterStep: enterStep,
      setAlt: (on) => { mode = on ? 'fault' : 'happy'; }
    };
  }

  /* ============================================================
     SCENE 4 — Live intake, dual-path (NEW). Reuses the PLAN-0017
     View-E framing + the PLAN-0018 GET /llm/status readiness — builds
     none of it new (AC-7). The live-demo risk (MS-S1 cold/slow
     mid-pitch) is met with a DUAL PATH: a cached draft that *looks*
     live + a true-live "Go live" button with a HARD TIMEOUT and a
     scripted fallback that reads as deliberate. Honest frame: this is a
     SKELETON of your operation — a starting draft you refine together,
     NOT "your whole business from a sentence" (ADR-0015 D5 human gate).
     The readiness pill is a safe GET /llm/status read (INV-1 never warms).
     "Go live" makes a REAL MS-S1 extraction call — O.Intake.extract is a
     host-state call (it loads the model) — raced against a hard timeout;
     on timeout / degraded / error it falls back to the cached draft
     (deliberate — the pitch never stalls). The timeout runs through
     scope.after → reclaimed on leave (AC-13).
     ============================================================ */
  const LLM_VIS = {
    resident:    ['s-ok',      'MS-S1 resident — live ready'],
    cold:        ['s-warn',    'MS-S1 cold — cached draft stands in'],
    warming:     ['s-info',    'MS-S1 warming…'],
    unreachable: ['s-crit',    'MS-S1 offline — cached draft stands in'],
    error:       ['s-crit',    'MS-S1 error — cached draft stands in'],
    unknown:     ['s-neutral', 'MS-S1 status unknown — cached draft stands in']
  };
  const SAMPLE_SENTENCE = 'We run shrimp ponds across coastal farms. At night dissolved oxygen can crash below 4 mg/L and kill a pond within hours; we start the emergency aerator.';
  const SKELETON = {
    namespace: 'aquaculture',
    asset: 'Pond', props: ['dissolved_oxygen', 'biomass_kg'],
    site: 'Farm',
    metric: 'Dissolved oxygen below 4.0 mg/L',
    actions: ['start_aerator', 'exchange_water']
  };
  // "Go live" demo-pacing cutoff: cut over to the cached draft if the REAL
  // MS-S1 extraction (backend per-call timeout 120s) has not returned. A warm
  // gpt-oss:20b single-sentence extraction measured ~19.5s (live smoke, s71);
  // 35s gives comfortable margin for variance / one retry while still falling
  // back well before the backend's multi-retry budget. Pre-warm MS-S1 first.
  const LIVE_TIMEOUT_MS = 35000;

  function createIntakeScene(ctx) {
    const scope = ctx.scope, host = ctx.host;
    const CAP = [
      'Every buyer’s real first question: “and what about MY operation?”',
      'A cached draft appears instantly — it looks live, and a pitch never stalls.',
      'It can also come live from MS-S1. If the box is cold or slow, we fall back to the cached draft — on purpose. The demo never freezes.',
      'And this is only a SKELETON of your operation — a starting draft. Nothing is built until you review and refine it, together.'
    ];
    let liveTimer = null, liveInFlight = false, liveGen = 0;

    const root = h('div', { class: 'scene-intake' });
    const pill = h('span', { class: 'intake-pill s-neutral' }, [icon('cpu', { width: 12, height: 12 }), h('span', { class: 'led' }), h('span', { class: 'pill-txt' }, 'checking MS-S1…')]);
    root.appendChild(h('div', { class: 'intake-head' }, [
      h('div', null, [h('div', { class: 'eyebrow' }, 'Build a vertical · live'), h('h3', null, 'And what’s YOUR operation?')]),
      h('div', { class: 'flex' }), pill
    ]));
    root.appendChild(h('div', { class: 'intake-sentence' }, '“' + SAMPLE_SENTENCE + '”'));

    const statusLine = h('div', { class: 'intake-status muted' }, 'Two ways to draft — both safe on stage.');
    root.appendChild(h('div', { class: 'intake-paths' }, [
      h('button', { class: 'btn primary sm', onClick: () => showDraft(false) }, [icon('grid', { width: 14, height: 14 }), 'Use cached draft']),
      h('span', { class: 'ca-or muted' }, 'or'),
      h('button', { class: 'btn ghost sm', onClick: goLive }, [icon('bolt', { width: 14, height: 14 }), 'Go live (MS-S1)']),
      h('span', { class: 'flex' }), statusLine
    ]));
    const resil = h('div', { class: 'intake-resilience' }, [icon('bolt', { width: 13, height: 13 }), 'Live path = hard timeout → cached fallback. The fallback reads as deliberate, never a stall.']);
    root.appendChild(resil);

    const draftWrap = h('div', { class: 'intake-draft' });
    root.appendChild(draftWrap);

    const frame = h('div', { class: 'intake-frame' }, [
      icon('check', { width: 15, height: 15 }),
      h('span', null, 'A SKELETON of your operation — a starting draft, not your whole business. You review + refine it, then the engine builds it.')
    ]);
    root.appendChild(frame);
    const cap = h('div', { class: 'intake-caption' }, CAP[0]);
    root.appendChild(cap);
    host.appendChild(root);

    function drField(label, val) {
      return h('div', { class: 'dr-field' }, [h('span', { class: 'dr-k eyebrow' }, label), h('span', { class: 'dr-v mono' }, val)]);
    }
    // Map a live MS-S1 IntakePackage onto the scene's compact draft shape.
    function packageToSkeleton(pkg) {
      const m = (pkg && pkg.metric) || {};
      const parts = [m.label || 'metric'];
      if (m.direction) parts.push(m.direction);
      if (m.threshold != null && m.threshold !== '') parts.push(String(m.threshold));
      if (m.unit) parts.push(m.unit);
      const props = (((pkg && pkg.asset_role) || {}).properties || []).map(p => p.name).filter(Boolean);
      return {
        namespace: (pkg && pkg.namespace) || '—',
        asset: ((pkg && pkg.asset_role) || {}).type_name || '—',
        props: props,
        site: ((pkg && pkg.site_role) || {}).type_name || '—',
        metric: parts.join(' '),
        actions: (pkg && pkg.action_types) || []
      };
    }
    function buildSkeleton(live, data) {
      data = data || SKELETON;
      const srcBadge = live
        ? h('span', { class: 'badge s-ok' }, [h('span', { class: 'led' }), 'MS-S1 EXTRACTION'])
        : h('span', { class: 'badge s-info' }, [h('span', { class: 'led' }), 'CACHED DRAFT']);
      return h('div', { class: 'draft-card' }, [
        h('div', { class: 'dr-band' }, [srcBadge, h('span', { class: 'muted mono dr-ns' }, data.namespace), h('span', { class: 'flex' }), h('span', { class: 'muted dr-gate' }, 'nothing is generated until you confirm')]),
        h('div', { class: 'dr-grid' }, [
          drField('Asset', data.asset + ' { ' + (data.props || []).join(', ') + ' }'),
          drField('Site', data.site),
          drField('Metric', data.metric),
          drField('Actions', (data.actions || []).join(', '))
        ])
      ]);
    }
    function showDraft(live, data) {
      clear(draftWrap);
      draftWrap.appendChild(buildSkeleton(live, data));
      if (scope) scope.tween(draftWrap, [{ opacity: 0.2, transform: 'translateY(6px)' }, { opacity: 1, transform: 'none' }], { duration: 320, fill: 'none' });
    }
    // "Go live" — race the REAL MS-S1 extraction against a hard timeout.
    // O.Intake.extract is a host-state call (loads the model). On success the
    // live-extracted skeleton renders (MS-S1 EXTRACTION badge); on timeout /
    // degraded / error / unreachable it falls back to the cached draft —
    // deliberate, so the pitch never stalls (AC-7). The timer is scope-owned →
    // reclaimed on scene leave (AC-13); liveGen invalidates an in-flight call
    // when the operator resets/leaves; liveInFlight guards double-clicks.
    function goLive() {
      if (!scope || liveInFlight) return;
      const gen = liveGen;
      liveInFlight = true;
      statusLine.className = 'intake-status s-info';
      statusLine.textContent = 'MS-S1: calling live…';
      clear(draftWrap);
      const stale = () => gen !== liveGen || scope.killed;
      const finishOwned = () => {
        liveInFlight = false;
        if (liveTimer != null) { scope.cancelTimer(liveTimer); liveTimer = null; }
      };
      const fallback = (msg) => {
        if (stale()) return;
        finishOwned();
        statusLine.className = 'intake-status s-warn';
        statusLine.textContent = msg;
        showDraft(false);
      };
      liveTimer = scope.after(LIVE_TIMEOUT_MS, () => {        // hard timeout (scope-owned)
        liveTimer = null;
        fallback('MS-S1 slow → fell back to the cached draft (deliberate). The pitch never stalls.');
      });
      O.Intake.extract(SAMPLE_SENTENCE).then((r) => {
        if (stale()) return;
        if (r && r.ok && r.body && r.body.state === 'ok' && r.body.package) {
          finishOwned();
          statusLine.className = 'intake-status s-ok';
          statusLine.textContent = 'MS-S1 drafted it live — a SKELETON to refine, not your whole business.';
          showDraft(true, packageToSkeleton(r.body.package));
        } else {
          fallback('MS-S1 unavailable → cached draft (deliberate). The pitch never stalls.');
        }
      }).catch(() => fallback('MS-S1 unreachable → cached draft (deliberate). The pitch never stalls.'));
    }

    // readiness pill — a safe GET /llm/status read (INV-1: never warms)
    if (O.Llm && O.Llm.status) {
      O.Llm.status().then(r => {
        if (scope.killed) return;
        const st = (r && r.ok && r.body && r.body.state) || 'unknown';
        const v = LLM_VIS[st] || LLM_VIS.unknown;
        pill.className = 'intake-pill ' + v[0];
        const txt = pill.querySelector('.pill-txt'); if (txt) txt.textContent = v[1];
      }).catch(() => {});
    }

    function applyStep(k) {
      cap.textContent = CAP[k] || CAP[CAP.length - 1];
      root.classList.toggle('show-live', k >= 2);
      root.classList.toggle('show-frame', k >= 3);
      if (k >= 1) { if (!draftWrap.children.length) showDraft(false); }
      else {
        clear(draftWrap);
        statusLine.className = 'intake-status muted';
        statusLine.textContent = 'Two ways to draft — both safe on stage.';
        liveGen++; liveInFlight = false;                    // invalidate any in-flight live extract
        if (liveTimer != null) { scope.cancelTimer(liveTimer); liveTimer = null; }
      }
    }
    return { title: 'And what’s YOUR operation? — drafted live', stepCount: 3, applyStep: applyStep };
  }

  /* ============================================================
     SCENE 5 — Before / After (NEW). ONE honest, in-repo-sourced number
     framed as ROBUSTNESS, not an accuracy leaderboard (AC-8 / SD-D).
     Anchored on the B-γ / A2 finding: ask the same DO-breach query two
     ways — raw text-to-SQL guesses a free-text literal
     (`description LIKE '%dissolved_oxygen%'`) and SILENTLY returns
     0 rows (0 of 40 runs, aquaculture); the grounded/ontology stack
     declares the mapping and is robust across every vertical. No
     "100%", no raw-accuracy supremacy bar. The number ties to money:
     "0 rows" on a real night = no alarm = the ฿2.3M pond (scene 1).
     Source is on screen (public-repo defensibility). The external dbt
     "86%→6%" stat is NOT used (SD-D verify-before-ship gate).
     Source: benchmarks/procedure_baseline/REPORT.md §B-3.
     ============================================================ */
  function createBeforeAfterScene(ctx) {
    const scope = ctx.scope, host = ctx.host;
    const CAP = [
      'Does the governed stack actually win? Honest answer: not on a leaderboard %. Ask the same breach question two ways.',
      'Raw LLM → SQL guesses a free-text literal — and silently returns 0 rows. No error thrown. No alarm raised.',
      'The grounded stack declares the mapping (do_mg_l < 4.0). The right rows — on every vertical, not just the lucky one.',
      'Not a leaderboard %. Robustness: “0 rows” on a real night would have lost the ฿2.3M pond. Grounding closes the gap raw LLMs open.'
    ];
    function arm(side, title, sub) {
      const result = h('div', { class: 'ba-result' });
      const card = h('div', { class: 'ba-arm ' + side }, [
        h('div', { class: 'ba-arm-head' }, [h('span', { class: 'ba-arm-title' }, title), h('span', { class: 'ba-arm-sub mono muted' }, sub)]),
        result
      ]);
      return { card: card, result: result };
    }
    const rawArm = arm('raw', 'Raw LLM → SQL', 'text-to-SQL, no ontology');
    const grdArm = arm('grounded', 'Grounded (ontology)', 'declared mapping');
    const verdict = h('div', { class: 'ba-verdict' });

    const root = h('div', { class: 'scene-ba' }, [
      h('div', { class: 'ba-head' }, [
        h('div', { class: 'eyebrow' }, 'Before / After · same question'),
        h('h3', null, '“Which ponds breached DO last night?”')
      ]),
      h('div', { class: 'ba-split' }, [rawArm.card, grdArm.card]),
      verdict
    ]);
    const cap = h('div', { class: 'ba-caption' }, CAP[0]);
    root.appendChild(cap);
    host.appendChild(root);

    function setRaw(on) {
      clear(rawArm.result);
      if (!on) return;
      rawArm.result.appendChild(h('div', { class: 'ba-sql mono' }, "… WHERE description LIKE '%dissolved_oxygen%'"));
      rawArm.result.appendChild(h('div', { class: 'ba-rows crit' }, [icon('anomaly', { width: 14, height: 14 }), '0 rows — a silent miss']));
    }
    function setGrounded(on) {
      clear(grdArm.result);
      if (!on) return;
      grdArm.result.appendChild(h('div', { class: 'ba-sql mono' }, '… WHERE do_mg_l < 4.0   (ontology-declared)'));
      grdArm.result.appendChild(h('div', { class: 'ba-rows ok' }, [icon('check', { width: 14, height: 14 }), 'breach caught · rows returned']));
    }
    function setVerdict(on) {
      clear(verdict);
      if (!on) return;
      verdict.appendChild(h('div', { class: 'ba-num' }, [
        h('span', { class: 'ba-num-v mono' }, '0 of 40'),
        h('span', { class: 'ba-num-k' }, 'raw runs returned the aquaculture breach — consistent, not luck')
      ]));
      verdict.appendChild(h('div', { class: 'ba-frame' }, 'Grounding closes the gap raw LLMs open. The win is robustness, not a leaderboard % — “0 rows” on a real night = no alarm = the ฿2.3M pond.'));
      verdict.appendChild(h('div', { class: 'ba-src mono muted' }, 'source: benchmarks/procedure_baseline/REPORT.md §B-3 (B-γ · gpt-oss:20b · 2026-06-17)'));
    }

    function applyStep(k) {
      cap.textContent = CAP[k] || CAP[CAP.length - 1];
      setRaw(k >= 1); setGrounded(k >= 2); setVerdict(k >= 3);
      root.classList.toggle('raw-on', k >= 1);
      root.classList.toggle('grounded-on', k >= 2);
    }
    function enterStep(k) {
      const el = k === 1 ? rawArm.result : k === 2 ? grdArm.result : k === 3 ? verdict : null;
      if (el && scope) scope.tween(el, [{ opacity: 0.2, transform: 'translateY(5px)' }, { opacity: 1, transform: 'none' }], { duration: 320, fill: 'none' });
    }
    return { title: 'Grounding closes the gap — robustness, not a leaderboard', stepCount: 3, applyStep: applyStep, enterStep: enterStep };
  }

  /* ============================================================
     SCENE 6 — Breadth + Ask (C2). The same engine shape across
     verticals (a new vertical is a YAML ontology — DATA, not code;
     it auto-registers via PLAN-0032 / Rule of Three), closed by the
     NL-query "ask your own data" beat that re-houses the View-C
     grounding-receipt grammar + the anti-hallucination guard.
     Synthetic mirror data (ADR-0015 D1), consistent with the story.
     ============================================================ */
  // nouns + YAML excerpts are FAITHFUL to the real in-repo ontologies
  // (verticals/<ns>/ontology/<ns>_v0.yaml) — abridged, not invented (AC-9).
  const VERTICALS = [
    { key: 'aquaculture', label: 'Aquaculture', tone: 's-ok', ns: 'aquaculture',
      asset: 'Pond', site: 'Farm', metric: 'Dissolved oxygen', dir: 'below', thr: '4.0 mg/L', action: 'start_emergency_aerator',
      yaml: `version: 0
namespace: aquaculture
object_types:
  Pond:                       # the managed unit
    primary_key: pond_id
    properties:
      species:
        type: enum
        values: [whiteleg_shrimp, tiger_prawn, tilapia]
      site_id:
        type: ref
        target: Farm
  Farm:                       # the geo site
    properties:
      site_type:
        type: enum
        values: [coastal, inland, recirculating]
  RecommendedAction:
    properties:
      action_type:
        type: enum
        values: [start_emergency_aerator, increase_water_exchange,
                 dispatch_technician, escalate]
# breach: dissolved-oxygen reading BELOW 4.0 mg/L  ->  a crash` },
    { key: 'energy', label: 'Energy grid', tone: 's-info', ns: 'energy',
      asset: 'Asset', site: 'Site', metric: 'Temperature', dir: 'above', thr: '', action: 'isolate / restart',
      yaml: `version: 0
namespace: energy
object_types:
  Asset:                      # the managed unit
    primary_key: asset_id
    properties:
      asset_type:
        type: enum
        values: [battery, inverter, meter, transformer]
      site_id:
        type: ref
        target: Site
  Site:
    properties:
      site_type:
        type: enum
        values: [substation, microgrid, depot]
  OperationalEvent:
    properties:
      measured_kind:
        type: enum
        values: [temperature, frequency]
  RecommendedAction:
    properties:
      action_type:
        type: enum
        values: [restart, isolate, dispatch_technician, escalate]
# breach: transformer temperature ABOVE threshold  ->  an overrun` },
    { key: 'supply', label: 'Cold-chain logistics', tone: 's-warn', ns: 'supply_chain',
      asset: 'Shipment', site: 'Facility', metric: 'Cold-chain temperature', dir: 'above', thr: '', action: 'reroute / expedite',
      yaml: `version: 0
namespace: supply_chain
object_types:
  Shipment:                   # the managed unit
    primary_key: shipment_id
    properties:
      cargo_type:
        type: enum
        values: [pharma, produce, frozen, biologic]
      facility_id:
        type: ref
        target: Facility
  Facility:
    properties:
      facility_type:
        type: enum
        values: [cold_storage, distribution_center, port, cross_dock]
  RecommendedAction:
    properties:
      action_type:
        type: enum
        values: [reroute, expedite, hold, inspect, escalate]
# breach: cold-chain temperature ABOVE threshold  ->  an excursion` }
  ];

  function createBreadthScene(ctx) {
    const scope = ctx.scope, host = ctx.host;
    const CAP = [
      'One engine asks every operation the same four things — here, filled for aquaculture.',
      'Swap the data: energy grid. The SAME four slots — only the values changed; the crash is now an overrun.',
      'Swap again: cold-chain. Each swap is just a different YAML file — data, not code. Open “View YAML” to see it.',
      'And the operator asks in plain language — grounded in the real records, never invented.'
    ];
    const ROWS = [
      ['Asset-role', v => [v.asset, '']],
      ['Site-role', v => [v.site, '']],
      ['Metric', v => [v.metric + ' ' + (v.dir === 'below' ? '↓' : '↑') + (v.thr ? ' ' + v.thr : ''), v.dir === 'below' ? 'down' : 'up']],
      ['Action', v => [v.action, '']]
    ];
    let mode = 'swap', active = -1, yamlVertical = 0, yamlOpen = false;

    const root = h('div', { class: 'scene-breadth mode-swap' });
    root.appendChild(h('div', { class: 'bd-head' }, [
      h('div', { class: 'eyebrow' }, 'One engine · many operations'),
      h('h3', null, 'The same ontology shape — a new vertical is data, not code'),
      h('div', { class: 'bd-subnote muted' }, 'The four slots are fixed by the engine (Asset · Site · Metric · Action). Swap a vertical to refill them, or “Compare all” to see the three side by side — each is just a YAML file a domain author wrote.')
    ]));

    // ---- mode toggle: Swap (default) | Compare all (matrix) ----
    const swapBtn = h('button', { class: 'bd-modebtn', onClick: () => setMode('swap') }, [icon('refresh', { width: 13, height: 13 }), 'Swap']);
    const matrixBtn = h('button', { class: 'bd-modebtn', onClick: () => setMode('matrix') }, [icon('grid', { width: 13, height: 13 }), 'Compare all']);
    root.appendChild(h('div', { class: 'bd-modebar' }, [h('span', { class: 'flex' }), h('div', { class: 'bd-modeseg' }, [swapBtn, matrixBtn])]));

    // ---- SWAP view: chips + ONE shared engine shape; only the values swap ----
    const chipRow = h('div', { class: 'bd-verticals' });
    const chips = VERTICALS.map((v, i) => {
      const c = h('button', { class: 'bd-vchip', onClick: () => selectVertical(i, true) }, [h('span', { class: 'bd-vdot ' + v.tone }), v.label]);
      chipRow.appendChild(c); return c;
    });
    const activeBadge = h('span', { class: 'bd-active' });
    const swapYamlBtn = h('button', { class: 'bd-yaml-btn', onClick: () => { yamlVertical = active < 0 ? 0 : active; yamlOpen = !yamlOpen; syncYaml(); } }, 'View YAML');
    const slotVals = {};
    function slotCell(key, label) {
      const val = h('div', { class: 'bd-slot-v mono' }, '—');
      slotVals[key] = val;
      return h('div', { class: 'bd-slot' }, [h('div', { class: 'bd-slot-k eyebrow' }, label), val]);
    }
    const engine = h('div', { class: 'bd-engine' }, [
      h('div', { class: 'bd-engine-head' }, [
        h('span', { class: 'bd-engine-tag' }, [icon('cpu', { width: 13, height: 13 }), 'Engine · 4 fixed roles']),
        h('span', { class: 'flex' }), activeBadge, swapYamlBtn
      ]),
      h('div', { class: 'bd-shape' }, [
        slotCell('asset', 'Asset-role'), slotCell('site', 'Site-role'),
        slotCell('metric', 'Metric'), slotCell('action', 'Action')
      ])
    ]);
    root.appendChild(h('div', { class: 'bd-swap' }, [chipRow, engine]));

    // ---- MATRIX view (Compare all): roles as rows, verticals as columns ----
    const hrow = h('tr', null, [h('th', { class: 'bd-mrole bd-mcorner' }, 'engine role')]);
    VERTICALS.forEach((v, i) => {
      hrow.appendChild(h('th', { class: 'bd-mvhead' }, [
        h('div', { class: 'bd-mvtop' }, [h('span', { class: 'bd-vdot ' + v.tone }), h('span', null, v.label)]),
        h('button', { class: 'bd-myaml-btn', onClick: () => { yamlVertical = i; yamlOpen = true; syncYaml(); } }, 'view yaml')
      ]));
    });
    const tbody = h('tbody');
    ROWS.forEach(row => {
      const tr = h('tr', null, [h('td', { class: 'bd-mrole' }, row[0])]);
      VERTICALS.forEach(v => { const r = row[1](v); tr.appendChild(h('td', { class: 'bd-mcell mono ' + r[1] }, r[0])); });
      tbody.appendChild(tr);
    });
    root.appendChild(h('div', { class: 'bd-matrix' }, [h('table', { class: 'bd-mtable' }, [h('thead', null, hrow), tbody])]));

    // ---- shared YAML area (drives both views) ----
    const yamlFile = h('span', { class: 'bd-ya-file mono' }, '');
    const yamlBox = h('pre', { class: 'bd-ya-pre mono' }, '');
    root.appendChild(h('div', { class: 'bd-yaml-area' }, [
      h('div', { class: 'bd-ya-head' }, [icon('flow', { width: 13, height: 13 }), yamlFile, h('span', { class: 'flex' }),
        h('button', { class: 'bd-ya-close', onClick: () => { yamlOpen = false; syncYaml(); } }, [icon('x', { width: 12, height: 12 }), 'close'])]),
      yamlBox
    ]));

    root.appendChild(buildAsk());
    const cap = h('div', { class: 'bd-caption' }, CAP[0]);
    root.appendChild(cap);
    host.appendChild(root);

    function buildAsk() {
      return h('div', { class: 'bd-ask' }, [
        h('div', { class: 'bd-ask-q' }, [icon('ask', { width: 14, height: 14 }), '“How many ponds are below the DO action line right now?”']),
        h('div', { class: 'bd-ask-a' }, '3 ponds — P-12, P-07, P-21.'),
        h('div', { class: 'bd-receipt' }, [
          h('div', { class: 'bd-rhead' }, [icon('receipt', { width: 13, height: 13 }), h('span', { class: 'eyebrow' }, 'Grounding receipt'), h('span', { class: 'badge s-ok', style: { textTransform: 'none' } }, [h('span', { class: 'led' }), 'grounded'])]),
          h('div', { class: 'bd-rq mono' }, 'LIST Pond WHERE do_mg_l < 4.0'),
          h('div', { class: 'bd-rids' }, ['P-12', 'P-07', 'P-21'].map(id => h('span', { class: 'bd-src mono' }, [icon('link', { width: 11, height: 11 }), id]))),
          h('div', { class: 'bd-rnote muted' }, 'Ask something with no match → an explicit “no records — not invented”, never a fabricated answer.')
        ])
      ]);
    }

    function setMode(m) {
      mode = m;
      root.classList.toggle('mode-matrix', m === 'matrix');
      root.classList.toggle('mode-swap', m === 'swap');
      swapBtn.classList.toggle('active', m === 'swap');
      matrixBtn.classList.toggle('active', m === 'matrix');
    }
    function syncYaml() {
      const v = VERTICALS[yamlVertical];
      yamlFile.textContent = 'verticals/' + v.ns + '/ontology/' + v.ns + '_v0.yaml';
      yamlBox.textContent = v.yaml;
      root.classList.toggle('yaml-open', yamlOpen);
      swapYamlBtn.textContent = (yamlOpen && mode === 'swap') ? 'Hide YAML' : 'View YAML';
    }
    function setVal(key, text, cls) {
      slotVals[key].textContent = text;
      slotVals[key].className = 'bd-slot-v mono ' + cls;
    }
    function selectVertical(i, animate) {
      if (i === active) return;
      active = i;
      const v = VERTICALS[i];
      chips.forEach((c, ci) => c.classList.toggle('active', ci === i));
      clear(activeBadge);
      activeBadge.appendChild(h('span', { class: 'bd-vdot ' + v.tone }));
      activeBadge.appendChild(document.createTextNode(v.label + ' · ' + v.ns + '_v0.yaml'));
      setVal('asset', v.asset, '');
      setVal('site', v.site, '');
      setVal('metric', v.metric + ' ' + (v.dir === 'below' ? '↓' : '↑') + (v.thr ? ' ' + v.thr : ''), v.dir === 'below' ? 'down' : 'up');
      setVal('action', v.action, '');
      if (yamlOpen && mode === 'swap') { yamlVertical = i; syncYaml(); }   // keep an open YAML following the swap
      if (animate && scope && !M.reduced()) {            // swap motion: the slots stay, the values refill
        ['asset', 'site', 'metric', 'action'].forEach(k =>
          scope.tween(slotVals[k], [{ opacity: 0.12, transform: 'translateY(5px)' }, { opacity: 1, transform: 'none' }], { duration: 300, fill: 'none' }));
      }
    }

    function applyStep(k) {
      cap.textContent = CAP[k] || CAP[CAP.length - 1];
      root.classList.toggle('show-ask', k >= 3);
      if (k <= 2) selectVertical(k, true);   // 0 aquaculture -> 1 energy -> 2 cold-chain, swapped in place
    }
    return { title: 'One engine, many operations — and ask your own data', stepCount: 3, applyStep: applyStep };
  }

  /* ============================================================
     SCENE 7 — Appendix · how it works (C2, optional). The
     ontology/engine explainer DEMOTED from scene 1 (AC-1): the
     three-layer mental model (CLAUDE.md §3). Reachable for technical
     audiences who want the "how", never the opener.
     ============================================================ */
  // the engine as a flow: a runtime pipeline (raw -> mapping -> semantic -> action)
  // whose Semantic layer (ONE YAML) GENERATES the whole stack (the moat). Every
  // node is clickable -> a detail card. (CLAUDE.md §3 three-layer model, enriched.)
  const ENGINE_NODES = {
    raw: { name: 'Raw sources', kind: 'input', sub: 'sensors · feeds', desc: 'Sensors, SCADA feeds, ERP exports — the messy inputs, every format and every vertical, before any structure.' },
    map: { name: 'Mapping layer', kind: 'runtime', sub: 'dbt / SQLMesh', desc: 'Transforms raw sources into canonical, typed records. Adapter logic lives here only — swap a data source and nothing downstream changes.' },
    sem: { name: 'Semantic layer', kind: 'moat', sub: 'YAML ontology', moat: true, desc: 'ONE YAML ontology = the single source of truth: object types, roles, properties, metrics and actions. Everything below is generated from it — edit the YAML and the whole stack re-skins.' },
    act: { name: 'Action layer', kind: 'runtime', sub: 'FastAPI · audit', desc: 'Governed functions tied to objects — every call gated by permissions and written to an audit trail. This is the approve → execute you saw in scenes 2 and 3.' },
    pydantic: { name: 'Pydantic models', short: 'Pydantic', kind: 'generated', desc: 'Typed request/response + validation models for every object — generated, never hand-written.' },
    sql: { name: 'SQL DDL', short: 'SQL DDL', kind: 'generated', desc: 'The database schema — tables, columns, types and foreign keys — for every object type.' },
    jsonschema: { name: 'JSON schema', short: 'JSON', kind: 'generated', desc: 'Machine-readable contracts for APIs and external integrations.' },
    mcp: { name: 'MCP tools', short: 'MCP tools', kind: 'generated', desc: 'Tool definitions so an LLM / agent can query the ontology safely and grounded — the Ask in scene 6.' },
    ts: { name: 'TypeScript types', short: 'TS types', kind: 'generated', desc: 'Front-end types — the console is typed straight from the ontology.' },
    ui: { name: 'UI', short: 'UI', kind: 'generated', desc: 'The operational console re-skins per vertical from the ontology — the map, the decision cards and the Ask view you have been looking at.' },
    orm: { name: 'SQLAlchemy ORM', short: 'ORM', kind: 'generated', desc: 'Runtime database models generated straight from the YAML into committed code. Alembic migrations stay hand-authored — a schema-parity test keeps them in lockstep with the generated schema.' }
  };
  const KIND_TAG = { input: ['s-neutral', 'input'], runtime: ['s-neutral', 'runtime layer'], moat: ['s-ok solid', 'the moat'], generated: ['s-info', 'generated'] };
  const AP_GEN = ['pydantic', 'sql', 'jsonschema', 'mcp', 'ts', 'ui', 'orm'];

  function createAppendixScene(ctx) {
    const scope = ctx.scope, host = ctx.host;
    const CAP = [
      'Under the hood: data flows left → right through the layers — raw, mapping, semantic, action.',
      'But the Semantic layer — ONE YAML ontology — also GENERATES the whole stack. Click any node to see what it does.',
      'The golden rule of the moat ↓'
    ];
    const nodeEls = {};

    const root = h('div', { class: 'scene-appendix' });
    root.appendChild(h('div', { class: 'ap-head' }, [
      h('div', { class: 'eyebrow' }, 'Appendix · how it works'),
      h('h3', null, 'One YAML ontology generates the whole stack')
    ]));

    // ---- the engine as an SVG flow: pipeline (→) + the generative fan-out (↓) ----
    const svg = s('svg', { class: 'ap-svg', viewBox: '0 0 720 146', xmlns: SVGNS, role: 'img',
      'aria-label': 'Runtime pipeline raw → mapping → semantic → action; the semantic YAML layer fans out to the generated Pydantic, SQL, JSON schema, MCP tools, TypeScript types, UI and SQLAlchemy ORM' });
    svg.appendChild(s('defs', null, s('marker', { id: 'ap-arrow', markerWidth: 8, markerHeight: 8, refX: 6, refY: 3, orient: 'auto' },
      s('path', { d: 'M0,0 L6,3 L0,6 Z', style: { fill: 'var(--tx-3)' } }))));

    function pnode(key, cx, w, title, sub) {
      const n = ENGINE_NODES[key], hh = 26;
      const g = s('g', { class: 'ap-svg-node' + (n.moat ? ' is-moat' : ''), transform: 'translate(' + cx + ',40)', style: { cursor: 'pointer' } });
      g.appendChild(s('rect', { class: 'ap-nbox', x: -w / 2, y: -hh, width: w, height: hh * 2, rx: 8 }));
      g.appendChild(s('text', { class: 'ap-ntitle', x: 0, y: -3, 'text-anchor': 'middle' }, title));
      g.appendChild(s('text', { class: 'ap-nsub', x: 0, y: 12, 'text-anchor': 'middle' }, sub));
      g.addEventListener('click', () => selectNode(key));
      nodeEls[key] = g; return g;
    }
    function fline(cls, x1, y1, x2, y2, arrow) {
      return s('line', { class: 'ap-fl ' + cls, x1: x1, y1: y1, x2: x2, y2: y2, 'marker-end': arrow ? 'url(#ap-arrow)' : null });
    }
    // pipeline nodes
    svg.appendChild(pnode('raw', 86, 156, 'Raw sources', 'sensors · feeds'));
    svg.appendChild(pnode('map', 269, 156, 'Mapping layer', 'dbt / SQLMesh'));
    svg.appendChild(pnode('sem', 451, 156, 'Semantic · YAML', 'the moat'));
    svg.appendChild(pnode('act', 634, 156, 'Action layer', 'FastAPI · audit'));
    // pipeline arrows (flow → )
    svg.appendChild(fline('ap-pipe-fl', 164, 40, 189, 40, true));
    svg.appendChild(fline('ap-pipe-fl', 347, 40, 372, 40, true));
    svg.appendChild(fline('ap-pipe-fl', 529, 40, 554, 40, true));
    // fan-out group (revealed at step 1)
    const fan = s('g', { class: 'ap-fan' });
    fan.appendChild(s('text', { class: 'ap-fan-label', x: 451, y: 82, 'text-anchor': 'middle' }, 'generated from the one YAML ↓'));
    fan.appendChild(fline('ap-gen-fl', 451, 66, 451, 90));        // trunk
    fan.appendChild(fline('ap-gen-fl', 46, 90, 662, 90));         // distributor
    const cxs = [46, 149, 251, 354, 457, 559, 662];
    AP_GEN.forEach((key, i) => {
      const cx = cxs[i];
      fan.appendChild(fline('ap-gen-fl', cx, 90, cx, 102));        // drop
      const g = s('g', { class: 'ap-svg-node ap-gen-node', transform: 'translate(' + cx + ',118)', style: { cursor: 'pointer' } });
      g.appendChild(s('rect', { class: 'ap-nbox', x: -45, y: -15, width: 90, height: 30, rx: 7 }));
      g.appendChild(s('text', { class: 'ap-ntitle', x: 0, y: 4, 'text-anchor': 'middle' }, ENGINE_NODES[key].short));
      g.addEventListener('click', () => selectNode(key));
      nodeEls[key] = g; fan.appendChild(g);
    });
    svg.appendChild(fan);
    root.appendChild(svg);

    // detail card (driven by node clicks)
    const detail = h('div', { class: 'ap-detail' });
    root.appendChild(detail);

    // the prominent moat takeaway (golden finale, revealed at step 2)
    const takeaway = h('div', { class: 'ap-takeaway' }, [
      h('div', { class: 'ap-tk-icon' }, icon('spark', { width: 20, height: 20 })),
      h('div', null, [
        h('div', { class: 'ap-tk-lead' }, 'Edit one YAML → the whole stack regenerates and stays in sync.'),
        h('div', { class: 'ap-tk-sub' }, 'A new vertical or field is data, not code — this is why scenes 1–6 just work.')
      ])
    ]);
    root.appendChild(takeaway);

    const cap = h('div', { class: 'ap-caption' }, CAP[0]);
    root.appendChild(cap);
    host.appendChild(root);

    function selectNode(key) {
      const n = ENGINE_NODES[key], tag = KIND_TAG[n.kind] || KIND_TAG.runtime;
      Object.keys(nodeEls).forEach(k => nodeEls[k].classList.toggle('sel', k === key));
      clear(detail);
      detail.appendChild(h('div', { class: 'ap-d-head' }, [
        h('span', { class: 'ap-d-name' }, n.name),
        h('span', { class: 'badge ' + tag[0], style: { textTransform: 'none' } }, tag[1])
      ]));
      detail.appendChild(h('div', { class: 'ap-d-body' }, n.desc));
    }

    function applyStep(k) {
      cap.textContent = CAP[k] || CAP[CAP.length - 1];
      svg.classList.toggle('show-fan', k >= 1);          // reveal the generative fan-out
      svg.classList.toggle('flowing', !M.reduced());      // marching-dash flow (suppressed under reduced-motion)
      root.classList.toggle('show-takeaway', k >= 2);     // the golden moat finale
    }
    function enterStep(k) {
      if (k === 1 && scope) scope.tween(fan, [{ opacity: 0.1 }, { opacity: 1 }], { duration: 360, fill: 'none' });
      if (k === 2 && scope) scope.tween(takeaway, [{ opacity: 0.1, transform: 'translateY(8px)' }, { opacity: 1, transform: 'none' }], { duration: 360, fill: 'none' });
    }
    selectNode('sem');   // default to the moat
    return { title: 'How it works — one YAML generates the whole stack', stepCount: 2, applyStep: applyStep, enterStep: enterStep };
  }

  /* ============================================================
     PROCUREMENT vertical scenes (PLAN-0036 Step 6). The 4th vertical
     as a procurement operator's round-trip: worklist → process timeline
     → approval "money screen" → graduation moment → monitoring dashboard.
     Three VISUAL REGISTERS, no exception (AC-10): AI-assist (.reg-llm,
     blue "AI draft", advisory+editable) / rule-decided (.reg-rule, gray +
     🔒, names the rule, deterministic) / human-approved (.reg-human, green
     + name·role·time, accountable). Governed ≠ generated (L-3): the LLM
     drafts/summarises; rules + humans select/threshold/approve.
     Data mirrors verticals/procurement/data_adapter/synthetic.py (the same
     ฿2.15M hero PO, the cert-blocked quote, the DOA tiers) so the demo and
     the engine never contradict. Thai-localized (AC-13): Thai-primary doc
     nouns + EN loanwords (PO·RFQ·AVL·lead time·supplier); ฿ + พ.ศ. dates.
     Additive overlay, no engine edit (the Option-A demo-presentation seam).
     ============================================================ */
  const PROC_EYEBROW = 'Story mode · Procurement (Fastenal TH)';
  function baht(n) { return '฿' + Math.round(n).toLocaleString('en-US'); }
  const PROC = {
    equipment: { id: 'CNC-07', name: 'CNC Machining Center #7', plant: 'EEC Assembly Plant 1', crit: 0.92 },
    part: { no: 'SP-DRV-01', name: 'CNC Spindle Servo Drive (สเปดเซอร์โว)', stock: 0 },
    filter: { no: 'FLT-02', name: 'Coolant Filter Cartridge (ไส้กรอง)', stock: 40, reorder: 100 },
    // the three spindle quotes — selection is the SCORED RULE, never the LLM
    quotes: [
      { sup: 'Contracted OEM Spares Co.', avl: 'approved', onContract: true, price: 1850000, lead: 21, selected: false, blocked: false, note: 'on-contract · lead time 21 วัน ช้าเกินไปสำหรับสายหยุด' },
      { sup: 'Regional Industrial Supply', avl: 'pending', onContract: false, price: 2150000, lead: 5, selected: true, blocked: false, note: 'RFQ · AVL exception (emergency, logged) · เร็วสุด 5 วัน — เลือกโดยกติกาให้คะแนน' },
      { sup: 'Allied Parts Trading', avl: 'approved', onContract: false, price: 1950000, lead: 9, selected: false, blocked: true, note: 'cert หมดอายุ → compliance บล็อก (ไม่ใช่ราคา)' }
    ],
    compliance: [
      { k: 'AVL', label: 'Approved Vendor List', pass: true, note: 'AVL exception (emergency) — logged' },
      { k: 'Tax', label: 'ภาษี · tax id', pass: true, note: 'ถูกต้อง' },
      { k: 'Cert', label: 'ใบรับรอง · cert', pass: true, note: 'valid (supplier ที่เลือก)' },
      { k: 'Sanctions', label: 'Sanctions screening', pass: true, note: 'ผ่าน' },
      { k: 'Single-source', label: 'Single-source', pass: true, note: 'documented + justified' }
    ],
    doa: [
      { tier: 1, role: 'หน.จัดซื้อ', max: 50000 },
      { tier: 2, role: 'ผจก.จัดซื้อ', max: 500000 },
      { tier: 3, role: 'ผจก.โรงงาน', max: 2000000 },
      { tier: 4, role: 'ผอ.', max: Infinity }
    ],
    po: { amount: 2150000, tierIdx: 3, waiver: true },
    sod: ['ผู้ขอ · maintenance', 'หน.จัดซื้อ', 'ผจก.โรงงาน', 'ผอ. · อนุมัติ'],
    kpis: [
      { k: 'รอบเวลา req → PO', v: '6.2 ชม.', trend: '↓ 18%', target: 'เป้า ≤ 8 ชม.', good: true },
      { k: 'rush-freight ที่เลี่ยงได้', v: '฿420k', trend: '↑ 12%', target: 'YTD', good: true },
      { k: 'อัตรา stockout', v: '1.8%', trend: '↓ 0.6pp', target: 'เป้า ≤ 2%', good: true },
      { k: 'maverick spend', v: '4.1%', trend: '↓ 1.2pp', target: 'เป้า ≤ 5%', good: true },
      { k: '% on-contract', v: '88%', trend: '↑ 3pp', target: 'เป้า ≥ 85%', good: true }
    ]
  };
  // a 3-register legend strip reused across procurement scenes (AC-10)
  function procRegisterLegend() {
    return h('div', { class: 'pr-legend' }, [
      h('span', { class: 'pr-chip reg-llm' }, 'AI draft · ช่วยร่าง'),
      h('span', { class: 'pr-chip reg-rule' }, '🔒 rule · กติกาตัดสิน'),
      h('span', { class: 'pr-chip reg-human' }, '✓ human · คนอนุมัติ')
    ]);
  }

  /* ---- P1: worklist / inbox (home — the demo opens here) ---- */
  function createProcWorklistScene(ctx) {
    const host = ctx.host;
    const root = h('div', { class: 'scene-pwork' });
    host.appendChild(root);
    root.appendChild(h('div', { class: 'pw-head' }, [
      h('div', { class: 'eyebrow' }, 'งานของฉัน · worklist'),
      h('h3', null, 'กล่องงานจัดซื้อ — เรียงตามความเร่งด่วน')
    ]));
    root.appendChild(procRegisterLegend());
    const queue = h('div', { class: 'pw-queue' });
    root.appendChild(queue);
    const TASKS = [
      { urg: 'crit', tag: 'ด่วนที่สุด', title: 'จัดหาด่วน: สเปด ' + PROC.equipment.id + ' — สายการผลิตหยุด', meta: 'PR · ' + PROC.equipment.plant + ' · criticality critical', stat: '⏸ รอการตัดสินใจของคุณ · อนุมัติ (ผอ.)', reg: 'human' },
      { urg: 'warn', tag: 'ปกติ', title: 'เติมสต๊อก: ' + PROC.filter.name, meta: 'reorder · stock 40 ≤ reorder point 100', stat: '⏸ รออนุมัติ · หน.จัดซื้อ', reg: 'human' }
    ];
    TASKS.forEach((t) => {
      queue.appendChild(h('div', { class: 'pw-task urg-' + t.urg }, [
        h('div', { class: 'pw-task-l' }, [
          h('span', { class: 'pw-urg' }, t.tag),
          h('div', { class: 'pw-task-title' }, t.title),
          h('div', { class: 'pw-task-meta mono' }, t.meta)
        ]),
        h('div', { class: 'pw-task-stat reg-' + t.reg }, t.stat)
      ]));
    });
    const cap = h('div', { class: 'pw-caption' }, '');
    root.appendChild(cap);
    const CAP = [
      'กล่องงานคือหน้าแรก — งานเรียงตามความเร่งด่วน, เคสฉุกเฉินลอยขึ้นบนสุด',
      'เคส CNC-07 สายหยุด = ด่วนที่สุด (แดง) · งานเติมสต๊อกปกติรอด้านล่าง',
      'คลิกเปิดงาน → เข้าสู่ไทม์ไลน์กระบวนการ 7 ขั้น (ฉากถัดไป)'
    ];
    function applyStep(k) {
      cap.textContent = CAP[Math.min(k, CAP.length - 1)] || '';
      Array.prototype.forEach.call(queue.children, (el, i) => el.classList.toggle('is-shown', k >= i + 1));
    }
    return { title: 'งานของฉัน — กล่องงานจัดซื้อ (worklist)', stepCount: 3, applyStep: applyStep, eyebrow: PROC_EYEBROW };
  }

  /* ---- P2: process timeline (the 7-step hero pipeline, bottleneck-first) ---- */
  function createProcTimelineScene(ctx) {
    const host = ctx.host;
    const root = h('div', { class: 'scene-ptime' });
    host.appendChild(root);
    root.appendChild(h('div', { class: 'pt-head' }, [
      h('div', { class: 'eyebrow' }, 'กระบวนการ · process timeline' ),
      h('h3', null, 'จัดหาฉุกเฉิน CNC-07 — 7 ขั้น, รออยู่ที่ "อนุมัติ"')
    ]));
    root.appendChild(procRegisterLegend());
    const band = h('div', { class: 'pt-band' });
    root.appendChild(band);
    // step_id, label, register (which color), sub
    const STEPS = [
      { id: 'intake', label: 'intake · รับเรื่อง', reg: 'llm', sub: 'AI ช่วยกรอก PR' },
      { id: 'judge', label: 'judge · ตัดวิกฤต', reg: 'rule', sub: 'band 0.8 (กติกา)' },
      { id: 'source', label: 'source · หาแหล่ง', reg: 'rule', sub: 'เลือกโดยคะแนน' },
      { id: 'compliance', label: 'compliance', reg: 'rule', sub: 'ต่อเกณฑ์' },
      { id: 'approve', label: 'approve · อนุมัติ', reg: 'human', sub: '⏸ รอคุณ' },
      { id: 'issue_po', label: 'issue PO', reg: 'human', sub: 'เขียนเมื่ออนุมัติ' },
      { id: 'audit', label: 'audit · บันทึก', reg: 'llm', sub: 'AI สรุป' }
    ];
    STEPS.forEach((st, i) => {
      band.appendChild(h('div', { class: 'pt-node reg-' + st.reg, 'data-step': st.id }, [
        h('span', { class: 'pt-n mono' }, String(i + 1)),
        h('div', { class: 'pt-node-l' }, [
          h('div', { class: 'pt-node-label' }, st.label),
          h('div', { class: 'pt-node-sub mono' }, st.sub)
        ]),
        h('span', { class: 'pt-wait' }, '⏸ รอการตัดสินใจของคุณ')
      ]));
      if (i < STEPS.length - 1) band.appendChild(h('span', { class: 'pt-arrow' }, '→'));
    });
    const cap = h('div', { class: 'pt-caption' }, '');
    root.appendChild(cap);
    const nodes = Array.prototype.filter.call(band.children, (c) => c.classList.contains('pt-node'));
    // bottleneck-first: the run advances to `approve` and SUSPENDS there
    const CAP = [
      'ขั้นที่เป็นกติกา (judge·source·compliance) รันเองจนจบ — ล็อก, ไม่ต้องรอคน',
      'intake: AI ช่วยร่าง PR (ฟ้า) · judge: กติกาตัดวิกฤต (เทา ล็อก)',
      'source + compliance: กติกาเลือก supplier + เช็คเกณฑ์ — ยังไม่มีคนแตะ',
      'หยุดที่ "approve" — ⏸ รอการตัดสินใจของคุณ (คอขวดที่ตั้งใจ)',
      'อนุมัติแล้ว → issue PO + audit รันต่อจนจบ'
    ];
    const PROG = [0, 1, 3, 4, 7]; // how many nodes are done/active by step
    function applyStep(k) {
      cap.textContent = CAP[Math.min(k, CAP.length - 1)] || '';
      const done = PROG[Math.min(k, PROG.length - 1)];
      nodes.forEach((nd, i) => {
        const isApprove = nd.getAttribute('data-step') === 'approve';
        nd.classList.toggle('st-done', i < done && !(isApprove && k < 4));
        nd.classList.toggle('st-active', i === done && k < 4);
        nd.classList.toggle('st-wait', isApprove && k >= 3 && k < 4);
        nd.classList.toggle('st-pending', i > done);
      });
    }
    return { title: 'ไทม์ไลน์กระบวนการ — 7 ขั้น (คอขวดอยู่ที่อนุมัติ)', stepCount: 5, applyStep: applyStep, eyebrow: PROC_EYEBROW };
  }

  /* ---- P3: approval "money screen" (the centerpiece) ---- */
  function createProcApprovalScene(ctx) {
    const host = ctx.host;
    const root = h('div', { class: 'scene-pappr' });
    host.appendChild(root);
    const card = h('div', { class: 'ap-card' });
    root.appendChild(card);
    // header: the ask + criticality
    card.appendChild(h('div', { class: 'apc-band' }, [
      h('span', { class: 'apc-crit' }, 'CRITICAL · สายการผลิตหยุด'),
      h('div', { class: 'apc-ask' }, 'อนุมัติจัดหา: ' + PROC.part.name + ' สำหรับ ' + PROC.equipment.id),
      h('span', { class: 'apc-amt mono' }, baht(PROC.po.amount))
    ]));
    // AI exec-summary (editable register)
    const sec = (cls, title, body) => h('div', { class: 'apc-sec ' + cls }, [h('div', { class: 'apc-sec-h' }, title), body]);
    card.appendChild(sec('s-llm', [h('span', { class: 'pr-chip reg-llm' }, 'AI draft · แก้ไขได้'), 'สรุปผู้บริหาร (AI ช่วยร่าง)'],
      h('div', { class: 'apc-exec', contenteditable: 'true' }, 'CNC-07 สายหยุด — สเปดหมดสต๊อก. on-contract OEM lead time 21 วัน ช้าเกินไป; เลือก RFQ 5 วัน (AVL exception, logged). ขออนุมัติภายใต้ waiver ฉุกเฉิน, escalate ถึง ผอ. (> ฿2M).')));
    // compliance per-criterion (rule register)
    const compBody = h('div', { class: 'apc-comp' });
    PROC.compliance.forEach((c) => compBody.appendChild(h('div', { class: 'apc-comp-row ' + (c.pass ? 'ok' : 'bad') }, [
      h('span', { class: 'apc-comp-i' }, c.pass ? '✓' : '✗'),
      h('span', { class: 'apc-comp-k' }, c.label),
      h('span', { class: 'apc-comp-n mono' }, c.note || '')
    ])));
    compBody.appendChild(h('div', { class: 'apc-comp-blocked' }, '✗ Allied Parts Trading — cert หมดอายุ → quote ถูกบล็อก (กติกา ไม่ใช่ราคา)'));
    card.appendChild(sec('s-rule', [h('span', { class: 'pr-chip reg-rule' }, '🔒 rule'), 'compliance ต่อเกณฑ์ (บล็อก PO ถ้าตก)'], compBody));
    // DOA ladder + waiver banner
    const doaBody = h('div', { class: 'apc-doa' });
    PROC.doa.forEach((t, i) => doaBody.appendChild(h('div', { class: 'apc-doa-row' + (i === PROC.po.tierIdx ? ' is-tier' : '') }, [
      h('span', { class: 'apc-doa-t mono' }, 'T' + t.tier),
      h('span', { class: 'apc-doa-r' }, t.role),
      h('span', { class: 'apc-doa-m mono' }, t.max === Infinity ? '> ฿2M' : '≤ ' + baht(t.max))
    ])));
    const doaWrap = h('div', null, [
      h('div', { class: 'apc-waiver' }, '⚠ Emergency waiver — ผ่อน 3-bid/sole-source แต่ escalate ผู้อนุมัติ + บังคับเหตุผล (ไม่ข้ามด่าน)'),
      doaBody
    ]);
    card.appendChild(sec('s-rule', [h('span', { class: 'pr-chip reg-rule' }, '🔒 rule'), 'DOA tier · ' + baht(PROC.po.amount) + ' → ผอ.'], doaWrap));
    // supplier / RFQ compare
    const cmp = h('div', { class: 'apc-quotes' });
    PROC.quotes.forEach((q) => cmp.appendChild(h('div', { class: 'apc-quote' + (q.selected ? ' is-sel' : '') + (q.blocked ? ' is-blocked' : '') }, [
      h('div', { class: 'apc-q-top' }, [
        h('span', { class: 'apc-q-sup' }, q.sup),
        q.selected ? h('span', { class: 'apc-q-pick' }, 'เลือก (คะแนน)') : (q.blocked ? h('span', { class: 'apc-q-block' }, 'บล็อก') : h('span', { class: 'apc-q-na' }, ''))
      ]),
      h('div', { class: 'apc-q-meta mono' }, baht(q.price) + ' · lead ' + q.lead + ' วัน · AVL ' + q.avl + (q.onContract ? ' · on-contract' : ' · RFQ')),
      h('div', { class: 'apc-q-note' }, q.note)
    ])));
    card.appendChild(sec('s-rule', [h('span', { class: 'pr-chip reg-rule' }, '🔒 rule'), 'เทียบ supplier · เลือกโดยกติกาให้คะแนน (ไม่ใช่ LLM)'], cmp));
    // SoD chain
    card.appendChild(sec('s-human', [h('span', { class: 'pr-chip reg-human' }, '✓ human'), 'Separation of Duties (SoD)'],
      h('div', { class: 'apc-sod' }, PROC.sod.map((s, i) => h('span', { class: 'apc-sod-step' }, (i ? '→ ' : '') + s)))));
    // actions
    const actions = h('div', { class: 'apc-actions' }, [
      h('button', { class: 'apc-btn reject' }, 'ปฏิเสธ'),
      h('button', { class: 'apc-btn approve' }, '✓ อนุมัติ (ผอ.)')
    ]);
    card.appendChild(actions);
    const cap = h('div', { class: 'apc-caption' }, '');
    root.appendChild(cap);
    const secs = Array.prototype.filter.call(card.children, (c) => c.classList.contains('apc-sec'));
    const CAP = [
      'หน้าจออนุมัติ = ที่เดียวจบ: คำขอ + วิกฤต + สรุป AI + compliance + DOA + เทียบเจ้า + SoD',
      'สรุปผู้บริหารคือ AI ช่วยร่าง (ฟ้า, แก้ไขได้) — ไม่ใช่ตัวตัดสิน',
      'compliance ต่อเกณฑ์ (เทา ล็อก): เจ้า cert หมดอายุถูกบล็อก — กติกากัดจริง',
      '฿2.15M > ฿2M → ผอ. + waiver (escalate + เหตุผล, ไม่ข้ามด่าน)',
      'เลือก supplier โดยคะแนน (เร็ว 5 วัน) — กติกา ไม่ใช่ LLM · SoD ครบ',
      'ปุ่มอนุมัติเป็นของคน — governed ≠ generated'
    ];
    function applyStep(k) {
      cap.textContent = CAP[Math.min(k, CAP.length - 1)] || '';
      secs.forEach((el, i) => el.classList.toggle('is-shown', k >= i + 1));
      actions.classList.toggle('is-shown', k >= secs.length + 1);
    }
    return { title: 'หน้าจออนุมัติ "money screen" — ที่เดียวจบ', stepCount: 6, applyStep: applyStep, eyebrow: PROC_EYEBROW };
  }

  /* ---- P4: graduation moment (AI-draft → human edit → approve → flips human-approved) ---- */
  function createProcGraduationScene(ctx) {
    const scope = ctx.scope, host = ctx.host;
    const root = h('div', { class: 'scene-pgrad' });
    host.appendChild(root);
    root.appendChild(h('div', { class: 'pg-head' }, [
      h('div', { class: 'eyebrow' }, 'governed ≠ generated' ),
      h('h3', null, 'จาก "AI ร่าง" → "คนอนุมัติ" — เห็นการกำกับด้วยตา')
    ]));
    const card = h('div', { class: 'pg-card reg-llm' });
    root.appendChild(card);
    const regTag = h('div', { class: 'pg-reg' }, [h('span', { class: 'pr-chip reg-llm' }, 'AI draft · ช่วยร่าง')]);
    const body = h('div', { class: 'pg-body', contenteditable: 'false' },
      'เหตุผลอนุมัติ: CNC-07 สายหยุด; on-contract 21 วัน vs RFQ 5 วัน. ขอ waiver ฉุกเฉิน, AVL exception (logged), escalate ผอ.');
    const stamp = h('div', { class: 'pg-stamp' }, '');
    card.appendChild(regTag);
    card.appendChild(body);
    card.appendChild(stamp);
    const cap = h('div', { class: 'pg-caption' }, '');
    root.appendChild(cap);
    const CAP = [
      'เริ่มจากร่างของ AI (ฟ้า, ป้าย "AI draft") — แค่ช่วยร่าง',
      'คนแก้ข้อความได้ (เพิ่ม "ยืนยันสายหยุด > 2 ชม.") — ยังเป็นร่าง',
      'กดอนุมัติ → การ์ดพลิกเป็นเขียว "human-approved · ผอ. · เวลา"',
      'นี่คือ governed ≠ generated: AI ร่าง, คนรับผิดชอบการตัดสิน'
    ];
    function applyStep(k) {
      cap.textContent = CAP[Math.min(k, CAP.length - 1)] || '';
      // step2: human edit
      if (k >= 2) {
        body.textContent = 'เหตุผลอนุมัติ: CNC-07 สายหยุด > 2 ชม. (ยืนยัน); on-contract 21 วัน vs RFQ 5 วัน. ขอ waiver ฉุกเฉิน, AVL exception (logged), escalate ผอ.';
        body.classList.add('is-edited');
      } else {
        body.textContent = 'เหตุผลอนุมัติ: CNC-07 สายหยุด; on-contract 21 วัน vs RFQ 5 วัน. ขอ waiver ฉุกเฉิน, AVL exception (logged), escalate ผอ.';
        body.classList.remove('is-edited');
      }
      // step3: flip to human-approved
      const approved = k >= 3;
      card.classList.toggle('reg-llm', !approved);
      card.classList.toggle('reg-human', approved);
      clear(regTag);
      regTag.appendChild(h('span', { class: 'pr-chip ' + (approved ? 'reg-human' : 'reg-llm') }, approved ? '✓ human-approved' : 'AI draft · ช่วยร่าง'));
      stamp.textContent = approved ? 'อนุมัติโดย ผอ. · สมชาย ก. · 24 มิ.ย. 2569 · 09:42' : '';
      stamp.classList.toggle('is-shown', approved);
    }
    function enterStep(k) {
      if (k === 3 && scope) scope.tween(card, [{ transform: 'scale(0.98)' }, { transform: 'scale(1)' }], { duration: 320, fill: 'none' });
    }
    return { title: 'ช่วงเปลี่ยนผ่าน — AI ร่าง สู่ คนอนุมัติ', stepCount: 4, applyStep: applyStep, enterStep: enterStep, eyebrow: PROC_EYEBROW };
  }

  /* ---- P5: monitoring dashboard (KPI tiles + waivers watched + AI-assist throughput) ---- */
  function createProcDashboardScene(ctx) {
    const host = ctx.host;
    const root = h('div', { class: 'scene-pdash' });
    host.appendChild(root);
    root.appendChild(h('div', { class: 'pd-head' }, [
      h('div', { class: 'eyebrow' }, 'มอนิเตอร์ · monitoring dashboard'),
      h('h3', null, 'ภาพรวมจัดซื้อ — KPI, waiver ที่ใช้, และ throughput ของ AI')
    ]));
    const tiles = h('div', { class: 'pd-tiles' });
    root.appendChild(tiles);
    PROC.kpis.forEach((kpi) => tiles.appendChild(h('div', { class: 'pd-tile' }, [
      h('div', { class: 'pd-k' }, kpi.k),
      h('div', { class: 'pd-v' }, kpi.v),
      h('div', { class: 'pd-foot' }, [
        h('span', { class: 'pd-trend ' + (kpi.good ? 'good' : 'bad') }, kpi.trend),
        h('span', { class: 'pd-target mono' }, kpi.target)
      ])
    ])));
    // watched tile: emergency waivers used
    tiles.appendChild(h('div', { class: 'pd-tile watched' }, [
      h('div', { class: 'pd-k' }, '⚠ emergency waiver ที่ใช้ (เดือนนี้)'),
      h('div', { class: 'pd-v' }, '3'),
      h('div', { class: 'pd-foot' }, [h('span', { class: 'pd-trend bad' }, 'เฝ้าดู'), h('span', { class: 'pd-target mono' }, 'เกณฑ์ ≤ 5')])
    ]));
    // pending by tier
    const pend = h('div', { class: 'pd-pend' }, [
      h('div', { class: 'pd-sec-h' }, 'รออนุมัติ แยกตาม DOA tier'),
      h('div', { class: 'pd-pend-bars' }, [
        h('div', { class: 'pd-bar' }, [h('span', null, 'หน.จัดซื้อ'), h('span', { class: 'pd-bar-f', style: { width: '60%' } }, '6')]),
        h('div', { class: 'pd-bar' }, [h('span', null, 'ผจก.จัดซื้อ'), h('span', { class: 'pd-bar-f', style: { width: '30%' } }, '3')]),
        h('div', { class: 'pd-bar' }, [h('span', null, 'ผจก.โรงงาน'), h('span', { class: 'pd-bar-f', style: { width: '10%' } }, '1')]),
        h('div', { class: 'pd-bar' }, [h('span', null, 'ผอ.'), h('span', { class: 'pd-bar-f crit', style: { width: '10%' } }, '1')])
      ])
    ]);
    root.appendChild(pend);
    // AI-assist throughput panel — the governance proof
    const ai = h('div', { class: 'pd-ai reg-llm' }, [
      h('div', { class: 'pd-sec-h' }, [h('span', { class: 'pr-chip reg-llm' }, 'AI draft'), 'AI-assist throughput (เดือนนี้)']),
      h('div', { class: 'pd-ai-row' }, [
        h('span', { class: 'pd-ai-n' }, 'AI ช่วยร่าง 142'),
        h('span', { class: 'pd-ai-n zero' }, '0 การเลือก supplier'),
        h('span', { class: 'pd-ai-n zero' }, '0 การอนุมัติ')
      ]),
      h('div', { class: 'pd-ai-note' }, 'AI ช่วยร่าง/สรุปเท่านั้น — การเลือกเจ้า·ตั้งเกณฑ์·อนุมัติ เป็นของกติกา+คน (governed ≠ generated)')
    ]);
    root.appendChild(ai);
    const cap = h('div', { class: 'pd-caption' }, '');
    root.appendChild(cap);
    const groups = [tiles, pend, ai];
    const CAP = [
      'แดชบอร์ดมอนิเตอร์: KPI จริง — มีค่า + แนวโน้ม + เป้า (ไม่ใช่เลขลอย)',
      'ไทล์เฝ้าดู: จำนวน emergency waiver ที่ใช้ — กันการใช้พร่ำเพรื่อ',
      'รออนุมัติแยกตาม tier · ผอ. มี 1 (เคส CNC-07)',
      'throughput ของ AI: ร่าง 142 · เลือก supplier 0 · อนุมัติ 0 — หลักฐานว่า AI ไม่ตัดสิน'
    ];
    function applyStep(k) {
      cap.textContent = CAP[Math.min(k, CAP.length - 1)] || '';
      groups.forEach((g, i) => g.classList.toggle('is-shown', k >= i + 1));
      tiles.classList.toggle('is-shown', k >= 1);
    }
    return { title: 'แดชบอร์ดมอนิเตอร์ — KPI + waiver + AI throughput', stepCount: 4, applyStep: applyStep, eyebrow: PROC_EYEBROW };
  }

  /* ============================================================
     The SCENES registry (arc order = G, pain-first). The appendix is
     the optional technical encore (AC-1 — reachable, never the opener).
     The procurement scene group (PLAN-0036 Step 6) is appended after the
     aquaculture arc — the same shell, a 4th vertical's operator round-trip.
     ============================================================ */
  const SCENES = [
    { id: 'hook',        create: createHookScene },
    { id: 'govern',      create: createGovernScene },
    { id: 'pipeline',    create: createPipelineScene },
    { id: 'intake',      create: createIntakeScene },
    { id: 'beforeafter', create: createBeforeAfterScene },
    { id: 'breadth',     create: createBreadthScene },
    { id: 'appendix',    create: createAppendixScene },
    { id: 'proc-worklist',   create: createProcWorklistScene },
    { id: 'proc-timeline',   create: createProcTimelineScene },
    { id: 'proc-approval',   create: createProcApprovalScene },
    { id: 'proc-graduation', create: createProcGraduationScene },
    { id: 'proc-dashboard',  create: createProcDashboardScene }
  ];
  const EYEBROW = 'Story mode · Aquaculture';

  /* ============================================================
     The shell — registry nav + generic stepper + the lifecycle
     teardown contract (two-tier scopes: shell + per-scene).
     ============================================================ */
  let isOpen = false, overlayEl = null, shellScope = null, sceneScope = null;
  let sceneIndex = 0, stepIndex = 0, playing = false, playTimer = null, altOn = false, active = null;
  let titleEl = null, eyebrowEl = null, sceneDotsEl = null, stepTextEl = null, playBtn = null, altBtn = null;
  let prevBtn = null, nextBtn = null, nextCta = null, bodyHost = null;

  function mountLauncher(hostEl) {
    if (!hostEl) return;
    hostEl.appendChild(h('button', { class: 'story-launch', onClick: open, title: 'Run the guided story (S)' }, [icon('play'), 'Story']));
    // app-lifetime 'S' hotkey (not an app.js view key A–E, so no collision).
    window.addEventListener('keydown', (e) => {
      if (isOpen) return;
      const tag = e.target && e.target.tagName;
      if (tag && /input|textarea|select/i.test(tag)) return;
      if (e.key === 's' || e.key === 'S') { e.preventDefault(); open(); }
    });
  }

  function open() {
    if (isOpen) return;
    isOpen = true;
    shellScope = M.scope('story-shell');
    buildShell();
    // capture phase so app.js A–E hotkeys never reach the console behind us (AC-11/AC-14)
    shellScope.on(window, 'keydown', onKey, true);
    enterScene(0);
  }
  function close() {
    if (!isOpen) return;
    isOpen = false;
    leaveScene();
    if (shellScope) shellScope.kill();
    shellScope = null;
    if (overlayEl && overlayEl.parentNode) overlayEl.parentNode.removeChild(overlayEl);
    overlayEl = null; titleEl = eyebrowEl = sceneDotsEl = stepTextEl = playBtn = altBtn = null;
    prevBtn = nextBtn = nextCta = bodyHost = null;
    sceneIndex = 0; stepIndex = 0; playing = false; playTimer = null; altOn = false;
  }

  function buildShell() {
    overlayEl = h('div', { class: 'story-overlay', role: 'dialog', 'aria-label': 'OCT story mode — aquaculture' });

    const top = h('div', { class: 'story-top' });
    titleEl = h('h2', null, '');
    eyebrowEl = h('div', { class: 'eyebrow' }, EYEBROW);
    top.appendChild(h('div', { class: 'story-id' }, [eyebrowEl, titleEl]));
    top.appendChild(h('div', { class: 'flex' }));

    sceneDotsEl = h('div', { class: 'story-dots', title: 'Scene' });
    SCENES.forEach((sc, i) => sceneDotsEl.appendChild(h('span', { class: 'dot', title: 'Scene ' + (i + 1) })));
    top.appendChild(sceneDotsEl);

    // transport (generic stepper) — alt button shown only when the scene declares one
    const transport = h('div', { class: 'story-transport' });
    playBtn = h('button', { class: 'iconbtn', onClick: togglePlay, title: 'Play / pause (Space)' }, [icon('play'), 'Play']);
    transport.appendChild(playBtn);
    transport.appendChild(h('button', { class: 'iconbtn', onClick: () => { pause(); stepForward(true); }, title: 'Step (→)' }, [icon('chevron'), 'Step']));
    transport.appendChild(h('button', { class: 'iconbtn', onClick: restart, title: 'Restart (R)' }, [icon('refresh'), 'Restart']));
    altBtn = h('button', { class: 'iconbtn story-alt', onClick: toggleAlt, style: { display: 'none' } }, [icon('anomaly'), 'Alt']);
    transport.appendChild(altBtn);
    top.appendChild(transport);

    stepTextEl = h('div', { class: 'story-steptext mono' }, '');
    top.appendChild(stepTextEl);

    // scene nav
    const nav = h('div', { class: 'story-scenenav' });
    prevBtn = h('button', { class: 'iconbtn', onClick: prevScene, title: 'Previous scene ([)' }, '‹');
    nextBtn = h('button', { class: 'iconbtn', onClick: nextScene, title: 'Next scene (])' }, '›');
    nav.appendChild(prevBtn); nav.appendChild(nextBtn);
    top.appendChild(nav);

    top.appendChild(h('button', { class: 'iconbtn', onClick: close, title: 'Exit story (Esc)' }, [icon('x'), 'Exit']));
    overlayEl.appendChild(top);

    bodyHost = h('div', { class: 'story-body' });
    overlayEl.appendChild(bodyHost);

    nextCta = h('button', { class: 'story-nextcta', onClick: nextScene, style: { display: 'none' } }, '');
    overlayEl.appendChild(nextCta);

    document.body.appendChild(overlayEl);
  }

  function enterScene(i) {
    if (i < 0 || i >= SCENES.length) return;
    leaveScene();
    sceneIndex = i; stepIndex = 0; playing = false; altOn = false;
    sceneScope = M.scope('story:' + SCENES[i].id);
    active = SCENES[i].create({ scope: sceneScope, host: bodyHost, advance: () => stepForward(true) });
    titleEl.textContent = active.title || '';
    if (eyebrowEl) eyebrowEl.textContent = active.eyebrow || EYEBROW;
    if (active.alt) {
      clear(altBtn);
      altBtn.appendChild(icon('anomaly'));
      altBtn.appendChild(document.createTextNode(active.alt.label));
      altBtn.title = active.alt.title || '';
      altBtn.style.display = '';
      altBtn.classList.remove('is-on');
    } else {
      altBtn.style.display = 'none';
    }
    active.applyStep(0);
    updateChrome();
  }
  function leaveScene() {
    pause();
    if (sceneScope) sceneScope.kill();
    sceneScope = null; active = null;
    if (bodyHost) clear(bodyHost);
  }
  function nextScene() { if (sceneIndex < SCENES.length - 1) enterScene(sceneIndex + 1); }
  function prevScene() { if (sceneIndex > 0) enterScene(sceneIndex - 1); }

  /* ---- generic stepper (shared by every scene) ---- */
  function stepForward(animate) {
    if (!active || stepIndex >= active.stepCount) return;
    stepIndex++;
    active.applyStep(stepIndex);
    if (animate && active.enterStep) active.enterStep(stepIndex);
    updateChrome();
  }
  function stepBack() {
    if (!active || stepIndex <= 0) return;
    pause(); stepIndex--; active.applyStep(stepIndex); updateChrome();
  }
  function restart() {
    if (!active) return;
    pause(); stepIndex = 0; active.applyStep(0); updateChrome();
  }
  function play() {
    if (playing || !active || stepIndex >= active.stepCount) return;
    playing = true; updateChrome(); scheduleNext();
  }
  function scheduleNext() {
    if (!sceneScope) return;
    playTimer = sceneScope.after(stepIndex === 0 ? 320 : 1080, () => {
      stepForward(true);
      if (playing && active && stepIndex < active.stepCount) scheduleNext();
      else { playing = false; updateChrome(); }
    });
  }
  function pause() {
    playing = false;
    if (playTimer != null && sceneScope) { sceneScope.cancelTimer(playTimer); playTimer = null; }
    updateChrome();
  }
  function togglePlay() { playing ? pause() : play(); }
  function toggleAlt() {
    if (!active || !active.alt || !active.setAlt) return;
    altOn = !altOn;
    active.setAlt(altOn);
    restart();
    altBtn.classList.toggle('is-on', altOn);
  }

  function updateChrome() {
    if (!active) return;
    if (sceneDotsEl) Array.prototype.forEach.call(sceneDotsEl.children, (d, i) => {
      d.classList.toggle('active', i === sceneIndex);
      d.classList.toggle('done', i < sceneIndex);
    });
    if (stepTextEl) stepTextEl.textContent = 'Step ' + stepIndex + ' / ' + active.stepCount;
    if (playBtn) { clear(playBtn); playBtn.appendChild(icon('play')); playBtn.appendChild(document.createTextNode(playing ? 'Pause' : 'Play')); }
    if (prevBtn) prevBtn.disabled = sceneIndex === 0;
    if (nextBtn) nextBtn.disabled = sceneIndex === SCENES.length - 1;
    // "continue ›" CTA appears once the scene has played out and a next scene exists
    const hasNext = sceneIndex < SCENES.length - 1;
    if (nextCta) {
      if (stepIndex >= active.stepCount && hasNext) {
        clear(nextCta);
        nextCta.appendChild(document.createTextNode('Continue '));
        nextCta.appendChild(icon('chevron', { width: 15, height: 15 }));
        nextCta.style.display = '';
      } else {
        nextCta.style.display = 'none';
      }
    }
  }

  /* ---- keyboard (capture phase; A–E swallowed so the console behind
     us doesn't switch tabs — AC-11/AC-14) ---- */
  function onKey(e) {
    if (!isOpen) return;
    const tag = e.target && e.target.tagName;
    if (tag && /input|textarea|select/i.test(tag)) return;
    const k = e.key;
    if (k === ' ' || k === 'Spacebar') { e.preventDefault(); togglePlay(); }
    else if (k === 'ArrowRight') { e.preventDefault(); pause(); stepForward(true); }
    else if (k === 'ArrowLeft') { e.preventDefault(); stepBack(); }
    else if (k === 'r' || k === 'R') { e.preventDefault(); restart(); }
    else if (k === '[') { e.preventDefault(); prevScene(); }
    else if (k === ']') { e.preventDefault(); nextScene(); }
    else if (k === 'Escape') { e.preventDefault(); close(); }
    else if (/^[a-eA-E]$/.test(k)) { e.stopPropagation(); }
  }

  window.OCT.ViewStory = {
    mountLauncher: mountLauncher,
    open: open,
    close: close,
    /* verification probe (AC-13 leak check): { open, scene, step, motion:{...,total} } */
    _probe: function () { return { open: isOpen, scene: sceneIndex, step: stepIndex, motion: O.Motion.activeCount() }; }
  };
})();
