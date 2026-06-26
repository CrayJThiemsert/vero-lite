/* ============================================================
   View F — Procedures  (read-only 5-facet procedure viewer)
   PLAN-0039 / ADR-0024 D8: the READ-mode of the one review surface.
   Every shipped procedure across all four verticals, each step
   decomposed by its five facets (input · decision_condition ·
   llm_assist · output · governance), with the typed authoritative
   band visually distinct from the non-authoritative prose.
   Zero-LLM, read-only: GET /procedures, no mutation, no model call.

   THE DE-RISK SEAM (AC-7): `facetModel(step)` is a PURE decomposition
   that tags every field with a provenance class + `editable: false`,
   and `mount`/`renderStep` are parameterized by `mode: 'read' | 'edit'`.
   v1 ships read-mode only (the edit branch is structurally present but
   inert); PLAN-0040 sets mode:'edit', flips `editable` on the H-class
   governance fields, and reuses `facetModel` UNCHANGED.
   ============================================================ */
(function () {
  'use strict';
  const O = window.OCT;
  const { h, clear, icon } = O;

  // provenance classes (OQ-4): every facet field is tagged one of these.
  const AUTH = 'authoritative-typed'; // the typed source of truth (ADR-016 D2-A2)
  const PROSE = 'advisory-prose'; // a non-authoritative facet note
  const LLM = 'llm-assist'; // what the LLM drafts/summarises (advisory)

  // the H partition (ADR-0024 D3): the human-author governance fields edit-mode makes
  // editable. Mirrors services/engine/procedures/draft.py STEP_GOVERNANCE_FIELDS — the
  // generator NEVER emits these; the gate is where a human authors them (PLAN-0040 C1).
  const H_FIELDS = new Set(['threshold', 'direction', 'watch_margin', 'handler', 'autonomy', 'tiers', 'env_var']);

  let data = null; // the GET /procedures payload: { verticals: [...] }
  const state = { vertical: null, procedureId: null, mode: 'read' };
  let root, navEl, subEl, bodyEl;

  /* ---- the load-bearing pure decomposition (AC-7 seam) -------------------
     Maps a Step -> the five-facet view-model. Each field carries its
     provenance class and an `editable` flag (always false in v1). PLAN-0040
     reuses this verbatim and flips `editable` on the governance H-class. */
  function facetModel(step, opts) {
    const f = step.facet || {};
    const dc = f.decision_condition || null;
    // `editable` is DERIVED from the field's H-class (PLAN-0040 finding #6a): a
    // governance H-field flips editable in edit-mode; everything else stays static.
    const field = (label, value, provenance) => ({ label, value, provenance, editable: H_FIELDS.has(label) });

    // input: the typed Step.input (from/where) is authoritative; facet.input is a prose note (finding #5)
    const input = [];
    if (step.input && step.input.from) input.push(field('from', step.input.from, AUTH));
    if (step.input && step.input.where) input.push(field('where', whereStr(step.input.where), AUTH));
    if (f.input) input.push(field('note', f.input, PROSE));

    // decision_condition: the typed gate_kind + the authored band are the source of truth; note is prose
    const decision = [];
    if (dc) {
      decision.push(field('gate_kind', dc.gate_kind, AUTH));
      if (dc.band_source) decision.push(field('band_source', dc.band_source, AUTH));
      if (dc.env_var) decision.push(field('env_var', dc.env_var, AUTH));
    }
    if (step.threshold != null) decision.push(field('threshold', step.threshold, AUTH));
    if (step.direction) decision.push(field('direction', step.direction, AUTH));
    if (step.watch_margin != null) decision.push(field('watch_margin', step.watch_margin, AUTH));
    if (dc && dc.note) decision.push(field('note', dc.note, PROSE));

    // llm_assist: advisory only — the net-new facet (D2-A2)
    const llm = [field('drafts', f.llm_assist != null ? f.llm_assist : '— (none)', LLM)];

    // output: the typed Step.output (produced artifact) is authoritative; facet.output is a prose note
    const output = [];
    if (step.output) output.push(field('produces', step.output, AUTH));
    if (f.output) output.push(field('note', f.output, PROSE));

    // governance: the typed handler/autonomy/tiers are the source of truth; facet.governance is a prose note
    const governance = [];
    if (step.handler) governance.push(field('handler', step.handler, AUTH));
    if (step.autonomy) governance.push(field('autonomy', step.autonomy, AUTH));
    if (step.tiers) governance.push(field('tiers', tiersStr(step.tiers), AUTH));
    if (f.governance) governance.push(field('note', f.governance, PROSE));

    const facets = [
      { key: 'input', label: 'input', fields: input },
      { key: 'decision_condition', label: 'decision', fields: decision },
      { key: 'llm_assist', label: 'llm assist', fields: llm },
      { key: 'output', label: 'output', fields: output },
      { key: 'governance', label: 'governance', fields: governance }
    ];
    // edit-mode: surface the unfilled governance STUBS the human must author
    // (finding #6b: facetModel emits only PRESENT fields, so an absent stub never
    // renders). The worklist is the procedure's governance_todo[step_id] (OQ-C/AC-A7),
    // passed in via opts — facetModel itself stays the load-bearing decomposition.
    if (opts && opts.mode === 'edit' && opts.todo) surfaceStubs(facets, step, opts.todo);
    return { step_id: step.step_id, name: step.name, description: step.description, kind: step.kind, facets: facets };
  }

  // which facet a governance H-field belongs to (mirrors view-procedures read layout)
  function facetForField(label) {
    return (label === 'handler' || label === 'autonomy' || label === 'tiers')
      ? 'governance' : 'decision_condition';
  }
  // whether the H-field already carries an authored value on the step (present ⇒ it is
  // already emitted as an editable field; only ABSENT obligations are surfaced as stubs)
  function isPresent(step, label) {
    if (label === 'env_var') {
      const dc = step.facet && step.facet.decision_condition;
      return !!(dc && dc.env_var != null);
    }
    return step[label] != null;
  }
  // append each unfilled governance obligation as a STUB field (value absent, editable,
  // carrying its reason + the oracle's archetype_expectation for the gate's zones, C2).
  function surfaceStubs(facets, step, todo) {
    todo.forEach((ob) => {
      if (isPresent(step, ob.field)) return;
      const target = facets.find((fc) => fc.key === facetForField(ob.field));
      if (!target) return;
      target.fields.push({
        label: ob.field, value: null, provenance: AUTH, editable: true,
        stub: true, reason: ob.reason, expectation: ob.archetype_expectation
      });
    });
  }

  /* ---- small formatters ---- */
  function whereStr(where) {
    return Object.keys(where).map((k) => k + '=' + where[k]).join(', ');
  }
  function tiersStr(t) {
    const parts = [];
    if (t.canonical) parts.push('canonical: ' + t.canonical);
    if (t.acceptable && t.acceptable.length) parts.push('acceptable: ' + t.acceptable.join('/'));
    if (t.forbidden && t.forbidden.length) parts.push('forbidden: ' + t.forbidden.join('/'));
    return parts.join('  ·  ');
  }
  function stepKindClass(kind) {
    return { query: 's-ok', evaluate: 's-info', action: 's-warn', human_task: 's-neutral' }[kind] || 's-neutral';
  }
  function provClass(p) {
    return p === AUTH ? 'pv-auth' : p === LLM ? 'pv-llm' : 'pv-prose';
  }

  /* ---- shell ---- */
  function build() {
    root = h('div', { class: 'view-inner procview' });
    root.appendChild(h('div', { class: 'view-head' }, [
      h('div', null, [
        h('div', { class: 'eyebrow', style: { marginBottom: '4px' } }, 'View F · Procedures'),
        h('h1', null, 'How a governed procedure decomposes')
      ]),
      h('div', { class: 'flex' }),
      legend(),
      h('button', { class: 'iconbtn', onClick: () => mount(root.parentElement, { mode: state.mode }) }, [icon('refresh'), 'Refresh'])
    ]));
    navEl = h('div', { class: 'pv-nav' });
    subEl = h('div', { class: 'pv-sub' });
    bodyEl = h('div', { class: 'pv-body scroll' });
    root.appendChild(navEl);
    root.appendChild(subEl);
    root.appendChild(bodyEl);
    return root;
  }

  // the ONE "authority vs advisory" affordance (AC-8): a legend explaining the
  // typed-vs-prose distinction the per-field styling encodes.
  function legend() {
    return h('div', { class: 'pv-legend' }, [
      h('span', { class: 'pv-leg pv-auth' }, [h('span', { class: 'pv-swatch' }), 'typed · source of truth']),
      h('span', { class: 'pv-leg pv-prose' }, [h('span', { class: 'pv-swatch' }), 'prose · advisory note']),
      h('span', { class: 'pv-leg pv-llm' }, [h('span', { class: 'pv-swatch' }), 'llm · drafted'])
    ]);
  }

  /* ---- selection ---- */
  function initSelection() {
    const names = data.verticals.map((v) => v.vertical);
    // default to the active OCT_VERTICAL when present (OQ-3), else the first vertical
    const active = O.State.meta && O.State.meta.vertical;
    state.vertical = names.indexOf(active) >= 0 ? active : names[0] || null;
    selectFirstProcedure();
  }
  function activeVertical() {
    return data.verticals.find((v) => v.vertical === state.vertical) || null;
  }
  function selectFirstProcedure() {
    const v = activeVertical();
    state.procedureId = v && v.procedures.length ? v.procedures[0].procedure_id : null;
  }

  /* ---- render ---- */
  function render() {
    renderNav();
    renderSub();
    renderBody();
  }

  function renderNav() {
    clear(navEl);
    data.verticals.forEach((v) => {
      const count = v.procedures.length;
      navEl.appendChild(h('button', {
        class: 'pv-chip' + (v.vertical === state.vertical ? ' active' : ''),
        onClick: () => { state.vertical = v.vertical; selectFirstProcedure(); render(); }
      }, [
        h('span', null, v.vertical),
        h('span', { class: 'pv-chip-n mono' }, String(count))
      ]));
    });
  }

  function renderSub() {
    clear(subEl);
    const v = activeVertical();
    if (!v) return;
    v.procedures.forEach((p) => {
      subEl.appendChild(h('button', {
        class: 'pv-proctab' + (p.procedure_id === state.procedureId ? ' active' : ''),
        onClick: () => { state.procedureId = p.procedure_id; renderSub(); renderBody(); }
      }, [
        h('span', { class: 'pv-arch-badge ' + archClass(p.archetype) }, p.archetype),
        h('span', null, p.title)
      ]));
    });
  }

  function archClass(a) {
    // AT-1 / AT-1b = the anomaly→action family (info); AT-2 = governance-heavy (warn); AT-3 = calm (ok)
    if (a === 'AT-2') return 's-warn';
    if (a === 'AT-3') return 's-ok';
    if (a === 'AT-1' || a === 'AT-1b') return 's-info';
    return 's-neutral';
  }

  function renderBody() {
    clear(bodyEl);
    const v = activeVertical();
    if (!v) { bodyEl.appendChild(O.errorState('No procedures', 'This vertical has no procedures.', null)); return; }
    const proc = v.procedures.find((p) => p.procedure_id === state.procedureId) || v.procedures[0];
    if (!proc) { bodyEl.appendChild(O.errorState('No procedure selected', '', null)); return; }
    bodyEl.appendChild(procedureCard(proc, v));
  }

  function procedureCard(proc, vEntry) {
    const agent = (vEntry.agents || []).find((a) => a.agent_id === proc.run_by) || null;
    const card = h('div', { class: 'card pv-proccard' });

    // ---- archetype header ----
    card.appendChild(h('div', { class: 'pv-proc-head' }, [
      h('span', { class: 'pv-arch-badge lg ' + archClass(proc.archetype) }, proc.archetype),
      h('div', null, [
        h('h2', { class: 'pv-proc-title' }, proc.title),
        h('div', { class: 'pv-proc-id mono faint' }, vEntry.vertical + ' · ' + proc.procedure_id)
      ]),
      h('div', { class: 'flex' }),
      h('span', { class: 'pv-trigger mono' }, [icon('play', { width: 12, height: 12 }), 'trigger: ' + (proc.trigger || 'manual')])
    ]));

    // ---- goal + agent (the governance context) ----
    if (proc.goal) card.appendChild(h('p', { class: 'pv-goal muted' }, proc.goal));
    if (agent) {
      card.appendChild(h('div', { class: 'pv-agent' }, [
        h('span', { class: 'eyebrow' }, 'Run by'),
        h('b', null, agent.name),
        h('span', { class: 'faint mono' }, agent.agent_id),
        h('span', { class: 'pv-agent-sep' }, '·'),
        h('span', { class: 'faint mono' }, 'model ' + (agent.llm_model || '—')),
        h('span', { class: 'pv-agent-sep' }, '·'),
        h('span', { class: 'faint mono' }, 'ceiling ' + (agent.autonomy_ceiling || '—'))
      ]));
    }

    // ---- the steps, each decomposed by its five facets ----
    const stepsWrap = h('div', { class: 'pv-steps' });
    // edit-mode threads the per-step governance_todo (OQ-C/AC-A7) into facetModel so
    // the unfilled stubs surface; read-mode passes no todo (renders present fields only).
    const todoMap = proc.governance_todo || {};
    (proc.steps || []).forEach((step, i) => stepsWrap.appendChild(
      renderStep(facetModel(step, { mode: state.mode, todo: todoMap[step.step_id] }), i + 1, { mode: state.mode })
    ));
    card.appendChild(stepsWrap);
    return card;
  }

  function renderStep(model, n, opts) {
    const mode = (opts && opts.mode) || 'read';
    const step = h('div', { class: 'pv-step' });
    step.appendChild(h('div', { class: 'pv-step-head' }, [
      h('span', { class: 'pv-step-n mono ' + stepKindClass(model.kind) }, String(n)),
      h('div', { class: 'pv-step-titles' }, [
        h('div', { class: 'pv-step-name' }, [
          h('span', null, model.name),
          h('span', { class: 'badge ' + stepKindClass(model.kind), style: { textTransform: 'none', marginLeft: '8px' } }, model.kind)
        ]),
        h('div', { class: 'pv-step-id mono faint' }, model.step_id)
      ])
    ]));
    if (model.description) step.appendChild(h('p', { class: 'pv-step-desc muted' }, model.description));

    const facets = h('div', { class: 'pv-facets' });
    model.facets.forEach((facet) => {
      facets.appendChild(h('div', { class: 'pv-facet' }, [
        h('div', { class: 'pv-facet-label mono' }, facet.label),
        h('div', { class: 'pv-facet-fields' },
          facet.fields.length
            ? facet.fields.map((fld) => renderField(fld, mode))
            : h('span', { class: 'pv-empty faint' }, '—'))
      ]));
    });
    step.appendChild(facets);
    return step;
  }

  function renderField(fld, mode) {
    // THE SEAM (AC-7 / PLAN-0040 C1): read-mode renders every field static; edit-mode
    // renders an authoring INPUT for the H-class governance fields (finding #6c: the
    // input was `disabled` in read-only v1 — un-disable it). A STUB (absent value)
    // renders an empty author-required control; guided controls (selects of the legal
    // domain) land in C2. No value is ever pre-filled into a stub (governed ≠ generated).
    let valEl;
    if (mode === 'edit' && fld.editable) {
      valEl = fld.stub
        ? h('input', { class: 'pv-edit is-stub', placeholder: 'author required', value: '' })
        : h('input', { class: 'pv-edit', value: String(fld.value) });
    } else {
      valEl = h('span', { class: 'pv-fval ' + provClass(fld.provenance) }, String(fld.value));
    }
    return h('div', { class: 'pv-field' }, [
      h('span', { class: 'pv-flabel mono' }, fld.label),
      valEl
    ]);
  }

  async function mount(container, opts) {
    opts = opts || {};
    state.mode = opts.mode || 'read';
    clear(container);
    container.appendChild(build());
    bodyEl.appendChild(O.loadingState(state.mode === 'edit' ? 'Loading the authoring gate…' : 'Loading procedures…'));
    // edit-mode renders a RECORDED generated draft OFFLINE (PLAN-0040 C1 / OQ-D D1):
    // no /procedures fetch, no backend dependency — the gate is exercisable offline.
    if (state.mode === 'edit') { mountEdit(); return; }
    try {
      // meta is only for the default-vertical pick (OQ-3); its failure is non-fatal
      if (!O.State.meta) await O.loadMeta().catch(() => {});
      data = await O.API.procedures();
      if (!data || !Array.isArray(data.verticals) || !data.verticals.length) {
        throw new Error('the /procedures endpoint returned no verticals');
      }
      initSelection();
      render();
    } catch (e) {
      clear(bodyEl);
      bodyEl.appendChild(O.errorState(
        'Could not load procedures',
        String(e.message || e) + ' — the read-only GET /procedures endpoint requires the live backend (no embedded demo for procedures).',
        () => mount(container, opts)
      ));
    }
  }

  // exposed: `mount` (read by app.js). `facetModel` is exported so PLAN-0040's
  // edit-mode can reuse the exact decomposition (the AC-7 seam contract).
  window.OCT.ViewProcedures = { mount, facetModel };
})();
