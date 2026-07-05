/* ============================================================
   OCT — View H: Monitor (PLAN-0052 Phase-3, v1 read-only).

   A read-only monitor over the already-persisted PipelineRun /
   StepResult records: a runs LIST + a live run-DETAIL view (poll).
   The ``waiting_human`` gate + its proposals are surfaced READ-ONLY
   (AC-7) behind a ``mode: 'read' | 'operate'`` seam — v1 renders
   'read'; a future Control increment flips 'operate' to wire the
   already-shipped POST /runs/{id}/gate/resolve endpoint (L4:
   extension, not rewrite; S5 config/act deferred).

   DIRECT fetch, NO mock fallback (mirrors view-procedures.js): an
   honest errorState offline is correct — a mocked copy would drift
   from the live persisted runs.
   ============================================================ */
(function () {
  'use strict';
  const O = window.OCT;
  const { h, clear, icon } = O;

  const DETAIL_POLL_MS = 3000;   // poll only the OPEN run detail (S4)
  const LIST_POLL_MS = 10000;    // the list refreshes on a slower cadence
  const TERMINAL = { completed: 1, failed: 1, cancelled: 1 };
  const RUN_STATUS_CLASS = {
    completed: 's-ok', running: 's-info', failed: 's-crit',
    cancelled: 's-neutral', waiting_human: 's-warn'  // amber = the actionable one
  };

  const state = {
    mode: 'read',        // 'read' | 'operate' — the Control seam; v1 is 'read' only.
    selected: null,
    listData: null,
    detailData: null,
    listTimer: null,
    detailTimer: null,
    listBusy: false,
    detailBusy: false,
    els: null            // { root, list, detail }
  };

  function statusBadge(status) {
    const cls = RUN_STATUS_CLASS[status] || 's-neutral';
    return h('span', {
      class: 'badge ' + cls, 'data-testid': 'run-status',
      title: status === 'waiting_human' ? 'Waiting on a human decision' : status
    }, [h('span', { class: 'led' }), status]);
  }

  /* ---- direct fetch, no mock ---- */
  async function getJSON(path) {
    const res = await fetch(path);
    const ct = res.headers.get('content-type') || '';
    if (!res.ok || !ct.includes('json')) {
      throw new Error('GET ' + path + ' unavailable (' + res.status + ')');
    }
    return res.json();
  }

  function active() {
    // Only fetch while the Monitor is the visible view and the tab is focused.
    return !!(state.els && state.els.root.closest('.view.active') && !document.hidden);
  }

  /* ---- LIST ---- */
  async function loadList() {
    if (state.listBusy) return;
    state.listBusy = true;
    try {
      state.listData = await getJSON('/runs');
      renderList();
    } catch (e) {
      if (!state.listData) {
        clear(state.els.list).appendChild(
          O.errorState('Monitor backend required', String(e.message || e), loadList));
      }
    } finally {
      state.listBusy = false;
    }
  }

  function runRow(r) {
    const prog = r.steps_total != null ? r.steps_recorded + '/' + r.steps_total
                                       : String(r.steps_recorded);
    return h('button', {
      class: 'mon-run' + (r.run_id === state.selected ? ' sel' : ''),
      role: 'listitem', 'data-testid': 'run-row-' + r.run_id,
      onClick: () => selectRun(r.run_id)
    }, [
      statusBadge(r.status),
      h('span', { class: 'mon-proc' }, r.procedure_id),
      h('span', { class: 'mon-agent faint' }, r.agent_id),
      h('span', { class: 'mon-trig faint mono' },
        r.trigger + (r.triggered_by ? ' · ' + r.triggered_by : '')),
      h('span', { class: 'mon-prog mono', title: r.steps_waiting ? r.steps_waiting + ' waiting' : 'steps' },
        prog + (r.steps_waiting ? ' · ' + r.steps_waiting + ' ⏸' : '')),
      h('span', { class: 'mon-time faint mono' }, O.fmtTimestamp(r.started_at))
    ]);
  }

  function renderList() {
    const d = state.listData;
    if (!d) return;
    const wrap = clear(state.els.list);
    const waiting = d.waiting_human_count || 0;
    wrap.appendChild(h('div', { class: 'mon-listhead' }, [
      h('h3', null, 'Pipeline runs'),
      h('span', {
        class: 'badge ' + (waiting ? 's-warn' : 's-neutral'), 'data-testid': 'waiting-count'
      }, [h('span', { class: 'led' }), waiting + ' waiting on you'])
    ]));
    if (!d.runs.length) {
      wrap.appendChild(h('div', { class: 'mon-empty', 'data-testid': 'runs-empty' },
        'No runs yet. Runs appear here as procedures execute.'));
      return;
    }
    const list = h('div', { class: 'mon-runs', role: 'list' });
    d.runs.forEach(r => list.appendChild(runRow(r)));
    wrap.appendChild(list);
  }

  /* ---- DETAIL ---- */
  async function selectRun(id) {
    state.selected = id;
    renderList();               // reflect the selection highlight
    await loadDetail(true);
    startDetailPoll();
  }

  async function loadDetail(showLoading) {
    if (!state.selected || state.detailBusy) return;
    state.detailBusy = true;
    if (showLoading) clear(state.els.detail).appendChild(O.loadingState('Loading run…'));
    try {
      state.detailData = await getJSON('/runs/' + encodeURIComponent(state.selected));
      renderDetail();
    } catch (e) {
      clear(state.els.detail).appendChild(
        O.errorState('Could not load run', String(e.message || e), () => loadDetail(true)));
    } finally {
      state.detailBusy = false;
    }
  }

  function proposalPanel(run) {
    // AC-7 + L4: the waiting_human gate + proposals, READ-ONLY. The operate
    // controls belong HERE — structurally present but INERT in v1 (mode==='read');
    // the Control increment sets mode='operate' and wires the resolve endpoint.
    const rows = (run.proposals || []).map(p => h('div', { class: 'mon-prop' }, [
      h('span', { class: 'mon-prop-title' }, p.title || p.action_id),
      p.suggested_handler ? h('span', { class: 'faint mono' }, p.suggested_handler) : null,
      state.mode === 'operate'
        ? h('span', { class: 'mon-prop-ops' })
        : h('span', {
            class: 'mon-prop-inert faint',
            title: 'Read-only in v1 — the Control leg wires POST /runs/{id}/gate/resolve here'
          }, 'awaiting human')
    ].filter(Boolean)));
    return h('div', { class: 'mon-gate', 'data-testid': 'gate-panel' }, [
      h('div', { class: 'mon-gate-top' }, [
        icon('anomaly', { width: 15, height: 15 }),
        h('b', null, 'Waiting on a human'),
        run.suspended_step ? h('span', { class: 'faint mono' }, 'step "' + run.suspended_step + '"') : null
      ].filter(Boolean)),
      rows.length ? h('div', { class: 'mon-props' }, rows)
                  : h('div', { class: 'faint' }, 'No decidable proposals at this gate.')
    ]);
  }

  function stepCard(s) {
    const kids = [
      h('div', { class: 'mon-step-top' }, [
        statusBadge(s.status),
        h('span', { class: 'mon-step-id mono' }, s.step_id),
        s.duration_ms != null ? h('span', { class: 'faint mono' }, s.duration_ms + ' ms') : null
      ].filter(Boolean))
    ];
    if (s.reasoning_trace && s.reasoning_trace.length) kids.push(O.reasoningTrace(s.reasoning_trace));
    if (s.audit && Object.keys(s.audit).length) {
      const box = h('div', { class: 'mon-audit' }, O.kvDump(s.audit));
      box.style.display = 'none';
      const toggle = h('button', {
        class: 'trace-toggle',
        onClick: () => {
          const open = box.style.display === 'none';
          box.style.display = open ? 'block' : 'none';
          toggle.textContent = open ? 'Hide audit' : 'Show audit';
        }
      }, 'Show audit');
      kids.push(h('div', { class: 'mon-audit-wrap' }, [toggle, box]));
    }
    return h('div', { class: 'mon-step', 'data-testid': 'step-row-' + s.step_id }, kids);
  }

  function renderDetail() {
    const run = state.detailData;
    if (!run) return;
    const wrap = clear(state.els.detail);
    wrap.appendChild(h('div', { class: 'mon-detail-head' }, [
      statusBadge(run.status),
      h('b', { class: 'mono' }, run.run_id),
      h('span', { class: 'faint' }, run.procedure_id + ' · ' + run.agent_id),
      h('span', { class: 'faint mono mon-detail-actor' },
        run.trigger + (run.triggered_by ? ' · ' + run.triggered_by : ''))
    ]));
    if (run.status === 'waiting_human') wrap.appendChild(proposalPanel(run));
    const steps = h('div', { class: 'mon-steps' });
    (run.steps || []).forEach(s => steps.appendChild(stepCard(s)));
    wrap.appendChild(steps);
  }

  /* ---- polling (S4: poll open detail ~3s, list ~10s; skip terminal/hidden/in-flight) ---- */
  function stopTimers() {
    if (state.listTimer) { clearInterval(state.listTimer); state.listTimer = null; }
    if (state.detailTimer) { clearInterval(state.detailTimer); state.detailTimer = null; }
  }
  function startListPoll() {
    if (state.listTimer) clearInterval(state.listTimer);
    state.listTimer = setInterval(() => { if (active()) loadList(); }, LIST_POLL_MS);
  }
  function startDetailPoll() {
    if (state.detailTimer) clearInterval(state.detailTimer);
    state.detailTimer = setInterval(() => {
      if (state.detailData && TERMINAL[state.detailData.status]) return;  // nothing more will change
      if (active() && state.selected) loadDetail(false);
    }, DETAIL_POLL_MS);
  }

  /* ---- self-contained styles (injected once; uses the app's design tokens) ---- */
  const STYLE_ID = 'mon-styles';
  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const css = `
.mon { height: 100%; }
.mon-cols { display: grid; grid-template-columns: minmax(300px, 400px) 1fr; gap: 14px; align-items: start; }
@media (max-width: 900px) { .mon-cols { grid-template-columns: 1fr; } }
.mon-list, .mon-detail { background: var(--bg-1); border: 1px solid var(--line); border-radius: var(--r-lg); padding: 12px; }
.mon-listhead { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.mon-listhead h3 { margin: 0; font-size: 14px; color: var(--tx-0); }
.mon-runs { display: flex; flex-direction: column; gap: 6px; }
.mon-run { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 8px; text-align: left;
  background: var(--bg-2); border: 1px solid var(--line); border-radius: var(--r-md);
  padding: 8px 10px; cursor: pointer; font: inherit; color: var(--tx-1); }
.mon-run:hover { background: var(--bg-3); border-color: var(--line-strong); }
.mon-run.sel { border-color: var(--accent-line); background: var(--accent-soft); }
.mon-run .mon-proc { color: var(--tx-0); font-weight: 600; flex: 1 1 auto; }
.mon-run .mon-agent, .mon-run .mon-trig, .mon-run .mon-prog, .mon-run .mon-time { font-size: 11.5px; }
.mon-run .mon-time { flex-basis: 100%; }
.mon-empty, .mon-detail-empty { color: var(--tx-2); padding: 24px 12px; text-align: center; }
.mon-detail-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  padding-bottom: 10px; margin-bottom: 10px; border-bottom: 1px solid var(--line); }
.mon-detail-actor { margin-left: auto; }
.mon-gate { background: var(--warn-bg); border: 1px solid var(--warn-line);
  border-radius: var(--r-md); padding: 10px; margin-bottom: 12px; }
.mon-gate-top { display: flex; align-items: center; gap: 8px; color: var(--warn); margin-bottom: 8px; }
.mon-props { display: flex; flex-direction: column; gap: 6px; }
.mon-prop { display: flex; align-items: center; gap: 8px; background: var(--bg-1);
  border: 1px solid var(--line); border-radius: var(--r-sm); padding: 6px 9px; }
.mon-prop-title { color: var(--tx-0); font-weight: 600; }
.mon-prop-inert { margin-left: auto; font-size: 11px; }
.mon-steps { display: flex; flex-direction: column; gap: 8px; }
.mon-step { background: var(--bg-2); border: 1px solid var(--line); border-radius: var(--r-md); padding: 9px 10px; }
.mon-step-top { display: flex; align-items: center; gap: 8px; }
.mon-step-id { color: var(--tx-1); }
.mon-audit-wrap { margin-top: 6px; }
`;
    const el = document.createElement('style');
    el.id = STYLE_ID;
    el.textContent = css;
    document.head.appendChild(el);
  }

  /* ---- mount ---- */
  async function mount(container) {
    injectStyles();
    stopTimers();  // re-mount (tab switch / global refresh) must never double-poll.
    clear(container);
    const list = h('div', { class: 'mon-list' });
    const detail = h('div', { class: 'mon-detail' },
      h('div', { class: 'mon-detail-empty' }, 'Select a run to see its steps, trace and gate.'));
    const root = h('div', { class: 'mon', 'data-testid': 'monitor' }, [
      h('div', { class: 'mon-cols' }, [list, detail])
    ]);
    container.appendChild(root);
    state.els = { root, list, detail };

    clear(list).appendChild(O.loadingState('Loading runs…'));
    await loadList();
    if (state.selected) await loadDetail(true);
    startListPoll();
    if (state.selected) startDetailPoll();
  }

  window.OCT = window.OCT || {};
  window.OCT.ViewMonitor = { mount };
})();
