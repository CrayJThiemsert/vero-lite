/* ============================================================
   OCT — Month-end KPI view (the export cover, rendered).

   PLAN-0096 Step 8 shipped the month-end export as two routes and NO UI:
   the KPI an operator's pilot charter is bound to was a JSON endpoint you
   had to type a URL to see. ADR-0032 D1.4 wants that number showable in a
   30-45 minute room. This view is that, and only that.

   DELIBERATELY NOT A DOWNLOAD BUTTON. Cray declined a UI button (and a CLI)
   for the CSV at s192 — see services/api/routers/exports.py. That decision
   stands: this view reads GET .../{year}/{month}/cover and renders it. It
   never touches the .csv route. The file stays something you fetch, and the
   number becomes something you can look at; they are different asks and
   only the second one was open.

   DIRECT fetch, NO mock fallback — the same call the read-only procedure
   viewer and the hero views make, for the same reason: a mocked cover would
   drift from the shipped reader and would put invented governance numbers on
   a screen someone is about to believe. Offline, this view says so.
   ============================================================ */
(function () {
  'use strict';
  const O = window.OCT;
  const { h, clear, icon } = O;

  /* The fields this view READS off the cover payload, as machine-readable data.
     tests/api/test_export_cover_ui_contract.py asserts set equality against
     ExportCoverResponse / ExportExceptionResponse, so renaming a field on
     either side turns CI red instead of silently blanking a tile. Same
     delimiter idiom as trace-kinds.js — the browser and the test read the SAME
     literal through these markers. Keep them. */
  const COVER_CONTRACT =
  /* EXPORT_COVER_FIELDS_JSON_BEGIN */
  {
    "cover": [
      "year", "month", "row_count", "traceable_row_count", "traceability_pct",
      "audit_answer_pct", "ungoverned_row_count", "ungoverned_thb", "total_thb",
      "outstanding_ratification_count", "exceptions"
    ],
    "exception": [
      "case_id", "repair_order_no", "state", "approver", "total_thb",
      "justification_ref", "run_id"
    ]
  }
  /* EXPORT_COVER_FIELDS_JSON_END */
  ;

  const MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  /* ---- formatting ----
     Every one of these returns an honest EMPTY string for null rather than a
     zero. A month nobody spent in has no traceability to report, and the
     reader must be able to tell that apart from a month that scored 0%. */
  function thb(value) {
    if (value === null || value === undefined) return '—';
    const n = Number(value);
    return '฿' + (Number.isFinite(n) ? n.toLocaleString('en-US') : String(value));
  }
  function pct(value) {
    if (value === null || value === undefined) return '—';
    const n = Number(value);
    return Number.isFinite(n) ? n.toFixed(1) + '%' : String(value);
  }
  function count(value) {
    const n = Number(value);
    return Number.isFinite(n) ? n.toLocaleString('en-US') : String(value);
  }

  /* The KPI's colour is a READING of the number, not decoration: this is the
     figure a pilot charter is bound to, so a bad month must not look calm. */
  function kpiClass(value) {
    if (value === null || value === undefined) return 's-neutral';
    const n = Number(value);
    if (!Number.isFinite(n)) return 's-neutral';
    if (n >= 95) return 's-ok';
    if (n >= 80) return 's-warn';
    return 's-crit';
  }

  /* ---- DOM helpers (the hero-* tile idiom, already themed + responsive) ---- */
  function tile(label, value, cls, sub) {
    const kids = [
      h('div', { class: 'hero-kpi-label' }, label),
      h('div', { class: 'hero-kpi-value ' + (cls || '') }, value)
    ];
    if (sub) kids.push(h('div', { class: 'hero-kpi-sub faint' }, sub));
    return h('div', { class: 'hero-kpi-tile' }, kids);
  }
  function kv(label, value, cls) {
    return h('div', { class: 'hero-kv' }, [
      h('span', { class: 'hero-k mono' }, label),
      h('span', { class: 'hero-v ' + (cls || '') }, value)
    ]);
  }
  function card(title, sub, body) {
    return h('div', { class: 'hero-card' }, [
      h('div', { class: 'hero-card-head' }, [
        h('div', { class: 'hero-card-title' }, title),
        sub ? h('div', { class: 'hero-card-sub faint' }, sub) : null
      ].filter(Boolean)),
      h('div', { class: 'hero-card-body' }, body)
    ]);
  }

  /* ---- the panels ---- */

  // A month with no rows renders THIS instead of four ฿0 tiles.
  //
  // 🔴 Four zeroes is not a neutral display, it is a misleading one: "Repair spend
  // fully traceable 0%" and "Spend that escaped governance ฿0" read as findings about
  // a fleet, when the truth is that nothing has been filed yet. The KPI's own reader
  // already refuses to score an empty month — `traceability_pct` returns None rather
  // than 100.0, with the comment that reporting a perfect score for a month nobody
  // looked at would put the best number the KPI can produce on the worst-observed
  // months. This is that same honesty carried to the surface a human actually reads.
  //
  // Reads only `row_count`, which the cover already declares — the UI-contract test
  // asserts set equality over the fields this view touches, so a new field here would
  // have to ship with its own response change.
  function renderEmptyMonth() {
    return card(
      'No repair spend filed to this month — yet',
      'this is the honest state of an empty month, not a score of zero',
      [
        h('div', null,
          'ยังไม่มีใบแจ้งซ่อมที่ผ่านการอนุมัติและคีย์ใบกำกับในเดือนนี้ ' +
          'ตัวเลขจะปรากฏเมื่อมีการอนุมัติและบันทึกใบกำกับภาษี'),
        h('div', { class: 'faint' },
          'A repair reaches this report when it has been approved through a governed ' +
          'run. Its ฿ column fills when the invoice is keyed against it — approval and ' +
          'invoice are separate events, so a repair can sit here authorised with the ' +
          'money column still blank.'),
        h('div', { class: 'faint' },
          'The percentage is deliberately left unscored rather than shown as 0% or ' +
          '100%: a month with no spend has no traceability to report.')
      ]
    );
  }

  function renderKpis(cover) {
    const traceable = cover.traceability_pct;
    const empty = traceable === null || traceable === undefined;
    return h('div', { class: 'hero-grid' }, [
      tile(
        'Repair spend fully traceable',
        pct(traceable),
        kpiClass(traceable),
        empty
          ? 'no spend filed to this month — not 100%'
          : count(cover.traceable_row_count) + ' of ' + count(cover.row_count) +
            ' rows: governed AND fully documented'
      ),
      tile(
        'Audit questions answerable',
        pct(cover.audit_answer_pct),
        's-info',
        'the companion proxy — moves where the all-or-nothing KPI cannot'
      ),
      tile(
        'Spend that escaped governance',
        thb(cover.ungoverned_thb),
        Number(cover.ungoverned_row_count) > 0 ? 's-crit' : 's-ok',
        count(cover.ungoverned_row_count) + ' row(s) never passed a governed run'
      ),
      tile(
        'Total repair spend',
        thb(cover.total_thb),
        's-neutral',
        count(cover.row_count) + ' Express entries filed to this month'
      )
    ]);
  }

  function renderBreakdown(cover) {
    const outstanding = Number(cover.outstanding_ratification_count);
    return card(
      'What the number is made of',
      'the same reader the CSV is built from, so the cover and the file cannot disagree about the rule',
      [
        kv('Express entries (rows)', count(cover.row_count)),
        kv('Fully traceable', count(cover.traceable_row_count), 's-ok'),
        kv('Ungoverned rows', count(cover.ungoverned_row_count),
          Number(cover.ungoverned_row_count) > 0 ? 's-crit' : ''),
        kv('Ungoverned spend', thb(cover.ungoverned_thb),
          Number(cover.ungoverned_row_count) > 0 ? 's-crit' : ''),
        kv('Awaiting a signature', count(cover.outstanding_ratification_count),
          outstanding > 0 ? 's-warn' : ''),
        kv('Total spend', thb(cover.total_thb))
      ]
    );
  }

  function renderExceptions(cover) {
    const rows = cover.exceptions || [];
    if (!rows.length) {
      return card(
        'Emergency-path repairs (E-2)',
        'bounded by construction — a waiver-invoked approval is the rare path',
        [h('div', { class: 'faint' }, 'None this month.')]
      );
    }
    // The callback parameter is named `exc`, not `r`: the UI-contract test scans
    // `exc.<name>` property accesses and asserts every one is a field the response
    // actually declares. A one-letter name would collide with any other `r` in the
    // file and make that scan unreliable.
    const body = rows.map(function (exc) {
      const head = h('div', { class: 'hero-kv' }, [
        h('span', { class: 'hero-k mono' }, exc.repair_order_no || exc.case_id),
        h('span', { class: 'hero-v ' + O.Onto.statusClass(exc.state) }, exc.state)
      ]);
      const detail = h('div', { class: 'hero-kpi-sub faint' }, [
        (exc.approver ? 'approved by ' + exc.approver : 'authorisation WITHDRAWN'),
        ' · ', thb(exc.total_thb),
        exc.justification_ref
          ? ' · reason ' + String(exc.justification_ref).slice(0, 12) + '…' : '',
        exc.run_id ? ' · run ' + String(exc.run_id).slice(0, 8) : ''
      ].join(''));
      return h('div', null, [head, detail]);
    });
    return card(
      'Emergency-path repairs (E-2)',
      rows.length + ' this month — a month where this list is long is a month somebody should be asked about',
      body
    );
  }

  function render(body, cover, host, year, month) {
    clear(body);

    const title = h('div', { class: 'hero-head' }, [
      h('div', { class: 'hero-title' },
        'Month-end repair spend — ' + MONTH_NAMES[month - 1] + ' ' + year)
    ]);
    // SIBLING of .hero-head, not a child: .hero-head is a flex row, so a child
    // would sit beside the title rather than under it.
    const subtitle = h('div', { class: 'hero-sub' },
      'The KPI a pilot charter is bound to: % of repair spend fully traceable — ' +
      'who approved it, who it was bought from, and why. Month bounded in Asia/Bangkok. ' +
      'ALL FIGURES PROVISIONAL.');

    // Month nav. Not a download control — this view never touches the .csv
    // route (s192). Without it the panel could only ever show one month, and an
    // empty month would make it useless in the room it exists for.
    const nav = h('div', { class: 'hero-kv' }, [
      h('button', {
        class: 'iconbtn',
        onClick: function () { mount(host, shift(year, month, -1)); }
      }, '‹ previous month'),
      h('button', {
        class: 'iconbtn',
        onClick: function () { mount(host, shift(year, month, 1)); }
      }, 'next month ›')
    ]);

    body.appendChild(title);
    body.appendChild(subtitle);
    body.appendChild(nav);
    if (Number(cover.row_count) === 0) {
      // The empty month replaces the KPI grid rather than sitting above it: leaving
      // four ฿0 tiles on screen beside an explanation of why they are meaningless
      // would still let a reader take the numbers at face value.
      body.appendChild(renderEmptyMonth());
    } else {
      body.appendChild(renderKpis(cover));
      body.appendChild(renderBreakdown(cover));
    }
    body.appendChild(renderExceptions(cover));
  }

  function shift(year, month, delta) {
    const m = month + delta;
    if (m < 1) return { year: year - 1, month: 12 };
    if (m > 12) return { year: year + 1, month: 1 };
    return { year: year, month: m };
  }

  /* The month the SERVER would pick if asked today, derived the same way the
     reader does: Asia/Bangkok, not the browser's zone. A viewer in another
     timezone must not see a different default month than the export produces. */
  function currentBangkokMonth() {
    const parts = new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Asia/Bangkok', year: 'numeric', month: '2-digit'
    }).format(new Date()).split('-');
    return { year: Number(parts[0]), month: Number(parts[1]) };
  }

  async function mount(container, opts) {
    const at = (opts && opts.year) ? opts : currentBangkokMonth();
    clear(container);
    const body = h('div', { class: 'hero-view' });
    container.appendChild(body);
    body.appendChild(O.loadingState
      ? O.loadingState('Loading the month-end cover…')
      : h('div', null, 'Loading…'));
    try {
      const cover = await O.Exports.cover(at.year, at.month);
      render(body, cover, container, at.year, at.month);
    } catch (e) {
      clear(body);
      const msg = String((e && e.message) || e) +
        ' — the export cover (/api/exports/repair-spend/…) requires the live backend ' +
        'and a database (no embedded demo: an invented KPI is worse than none).';
      body.appendChild(O.errorState
        ? O.errorState('Could not load the month-end cover', msg,
            function () { mount(container, at); })
        : h('div', { class: 'hero-err' }, msg));
    }
  }

  window.OCT.ViewExport = { mount, COVER_CONTRACT, currentBangkokMonth, shift };
})();
