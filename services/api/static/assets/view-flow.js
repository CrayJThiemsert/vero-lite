/* ============================================================
   View D — Data → Decision Flow
   One screen: raw data (left) → a governed decision (right).
   4 stages: Ingest · Condition · Process · Result. No new endpoint.
   ============================================================ */
(function () {
  'use strict';
  const O = window.OCT;
  const { h, clear, icon, badge } = O;

  let root, pipeEl;

  function build() {
    root = h('div', { class: 'view-inner flowview' });
    root.appendChild(h('div', { class: 'view-head' }, [
      h('div', null, [
        h('div', { class: 'eyebrow', style: { marginBottom: '4px' } }, 'View D · Data → Decision Flow'),
        h('h1', null, 'Your data becomes a decision someone can stand behind')
      ]),
      h('div', { class: 'flex' }),
      h('button', { class: 'iconbtn', onClick: () => mount(root.parentElement) }, [icon('refresh'), 'Refresh'])
    ]));
    pipeEl = h('div', { class: 'flow-scroll scroll' });
    root.appendChild(pipeEl);
    return root;
  }

  function stage(n, ic, title, sub, body, accent) {
    return h('div', { class: 'stage', style: { '--accent-stage': accent } }, [
      h('div', { class: 'stage-head' }, [
        h('span', { class: 'stage-n mono' }, n),
        h('span', { class: 'stage-ic' }, icon(ic, { width: 16, height: 16 })),
        h('div', { class: 'stage-titles' }, [
          h('div', { class: 'stage-title' }, title),
          h('div', { class: 'stage-sub muted' }, sub)
        ])
      ]),
      h('div', { class: 'stage-body' }, body)
    ]);
  }

  function connector() { return h('div', { class: 'flow-arrow' }, icon('arrow', { width: 22, height: 22 })); }

  function findAnomalyEvent(rec) {
    // pull the breaching reading out of the trace (rule path carries it)
    let measured = null, unit = null, threshold = null;
    (rec.reasoning_trace || []).forEach(s => {
      const d = s.detail || {};
      if (d.measured_value != null) { measured = d.measured_value; unit = d.unit || unit; }
      if (d.threshold != null) threshold = d.threshold;
    });
    // entity is ontology-driven: the recommendation's first affected entity,
    // whatever its object_type (Asset, Shipment, …) — no hard-coded type
    const ent = (rec.affected_entities || [])[0] || null;
    return { measured, unit, threshold, entityType: ent ? ent.object_type : null, entityId: ent ? ent.primary_key : null };
  }

  // A grounded, domain-driven question to seed View C — derived from the
  // condition: the breaching threshold when the trace carries it, else a
  // status query over the monitored entity type (both ground in /objects data).
  function conditionQuestion(cond) {
    if (cond.threshold != null) return 'Any readings above ' + cond.threshold + (cond.unit ? ' ' + cond.unit : '') + '?';
    const et = cond.entityType;
    if (et && O.State.meta) {
      const sp = O.Onto.statusProp(et);
      if (sp && sp.enum && sp.enum.length) {
        const attn = sp.enum.find(v => /delay|held|hold|maint|pending|warn|fault|critical|excursion|breach/i.test(v)) || sp.enum[sp.enum.length - 1];
        return 'Show ' + et.toLowerCase() + 's with status "' + attn + '"';
      }
      return 'How many ' + et.toLowerCase() + 's are there?';
    }
    return 'What needs attention right now?';
  }

  function render() {
    clear(pipeEl);
    const meta = O.State.meta;
    const rec = O.State.recommendations[0];

    // -------- Stage 1: Ingest --------
    const counts = meta.object_types.map(t => {
      const c = (O.State.objects[t.name] || { count: 0 }).count;
      return { name: t.name, count: c };
    }).filter(x => x.count > 0 || ['Site', 'Asset'].includes(x.name));
    const ingest = h('div', null, [
      h('div', { class: 'ingest-grid' }, counts.map(c =>
        h('div', { class: 'ingest-cell' }, [
          h('div', { class: 'ingest-n mono' }, c.count),
          h('div', { class: 'ingest-l muted' }, c.name + (c.count === 1 ? '' : 's'))
        ])
      )),
      h('div', { class: 'stage-foot mono faint' }, 'live · GET /objects/{type}')
    ]);

    // -------- Stage 2: Condition --------
    const cond = findAnomalyEvent(rec || { reasoning_trace: [] });
    const entityType = cond.entityType;
    const entPk = entityType ? O.Onto.pk(entityType) : null;
    const entityObj = (entityType && entPk)
      ? ((O.State.objects[entityType] || { objects: [] }).objects.find(o => o[entPk] === cond.entityId) || null)
      : null;
    const askQ = conditionQuestion(cond);
    const condBody = h('div', null, [
      h('div', { class: 'cond-card' }, [
        h('div', { class: 'cond-top' }, [
          h('span', { class: 'badge s-crit' }, [h('span', { class: 'led' }), 'threshold breach']),
          entityType ? O.typeTag(entityType) : null
        ]),
        h('div', { class: 'cond-reading' }, [
          h('span', { class: 'cond-val mono' }, cond.measured != null ? cond.measured : '—'),
          h('span', { class: 'cond-unit mono' }, cond.unit || '')
        ]),
        h('div', { class: 'cond-thr mono muted' }, cond.threshold != null ? ('threshold ' + cond.threshold + ' ' + (cond.unit || '')) : ''),
        (entityType && cond.entityId) ? h('div', { class: 'cond-asset' }, [
          h('span', { class: 'muted' }, 'on '), h('b', null, entityObj ? O.Onto.label(entityType, entityObj) : cond.entityId),
          h('span', { class: 'faint mono', style: { marginLeft: '6px' } }, cond.entityId)
        ]) : null
      ]),
      h('div', { class: 'cond-or' }, [h('span', { class: 'line' }), h('span', { class: 'or-txt mono' }, 'OR ASK A QUESTION'), h('span', { class: 'line' })]),
      h('button', { class: 'cond-ask', onClick: () => document.dispatchEvent(new CustomEvent('oct:goto', { detail: { view: 'C', ask: askQ } })) }, [
        icon('ask', { width: 14, height: 14 }),
        h('span', null, '"' + askQ + '"'),
        icon('arrow', { width: 13, height: 13 })
      ])
    ]);

    // -------- Stage 3: Process --------
    const steps = (rec && rec.reasoning_trace) || [];
    const proc = h('div', null, [
      h('div', { class: 'proc-steps' }, steps.map((s, i) =>
        h('div', { class: 'proc-step' }, [
          h('span', { class: 'proc-n mono ' + kindClass(s.kind) }, i + 1),
          h('div', { class: 'proc-body' }, [
            h('span', { class: 'badge ' + kindClass(s.kind), style: { textTransform: 'none', marginBottom: '4px' } }, s.kind),
            h('div', { class: 'proc-sum' }, s.summary)
          ])
        ])
      )),
      h('div', { class: 'stage-foot mono faint' }, steps.length + ' steps · reasoning_trace[]')
    ]);

    // -------- Stage 4: Result --------
    const result = h('div', null, [
      rec ? h('div', { class: 'result-card' }, [
        h('div', { class: 'result-band ' + bandCls(rec.status) }, [
          icon('bolt', { width: 14, height: 14 }), h('span', null, 'RecommendedAction')
        ]),
        h('div', { class: 'result-title' }, rec.title),
        h('div', { class: 'result-status' }, [
          h('span', { class: 'eyebrow' }, 'Status'), O.badge(rec.status, { solid: true })
        ]),
        resultControl(rec)
      ]) : h('div', { class: 'muted' }, 'No open recommendation.'),
      h('div', { class: 'stage-foot mono faint' }, 'GET /recommendations → approve → execute')
    ]);

    const pipe = h('div', { class: 'pipeline' }, [
      stage('01', 'db', 'Ingest', 'Raw operational data', ingest, 'var(--info)'), connector(),
      stage('02', 'gauge', 'Condition', 'A threshold trips', condBody, 'var(--warn)'), connector(),
      stage('03', 'cpu', 'Process', 'The engine reasons', proc, 'var(--info)'), connector(),
      stage('04', 'bolt', 'Result', 'A governed decision', result, 'var(--ok)')
    ]);

    pipeEl.appendChild(h('div', { class: 'flow-rail-label' }, [
      h('span', { class: 'mono faint' }, 'RAW DATA'),
      h('span', { class: 'rail-line' }),
      h('span', { class: 'mono faint' }, 'GOVERNED DECISION')
    ]));
    pipeEl.appendChild(pipe);
  }

  function resultControl(rec) {
    const wrap = h('div', { class: 'result-ctl' });
    if (rec.status === 'proposed') {
      wrap.appendChild(h('button', { class: 'btn primary sm', onClick: async () => {
        wrap.replaceWith(busy('Approving…')); try { const u = await O.API.approve(rec.action_id); rec.status = u.status || 'approved'; } catch (e) {} render();
      } }, [icon('check', { width: 14, height: 14 }), 'Approve']));
    } else if (rec.status === 'approved') {
      wrap.appendChild(h('button', { class: 'btn ok sm', onClick: async () => {
        wrap.replaceWith(busy('Executing…')); try { const r = await O.API.execute(rec.action_id); rec.status = r.status || 'executed'; rec._receipt = r.handler_receipt; } catch (e) {} render();
      } }, [icon('play', { width: 14, height: 14 }), 'Execute']));
    } else if (rec.status === 'executed') {
      wrap.appendChild(h('div', { class: 'result-done' }, [icon('check', { width: 14, height: 14 }), 'Dispatched' + (rec._receipt && rec._receipt.work_order_id ? ' · ' + rec._receipt.work_order_id : '')]));
    }
    return wrap;
  }
  function busy(label) { return h('div', { class: 'result-ctl' }, h('div', { class: 'dc-busy' }, [h('span', { class: 'spinner-sm' }), h('span', { class: 'muted' }, label)])); }

  function kindClass(kind) {
    const k = String(kind).toLowerCase();
    if (k.includes('rule')) return 's-warn';
    if (k.includes('llm') || k.includes('infer')) return 's-info';
    if (k.includes('ontology') || k.includes('query')) return 's-ok';
    return 's-neutral';
  }
  function bandCls(status) { return { proposed: 's-crit', approved: 's-info', executed: 's-ok', rejected: 's-neutral' }[status] || 's-crit'; }

  async function mount(container) {
    clear(container);
    container.appendChild(build());
    pipeEl.appendChild(O.loadingState('Assembling the flow…'));
    try {
      if (!O.State.meta) await O.loadMeta();
      await O.loadAllObjects();
      await O.loadRecommendations();
      render();
    } catch (e) {
      clear(pipeEl); pipeEl.appendChild(O.errorState('Could not assemble flow', String(e.message || e), () => mount(container)));
    }
  }

  window.OCT.ViewFlow = { mount };
})();
