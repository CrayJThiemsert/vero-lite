/* view-story-procurement.js — PLAN-0036 Step 6
   5 procurement operator surfaces on the PLAN-0033 SCENES/shell architecture.
   Additive overlay — zero services/ core edits (AC-6 / CQ-1).
   Synthetic data mirrors verticals/procurement/data_adapter/synthetic.py. */
(function () {
  'use strict';
  var O = window.OCT;
  var h = O.h, clear = O.clear, icon = O.icon;
  var M = O.Motion;

  function fmtThb(v) {
    return '฿' + Math.round(v).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  }

  /* ---- data (mirrors synthetic.py — deterministic, no brand names) ---- */
  var DOA = [
    { tier: 1, role: 'หน.จัดซื้อ',    en: 'Head Purchasing',    maxStr: '≤ ฿50,000' },
    { tier: 2, role: 'ผจก.จัดซื้อ',   en: 'Purchasing Manager', maxStr: '≤ ฿500,000' },
    { tier: 3, role: 'ผจก.โรงงาน',    en: 'Plant Manager',      maxStr: '≤ ฿2,000,000' },
    { tier: 4, role: 'ผอ.',            en: 'Director',           maxStr: '> ฿2,000,000' }
  ];

  var HERO_QUOTES = [
    { sup: 'Contracted OEM Spares Co.', price: 1850000, lead: 21, onContract: true,  state: 'slow',     verdict: 'OEM — lead time 21d ช้าเกิน' },
    { sup: 'Regional Industrial Supply', price: 2150000, lead: 5,  onContract: false, state: 'selected', verdict: 'เลือก — lead time 5d (scored rule)' },
    { sup: 'Allied Parts Trading',       price: 1950000, lead: 9,  onContract: false, state: 'blocked',  verdict: 'บล็อก — cert หมดอายุ' }
  ];

  var HERO_COMP = {
    selected: {
      label: 'Regional Industrial Supply (RFQ winner)',
      rows: [
        { rule: 'AVL',           pass: true,  note: 'Emergency AVL exception logged' },
        { rule: 'Tax',           pass: true,  note: 'Tax ID verified' },
        { rule: 'Cert',          pass: true,  note: 'cert valid' },
        { rule: 'Sanctions',     pass: true,  note: 'No match' },
        { rule: 'Single-source', pass: true,  note: 'Emergency waiver covers' }
      ]
    },
    blocked: {
      label: 'Allied Parts Trading (blocked)',
      rows: [{ rule: 'Cert', pass: false, note: 'CERTIFICATION EXPIRED → blocked' }]
    }
  };

  var AI_DRAFT = 'จำเป็นต้องใช้ spindle servo drive (part-spindle-01) เพื่อนำสาย production กลับมาทำงาน ใช้ emergency waiver เนื่องจาก line-down — lead time contract OEM (21 วัน) ยาวเกินไป, ผู้ขาย RFQ สามารถจัดส่งได้ใน 5 วัน. Request AVL exception for Regional Industrial Supply. Amount ฿2,150,000 ต้องได้รับอนุมัติจาก ผอ. ตาม DOA tier-4.';
  var AI_EDITED = 'จำเป็นต้องใช้ spindle servo drive สำหรับ CNC #7 — สายการผลิต line-down ตั้งแต่เช้า ใช้ emergency waiver เนื่องจาก OEM ส่งได้ 21 วัน; เลือก Regional Industrial Supply ที่ส่งได้ใน 5 วัน พร้อม AVL exception. ยืนยัน compliance ครบถ้วนแล้ว. ขอให้ ผอ. อนุมัติ ฿2,150,000.';

  var KPI_DATA = [
    { label: 'Req-to-PO cycle',     value: '3.2 วัน', trend: '↓ 0.8d',    ok: true, target: 'เป้า ≤4 วัน' },
    { label: 'Rush-freight avoided', value: '฿1.8M',   trend: '↑ ฿300k',   ok: true, target: 'vs ไตรมาสก่อน' },
    { label: 'Stockout rate',        value: '0.4%',    trend: '↓ 0.6pp',   ok: true, target: 'เป้า <1%' },
    { label: 'Maverick spend',       value: '2.1%',    trend: '↓ 0.5pp',   ok: true, target: 'เป้า <5%' },
    { label: '% on-contract',        value: '94%',     trend: '↑ 2pp',     ok: true, target: 'เป้า ≥90%' }
  ];

  /* ---- 3 visual register helpers ---- */
  function regAi(label, bodyEl) {
    return h('div', { class: 'pc-reg pc-reg-ai' }, [
      h('div', { class: 'pc-reg-hd' }, [
        h('span', { class: 'badge s-info pc-reg-badge' }, [icon('cpu', { width: 10, height: 10 }), ' AI draft']),
        h('span', { class: 'pc-reg-lbl' }, label)
      ]),
      h('div', { class: 'pc-reg-body' }, [bodyEl])
    ]);
  }
  function regRule(label, bodyEl) {
    return h('div', { class: 'pc-reg pc-reg-rule' }, [
      h('div', { class: 'pc-reg-hd' }, [
        h('span', { class: 'badge s-warn pc-reg-badge' }, 'rule'),
        h('span', { class: 'pc-reg-lbl' }, label)
      ]),
      h('div', { class: 'pc-reg-body' }, [bodyEl])
    ]);
  }

  /* ================================================================
     SCENE 1 — Worklist
     ================================================================ */
  function createWorklistScene(ctx) {
    var scope = ctx.scope, host = ctx.host;
    var CAP = [
      'สายการผลิตไม่เคยหยุด — เช้าของคุณเริ่มต้นที่นี่.',
      'แจ้งเตือนวิกฤต: CNC Machining Center #7 — spindle drive ล้มเหลว, สายการผลิต line down.',
      'Routine: สต๊อก coolant filter ต่ำกว่า reorder point — สั่งซื้อตามสัญญาปกติ.',
      'สองงาน, engine เดียวกัน — hero หนักกว่าเพราะ emergency waiver + DOA tier-4 + ฿2.1M.'
    ];
    var root = h('div', { class: 'pc-scene-wl' });
    root.appendChild(h('div', { class: 'pc-scene-hd' }, [
      h('div', { class: 'eyebrow' }, 'งานที่รอดำเนินการ · Worklist'),
      h('h3', null, 'กรณีเร่งด่วนที่ต้องตัดสินใจของคุณ')
    ]));
    var queue = h('div', { class: 'pc-wl-queue' });

    function makeItem(isHero) {
      return h('div', { class: 'pc-wl-item ' + (isHero ? 'pc-wl-hero' : 'pc-wl-calm') }, [
        h('div', { class: 'pc-wl-top' }, [
          h('span', { class: 'badge ' + (isHero ? 'solid s-crit' : 's-warn') },
            isHero ? 'CRITICAL — LINE DOWN' : 'ROUTINE'),
          h('span', { class: 'pc-wl-age muted' }, isHero ? '15 นาทีที่แล้ว' : '2 ชม. ที่แล้ว')
        ]),
        h('div', { class: 'pc-wl-body' }, [
          h('div', { class: 'pc-wl-title' }, isHero
            ? 'ใบขอซื้อฉุกเฉิน (Emergency PR) — CNC Spindle Servo Drive'
            : 'ใบขอซื้อสต๊อก (Reorder PR) — Coolant Filter Cartridge'),
          h('div', { class: 'pc-wl-sub mono' }, isHero
            ? 'part-spindle-01 · equip-cnc-07 · EEC Assembly Plant 1'
            : 'part-filter-02 · equip-conveyor-05 · EEC Machining Plant 2'),
          h('div', { class: 'pc-wl-meta muted' }, isHero
            ? '⏸ รอ ผอ. (DOA tier-4 + emergency waiver)'
            : '⏸ รอ หน.จัดซื้อ (DOA tier-1 · on-contract)')
        ]),
        h('div', { class: 'pc-wl-amount mono' }, fmtThb(isHero ? 2150000 : 45000))
      ]);
    }

    var heroEl = makeItem(true);
    var calmEl = makeItem(false);
    queue.appendChild(heroEl);
    queue.appendChild(calmEl);
    root.appendChild(queue);
    var cap = h('div', { class: 'pc-scene-cap' }, CAP[0]);
    root.appendChild(cap);
    host.appendChild(root);

    function applyStep(k) {
      cap.textContent = CAP[Math.min(k, CAP.length - 1)];
      heroEl.classList.toggle('pc-shown', k >= 1);
      calmEl.classList.toggle('pc-shown', k >= 2);
      heroEl.classList.toggle('pc-focus', k >= 3);
    }
    function enterStep(k) {
      var el = k === 1 ? heroEl : k === 2 ? calmEl : null;
      if (el && scope) scope.tween(el,
        [{ opacity: 0, transform: 'translateY(8px)' }, { opacity: 1, transform: 'none' }],
        { duration: 340, fill: 'none' });
    }
    return {
      title: 'งานที่รอดำเนินการ — กรณีเร่งด่วน + routine บน engine เดียว',
      stepCount: 3, applyStep: applyStep, enterStep: enterStep
    };
  }

  /* ================================================================
     SCENE 2 — Process Timeline
     ================================================================ */
  function createTimelineScene(ctx) {
    var scope = ctx.scope, host = ctx.host;
    var STEPS = [
      { id: 'intake',     th: 'รับเรื่อง (Intake)',      kind: 'query',  note: 'อ่าน CMMS work-order; LLM-assist เติม PR (advisory draft เท่านั้น)' },
      { id: 'judge',      th: 'ประเมิน (Judge)',          kind: 'rule',   note: 'criticality 0.92 ≥ 0.8 → BREACH → เส้นทาง emergency (deterministic, ไม่ใช้ AI)' },
      { id: 'source',     th: 'จัดหา (Source)',           kind: 'auto',   note: 'OEM 21d → RFQ exception 5d; scored rule เลือก supplier, ไม่ใช่ AI' },
      { id: 'compliance', th: 'Compliance',               kind: 'rule',   note: '5 criteria: AVL exception ✓, cert-expired supplier บล็อก' },
      { id: 'approve',    th: 'อนุมัติ (Approve)',        kind: 'gated',  note: '⏸ รอการตัดสินใจของคุณ — ไม่มีอะไรเกิดขึ้นก่อนคุณเซ็น' },
      { id: 'issue_po',   th: 'ออก PO (Issue PO)',        kind: 'gated',  note: 'ออกใบสั่งซื้อ (PO) หลังอนุมัติ' },
      { id: 'audit',      th: 'บันทึก (Audit)',           kind: 'auto',   note: 'audit record — ใคร/เมื่อไหร่/ตามกฎข้อไหน' }
    ];
    var KIND_CLS = { query: 's-ok', rule: 's-warn', auto: 's-info', gated: 's-crit' };
    var CAP = [
      'Hero · Emergency Sourcing Round — 7 ขั้นตอนบน engine เดียวกัน.',
      '1 — Intake (query): รับ CMMS work-order; LLM-assist ช่วยเติม PR (advisory draft เท่านั้น).',
      '2 — Judge (rule, deterministic): criticality 0.92 ≥ band 0.8 → BREACH → เส้นทาง emergency sourcing.',
      '3 — Source (auto, rule): OEM 21 วัน — ช้าเกิน; scored rule เลือก RFQ exception 5 วัน. ไม่ใช่ AI ที่เลือก.',
      '4 — Compliance (rule, per-criterion): 5 criteria ผ่านสำหรับ supplier ที่เลือก; cert-expired supplier บล็อก.',
      '⏸ 5 — Approve (gated): ระบบหยุด รอการตัดสินใจของคุณ. ไม่มีอะไรเกิดขึ้นก่อนคุณเซ็น.',
      'อนุมัติ → Issue PO → Audit (auto): ทุกขั้นตอนบันทึก — ใคร, เมื่อไหร่, ตามกฎข้อไหน.'
    ];

    var root = h('div', { class: 'pc-scene-tl' });
    root.appendChild(h('div', { class: 'pc-scene-hd' }, [
      h('div', { class: 'eyebrow' }, 'Hero · Emergency Sourcing Round'),
      h('h3', null, '7 ขั้นตอน — จาก line-down ไปถึง PO')
    ]));
    var list = h('div', { class: 'pc-tl-list' });
    var stepEls = {};
    STEPS.forEach(function (s, i) {
      var lineEl = i < STEPS.length - 1 ? h('div', { class: 'pc-tl-line' }) : null;
      var el = h('div', { class: 'pc-tl-step' }, [
        h('div', { class: 'pc-tl-left' }, [h('div', { class: 'pc-tl-n' }, String(i + 1)), lineEl]),
        h('div', { class: 'pc-tl-right' }, [
          h('div', { class: 'pc-tl-top' }, [
            h('span', { class: 'pc-tl-label' }, s.th),
            h('span', { class: 'badge pc-tl-kind ' + KIND_CLS[s.kind] }, s.kind)
          ]),
          h('div', { class: 'pc-tl-note muted' }, s.note)
        ])
      ]);
      stepEls[s.id] = el;
      list.appendChild(el);
    });
    root.appendChild(list);
    var cap = h('div', { class: 'pc-scene-cap' }, CAP[0]);
    root.appendChild(cap);
    host.appendChild(root);

    function applyStep(k) {
      cap.textContent = CAP[Math.min(k, CAP.length - 1)];
      STEPS.forEach(function (s, i) {
        var el = stepEls[s.id];
        el.classList.remove('pc-tl-done', 'pc-tl-active', 'pc-tl-waiting');
        if (k === 0) return;
        if (k >= 6) { el.classList.add('pc-tl-done'); return; }
        var oneIdx = i + 1;
        if (oneIdx < k) el.classList.add('pc-tl-done');
        else if (oneIdx === k) el.classList.add(s.kind === 'gated' ? 'pc-tl-waiting' : 'pc-tl-active');
      });
    }
    function enterStep(k) {
      var s = STEPS[k - 1];
      if (!s) return;
      var el = stepEls[s.id];
      if (el && scope) scope.tween(el,
        [{ opacity: 0.3, transform: 'translateX(-6px)' }, { opacity: 1, transform: 'none' }],
        { duration: 260, fill: 'none' });
    }
    return {
      title: '7 ขั้นตอน — จาก line-down ไปถึง PO',
      stepCount: 6, applyStep: applyStep, enterStep: enterStep
    };
  }

  /* ================================================================
     SCENE 3 — Approval Money Screen
     ================================================================ */
  function createApprovalScene(ctx) {
    var scope = ctx.scope, host = ctx.host, advance = ctx.advance;
    var CAP = [
      'ใบขอซื้อฉุกเฉิน — สิ่งที่คุณเห็นก่อนเซ็น.',
      'Criticality (rule, deterministic): 0.92 ≥ 0.8 → BREACH. ระบบตัดสิน, ไม่ใช่ AI.',
      'AI exec-summary (advisory): ร่างโดย AI — คุณแก้ไขได้ก่อนเซ็น.',
      'Compliance per-criterion + DOA ladder — โอกาสตรวจสอบก่อนเซ็น.',
      'Quote comparison + SoD chain. Scored rule เลือก supplier. คุณตัดสินใจ.'
    ];

    var root = h('div', { class: 'pc-scene-apv' });
    root.appendChild(h('div', { class: 'pc-scene-hd' }, [
      h('div', { class: 'eyebrow' }, 'Approval · Money Screen'),
      h('h3', null, 'ใบขอซื้อฉุกเฉิน (Emergency PR) — CNC Spindle Servo Drive')
    ]));
    var cols = h('div', { class: 'pc-apv-cols' });
    var leftCol  = h('div', { class: 'pc-apv-left' });
    var rightCol = h('div', { class: 'pc-apv-right' });
    cols.appendChild(leftCol); cols.appendChild(rightCol);
    root.appendChild(cols);
    var cap = h('div', { class: 'pc-scene-cap' }, CAP[0]);
    root.appendChild(cap);
    host.appendChild(root);

    function bAsk() {
      return h('div', { class: 'pc-apv-ask' }, [
        h('div', { class: 'pc-apv-ask-row' }, [
          h('span', { class: 'eyebrow' }, 'ใบขอซื้อ (PR) · สาเหตุ: equipment failure'),
          h('span', { class: 'mono muted' }, 'part-spindle-01')
        ]),
        h('div', { class: 'pc-apv-ask-title' }, 'CNC Spindle Servo Drive'),
        h('div', { class: 'pc-apv-ask-meta' }, [
          h('span', null, 'equip-cnc-07 · EEC Assembly Plant 1'),
          h('span', { class: 'pc-apv-amount' }, fmtThb(2150000))
        ])
      ]);
    }
    function bCrit() {
      return regRule('criticality_band · judge step (deterministic)',
        h('div', { class: 'pc-crit-row' }, [
          h('span', { class: 'pc-crit-val' }, '0.92'),
          h('span', { class: 'pc-crit-sep' }, ' ≥ 0.8 → '),
          h('span', { class: 'badge solid s-crit' }, 'BREACH · CRITICAL'),
          h('span', { class: 'pc-crit-note muted' }, '(threshold ใน procedures.yaml)')
        ]));
    }
    function bSummary() {
      var wrap = regAi('exec-summary · approve step (advisory, แก้ไขได้)',
        h('div', { class: 'pc-summ-text' }, AI_DRAFT));
      wrap.appendChild(h('div', { class: 'pc-summ-hint muted' }, '✎ แก้ไขก่อนเซ็น — ร่างโดย AI, คุณเป็นผู้ตัดสินใจ'));
      return wrap;
    }
    function bWaiver() {
      return h('div', { class: 'pc-waiver' }, [
        h('span', { class: 'badge s-warn pc-reg-badge' }, [icon('anomaly', { width: 11, height: 11 }), ' Emergency Waiver']),
        h('span', { class: 'pc-waiver-txt' }, '3-bid/sole-source ผ่อนปรน · escalate approver → ผอ. · force logged justification')
      ]);
    }
    function bComp() {
      var sec = h('div', { class: 'pc-apv-section' });
      sec.appendChild(h('div', { class: 'eyebrow pc-sec-hd' }, 'Compliance · per-criterion'));
      ['selected', 'blocked'].forEach(function (grp) {
        var d = HERO_COMP[grp];
        sec.appendChild(h('div', { class: 'pc-comp-grp' }, [
          h('div', { class: 'pc-comp-sup' }, d.label),
          h('div', { class: 'pc-comp-rows' },
            d.rows.map(function (r) {
              return h('div', { class: 'pc-comp-row ' + (r.pass ? 'pc-comp-pass' : 'pc-comp-fail') }, [
                h('span', { class: 'pc-comp-icon' }, r.pass ? '✓' : '✗'),
                h('span', { class: 'pc-comp-name' }, r.rule),
                h('span', { class: 'pc-comp-note muted' }, r.note)
              ]);
            })
          )
        ]));
      });
      return sec;
    }
    function bDoa() {
      var sec = h('div', { class: 'pc-apv-section' });
      sec.appendChild(h('div', { class: 'eyebrow pc-sec-hd' }, 'DOA Ladder · ' + fmtThb(2150000)));
      DOA.forEach(function (d) {
        var active = d.tier === 4;
        sec.appendChild(h('div', { class: 'pc-doa-row' + (active ? ' pc-doa-active' : '') }, [
          h('span', { class: 'pc-doa-t' }, 'T' + d.tier),
          h('span', { class: 'pc-doa-role' }, d.role + ' (' + d.en + ')'),
          h('span', { class: 'pc-doa-max mono' }, d.maxStr),
          active ? h('span', { class: 'badge s-crit' }, 'required') : null
        ]));
      });
      return sec;
    }
    function bQuotes() {
      var sec = h('div', { class: 'pc-apv-section' });
      sec.appendChild(h('div', { class: 'eyebrow pc-sec-hd' }, 'Quote comparison · scored rule เลือก'));
      HERO_QUOTES.forEach(function (q) {
        var badge = q.state === 'selected' ? h('span', { class: 'badge s-ok' }, 'เลือก')
                  : q.state === 'blocked'  ? h('span', { class: 'badge s-crit' }, 'บล็อก')
                  : h('span', { class: 'badge s-neutral' }, 'ช้า');
        sec.appendChild(h('div', { class: 'pc-q-row pc-q-' + q.state }, [
          h('div', { class: 'pc-q-sup' }, q.sup + (q.onContract ? ' ★' : '')),
          h('div', { class: 'pc-q-detail' }, [
            h('span', null, fmtThb(q.price)),
            h('span', { class: 'pc-q-lt' }, 'lead ' + q.lead + 'd')
          ]),
          h('div', { class: 'pc-q-v' }, [badge, h('span', { class: 'pc-q-vt muted' }, q.verdict)])
        ]));
      });
      return sec;
    }
    function bSod() {
      var chain = ['วิศวกรซ่อม (requester)', 'หน.จัดซื้อ', 'ผจก.โรงงาน', 'ผอ. (approver)'];
      var row = h('div', { class: 'pc-sod-row' });
      chain.forEach(function (s, i) {
        row.appendChild(h('span', { class: 'pc-sod-s' }, s));
        if (i < chain.length - 1) row.appendChild(h('span', { class: 'pc-sod-sep' }, ' › '));
      });
      return h('div', { class: 'pc-apv-section' }, [
        h('div', { class: 'eyebrow pc-sec-hd' }, 'SoD — ผู้ขอ ≠ ผู้อนุมัติ ≠ ผู้รับ ≠ AP'), row
      ]);
    }

    var rejected = false;
    function bActions() {
      return h('div', { class: 'pc-apv-actions' }, [
        h('div', { class: 'pc-apv-hint muted' }, 'Reject / Hold ก็บันทึกเช่นกัน — ทุกการตัดสินใจมี audit trail'),
        h('div', { class: 'pc-apv-btns' }, [
          h('button', { class: 'pc-btn pc-btn-danger', onClick: function () { rejected = true; rebuild(4); cap.textContent = 'ปฏิเสธ — การตัดสินใจปฏิเสธถูกบันทึกด้วย. ไม่มีอะไรเกิดขึ้น.'; } },
            [icon('x', { width: 12, height: 12 }), ' Reject']),
          h('button', { class: 'pc-btn pc-btn-primary', onClick: advance },
            [icon('check', { width: 12, height: 12 }), ' อนุมัติ'])
        ])
      ]);
    }

    function rebuild(k) {
      clear(leftCol); clear(rightCol);
      leftCol.appendChild(bAsk());
      if (k >= 1) leftCol.appendChild(bCrit());
      if (k >= 2) { leftCol.appendChild(bSummary()); leftCol.appendChild(bWaiver()); }
      if (k >= 3) { rightCol.appendChild(bComp()); rightCol.appendChild(bDoa()); }
      if (k >= 4) {
        rightCol.appendChild(bQuotes()); rightCol.appendChild(bSod());
        if (rejected) {
          rightCol.appendChild(h('div', { class: 'pc-apv-rejected' }, [
            h('span', { class: 'badge s-neutral' }, 'Rejected'),
            h('span', { class: 'muted' }, 'ไม่มีอะไรเกิดขึ้น — การปฏิเสธถูกบันทึกด้วย')
          ]));
        } else {
          rightCol.appendChild(bActions());
        }
      }
    }

    function applyStep(k) {
      rejected = false;
      cap.textContent = CAP[Math.min(k, CAP.length - 1)];
      rebuild(k);
    }
    function enterStep(k) {
      var col = k <= 2 ? leftCol : rightCol;
      var last = col.lastElementChild;
      if (last && scope) scope.tween(last,
        [{ opacity: 0, transform: 'translateY(5px)' }, { opacity: 1, transform: 'none' }],
        { duration: 260, fill: 'none' });
    }
    return {
      title: 'Approval "Money Screen" — ลงรายละเอียดก่อนเซ็น',
      stepCount: 4, applyStep: applyStep, enterStep: enterStep
    };
  }

  /* ================================================================
     SCENE 4 — Graduation Moment
     ================================================================ */
  function createGraduationScene(ctx) {
    var scope = ctx.scope, host = ctx.host;
    var CAP = [
      'AI ร่าง exec-summary — advisory, แก้ไขได้. ยังไม่มีอะไรถูกตัดสินใจ.',
      'คุณอ่าน, ปรับถ้อยคำ, ทำให้เป็นของคุณ.',
      'อนุมัติ → badge พลิก: จาก "AI draft" เป็น "human-approved" พร้อมชื่อ, ตำแหน่ง, เวลา.',
      'Governed ≠ generated: AI ช่วยร่าง. Rules ตัดสิน. Humans อนุมัติ. ระบบรู้ว่าใครตัดสินใจ, เมื่อไหร่, ทำไม.'
    ];

    var root = h('div', { class: 'pc-scene-grad' });
    root.appendChild(h('div', { class: 'pc-scene-hd' }, [
      h('div', { class: 'eyebrow' }, 'Graduation Moment — governed ≠ generated'),
      h('h3', null, 'จาก AI draft → human-approved')
    ]));
    var card = h('div', { class: 'pc-grad-card' });
    root.appendChild(card);
    var cap = h('div', { class: 'pc-scene-cap' }, CAP[0]);
    root.appendChild(cap);
    host.appendChild(root);

    function buildCard(k) {
      clear(card);
      var approved = k >= 2;
      card.classList.toggle('pc-human-approved', approved);
      var regBar = approved
        ? h('div', { class: 'pc-grad-reg' }, [
            h('span', { class: 'badge solid s-ok pc-reg-badge' }, [icon('check', { width: 10, height: 10 }), ' human-approved']),
            h('span', { class: 'pc-grad-who' }, 'นัตพงษ์ ว. · ผอ. (Director) · 01/06/2569 10:42')
          ])
        : h('div', { class: 'pc-grad-reg' }, [
            h('span', { class: 'badge s-info pc-reg-badge' }, [icon('cpu', { width: 10, height: 10 }), ' AI draft · advisory · แก้ไขได้']),
            k >= 1 ? h('span', { class: 'pc-grad-edited muted' }, '✓ คุณแก้ไขแล้ว') : null
          ]);
      card.appendChild(regBar);
      card.appendChild(h('div', { class: 'pc-grad-lbl eyebrow' }, 'exec-summary · justification draft'));
      card.appendChild(h('div', { class: 'pc-grad-text' + (approved ? ' pc-settled' : '') },
        k >= 1 ? AI_EDITED : AI_DRAFT));
      if (approved) {
        card.appendChild(h('div', { class: 'pc-grad-receipt' }, [
          icon('receipt', { width: 12, height: 12 }),
          ' po-spindle-01 · audit#pr-001 · ย้อนกลับได้'
        ]));
      }
      if (k >= 3) {
        card.appendChild(h('div', { class: 'pc-grad-takeaway' }, [
          h('div', { class: 'pc-grad-tk-line' }, [
            h('span', { class: 'badge solid s-ok pc-reg-badge' }, [icon('check', { width: 11, height: 11 }), ' governed ≠ generated']),
            '  AI ช่วยร่าง · Rules ตัดสิน · Humans อนุมัติ'
          ])
        ]));
      }
    }

    function applyStep(k) {
      cap.textContent = CAP[Math.min(k, CAP.length - 1)];
      buildCard(k);
    }
    function enterStep(k) {
      if (k === 2 && scope)
        scope.tween(card, [{ opacity: 0.2, transform: 'scale(0.97)' }, { opacity: 1, transform: 'none' }], { duration: 380, fill: 'none' });
      if (k === 3) {
        var tk = card.querySelector('.pc-grad-takeaway');
        if (tk && scope) scope.tween(tk, [{ opacity: 0, transform: 'translateY(6px)' }, { opacity: 1, transform: 'none' }], { duration: 280, fill: 'none' });
      }
    }
    return {
      title: 'Graduation — AI draft → human-approved (governed ≠ generated)',
      stepCount: 3, applyStep: applyStep, enterStep: enterStep
    };
  }

  /* ================================================================
     SCENE 5 — Monitoring Dashboard
     ================================================================ */
  function createDashboardScene(ctx) {
    var scope = ctx.scope, host = ctx.host;
    var CAP = [
      'ผลลัพธ์ที่วัดได้ — ไม่ใช่แค่ตัวเลขสวยงาม.',
      '5 KPI — แต่ละตัวมี value + trend + target.',
      'Emergency waivers (watched) + งานรอแยกตาม DOA tier.',
      'AI throughput: AI ช่วยร่าง 12 รายการ · 0 การเลือก supplier · 0 การอนุมัติ — governed ≠ generated.'
    ];
    var root = h('div', { class: 'pc-scene-dash' });
    root.appendChild(h('div', { class: 'pc-scene-hd' }, [
      h('div', { class: 'eyebrow' }, 'Monitoring Dashboard · EEC Plants'),
      h('h3', null, 'KPI ที่วัดได้ + AI ที่โปร่งใส')
    ]));
    var body = h('div', { class: 'pc-dash-body' });
    root.appendChild(body);
    var cap = h('div', { class: 'pc-scene-cap' }, CAP[0]);
    root.appendChild(cap);
    host.appendChild(root);

    function buildKpis() {
      var row = h('div', { class: 'pc-kpi-row' });
      KPI_DATA.forEach(function (kd) {
        row.appendChild(h('div', { class: 'pc-kpi' }, [
          h('div', { class: 'pc-kpi-lbl eyebrow' }, kd.label),
          h('div', { class: 'pc-kpi-val mono' }, kd.value),
          h('div', { class: 'pc-kpi-trend ' + (kd.ok ? 'pc-trend-ok' : 'pc-trend-bad') }, kd.trend),
          h('div', { class: 'pc-kpi-tgt muted' }, kd.target)
        ]));
      });
      return row;
    }
    function buildRow2() {
      var row = h('div', { class: 'pc-dash-r2' });
      row.appendChild(h('div', { class: 'pc-dash-waivers' }, [
        h('div', { class: 'eyebrow' }, 'Emergency Waivers'),
        h('div', { class: 'pc-w-val' }, [
          h('span', { class: 'pc-w-n' }, '2'),
          h('span', { class: 'pc-w-denom muted' }, ' / 5 ต่อไตรมาส')
        ]),
        h('span', { class: 'badge s-warn pc-reg-badge' }, [icon('anomaly', { width: 11, height: 11 }), ' WATCHED'])
      ]));
      var tiers = h('div', { class: 'pc-dash-tiers' });
      tiers.appendChild(h('div', { class: 'eyebrow' }, 'รอแยกตาม DOA tier'));
      [
        { tier: 1, label: 'หน.จัดซื้อ',  count: 3, hero: false },
        { tier: 2, label: 'ผจก.จัดซื้อ', count: 1, hero: false },
        { tier: 4, label: 'ผอ.',          count: 1, hero: true  }
      ].forEach(function (t) {
        tiers.appendChild(h('div', { class: 'pc-tier-row' + (t.hero ? ' pc-tier-hero' : '') }, [
          h('span', { class: 'pc-tier-lbl' }, 'Tier ' + t.tier + ' · ' + t.label),
          h('span', { class: 'badge ' + (t.hero ? 's-crit' : 's-neutral') }, t.count + ' PO')
        ]));
      });
      row.appendChild(tiers);
      return row;
    }
    function buildAiPanel() {
      var inner = h('div', { class: 'pc-ai-grid' }, [
        h('div', { class: 'pc-ai-row' }, [h('span', { class: 'pc-ai-k' }, 'AI ร่าง justification'), h('span', { class: 'pc-ai-v' }, '12 รายการ')]),
        h('div', { class: 'pc-ai-row' }, [h('span', { class: 'pc-ai-k' }, 'AI เลือก supplier'),    h('span', { class: 'pc-ai-v pc-ai-zero' }, '0 (scored rule เลือกเสมอ)')]),
        h('div', { class: 'pc-ai-row' }, [h('span', { class: 'pc-ai-k' }, 'AI อนุมัติ'),          h('span', { class: 'pc-ai-v pc-ai-zero' }, '0 (human gate เสมอ)')])
      ]);
      var wrap = h('div', { class: 'pc-dash-ai-wrap' });
      wrap.appendChild(regAi('throughput panel · AI assistance', inner));
      wrap.appendChild(h('div', { class: 'pc-ai-note' }, [
        icon('check', { width: 11, height: 11 }),
        ' Governed ≠ generated: AI assists (drafts). Rules + humans govern (selection / approval / audit).'
      ]));
      return wrap;
    }

    function rebuild(k) {
      clear(body);
      if (k >= 1) body.appendChild(buildKpis());
      if (k >= 2) body.appendChild(buildRow2());
      if (k >= 3) body.appendChild(buildAiPanel());
    }
    function applyStep(k) {
      cap.textContent = CAP[Math.min(k, CAP.length - 1)];
      rebuild(k);
    }
    function enterStep() {
      var last = body.lastElementChild;
      if (last && scope) scope.tween(last,
        [{ opacity: 0, transform: 'translateY(6px)' }, { opacity: 1, transform: 'none' }],
        { duration: 320, fill: 'none' });
    }
    return {
      title: 'Dashboard — KPI ที่วัดได้ + AI ที่โปร่งใส',
      stepCount: 3, applyStep: applyStep, enterStep: enterStep
    };
  }

  /* ================================================================
     SCENES registry
     ================================================================ */
  var SCENES = [
    { id: 'worklist',   create: createWorklistScene },
    { id: 'timeline',   create: createTimelineScene },
    { id: 'approval',   create: createApprovalScene },
    { id: 'graduation', create: createGraduationScene },
    { id: 'dashboard',  create: createDashboardScene }
  ];
  var EYEBROW = 'Story mode · Procurement';

  /* ================================================================
     Shell — two-tier scope teardown contract
     Shell scope: keyboard listener + overlay lifetime.
     Scene scope: per-scene tweens; killed on leaveScene.
     ================================================================ */
  var isOpen = false, overlayEl = null;
  var shellScope = null, sceneScope = null;
  var sceneIdx = 0, stepIdx = 0, playing = false, playTimer = null;
  var titleEl = null, dotsEl = null, stepEl = null, playBtn = null;
  var prevBtn = null, nextBtn = null, nextCtaEl = null, bodyHost = null;
  var activeScene = null;

  function mountLauncher(hostEl) {
    if (!hostEl) return;
    hostEl.appendChild(h('button', {
      class: 'story-launch story-launch-proc',
      onClick: open,
      title: 'Procurement story (P)'
    }, [icon('receipt', { width: 13, height: 13 }), ' Procurement']));
    window.addEventListener('keydown', function (e) {
      if (isOpen) return;
      var tag = e.target && e.target.tagName;
      if (tag && /^(INPUT|TEXTAREA|SELECT)$/i.test(tag)) return;
      if (e.key === 'p' || e.key === 'P') { e.preventDefault(); open(); }
    });
  }

  function open() {
    if (isOpen) return;
    isOpen = true;
    shellScope = M.scope('proc-shell');
    buildShell();
    shellScope.on(window, 'keydown', onKey, true);
    enterScene(0);
  }

  function close() {
    if (!isOpen) return;
    isOpen = false;
    leaveScene();
    if (shellScope) { shellScope.kill(); shellScope = null; }
    if (overlayEl && overlayEl.parentNode) overlayEl.parentNode.removeChild(overlayEl);
    overlayEl = null; titleEl = null; dotsEl = null; stepEl = null;
    playBtn = null; prevBtn = null; nextBtn = null; nextCtaEl = null; bodyHost = null;
    sceneIdx = 0; stepIdx = 0; playing = false; playTimer = null;
  }

  function buildShell() {
    overlayEl = h('div', { class: 'story-overlay', role: 'dialog', 'aria-label': 'OCT procurement story mode' });

    var top = h('div', { class: 'story-top' });
    titleEl = h('h2', null, '');
    top.appendChild(h('div', { class: 'story-id' }, [
      h('div', { class: 'eyebrow story-id-proc' }, EYEBROW), titleEl
    ]));
    top.appendChild(h('div', { class: 'flex' }));

    dotsEl = h('div', { class: 'story-dots' });
    SCENES.forEach(function (s, i) {
      dotsEl.appendChild(h('span', { class: 'dot', title: 'Scene ' + (i + 1) + ': ' + s.id }));
    });
    top.appendChild(dotsEl);

    var transport = h('div', { class: 'story-transport' });
    playBtn = h('button', { class: 'iconbtn', onClick: togglePlay, title: 'Play/pause (Space)' }, [icon('play'), ' Play']);
    transport.appendChild(playBtn);
    transport.appendChild(h('button', { class: 'iconbtn', title: 'Step (→)', onClick: function () { pause(); stepForward(true); } }, [icon('chevron'), ' Step']));
    transport.appendChild(h('button', { class: 'iconbtn', title: 'Restart (R)', onClick: restart }, [icon('refresh'), ' Restart']));
    top.appendChild(transport);

    stepEl = h('div', { class: 'story-steptext mono' }, '');
    top.appendChild(stepEl);

    var nav = h('div', { class: 'story-scenenav' });
    prevBtn = h('button', { class: 'iconbtn', onClick: prevScene, title: 'Prev ([)' }, '‹');
    nextBtn = h('button', { class: 'iconbtn', onClick: nextScene, title: 'Next (])' }, '›');
    nav.appendChild(prevBtn); nav.appendChild(nextBtn);
    top.appendChild(nav);
    top.appendChild(h('button', { class: 'iconbtn', onClick: close, title: 'Exit (Esc)' }, [icon('x'), ' Exit']));
    overlayEl.appendChild(top);

    bodyHost = h('div', { class: 'story-body' });
    overlayEl.appendChild(bodyHost);
    nextCtaEl = h('button', { class: 'story-nextcta', style: { display: 'none' }, onClick: nextScene }, '');
    overlayEl.appendChild(nextCtaEl);
    document.body.appendChild(overlayEl);
  }

  function enterScene(i) {
    if (i < 0 || i >= SCENES.length) return;
    leaveScene();
    sceneIdx = i; stepIdx = 0; playing = false;
    sceneScope = M.scope('proc:' + SCENES[i].id);
    activeScene = SCENES[i].create({ scope: sceneScope, host: bodyHost, advance: nextScene });
    if (titleEl) titleEl.textContent = activeScene.title || '';
    activeScene.applyStep(0);
    updateChrome();
  }

  function leaveScene() {
    pause();
    if (sceneScope) { sceneScope.kill(); sceneScope = null; }
    activeScene = null;
    if (bodyHost) clear(bodyHost);
  }

  function nextScene() { if (sceneIdx < SCENES.length - 1) enterScene(sceneIdx + 1); }
  function prevScene() { if (sceneIdx > 0) enterScene(sceneIdx - 1); }

  function stepForward(animate) {
    if (!activeScene || stepIdx >= activeScene.stepCount) return;
    stepIdx++;
    activeScene.applyStep(stepIdx);
    if (animate && activeScene.enterStep) activeScene.enterStep(stepIdx);
    updateChrome();
  }
  function stepBack() {
    if (!activeScene || stepIdx <= 0) return;
    pause(); stepIdx--; activeScene.applyStep(stepIdx); updateChrome();
  }
  function restart() {
    if (!activeScene) return;
    pause(); stepIdx = 0; activeScene.applyStep(0); updateChrome();
  }

  function play() {
    if (playing || !activeScene || stepIdx >= activeScene.stepCount) return;
    playing = true; updateChrome(); scheduleNext();
  }
  function scheduleNext() {
    playTimer = setTimeout(function () {
      playTimer = null;
      stepForward(true);
      if (playing && activeScene && stepIdx < activeScene.stepCount) scheduleNext();
      else { playing = false; updateChrome(); }
    }, stepIdx === 0 ? 320 : 1400);
  }
  function pause() {
    playing = false;
    if (playTimer !== null) { clearTimeout(playTimer); playTimer = null; }
    updateChrome();
  }
  function togglePlay() { playing ? pause() : play(); }

  function updateChrome() {
    if (!activeScene) return;
    if (dotsEl) Array.prototype.forEach.call(dotsEl.children, function (d, i) {
      d.classList.toggle('active', i === sceneIdx);
      d.classList.toggle('done', i < sceneIdx);
    });
    if (stepEl) stepEl.textContent = 'Step ' + stepIdx + ' / ' + activeScene.stepCount;
    if (playBtn) {
      clear(playBtn);
      playBtn.appendChild(icon('play'));
      playBtn.appendChild(document.createTextNode(playing ? ' Pause' : ' Play'));
    }
    if (prevBtn) prevBtn.disabled = sceneIdx === 0;
    if (nextBtn) nextBtn.disabled = sceneIdx === SCENES.length - 1;
    if (nextCtaEl) {
      var atEnd = stepIdx >= activeScene.stepCount;
      var hasNext = sceneIdx < SCENES.length - 1;
      if (atEnd && hasNext) {
        clear(nextCtaEl);
        nextCtaEl.appendChild(document.createTextNode('Continue '));
        nextCtaEl.appendChild(icon('chevron', { width: 14, height: 14 }));
        nextCtaEl.style.display = '';
      } else { nextCtaEl.style.display = 'none'; }
    }
  }

  function onKey(e) {
    if (!isOpen) return;
    var tag = e.target && e.target.tagName;
    if (tag && /^(INPUT|TEXTAREA|SELECT)$/i.test(tag)) return;
    var k = e.key;
    if (k === ' ' || k === 'Spacebar') { e.preventDefault(); togglePlay(); }
    else if (k === 'ArrowRight') { e.preventDefault(); pause(); stepForward(true); }
    else if (k === 'ArrowLeft')  { e.preventDefault(); stepBack(); }
    else if (k === 'r' || k === 'R') { e.preventDefault(); restart(); }
    else if (k === '[') { e.preventDefault(); prevScene(); }
    else if (k === ']') { e.preventDefault(); nextScene(); }
    else if (k === 'Escape') { e.preventDefault(); close(); }
  }

  O.ViewStoryProcurement = {
    mountLauncher: mountLauncher, open: open, close: close,
    _probe: function () { return { open: isOpen, scene: sceneIdx, step: stepIdx, playing: playing }; }
  };
})();
