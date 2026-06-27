/* ============================================================
   intake-procedures.js — View F authoring intake (PLAN-0040 AC-B5 / LOCKED-9 / D9).

   The PLAN-0017 capture face reused for the procedure generator: a free-text
   narrative → MS-S1-local classify → the human CONFIRMS the proposed archetype →
   build the governed skeleton → hand it to the edit-mode gate (view-procedures.js)
   via the `onDraft` callback. The model never auto-confirms: the only path to a
   skeleton is the explicit Confirm click (LOCKED-5).

   GRACEFUL DEGRADATION (D9): MS-S1 cold / abstain / backend down → a clear
   non-silent state with a manual archetype-pick (instantiate = zero-LLM, works
   offline) or the recorded sample (gate-fixture.js). A silently-wrong skeleton is
   never produced.

   This module owns CAPTURE only. The gate RENDER stays in view-procedures.js
   (LOCKED-8: one review surface, no second renderer) — `onDraft(envelope)` re-mounts
   View F in edit-mode with the built draft.
   ============================================================ */
(function () {
  'use strict';
  const O = window.OCT;
  const { h, clear, icon } = O;

  // the v1 catalog (the AT-1 family) — a presentation fallback for the manual-pick
  // BEFORE a classify returns the live catalog; the server validates the pick and a
  // classify response refreshes this. Mirrors the closed REGISTRY (D7).
  const FALLBACK_CATALOG = [
    { archetype_id: 'AT-1', title: 'anomaly → action' },
    { archetype_id: 'AT-1b', title: 'anomaly → action + watch + summary' },
    { archetype_id: 'AT-3', title: 'monitor → reorder' }
  ];

  let container = null;
  let onDraft = function () {};
  let vertical = 'draft';
  let narrative = '';
  let catalog = FALLBACK_CATALOG;

  function mount(c, opts) {
    opts = opts || {};
    container = c;
    onDraft = opts.onDraft || function () {};
    if (opts.vertical) vertical = opts.vertical;
    showCapture(null);
  }

  /* ---- small builders ---- */
  function labelled(label, control, hint) {
    return h('label', { class: 'pv-cap-field' }, [
      h('span', { class: 'pv-cap-label eyebrow' }, label),
      control,
      hint ? h('span', { class: 'pv-cap-hint faint' }, hint) : null
    ]);
  }
  function verticalInput() {
    return h('input', {
      class: 'pv-cap-input mono', value: vertical, 'aria-label': 'target vertical',
      onInput: (e) => { vertical = e.target.value; }
    });
  }
  function narrativeInput() {
    return h('textarea', {
      class: 'pv-cap-textarea', rows: 5, 'aria-label': 'procedure narrative',
      placeholder: 'e.g. Watch each transformer’s temperature; when one runs above its safe '
        + 'band, restart it after a human signs off.',
      onInput: (e) => { narrative = e.target.value; }
    }, narrative);
  }
  function manualPick() {
    const sel = h('select', { class: 'pv-cap-input', 'aria-label': 'pick an archetype manually' },
      [h('option', { value: '' }, 'author manually — pick an archetype…')].concat(
        catalog.map((c) => h('option', { value: c.archetype_id }, c.archetype_id + ' · ' + c.title))
      ));
    sel.addEventListener('change', (e) => { if (e.target.value) doInstantiate(e.target.value); });
    return sel;
  }
  function archBadge(id) {
    const cls = id === 'AT-3' ? 's-ok' : (id === 'AT-2' ? 's-warn' : 's-info');
    return h('span', { class: 'pv-arch-badge lg ' + cls }, id);
  }

  /* ---- capture screen ---- */
  function showCapture(note) {
    clear(container);
    container.appendChild(h('div', { class: 'card pv-capture' }, [
      h('div', { class: 'pv-cap-head' }, [
        icon('spark', { width: 16, height: 16 }),
        h('div', null, [
          h('div', { class: 'eyebrow' }, 'Authoring gate · from a narrative'),
          h('h2', { class: 'pv-cap-title' }, 'Describe the operating procedure in plain words')
        ])
      ]),
      h('p', { class: 'pv-cap-sub muted' },
        'The model proposes a catalogued archetype; you confirm it, then author every '
        + 'governance value behind the gate. Nothing is generated that you don’t author — '
        + 'governed ≠ generated.'),
      note ? h('div', { class: 'pv-cap-note ' + (note.cls || '') }, note.text) : null,
      labelled('Target vertical', verticalInput(), 'where the procedure will run'),
      labelled('Narrative', narrativeInput(),
        'plain words — no thresholds, handlers, or amounts (those are yours to author)'),
      h('div', { class: 'pv-cap-actions' }, [
        h('button', { class: 'btn primary', onClick: doClassify },
          [icon('spark', { width: 13, height: 13 }), 'Classify narrative']),
        h('button', { class: 'btn', onClick: loadSample }, 'Load recorded sample'),
        manualPick()
      ])
    ]));
  }

  /* ---- proposal screen (after a match — the human-confirm boundary) ---- */
  function showProposal(match) {
    clear(container);
    const conf = (typeof match.confidence === 'number')
      ? (Math.round(match.confidence * 100) + '%') : '—';
    container.appendChild(h('div', { class: 'card pv-capture' }, [
      h('div', { class: 'pv-cap-head' }, [
        icon('check', { width: 16, height: 16 }),
        h('div', null, [
          h('div', { class: 'eyebrow' }, 'Proposed archetype · confirm to build'),
          h('h2', { class: 'pv-cap-title' }, 'Confirm the match, then author the governance')
        ])
      ]),
      h('div', { class: 'pv-prop-arch' }, [
        archBadge(match.archetype_id),
        h('div', null, [
          h('b', null, match.title || match.archetype_id),
          h('div', { class: 'mono faint' }, match.archetype_id)
        ]),
        h('div', { class: 'flex' }),
        h('span', { class: 'pv-prop-conf mono faint' }, 'model confidence ' + conf + ' · advisory')
      ]),
      match.rationale
        ? h('p', { class: 'pv-prop-rationale muted' }, match.rationale)
        : h('p', { class: 'pv-prop-rationale faint' }, '(no advisory rationale)'),
      h('div', { class: 'pv-cap-actions' }, [
        h('button', { class: 'btn primary', onClick: () => doBuild(match.archetype_id) },
          [icon('check', { width: 13, height: 13 }), 'Confirm & build draft']),
        h('button', { class: 'btn', onClick: () => showCapture(null) }, 'Back')
      ]),
      h('div', { class: 'pv-cap-foot faint' },
        'Confirming builds a governed SKELETON — every governance value stays an unfilled '
        + 'stub you author at the gate (governed ≠ generated).')
    ]));
  }

  function busy(msg) {
    clear(container);
    container.appendChild(O.loadingState ? O.loadingState(msg) : h('div', { class: 'pv-busy' }, msg));
  }

  /* ---- actions ---- */
  async function doClassify() {
    if (!narrative.trim()) {
      showCapture({ cls: 's-warn', text: 'Enter a narrative first.' });
      return;
    }
    busy('Classifying the narrative on MS-S1…');
    const r = await O.Draft.classify(narrative, vertical || 'draft');
    if (!r.ok || !r.body) {
      showCapture({ cls: 's-warn',
        text: 'The backend is unreachable — load the recorded sample, or pick an archetype manually.' });
      return;
    }
    const b = r.body;
    if (Array.isArray(b.catalog) && b.catalog.length) catalog = b.catalog;
    if (b.state === 'match' && b.match) { showProposal(b.match); return; }
    if (b.state === 'degraded') {
      showCapture({ cls: 's-warn',
        text: 'MS-S1 is unavailable (' + (b.detail || b.reason) + '). Pick an archetype manually '
          + '(works offline) or load the recorded sample.' });
      return;
    }
    // abstain — no catalogued archetype fits (route to hand-author)
    showCapture({ cls: 's-info',
      text: 'No catalogued archetype fits this narrative (' + (b.detail || b.reason) + '). '
        + 'Refine it, or author manually by picking an archetype.' });
  }

  async function doBuild(archetypeId) {
    busy('Building the governed skeleton on MS-S1…');
    const r = await O.Draft.build(narrative, vertical || 'draft', archetypeId);
    if (!r.ok || !r.body) {
      showCapture({ cls: 's-warn',
        text: 'The backend is unreachable — load the recorded sample, or pick an archetype manually.' });
      return;
    }
    const b = r.body;
    if (b.state === 'ok' && b.draft) { onDraft(b.draft); return; }
    if (b.state === 'degraded') {
      showCapture({ cls: 's-warn',
        text: 'MS-S1 is unavailable. Pick an archetype manually (works offline) or load the sample.' });
      return;
    }
    showCapture({ cls: 's-info',
      text: 'The generator abstained (' + (b.detail || b.reason) + '). Refine the narrative, '
        + 'or author manually.' });
  }

  async function doInstantiate(archetypeId) {
    busy('Instantiating the ' + archetypeId + ' skeleton…');
    const r = await O.Draft.instantiate(archetypeId, vertical || 'draft');
    if (!r.ok || !r.body || !r.body.draft) {
      showCapture({ cls: 's-warn',
        text: 'Could not instantiate (backend unreachable?) — load the recorded sample.' });
      return;
    }
    onDraft(r.body.draft);
  }

  function loadSample() {
    if (O.GateFixture) onDraft(O.GateFixture);
    else showCapture({ cls: 's-warn', text: 'No recorded sample available.' });
  }

  window.OCT = window.OCT || {};
  window.OCT.IntakeProcedures = { mount };
})();
