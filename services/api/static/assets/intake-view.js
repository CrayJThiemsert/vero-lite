/* ============================================================
   View E — Build a Vertical (PLAN-0017 live co-creation intake face)
   "…and what's *your* operation?" — free-text capture -> MS-S1 extraction
   -> the MANDATORY human review/edit gate -> invoke the engine -> vertical #4.

   The gate is the one non-negotiable (AC-2): generation happens ONLY when the
   operator clicks Confirm — this view has no auto-confirm path. The package
   source (MS-S1 extraction / prebaked starter / manual entry) is surfaced as a
   prominent badge so the operator always knows which dataset is in play (AC-4).
   ============================================================ */
(function () {
  'use strict';
  const O = window.OCT;
  const { h, clear, icon } = O;

  const SOURCE_VIS = {
    ms_s1_live: { cls: 's-ok', text: 'MS-S1 EXTRACTION' },
    prebaked_default: { cls: 's-info', text: 'PREBAKED STARTER' },
    manual_entry: { cls: 's-warn', text: 'MANUAL ENTRY' }
  };
  const PROP_TYPES = ['string', 'int', 'float', 'bool', 'enum', 'timestamp', 'date'];

  let container = null;
  let draft = null; // the working IntakePackage the gate edits

  function mount(c) {
    container = c;
    showCapture();
  }

  // ----------------------------------------------------------------- helpers
  function blankPackage() {
    return {
      namespace: '', domain_label: '',
      asset_role: { type_name: '', properties: [] },
      site_role: { type_name: '', properties: [] },
      metric: { label: '', unit: '', threshold: 0, direction: 'above' },
      action_types: [], problem: '', decision: '',
      recovery_value: 0, recovery_description: '',
      source: 'manual_entry', confidence: 1.0
    };
  }
  function clone(pkg) { return JSON.parse(JSON.stringify(pkg)); }

  function viewHead(title) {
    return h('div', { class: 'view-head' }, [
      h('div', null, [
        h('div', { class: 'eyebrow', style: { marginBottom: '4px' } }, 'View E · Build a Vertical'),
        h('h1', null, title)
      ])
    ]);
  }

  function sourceBadge(source) {
    const v = SOURCE_VIS[source] || { cls: 's-neutral', text: String(source || '—').toUpperCase() };
    return h('span', { class: 'badge ' + v.cls }, [h('span', { class: 'led' }), v.text]);
  }

  function busy(msg) {
    clear(container);
    container.appendChild(h('div', { class: 'view-inner intakeview' }, [
      h('div', { class: 'state' }, h('div', { class: 'box' }, [
        h('div', { class: 'spinner' }),
        h('p', null, msg || 'Working…')
      ]))
    ]));
  }

  // ----------------------------------------------------------------- capture
  function showCapture(opts) {
    opts = opts || {};
    clear(container);
    const root = h('div', { class: 'view-inner intakeview' });
    root.appendChild(viewHead('Describe your operation — build a control tower for it, live'));

    const scroll = h('div', { class: 'intake-scroll' });
    const card = h('div', { class: 'card card-pad capture-card' });

    const msHint = h('div', { class: 'ms-hint s-neutral' }, 'checking MS-S1…');
    refreshMsHint(msHint);
    card.appendChild(msHint);

    card.appendChild(h('div', { class: 'eyebrow', style: { marginTop: '14px' } }, 'Tell us about your operation'));
    card.appendChild(h('p', { class: 'muted capture-help' },
      'In a sentence or two: what are your assets and where do they sit? What breaks and why does it hurt? ' +
      'What reading crosses what threshold — a crash (value falling) or an overrun (value rising)? ' +
      'What is the corrective action?'));

    const ta = h('textarea', {
      class: 'intake-textarea', rows: 5,
      placeholder: 'e.g. We run shrimp ponds across coastal farms. At night dissolved oxygen can crash below 4 mg/L and kill a pond within hours; we start the emergency aerator.'
    });
    if (opts.prefill) ta.value = opts.prefill;
    card.appendChild(ta);

    if (opts.error) {
      card.appendChild(h('div', { class: 'intake-degraded' }, [
        h('div', { class: 'idg-top' }, [icon('anomaly', { width: 15, height: 15 }), h('b', null, 'MS-S1 extraction unavailable')]),
        h('div', { class: 'idg-detail' }, opts.error),
        h('div', { class: 'idg-fallback muted' }, 'Use a prebaked starter or enter the package manually below — the demo continues either way.')
      ]));
    }

    const extractBtn = h('button', { class: 'btn primary', onClick: () => doExtract(ta.value) }, [icon('spark'), 'Extract draft (MS-S1)']);
    const starterBtn = h('button', { class: 'btn ghost', onClick: () => toggleStarters(startersWrap) }, [icon('grid'), 'Use a starter']);
    const manualBtn = h('button', { class: 'btn ghost', onClick: () => showGate(blankPackage()) }, [icon('flow'), 'Enter manually']);
    card.appendChild(h('div', { class: 'capture-actions' }, [extractBtn, h('span', { class: 'ca-or muted' }, 'or'), starterBtn, manualBtn]));

    const startersWrap = h('div', { class: 'starters-wrap' });
    card.appendChild(startersWrap);

    scroll.appendChild(card);
    root.appendChild(scroll);
    container.appendChild(root);
    setTimeout(() => ta.focus(), 40);
  }

  async function refreshMsHint(el) {
    const r = await O.Llm.status();
    const st = (r && r.ok && r.body && r.body.state) || 'unknown';
    const map = {
      resident: ['s-ok', 'MS-S1 resident — extraction ready'],
      cold: ['s-warn', 'MS-S1 cold — warm it from the header, or use a starter / manual entry'],
      unreachable: ['s-crit', 'MS-S1 offline — use a starter or manual entry'],
      error: ['s-crit', 'MS-S1 error — use a starter or manual entry'],
      unknown: ['s-neutral', 'MS-S1 status unknown — extraction may degrade']
    };
    const v = map[st] || map.unknown;
    clear(el);
    el.className = 'ms-hint ' + v[0];
    el.appendChild(icon('cpu', { width: 13, height: 13 }));
    el.appendChild(h('span', { class: 'led' }));
    el.appendChild(h('span', null, v[1]));
  }

  async function toggleStarters(wrap) {
    if (wrap.childNodes.length) { clear(wrap); return; }
    wrap.appendChild(h('div', { class: 'muted', style: { padding: '10px 0' } }, 'Loading starters…'));
    const r = await O.Intake.defaults();
    clear(wrap);
    const defaults = (r && r.ok && r.body && r.body.defaults) || [];
    if (!defaults.length) { wrap.appendChild(h('div', { class: 'muted' }, 'No starters available.')); return; }
    wrap.appendChild(h('div', { class: 'eyebrow', style: { margin: '6px 0' } }, 'Prebaked starters'));
    defaults.forEach(pkg => {
      wrap.appendChild(h('button', { class: 'starter-row', onClick: () => showGate(clone(pkg)) }, [
        h('div', { class: 'sr-main' }, [
          h('div', { class: 'sr-title' }, pkg.domain_label || pkg.namespace),
          h('div', { class: 'sr-meta muted mono' }, pkg.namespace + ' · ' + pkg.asset_role.type_name + '/' + pkg.site_role.type_name)
        ]),
        h('span', { class: 'badge ' + (pkg.metric.direction === 'below' ? 's-crit' : 's-warn') }, pkg.metric.direction),
        icon('chevron', { width: 14, height: 14 })
      ]));
    });
  }

  async function doExtract(text) {
    text = (text || '').trim();
    if (!text) { showCapture({ error: 'Please describe your operation first.' }); return; }
    busy('Extracting a draft package from MS-S1 (local)…');
    const r = await O.Intake.extract(text);
    if (r && r.ok && r.body && r.body.state === 'ok' && r.body.package) {
      showGate(r.body.package);
      return;
    }
    const detail = (r && r.body && r.body.detail) ||
      (r && r.networkError ? 'the demo backend is unreachable' : 'extraction failed');
    showCapture({ prefill: text, error: detail });
  }

  // -------------------------------------------------------------------- gate
  function showGate(pkg) {
    draft = clone(pkg);
    clear(container);
    const root = h('div', { class: 'view-inner intakeview' });
    root.appendChild(viewHead('Review the proposed control tower — edit anything, then confirm'));

    const scroll = h('div', { class: 'intake-scroll' });
    const card = h('div', { class: 'card gate-card' });

    // header band: source + confidence
    card.appendChild(h('div', { class: 'gate-band' }, [
      sourceBadge(draft.source),
      draft.source === 'ms_s1_live' && draft.confidence != null
        ? h('span', { class: 'muted mono', style: { fontSize: '11px' } }, 'confidence ' + Math.round(draft.confidence * 100) + '%')
        : null,
      h('span', { class: 'muted', style: { marginLeft: 'auto', fontSize: '12px' } },
        'Nothing is generated until you confirm.')
    ]));

    const body = h('div', { class: 'gate-body' });

    // basics
    body.appendChild(section('Vertical', [
      fieldGrid([
        textField('Namespace (slug)', draft.namespace, v => draft.namespace = v, { mono: true, placeholder: 'snake_case' }),
        textField('Domain label', draft.domain_label, v => draft.domain_label = v)
      ])
    ]));

    // metric + direction (AC-3)
    body.appendChild(section('Anomaly metric & breach direction', [
      fieldGrid([
        textField('Metric label', draft.metric.label, v => draft.metric.label = v),
        textField('Unit', draft.metric.unit, v => draft.metric.unit = v, { placeholder: 'e.g. mg/L' }),
        numField('Threshold', draft.metric.threshold, v => draft.metric.threshold = v),
        selectField('Direction', draft.metric.direction, ['above', 'below'], v => draft.metric.direction = v,
          'below = a crash (value falls through); above = an overrun (value rises through)')
      ])
    ]));

    // asset role
    body.appendChild(section('Asset-role (the managed unit that breaches)', [
      textField('Type name (PascalCase)', draft.asset_role.type_name, v => draft.asset_role.type_name = v, { mono: true, placeholder: 'e.g. Pond' }),
      h('div', { class: 'eyebrow props-label' }, 'Domain properties'),
      propsEditor(draft.asset_role)
    ]));

    // site role
    body.appendChild(section('Site-role (the geo-located place grouping assets)', [
      textField('Type name (PascalCase)', draft.site_role.type_name, v => draft.site_role.type_name = v, { mono: true, placeholder: 'e.g. Farm' }),
      h('div', { class: 'muted', style: { fontSize: '11.5px', marginTop: '4px' } }, 'lat/lng are added automatically — this is the type that renders on the map.'),
      h('div', { class: 'eyebrow props-label' }, 'Domain properties'),
      propsEditor(draft.site_role)
    ]));

    // actions
    body.appendChild(section('Corrective actions', [
      textField('Action types (comma-separated, snake_case)', draft.action_types.join(', '),
        v => draft.action_types = v.split(',').map(s => s.trim()).filter(Boolean), { mono: true })
    ]));

    // problem / decision
    body.appendChild(section('Narrative', [
      textareaField('Problem statement', draft.problem, v => draft.problem = v),
      textareaField('Corrective decision', draft.decision, v => draft.decision = v)
    ]));

    // recovery
    body.appendChild(section('Recovery (after the action executes)', [
      fieldGrid([
        numField('Recovery value', draft.recovery_value, v => draft.recovery_value = v),
        textField('Recovery description', draft.recovery_description, v => draft.recovery_description = v)
      ])
    ]));

    card.appendChild(body);

    // footer: the explicit confirm (AC-2)
    const errBox = h('div', { class: 'gate-err' });
    card.appendChild(h('div', { class: 'gate-foot' }, [
      h('button', { class: 'btn ghost', onClick: () => showCapture() }, [icon('x'), 'Back']),
      h('div', { class: 'gf-right' }, [
        h('span', { class: 'gf-hint muted' }, 'Review complete?'),
        h('button', { class: 'btn primary', onClick: () => doGenerate(errBox) }, [icon('check'), 'Confirm & build vertical #4'])
      ])
    ]));
    card.appendChild(errBox);

    scroll.appendChild(card);
    root.appendChild(scroll);
    container.appendChild(root);
  }

  function section(title, children) {
    return h('div', { class: 'gate-section' }, [
      h('div', { class: 'gate-section-title' }, title),
      h('div', { class: 'gate-section-body' }, children)
    ]);
  }
  function fieldGrid(fields) { return h('div', { class: 'field-grid' }, fields); }

  function field(label, control, note) {
    return h('label', { class: 'field' }, [
      h('span', { class: 'field-label' }, label),
      control,
      note ? h('span', { class: 'field-note muted' }, note) : null
    ]);
  }
  function textField(label, value, onset, opts) {
    opts = opts || {};
    const inp = h('input', {
      class: 'intake-input' + (opts.mono ? ' mono' : ''), type: 'text',
      value: value == null ? '' : String(value), placeholder: opts.placeholder || ''
    });
    inp.addEventListener('input', e => onset(e.target.value));
    return field(label, inp, opts.note);
  }
  function numField(label, value, onset) {
    const inp = h('input', { class: 'intake-input mono', type: 'number', step: 'any', value: value == null ? '' : String(value) });
    inp.addEventListener('input', e => { const n = parseFloat(e.target.value); onset(isNaN(n) ? 0 : n); });
    return field(label, inp);
  }
  function selectField(label, value, options, onset, note) {
    const sel = h('select', { class: 'intake-select' },
      options.map(o => h('option', { value: o, selected: o === value ? 'selected' : null }, o)));
    sel.addEventListener('change', e => onset(e.target.value));
    return field(label, sel, note);
  }
  function textareaField(label, value, onset) {
    const ta = h('textarea', { class: 'intake-textarea sm', rows: 2 });
    ta.value = value == null ? '' : String(value);
    ta.addEventListener('input', e => onset(e.target.value));
    return field(label, ta);
  }

  function propsEditor(role) {
    const wrap = h('div', { class: 'props-editor' });
    function render() {
      clear(wrap);
      role.properties.forEach((p, i) => wrap.appendChild(propRow(role, p, i, render)));
      wrap.appendChild(h('button', { class: 'btn sm ghost add-prop', onClick: () => {
        role.properties.push({ name: '', type: 'string', values: [], required: false });
        render();
      } }, [icon('arrow'), 'Add property']));
    }
    render();
    return wrap;
  }
  function propRow(role, p, i, rerender) {
    const nameI = h('input', { class: 'intake-input mono prop-name', type: 'text', value: p.name || '', placeholder: 'snake_case' });
    nameI.addEventListener('input', e => p.name = e.target.value);

    const typeSel = h('select', { class: 'intake-select prop-type' },
      PROP_TYPES.map(t => h('option', { value: t, selected: t === p.type ? 'selected' : null }, t)));
    typeSel.addEventListener('change', e => { p.type = e.target.value; if (p.type !== 'enum') p.values = []; rerender(); });

    const cells = [nameI, typeSel];
    if (p.type === 'enum') {
      const valI = h('input', { class: 'intake-input prop-values', type: 'text', value: (p.values || []).join(', '), placeholder: 'a, b, c' });
      valI.addEventListener('input', e => p.values = e.target.value.split(',').map(s => s.trim()).filter(Boolean));
      cells.push(valI);
    } else {
      cells.push(h('span', { class: 'prop-values-spacer' }));
    }

    const reqWrap = h('label', { class: 'prop-req', title: 'required' });
    const reqBox = h('input', { type: 'checkbox' });
    reqBox.checked = !!p.required;
    reqBox.addEventListener('change', e => p.required = e.target.checked);
    reqWrap.appendChild(reqBox);
    reqWrap.appendChild(document.createTextNode('req'));
    cells.push(reqWrap);

    const del = h('button', { class: 'prop-del', title: 'remove' }, icon('x', { width: 13, height: 13 }));
    del.addEventListener('click', () => { role.properties.splice(i, 1); rerender(); });
    cells.push(del);

    return h('div', { class: 'prop-row' }, cells);
  }

  // ------------------------------------------------------------------ result
  async function doGenerate(errBox, force) {
    clear(errBox);
    busy('Building vertical #4 — assembling the ontology and invoking the engine…');
    const r = await O.Intake.generate(draft, force);
    if (r && r.ok && r.body) { showResult(r.body); return; }
    // re-render the gate, then surface the error inline
    showGate(draft);
    const box = container.querySelector('.gate-err');
    const status = r ? r.status : 0;
    const detail = r && r.body && r.body.detail;
    if (status === 409) {
      box.appendChild(h('div', { class: 'gate-err-banner' }, [
        icon('anomaly', { width: 15, height: 15 }),
        h('span', null, (detail && detail.error) || 'A vertical with this namespace already exists.'),
        h('button', { class: 'btn sm danger', onClick: () => { const eb = container.querySelector('.gate-err'); doGenerate(eb, true); } }, 'Overwrite (force)')
      ]));
    } else {
      let msg = 'Generation failed.';
      if (typeof detail === 'string') msg = detail;
      else if (detail && detail.error) msg = detail.error;
      else if (r && r.networkError) msg = 'The demo backend is unreachable.';
      box.appendChild(h('div', { class: 'gate-err-banner' }, [icon('anomaly', { width: 15, height: 15 }), h('span', null, msg)]));
    }
  }

  function showResult(resp) {
    clear(container);
    const root = h('div', { class: 'view-inner intakeview' });
    root.appendChild(viewHead('Vertical #4 is built'));
    const scroll = h('div', { class: 'intake-scroll' });
    const card = h('div', { class: 'card card-pad result-card-e' });

    card.appendChild(h('div', { class: 'res-top' }, [
      h('div', { class: 'res-check' }, icon('check', { width: 22, height: 22 })),
      h('div', null, [
        h('div', { class: 'res-title' }, resp.namespace),
        h('div', { class: 'muted' }, resp.asset_type + ' / ' + resp.site_type + ' · breach direction ' + resp.direction)
      ])
    ]));

    card.appendChild(h('div', { class: 'eyebrow', style: { marginTop: '16px' } }, 'Boot the vertical (env block)'));
    card.appendChild(h('pre', { class: 'env-block mono' }, resp.env_block));

    card.appendChild(h('div', { class: 'eyebrow', style: { marginTop: '14px' } }, 'Scaffold written'));
    card.appendChild(h('div', { class: 'written-list' },
      (resp.written || []).map(p => h('div', { class: 'mono written-row' }, p))));

    card.appendChild(h('div', { class: 'res-next muted' }, resp.next_steps));

    card.appendChild(h('div', { class: 'result-actions' }, [
      h('button', { class: 'btn ghost', onClick: () => showCapture() }, [icon('arrow'), 'Build another']),
      h('span', { class: 'badge s-ok' }, [h('span', { class: 'led' }), 'registered: ' + (resp.registered ? 'yes' : 'no')])
    ]));

    scroll.appendChild(card);
    root.appendChild(scroll);
    container.appendChild(root);
  }

  window.OCT.ViewIntake = { mount };
})();
