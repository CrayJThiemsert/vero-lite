/* ============================================================
   OCT — View H: Monitor (PLAN-0052 read-only + PLAN-0054 Control-leg operate).

   A monitor over the persisted PipelineRun / StepResult records: a runs LIST
   + a live run-DETAIL view (poll). The ``waiting_human`` gate + its proposals
   render behind a ``mode: 'read' | 'operate'`` seam. mode is now DERIVED from
   the operate auth-module (window.OCT.Auth): logged out = 'read' (read-only,
   the PLAN-0052 behaviour); logged in = 'operate' — approve/reject each
   proposal + submit (POST /runs/{id}/gate/resolve) and cancel a waiting_human
   run (POST /runs/{id}/cancel), with SoD + a tamper-evident audit actor
   enforced server-side (PLAN-0054, ADR-016 S2 RF-1).

   DIRECT fetch, NO mock fallback: an honest errorState offline is correct — a
   mocked copy would drift from the live persisted runs. Operate POSTs bypass
   api.js request() deliberately (its mock fallback would fake a governed write).
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
    mode: 'read',        // 'read' | 'operate' — DERIVED from Auth.isLoggedIn() (syncMode).
    selected: null,
    listData: null,
    detailData: null,
    listTimer: null,
    detailTimer: null,
    listBusy: false,
    detailBusy: false,
    decisions: {},       // {action_id: 'approve'|'reject'} — operate; reset per selected run.
    operateMsg: null,    // {kind, text, runId, retry?} — the operate status line, stamped w/ its run.
    operateBusy: false,  // disables operate controls during a submit/cancel POST.
    els: null            // { root, authbar, list, detail }
  };

  function syncMode() {
    state.mode = (O.Auth && O.Auth.isLoggedIn()) ? 'operate' : 'read';
  }

  // The operate message belongs to ONE run (the one it was raised on). Render it only
  // while that run is the open detail — so a poll / re-select never shows a stale banner
  // under a different run or above a fresh gate the operator has moved on to.
  function currentMsg() {
    const m = state.operateMsg, run = state.detailData;
    return (m && run && m.runId === run.run_id) ? m : null;
  }

  function statusBadge(status) {
    const cls = RUN_STATUS_CLASS[status] || 's-neutral';
    return h('span', {
      class: 'badge ' + cls, 'data-testid': 'run-status',
      title: status === 'waiting_human' ? 'Waiting on a human decision' : status
    }, [h('span', { class: 'led' }), status]);
  }

  /* ---- direct fetch, no mock (reads — header-less) ---- */
  async function getJSON(path) {
    const res = await fetch(path);
    const ct = res.headers.get('content-type') || '';
    if (!res.ok || !ct.includes('json')) {
      throw new Error('GET ' + path + ' unavailable (' + res.status + ')');
    }
    return res.json();
  }

  /* ---- operate: POST with the Bearer auth header, NO mock fallback (a governed
     write must hit the real backend), surfacing the FastAPI error detail (a string
     for RF-1 / ProcedureError, or a {error, verdict} dict for a PrincipalSoDError) ---- */
  function detailText(detail) {
    if (detail == null) return '';
    if (typeof detail === 'string') return detail;
    if (typeof detail === 'object') return detail.error || JSON.stringify(detail);
    return String(detail);
  }
  async function postOperate(path, body) {
    const opts = { method: 'POST', headers: Object.assign({}, O.Auth.authHeader()) };
    if (body !== undefined) {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(path, opts);
    let data = null;
    try { data = await res.json(); } catch (e) { /* non-JSON / empty body */ }
    if (!res.ok) {
      const err = new Error(detailText(data && data.detail) || ('HTTP ' + res.status));
      err.status = res.status;
      err.detail = data ? data.detail : null;
      throw err;
    }
    return data;
  }
  function operateError(e) {
    if (e.status === 401) {
      return { kind: 'error', text: 'Session invalid — log in again with a valid operator key.' };
    }
    if (e.status === 403) {
      // The backend returns a STRING detail for RF-1 (no accountable human) and an
      // OBJECT detail ({error, verdict}) only for a PrincipalSoDError — so an object
      // detail IS the SoD case (robust even if the verdict fields are falsy).
      const d = e.detail;
      const isSoD = d && typeof d === 'object';
      return { kind: 'error', text: isSoD
        ? ('Separation-of-duties blocked this: ' + (detailText(d) || 'you may not approve this run.'))
        : ('Not authorized (403): ' + (detailText(d) || 'log in as an authorized approver.')) };
    }
    if (e.status === 409) {
      return { kind: 'error', retry: true,
        text: 'Conflict (409): ' + (e.message || 'the run changed under you — reload and retry.') };
    }
    return { kind: 'error', text: e.message || 'The operate request failed.' };
  }

  async function submitDecisions(run) {
    if (state.operateBusy) return;
    state.operateBusy = true; state.operateMsg = null; renderDetail();
    try {
      // Build the decisions body from the CURRENT proposals only — never the raw
      // state.decisions map, which could carry stale action_ids from a prior gate.
      const proposals = run.proposals || [];
      const decisions = {};
      proposals.forEach(p => { decisions[p.action_id] = state.decisions[p.action_id]; });
      await postOperate('/runs/' + encodeURIComponent(run.run_id) + '/gate/resolve',
        { step_id: run.suspended_step, decisions: decisions });
      state.decisions = {};
      state.operateMsg = { kind: 'ok', text: 'Decisions submitted — the run resumed.', runId: run.run_id };
      await loadDetail(false);   // re-render to the new run_status (may complete / suspend again)
    } catch (e) {
      const m = operateError(e); m.runId = run.run_id; state.operateMsg = m;
    } finally {
      state.operateBusy = false; renderDetail();
    }
  }
  async function cancelRun(run) {
    if (state.operateBusy) return;
    state.operateBusy = true; state.operateMsg = null; renderDetail();
    try {
      await postOperate('/runs/' + encodeURIComponent(run.run_id) + '/cancel');
      state.operateMsg = { kind: 'ok', text: 'Run cancelled.', runId: run.run_id };
      await loadDetail(false);   // re-render to cancelled
    } catch (e) {
      const m = operateError(e); m.runId = run.run_id; state.operateMsg = m;
    } finally {
      state.operateBusy = false; renderDetail();
    }
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
    state.decisions = {};        // a fresh gate starts with no decisions
    state.operateMsg = null;     // drop a prior run's operate message
    renderList();                // reflect the selection highlight
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

  /* ---- operate controls (PLAN-0054 Steps 2/4/5) ---- */
  function decisionBtn(p, kind) {
    const on = state.decisions[p.action_id] === kind;
    return h('button', {
      class: 'mon-dec ' + kind + (on ? ' on' : ''),
      'data-testid': 'decide-' + kind + '-' + p.action_id,
      'aria-pressed': on ? 'true' : 'false',
      disabled: state.operateBusy ? '' : null,
      // deciding clears a lingering resumed/error banner from the previous action
      onClick: () => { state.decisions[p.action_id] = kind; state.operateMsg = null; renderDetail(); }
    }, kind === 'approve' ? 'Approve' : 'Reject');
  }

  function operateMsgEl(m) {
    const kids = [m.text];
    if (m.retry) {
      kids.push(h('button', {
        class: 'btn sm ghost', style: { marginLeft: '8px' },
        onClick: () => { state.operateMsg = null; loadDetail(true); }
      }, 'Reload'));
    }
    return h('div', {
      class: 'mon-op-msg ' + (m.kind === 'ok' ? 'ok' : 'err'),
      role: 'status', 'aria-live': 'polite', 'data-testid': 'operate-msg'
    }, kids);
  }

  function proposalPanel(run) {
    const operate = state.mode === 'operate';
    const proposals = run.proposals || [];
    const rows = proposals.map(p => {
      const ops = operate
        ? h('span', { class: 'mon-prop-ops' }, [decisionBtn(p, 'approve'), decisionBtn(p, 'reject')])
        : h('span', {
            class: 'mon-prop-inert faint',
            title: 'Log in to operate — approve/reject wires POST /runs/{id}/gate/resolve here'
          }, 'awaiting human');
      return h('div', { class: 'mon-prop' }, [
        h('span', { class: 'mon-prop-title' }, p.title || p.action_id),
        p.suggested_handler ? h('span', { class: 'faint mono' }, p.suggested_handler) : null,
        ops
      ].filter(Boolean));
    });
    const kids = [
      h('div', { class: 'mon-gate-top' }, [
        icon('anomaly', { width: 15, height: 15 }),
        h('b', null, 'Waiting on a human'),
        run.suspended_step ? h('span', { class: 'faint mono' }, 'step "' + run.suspended_step + '"') : null
      ].filter(Boolean)),
      rows.length ? h('div', { class: 'mon-props' }, rows)
                  : h('div', { class: 'faint' }, 'No decidable proposals at this gate.')
    ];
    if (operate && rows.length) {
      // the resolve endpoint requires an explicit decision per proposal (no silent default)
      const allDecided = proposals.every(p => state.decisions[p.action_id]);
      kids.push(h('div', { class: 'mon-gate-actions' }, [
        h('button', {
          class: 'btn sm', 'data-testid': 'operate-submit',
          disabled: (!allDecided || state.operateBusy) ? '' : null,
          onClick: () => submitDecisions(run)
        }, state.operateBusy ? 'Submitting…' : 'Submit decisions'),
        allDecided ? null
                   : h('span', { class: 'faint', style: { fontSize: '11px' } },
                       'Decide every proposal to submit.')
      ].filter(Boolean)));
    }
    const msg = currentMsg();
    if (msg) kids.push(operateMsgEl(msg));
    return h('div', { class: 'mon-gate', 'data-testid': 'gate-panel' }, kids);
  }

  function stepApprover(s) {
    // The human who RESOLVED this gate — recorded by resolve_gated_step on the step's trace
    // (gate_principal_recorded), for BOTH the SoD gate (approve) and a plain gate (issue_po).
    // This is the SERVER-resolved person_id (from the API key), the accountable approver in the
    // audit — NOT the cosmetic typed identity.
    const rec = (s.reasoning_trace || []).find(
      e => e && e.kind === 'gate_principal_recorded' && e.principal_id);
    if (!rec) return null;
    const approved = (s.reasoning_trace || []).some(e => e && e.kind === 'action_executed');
    return { who: rec.principal_id, approved: approved };
  }

  function stepCard(s) {
    const appr = stepApprover(s);
    const kids = [
      h('div', { class: 'mon-step-top' }, [
        statusBadge(s.status),
        h('span', { class: 'mon-step-id mono' }, s.step_id),
        s.duration_ms != null ? h('span', { class: 'faint mono' }, s.duration_ms + ' ms') : null,
        appr ? h('span', {
          class: 'mon-approver ' + (appr.approved ? 'approved' : 'resolved'),
          'data-testid': 'step-approver',
          title: 'The human who resolved this gate — the server-resolved person_id (from the '
               + 'API key), the accountable approver recorded in the audit'
        }, [icon('check', { width: 12, height: 12 }),
            (appr.approved ? 'approved by ' : 'resolved by '), h('b', null, appr.who)]) : null
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
    if (!state.els || !run) return;
    const wrap = clear(state.els.detail);
    const head = [
      statusBadge(run.status),
      h('b', { class: 'mono' }, run.run_id),
      h('span', { class: 'faint' }, run.procedure_id + ' · ' + run.agent_id),
      h('span', { class: 'faint mono mon-detail-actor' },
        run.trigger + (run.triggered_by ? ' · ' + run.triggered_by : ''))
    ];
    // Cancel: operate-mode + waiting_human ONLY (SD-B — a parked run has no in-flight effect)
    if (state.mode === 'operate' && run.status === 'waiting_human') {
      head.push(h('button', {
        class: 'btn sm ghost mon-cancel', 'data-testid': 'operate-cancel',
        disabled: state.operateBusy ? '' : null, onClick: () => cancelRun(run)
      }, 'Cancel run'));
    }
    wrap.appendChild(h('div', { class: 'mon-detail-head' }, head));
    if (run.status === 'waiting_human') {
      wrap.appendChild(proposalPanel(run));   // proposalPanel renders the operate message inline
    } else {
      const msg = currentMsg();               // after a resolve/cancel the gate is gone — show it here
      if (msg) wrap.appendChild(operateMsgEl(msg));
    }
    const steps = h('div', { class: 'mon-steps' });
    (run.steps || []).forEach(s => steps.appendChild(stepCard(s)));
    wrap.appendChild(steps);
  }

  /* ---- operate auth bar (PLAN-0054 Step 3, SD-A): login form <-> logged-in banner ---- */
  function authBar() {
    const bar = h('div', { class: 'mon-authbar', 'data-testid': 'operate-auth' });
    if (O.Auth && O.Auth.isLoggedIn()) {
      bar.appendChild(h('span', { class: 'mon-auth-who', 'data-testid': 'operate-who' }, [
        icon('check', { width: 14, height: 14 }), 'Operating as ', h('b', null, O.Auth.identity())
      ]));
      bar.appendChild(h('button', {
        class: 'btn sm ghost', 'data-testid': 'operate-logout',
        onClick: () => { O.Auth.logout(); state.decisions = {}; state.operateMsg = null; afterAuth(); }
      }, 'Log out'));
      return bar;
    }
    if (!O.Auth) {
      bar.appendChild(h('span', { class: 'faint' }, 'Operate unavailable — auth module not loaded.'));
      return bar;
    }
    const keyIn = h('input', {
      class: 'mon-auth-in mono', type: 'password', autocomplete: 'off',
      placeholder: 'operator API key', 'data-testid': 'operate-key'
    });
    const idIn = h('input', {
      class: 'mon-auth-in', type: 'text', autocomplete: 'off',
      placeholder: 'your identity (e.g. appr-pm)', 'data-testid': 'operate-identity'
    });
    const err = h('span', { class: 'mon-auth-err', role: 'status', 'aria-live': 'polite',
      'data-testid': 'operate-login-err' });
    const doLogin = () => {
      try { O.Auth.login(keyIn.value, idIn.value); afterAuth(); }
      catch (e) { err.textContent = String(e.message || e); }
    };
    keyIn.addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); });
    idIn.addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); });
    bar.appendChild(h('span', { class: 'faint' }, 'Log in to operate:'));
    bar.appendChild(keyIn);
    bar.appendChild(idIn);
    bar.appendChild(h('button', { class: 'btn sm', 'data-testid': 'operate-login', onClick: doLogin }, 'Log in'));
    bar.appendChild(err);
    return bar;
  }

  function renderAuthBar() {
    if (!state.els || !state.els.authbar) return;
    clear(state.els.authbar).appendChild(authBar());
  }

  function afterAuth() {
    // login / logout flipped the credential — re-derive the mode + repaint both panes.
    syncMode();
    renderAuthBar();
    renderDetail();
  }

  /* ---- polling (S4: poll open detail ~3s, list ~10s) ---- */
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
      const d = state.detailData;
      // Only a live 'running' run changes on its own. A terminal run is done, and a
      // waiting_human gate does NOT advance without an operator action — polling it
      // would tear the gate (and any in-progress decision + focus) down every tick.
      if (d && TERMINAL[d.status]) { clearInterval(state.detailTimer); state.detailTimer = null; return; }
      if (!d || d.status === 'waiting_human' || state.operateBusy) return;
      if (active() && state.selected) loadDetail(false);
    }, DETAIL_POLL_MS);
  }

  /* ---- self-contained styles (injected once; uses the app's design tokens) ---- */
  const STYLE_ID = 'mon-styles';
  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const css = `
.mon { height: 100%; display: flex; flex-direction: column; min-height: 0; }
.mon-cols { flex: 1 1 auto; min-height: 0; display: grid;
  grid-template-columns: minmax(300px, 400px) 1fr; gap: 14px; }
.mon-list, .mon-detail { background: var(--bg-1); border: 1px solid var(--line); border-radius: var(--r-lg);
  padding: 12px; overflow-y: auto; min-height: 0; }
/* the .view container is fixed-height + overflow-hidden (app shell) — so each pane
   scrolls INTERNALLY on desktop; on a narrow screen the whole monitor scrolls instead. */
@media (max-width: 900px) {
  .mon { display: block; overflow-y: auto; }
  .mon-cols { grid-template-columns: 1fr; }
  .mon-list, .mon-detail { overflow-y: visible; min-height: auto; }
}
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
.mon-authbar-wrap { flex: 0 0 auto; margin-bottom: 12px; }
.mon-authbar { display: flex; align-items: center; flex-wrap: wrap; gap: 8px;
  background: var(--bg-1); border: 1px solid var(--line); border-radius: var(--r-md); padding: 8px 10px; }
.mon-auth-who { display: flex; align-items: center; gap: 6px; color: var(--ok); font-weight: 600; }
.mon-auth-in { background: var(--bg-2); border: 1px solid var(--line); border-radius: var(--r-sm);
  padding: 5px 8px; color: var(--tx-0); font: inherit; font-size: 12.5px; min-width: 150px; }
.mon-auth-in:focus { outline: none; border-color: var(--accent-line); }
.mon-auth-err { color: var(--crit); font-size: 11.5px; }
.mon-detail-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  padding-bottom: 10px; margin-bottom: 10px; border-bottom: 1px solid var(--line); }
.mon-detail-actor { margin-left: auto; }
.mon-cancel { margin-left: 6px; }
.mon-gate { background: var(--warn-bg); border: 1px solid var(--warn-line);
  border-radius: var(--r-md); padding: 10px; margin-bottom: 12px; }
.mon-gate-top { display: flex; align-items: center; gap: 8px; color: var(--warn); margin-bottom: 8px; }
.mon-props { display: flex; flex-direction: column; gap: 6px; }
.mon-prop { display: flex; align-items: center; gap: 8px; background: var(--bg-1);
  border: 1px solid var(--line); border-radius: var(--r-sm); padding: 6px 9px; }
.mon-prop-title { color: var(--tx-0); font-weight: 600; }
.mon-prop-inert { margin-left: auto; font-size: 11px; }
.mon-prop-ops { margin-left: auto; display: inline-flex; gap: 6px; }
.mon-dec { border: 1px solid var(--line); border-radius: var(--r-sm); padding: 3px 11px;
  background: var(--bg-2); color: var(--tx-1); font: inherit; font-size: 12px; cursor: pointer; }
.mon-dec:hover { border-color: var(--line-strong); }
.mon-dec.approve.on { border-color: var(--ok); color: var(--ok); background: var(--accent-soft); }
.mon-dec.reject.on { border-color: var(--crit); color: var(--crit); background: var(--warn-bg); }
.mon-dec[disabled] { opacity: .5; cursor: default; }
.mon-gate-actions { display: flex; align-items: center; gap: 10px; margin-top: 10px; }
.mon-op-msg { margin-top: 10px; padding: 8px 10px; border-radius: var(--r-sm); font-size: 12.5px; }
.mon-op-msg.ok { background: var(--accent-soft); border: 1px solid var(--accent-line); color: var(--tx-0); }
.mon-op-msg.err { background: var(--warn-bg); border: 1px solid var(--warn-line); color: var(--warn); }
.mon-steps { display: flex; flex-direction: column; gap: 8px; }
.mon-step { background: var(--bg-2); border: 1px solid var(--line); border-radius: var(--r-md); padding: 9px 10px; }
.mon-step-top { display: flex; align-items: center; gap: 8px; }
.mon-step-id { color: var(--tx-1); }
.mon-approver { margin-left: auto; display: inline-flex; align-items: center; gap: 4px;
  font-size: 11px; font-weight: 600; padding: 2px 9px; border-radius: 999px; }
.mon-approver.approved { color: var(--ok); background: var(--accent-soft); border: 1px solid var(--ok); }
.mon-approver.resolved { color: var(--tx-1); background: var(--bg-2); border: 1px solid var(--line); }
.mon-audit-wrap { margin-top: 6px; }
.btn.ghost { background: transparent; }
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
    syncMode();
    clear(container);
    const authbar = h('div', { class: 'mon-authbar-wrap' });
    const list = h('div', { class: 'mon-list' });
    const detail = h('div', { class: 'mon-detail' },
      h('div', { class: 'mon-detail-empty' }, 'Select a run to see its steps, trace and gate.'));
    const root = h('div', { class: 'mon', 'data-testid': 'monitor' }, [
      authbar,
      h('div', { class: 'mon-cols' }, [list, detail])
    ]);
    container.appendChild(root);
    state.els = { root, authbar, list, detail };

    renderAuthBar();
    clear(list).appendChild(O.loadingState('Loading runs…'));
    await loadList();
    if (state.selected) await loadDetail(true);
    startListPoll();
    if (state.selected) startDetailPoll();
  }

  window.OCT = window.OCT || {};
  window.OCT.ViewMonitor = { mount };
})();
