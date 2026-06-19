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
      'ตี 2 ครึ่ง. ทั้งฟาร์มหลับ — แต่บ่อ P-12 ไม่ได้หลับ.',
      'ออกซิเจนในน้ำกำลังร่วง ช้า ๆ — 4.8 … 4.7 … 4.6 mg/L. ยังไม่มีใครเห็น.',
      'ถ้าปล่อยไว้ มันจะแตะเส้นอันตราย 4.0 ในราว ๆ 70 นาที. นี่คือ “เวลานำ” ที่คุณมี.',
      'บ่อนี้ = ~16 ตันชีวมวล · ราว ฿2.3M. ออกซิเจนหมดตอนตี 3 — กว่าจะรู้ตอนเช้า ก็สาย.',
      'แล้วถ้ามีบางอย่างเฝ้าดูแทนคุณ — และปลุกคุณ ก่อน เส้น 4.0 ล่ะ?'
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
        h('div', { class: 'hook-place' }, 'ฟาร์มกุ้ง · บ่อ P-12')
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
    etaBadge.appendChild(s('text', { x: 40, y: 13, 'text-anchor': 'middle' }, '~70 นาที'));
    gProj.appendChild(etaBadge);
    chart.appendChild(gProj);
    stage.appendChild(chart);

    // the stake (shown step 3) — $/biomass attached
    const stake = h('div', { class: 'hook-stake', 'data-layer': 'stake' }, [
      h('div', { class: 'stk' }, [h('span', { class: 'stk-k' }, 'ชีวมวลในบ่อ'), h('span', { class: 'stk-v' }, '~16 ตัน')]),
      h('div', { class: 'stk' }, [h('span', { class: 'stk-k' }, 'มูลค่าเสี่ยง'), h('span', { class: 'stk-v crit' }, '≈ ฿2.3M')]),
      h('div', { class: 'stk' }, [h('span', { class: 'stk-k' }, 'รู้ตอนเช้า'), h('span', { class: 'stk-v crit' }, 'สาย')])
    ]);
    stage.appendChild(stake);

    // the turn (shown step 4) — couples into scene 2
    const turn = h('div', { class: 'hook-turn', 'data-layer': 'turn' }, [
      icon('anomaly', { width: 15, height: 15 }),
      'มีบางอย่างเฝ้าดูแทนคุณได้ — และปลุกคุณ ก่อน เส้น 4.0'
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

    return { title: 'ตี 2 — ออกซิเจนในบ่อกำลังร่วง', stepCount: 4, applyStep: applyStep, enterStep: enterStep };
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
        ['จับได้ — ก่อนเส้นอันตราย', 'เฝ้าดูบ่อ P-12 ตลอดคืน'],
        ['เสนอการแก้ + เหตุผล', 'DO 4.6 ยังไม่แตะ 4.0'],
        ['เปิดเหตุผลทั้งหมด', 'query → rule → llm · โปร่งใส'],
        ['ไม่มีอะไรทำงานก่อน คุณ เซ็น', 'governance = จุดแข็ง'],
        ['เซ็น → ทำงาน → log ครบ', 'ใครเซ็นก็รู้ · ย้อนกลับได้']
      ],
      fault: [
        ['จับได้ — ก่อนเส้นอันตราย', 'เฝ้าดูบ่อ P-12 ตลอดคืน'],
        ['เสนอการแก้ + เหตุผล', 'DO 4.6 ยังไม่แตะ 4.0'],
        ['🌟 AI ไม่มั่นใจ → จับตัวเองได้', '0.41 < 0.70 → กฎ fail-safe'],
        ['กฎ ก็ยัง รอ คุณ เซ็น', 'error ก็ยัง governed'],
        ['เซ็น → กฎทำงาน → log ครบ', 'ปลอดภัยแม้ AI พลาด']
      ]
    };
    const CAP = {
      happy: [
        'มีบางอย่างเฝ้าดูบ่อ P-12 ตลอดคืน. และมันเพิ่งจับอะไรได้.',
        'จับได้ตั้งแต่ DO ยัง 4.6 — ก่อน แตะเส้น 4.0. ไม่ใช่หลังกุ้งตาย.',
        'นี่คือเหตุผลทั้งหมด: query → rule → llm. ทุกขั้นเปิดให้ตรวจ.',
        'แต่มันไม่ทำอะไรเลย จนกว่า คุณ จะเซ็น. นี่คือจุดแข็ง ไม่ใช่ข้อจำกัด.',
        'เซ็นแล้ว → เครื่องเติมอากาศทำงาน → log ครบ ใครเซ็นก็รู้ · ย้อนกลับได้.'
      ],
      fault: [
        'คืนนี้ AI ที่แต่งคำสั่ง “ไม่มั่นใจ”. ดูสิ่งที่ระบบทำ.',
        'จับได้เหมือนเดิม — DO ร่วง ก่อนเส้น 4.0.',
        'AI มั่นใจแค่ 0.41 (ต่ำกว่าเกณฑ์ 0.70) → ระบบสลับไปกฎ fail-safe เอง. มันจับตัวเองได้.',
        'และถึงจะเป็นกฎ ไม่ใช่ AI — มันก็ยัง รอคุณเซ็น เหมือนเดิม. error ก็ยัง governed.',
        'เซ็น → กฎ SOP-DO-01 ทำงาน → log ครบ · ย้อนกลับได้. ปลอดภัยแม้ AI พลาด.'
      ]
    };

    const root = h('div', { class: 'scene-govern' });

    // ---- LEFT: the governance narration rail ----
    const railEls = [];
    const rail = h('div', { class: 'govern-rail' }, [
      h('div', { class: 'col-head' }, [
        h('div', { class: 'eyebrow' }, 'จับได้ + คุณคุม'),
        h('h3', null, 'ระบบโชว์เหตุผล — แล้ว รอ คุณ')
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
      h('span', null, 'ไม่มีอะไรทำงานก่อนคุณเซ็น · ทุก action ถูก log · ย้อนกลับได้')
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
      h('div', { class: 'gc-sec' }, [h('div', { class: 'gc-trace-head' }, [h('div', { class: 'eyebrow' }, 'Reasoning trace'), h('span', { class: 'muted' }, 'อ่านบนลงล่าง')]), traceWrap]),
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
        proposed: ['s-crit', 'Proposed — รอคุณอนุมัติ'],
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
        actionsEl.appendChild(h('span', { class: 'gc-hint' }, 'Reject / Hold ก็ได้ — ทุกทางถูก log'));
        const wrap = h('div', { class: 'gc-act-btns' }, [
          h('button', { class: 'btn primary', onClick: () => advance() }, [icon('check'), 'Approve']),
          h('button', { class: 'btn danger sm', onClick: () => { cap.textContent = 'ปฏิเสธ — ไม่มี action ใดทำงาน. และการปฏิเสธ ก็ถูก log เช่นกัน.'; } }, [icon('x', { width: 14, height: 14 }), 'Reject'])
        ]);
        actionsEl.appendChild(wrap);
      } else {
        actionsEl.appendChild(h('span', { class: 'gc-hint muted' }, 'ระบบกำลังเสนอ — ยังไม่มีอะไรทำงาน'));
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
        ? 'AI ไม่ผ่านเกณฑ์ความมั่นใจ → ระบบใช้กฎ fail-safe ที่กำหนดไว้ล่วงหน้า'
        : 'เติมอากาศล่วงหน้า ก่อน DO แตะเส้น 4.0 — ขณะที่ยังถูกและทันเวลา';
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
      title: 'จับได้ — และคุณยังคุมทุกอย่าง',
      stepCount: 4,
      alt: { label: 'ถ้า AI ไม่มั่นใจ?', title: 'แสดง self-catch: LLM ไม่มั่นใจ → กฎ fail-safe (ยังต้องเซ็น)' },
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
     The SCENES registry (arc order = G, pain-first). Scenes 4/5 (C1
     remainder) and 6 (C2 breadth) append here on the same contract.
     ============================================================ */
  const SCENES = [
    { id: 'hook',     create: createHookScene },
    { id: 'govern',   create: createGovernScene },
    { id: 'pipeline', create: createPipelineScene }
  ];
  const EYEBROW = 'Story mode · Aquaculture';

  /* ============================================================
     The shell — registry nav + generic stepper + the lifecycle
     teardown contract (two-tier scopes: shell + per-scene).
     ============================================================ */
  let isOpen = false, overlayEl = null, shellScope = null, sceneScope = null;
  let sceneIndex = 0, stepIndex = 0, playing = false, playTimer = null, altOn = false, active = null;
  let titleEl = null, sceneDotsEl = null, stepTextEl = null, playBtn = null, altBtn = null;
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
    overlayEl = null; titleEl = sceneDotsEl = stepTextEl = playBtn = altBtn = null;
    prevBtn = nextBtn = nextCta = bodyHost = null;
    sceneIndex = 0; stepIndex = 0; playing = false; playTimer = null; altOn = false;
  }

  function buildShell() {
    overlayEl = h('div', { class: 'story-overlay', role: 'dialog', 'aria-label': 'OCT story mode — aquaculture' });

    const top = h('div', { class: 'story-top' });
    titleEl = h('h2', null, '');
    top.appendChild(h('div', { class: 'story-id' }, [h('div', { class: 'eyebrow' }, EYEBROW), titleEl]));
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
        nextCta.appendChild(document.createTextNode('ต่อ →'));
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
