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

  // guided-authoring presentation meta (PLAN-0040 C2): each H-field's TYPE + legal domain
  // + where to source it — never a VALUE (so it never crosses D4). An `options` key pulls
  // the LEGAL set from data.governance_options (the allowlist a human picks from, not a
  // recommendation): the dropdown answers "what is legal here", the human still authors.
  const FIELD_GUIDE = {
    threshold: { type: 'float', source: 'read it off the asset’s operating spec — the safe-operating band' },
    direction: { type: 'enum', options: 'direction' },
    watch_margin: { type: 'float', source: 'optional — blank skips the early-warning watch' },
    handler: { type: 'enum', options: 'handler', source: 'a registered handler in the allowlist' },
    autonomy: { type: 'enum', options: 'autonomy', source: 'confirm the safe default (gated)' },
    tiers: { type: 'text', source: 'optional — canonical / acceptable / forbidden' },
    env_var: { type: 'text', source: 'the env var carrying the band' }
  };
  function govOptions(key) {
    return (data && data.governance_options && data.governance_options[key]) || [];
  }
  // the archetype oracle's expectation for a step (derived from kind + gate_kind, the
  // template's signature) — the "must be a band" affordance (D4/D8).
  function oracleExpectation(kind, gateKind) {
    if (kind === 'evaluate' && gateKind === 'in_file_band') return 'must be an in_file band — author threshold + direction';
    if (kind === 'evaluate' && gateKind === 'env_band') return 'must be an env band — author the env var';
    if (kind === 'evaluate') return 'must be a band — never none';
    if (kind === 'action') return 'no gate · author a registered handler + confirm autonomy';
    return 'no gate expected';
  }

  /* ---- shell ---- */
  function build() {
    root = h('div', { class: 'view-inner procview' });
    const editing = state.mode === 'edit';
    root.appendChild(h('div', { class: 'view-head' }, [
      h('div', null, [
        h('div', { class: 'eyebrow', style: { marginBottom: '4px' } }, editing ? 'View F · Authoring gate' : 'View F · Procedures'),
        h('h1', null, editing ? 'Author a generated procedure draft' : 'How a governed procedure decomposes')
      ]),
      h('div', { class: 'flex' }),
      modeToggle(),
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

  // read ↔ authoring-gate toggle (PLAN-0040 C1). Edit-mode renders the offline
  // generated draft (gate-fixture.js); read-mode fetches the live shipped procedures.
  function modeToggle() {
    const tab = (mode, label) => h('button', {
      class: 'pv-modetab' + (state.mode === mode ? ' active' : ''),
      onClick: () => { if (state.mode !== mode) mount(root.parentElement, { mode: mode }); }
    }, label);
    return h('div', { class: 'pv-modetoggle' }, [tab('read', 'Shipped'), tab('edit', 'Authoring gate')]);
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

    // ---- gate status (edit-mode): a LIVE mirror of validate_governance_complete — how many
    // required gates are still unauthored (the "don't pass too easily" affordance, C3) ----
    if (state.mode === 'edit') card.appendChild(h('div', { class: 'pv-gate-status' }));

    // ---- goal + agent (the governance context) ----
    // edit-mode: the goal is the runtime LLM directive — a leak-class-3 G-field the human
    // authors behind an ELEVATED-scrutiny affordance (OQ-B B2: generated empty, not drafted).
    if (state.mode === 'edit') {
      card.appendChild(h('div', { class: 'pv-goal-edit' }, [
        h('div', { class: 'pv-goal-head' }, [
          icon('anomaly', { width: 14, height: 14 }),
          h('span', null, 'procedure goal — elevated scrutiny · runtime directive')
        ]),
        h('input', {
          class: 'pv-edit is-stub pv-goal-input',
          placeholder: 'author the runtime directive — describe intent, not thresholds or amounts',
          value: proc.goal || '',
          'aria-label': 'procedure goal'
        }),
        h('div', { class: 'pv-fhint faint' }, 'the goal is the agent’s runtime instruction — a human authors it (governed ≠ generated)')
      ]));
    } else if (proc.goal) {
      card.appendChild(h('p', { class: 'pv-goal muted' }, proc.goal));
    }
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
    // wire the live completion gate (C3): recompute the banner + clear a stub's "unfilled"
    // styling as each required gate is authored.
    if (state.mode === 'edit') wireGateStatus(card);
    return card;
  }

  // the LIVE completion gate (PLAN-0040 C3): mirrors validate_governance_complete in the
  // browser — counts the unauthored REQUIRED stubs (the gates that block the run), updates
  // the banner, and clears a stub's dashed "unfilled" styling the moment it is authored.
  // Review-only: no write-back, no submit endpoint (LOCKED-10) — it shows the verdict, it
  // does not act on it. `required` = the surfaced stubs (threshold/direction/handler); the
  // autonomy confirm defaults to gated and never blocks, mirroring unfilled_governance.
  function wireGateStatus(card) {
    const required = Array.from(card.querySelectorAll('.pv-edit[data-required]'));
    const banner = card.querySelector('.pv-gate-status');
    if (!banner) return;
    const filled = (el) => String(el.value || '').trim() !== '';
    function update() {
      required.forEach((el) => el.classList.toggle('is-filled', filled(el)));
      const done = required.filter(filled).length;
      const total = required.length;
      const ok = done === total;
      banner.className = 'pv-gate-status ' + (ok ? 'is-ok' : 'is-pending');
      clear(banner);
      banner.appendChild(icon(ok ? 'check' : 'anomaly', { width: 14, height: 14 }));
      banner.appendChild(h('span', null, ok
        ? 'all ' + total + ' required gates authored — this draft would pass validate_governance_complete (review-only · no write-back)'
        : done + ' of ' + total + ' required gates authored — ' + (total - done) + ' still unauthored; this draft would fail validate_governance_complete'));
    }
    required.forEach((el) => { el.addEventListener('input', update); el.addEventListener('change', update); });
    update();
  }

  function renderStep(model, n, opts) {
    const mode = (opts && opts.mode) || 'read';
    const step = h('div', { class: 'pv-step' + (mode === 'edit' ? ' pv-step-edit' : '') });
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
    // edit-mode: the SAME facetModel, regrouped into the three authoring zones (C2/AC-C2).
    if (mode === 'edit') { step.appendChild(renderZones(model)); return step; }

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

  // the THREE zones (PLAN-0040 C2 / AC-C2 / LOCKED-8): one facetModel, regrouped — NOT a
  // second renderer. The same fields, bucketed: LLM-drafted (advisory prose) · YOU must
  // author (the editable H-fields, guided) · archetype expectation (the oracle).
  function renderZones(model) {
    const all = [];
    model.facets.forEach((fc) => fc.fields.forEach((fl) => all.push(fl)));
    const llm = all.filter((f) => f.provenance === PROSE || f.provenance === LLM);
    const author = all.filter((f) => f.editable);
    const dc = model.facets.find((fc) => fc.key === 'decision_condition');
    const gk = dc && dc.fields.find((f) => f.label === 'gate_kind');
    const gateKind = gk ? gk.value : 'none';

    const llmBody = [];
    if (model.description) llmBody.push(h('p', { class: 'pv-zbody' }, model.description));
    llm.forEach((f) => llmBody.push(h('div', { class: 'pv-znote' }, [
      h('span', { class: 'pv-flabel mono' }, f.label),
      h('span', { class: 'pv-fval ' + provClass(f.provenance) }, String(f.value))
    ])));
    if (!llmBody.length) llmBody.push(h('span', { class: 'pv-empty faint' }, '—'));

    const authBody = author.length
      ? author.map((f) => renderAuthorField(f))
      : [h('div', { class: 'pv-noauth' }, [icon('check', { width: 13, height: 13 }), 'no governance required'])];

    const oracleBody = [
      h('div', { class: 'pv-orow mono' }, 'kind: ' + model.kind),
      h('div', { class: 'pv-orow mono' }, 'gate_kind: ' + gateKind),
      h('div', { class: 'pv-oexp' }, oracleExpectation(model.kind, gateKind))
    ];

    return h('div', { class: 'pv-zones' }, [
      zone('zone-llm', 'LLM-drafted · advisory', llmBody),
      zone('zone-author', 'YOU must author', authBody),
      zone('zone-oracle', 'archetype expectation', oracleBody)
    ]);
  }
  function zone(cls, label, body) {
    return h('div', { class: 'pv-zone ' + cls }, [h('div', { class: 'pv-zone-label mono' }, label)].concat(body));
  }

  // one H-field in the author zone: a GUIDED control (a select of the legal domain from
  // governance_options, or a typed input) + a type/source hint + (for a stub) the reason.
  // NEVER a pre-filled value into a stub — guided authoring that does not cross D4.
  function renderAuthorField(fld) {
    const guide = FIELD_GUIDE[fld.label] || {};
    let control;
    if (guide.options) {
      const opts = govOptions(guide.options);
      control = h('select', { class: 'pv-edit' + (fld.stub ? ' is-stub' : ''), 'aria-label': fld.label, 'data-required': fld.stub ? '1' : null },
        (fld.stub ? [h('option', { value: '' }, 'choose…')] : []).concat(
          opts.map((o) => h('option', { value: o, selected: !fld.stub && String(fld.value) === o }, o))
        ));
    } else {
      control = fld.stub
        ? h('input', { class: 'pv-edit is-stub', placeholder: 'author required', value: '', 'aria-label': fld.label, 'data-required': '1' })
        : h('input', { class: 'pv-edit', value: String(fld.value), 'aria-label': fld.label });
    }
    const rows = [
      h('div', { class: 'pv-afield-head' }, [
        h('span', { class: 'pv-flabel mono' }, fld.label),
        guide.type ? h('span', { class: 'pv-ftype mono faint' }, guide.type) : null
      ]),
      control
    ];
    if (guide.source) rows.push(h('div', { class: 'pv-fhint faint' }, guide.source));
    if (fld.reason) rows.push(h('div', { class: 'pv-freason faint' }, fld.reason));
    return h('div', { class: 'pv-afield' }, rows);
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

  // edit-mode (PLAN-0040 C1): render the recorded generated draft from gate-fixture.js
  // — OFFLINE, no fetch (OQ-D D1). Deep-clone so authoring edits never mutate the source.
  function mountEdit() {
    data = O.GateFixture ? JSON.parse(JSON.stringify(O.GateFixture)) : null;
    if (!data || !Array.isArray(data.verticals) || !data.verticals.length) {
      clear(bodyEl);
      bodyEl.appendChild(O.errorState(
        'No draft to author',
        'the edit-mode gate fixture (gate-fixture.js) is unavailable.', null
      ));
      return;
    }
    initSelection();
    render();
  }

  // exposed: `mount` (read by app.js). `facetModel` is exported so PLAN-0040's
  // edit-mode can reuse the exact decomposition (the AC-7 seam contract).
  window.OCT.ViewProcedures = { mount, facetModel };
})();
