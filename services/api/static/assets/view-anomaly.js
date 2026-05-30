/* ============================================================
   View B — Anomaly & Decision  (the headline "show me WHY")
   Decision card: confidence, status, affected entities, the
   reasoning trace as a vertical stepper, live Approve → Execute.
   ============================================================ */
(function () {
  'use strict';
  const O = window.OCT;
  const { h, clear, icon, badge } = O;

  let root, listEl;
  let focusAction = null;

  function build() {
    root = h('div', { class: 'view-inner anomview' });
    root.appendChild(h('div', { class: 'view-head' }, [
      h('div', null, [
        h('div', { class: 'eyebrow', style: { marginBottom: '4px' } }, 'View B · Anomaly & Decision'),
        h('h1', null, 'The system shows its work — then waits for you'),
      ]),
      h('div', { class: 'flex' }),
      h('button', { class: 'iconbtn', onClick: () => mount(root.parentElement) }, [icon('refresh'), 'Refresh'])
    ]));
    listEl = h('div', { class: 'anom-scroll scroll' });
    root.appendChild(listEl);
    return root;
  }

  function decisionCard(rec) {
    const conf = Math.round((rec.confidence || 0) * 100);
    const card = h('div', { class: 'card decision-card', dataset: { action: rec.action_id } });

    // ---- header band ----
    card.appendChild(h('div', { class: 'dc-band ' + bandClass(rec.status) }, [
      h('div', { class: 'dc-band-left' }, [
        h('span', { class: 'dc-band-icon' }, icon('anomaly', { width: 16, height: 16 })),
        h('span', { class: 'dc-band-label' }, statusHeadline(rec.status))
      ]),
      O.badge(rec.status, { solid: true })
    ]));

    // ---- title + meta ----
    const head = h('div', { class: 'dc-head' }, [
      h('h2', { class: 'dc-title' }, rec.title),
      h('p', { class: 'dc-desc' }, rec.description),
      h('div', { class: 'dc-metarow' }, [
        h('div', { class: 'dc-conf' }, [
          h('div', { class: 'dc-conf-top' }, [
            h('span', { class: 'eyebrow' }, 'Confidence'),
            h('span', { class: 'dc-conf-val mono' }, conf + '%')
          ]),
          h('div', { class: 'meter' }, h('i', { style: { width: conf + '%' } }))
        ]),
        h('div', { class: 'dc-handler' }, [
          h('span', { class: 'eyebrow' }, 'Suggested handler'),
          h('span', { class: 'mono dc-handler-v' }, rec.suggested_handler || '—')
        ])
      ])
    ]);
    card.appendChild(head);

    // ---- affected entities ----
    if (rec.affected_entities && rec.affected_entities.length) {
      card.appendChild(h('div', { class: 'dc-section' }, [
        h('div', { class: 'eyebrow', style: { marginBottom: '9px' } }, 'Affected entities'),
        h('div', { class: 'ent-row' }, rec.affected_entities.map(e =>
          O.entityChip(e, () => document.dispatchEvent(new CustomEvent('oct:navobj', { detail: { type: e.object_type, id: e.primary_key } })))
        ))
      ]));
    }

    // ---- THE REASONING TRACE (centerpiece) ----
    card.appendChild(h('div', { class: 'dc-section dc-trace' }, [
      h('div', { class: 'dc-trace-head' }, [
        h('div', { class: 'eyebrow' }, 'Reasoning trace'),
        h('span', { class: 'muted dc-trace-sub' }, 'How the engine reached this — read top to bottom')
      ]),
      O.reasoningTrace(rec.reasoning_trace)
    ]));

    // ---- actions / receipt footer ----
    const footer = h('div', { class: 'dc-actions' });
    renderActions(footer, rec, card);
    card.appendChild(footer);

    return card;
  }

  function renderActions(footer, rec, card) {
    clear(footer);
    const status = rec.status;

    if (status === 'executed' && rec._receipt) {
      footer.appendChild(receiptBlock(rec._receipt));
      return;
    }

    const left = h('div', { class: 'dc-actions-left' });
    const right = h('div', { class: 'dc-actions-right' });

    if (status === 'proposed') {
      left.appendChild(h('span', { class: 'dc-hint muted' }, [icon('check', { width: 14, height: 14 }), 'Requires human approval before anything runs']));
      const reject = h('button', { class: 'btn danger', onClick: () => visualReject(rec, card) }, [icon('x', { width: 15, height: 15 }), 'Reject']);
      const approve = h('button', { class: 'btn primary', onClick: () => doApprove(rec, footer, card) }, [icon('check'), 'Approve']);
      right.appendChild(reject); right.appendChild(approve);
    } else if (status === 'approved') {
      left.appendChild(h('span', { class: 'dc-hint ok-text' }, [icon('check', { width: 14, height: 14 }), 'Approved — ready to execute']));
      const exec = h('button', { class: 'btn ok', onClick: () => doExecute(rec, footer, card) }, [icon('play'), 'Execute']);
      right.appendChild(exec);
    } else if (status === 'rejected') {
      left.appendChild(h('span', { class: 'dc-hint muted' }, [icon('x', { width: 14, height: 14 }), 'Dismissed — no action taken']));
      const undo = h('button', { class: 'btn ghost sm', onClick: () => { rec.status = 'proposed'; renderActions(footer, rec, card); updateBand(card, rec); } }, 'Undo');
      right.appendChild(undo);
    }
    footer.appendChild(left); footer.appendChild(right);
  }

  function setBusy(footer, label) {
    clear(footer);
    footer.appendChild(h('div', { class: 'dc-busy' }, [
      h('span', { class: 'spinner-sm' }), h('span', { class: 'muted' }, label)
    ]));
  }

  async function doApprove(rec, footer, card) {
    setBusy(footer, 'Submitting approval…');
    try {
      const updated = await O.API.approve(rec.action_id);
      rec.status = updated.status || 'approved';
      updateBand(card, rec); flashBadge(card, rec.status);
      renderActions(footer, rec, card);
    } catch (e) {
      footer.innerHTML = '';
      footer.appendChild(errInline('Approval failed: ' + (e.message || e), () => renderActions(footer, rec, card)));
    }
  }

  async function doExecute(rec, footer, card) {
    setBusy(footer, 'Executing via ' + (rec.suggested_handler || 'handler') + '…');
    try {
      const res = await O.API.execute(rec.action_id);
      rec.status = res.status || 'executed';
      rec._receipt = res.handler_receipt || {};
      updateBand(card, rec); flashBadge(card, rec.status);
      renderActions(footer, rec, card);
    } catch (e) {
      footer.innerHTML = '';
      footer.appendChild(errInline('Execution failed: ' + (e.message || e), () => renderActions(footer, rec, card)));
    }
  }

  function visualReject(rec, card) {
    rec.status = 'rejected';
    updateBand(card, rec); flashBadge(card, rec.status);
    renderActions(card.querySelector('.dc-actions'), rec, card);
  }

  function receiptBlock(receipt) {
    const wrap = h('div', { class: 'receipt' });
    wrap.appendChild(h('div', { class: 'receipt-head' }, [
      h('span', { class: 'receipt-ic' }, icon('receipt', { width: 15, height: 15 })),
      h('b', null, 'Handler receipt'),
      O.badge('executed', { solid: true })
    ]));
    wrap.appendChild(O.kvDump(receipt));
    return wrap;
  }

  function errInline(msg, retry) {
    return h('div', { class: 'dc-err' }, [
      h('span', null, msg),
      retry ? h('button', { class: 'btn ghost sm', onClick: retry }, 'Back') : null
    ]);
  }

  function bandClass(status) {
    return { proposed: 'band-crit', approved: 'band-info', executed: 'band-ok', rejected: 'band-neutral' }[status] || 'band-crit';
  }
  function statusHeadline(status) {
    return { proposed: 'Anomaly detected — action proposed', approved: 'Approved — awaiting execution', executed: 'Executed — handler dispatched', rejected: 'Dismissed by operator' }[status] || 'Action';
  }
  function updateBand(card, rec) {
    const band = card.querySelector('.dc-band');
    band.className = 'dc-band ' + bandClass(rec.status);
    band.querySelector('.dc-band-label').textContent = statusHeadline(rec.status);
    const b = band.querySelector('.badge');
    const nb = O.badge(rec.status, { solid: true });
    b.replaceWith(nb);
  }
  function flashBadge(card, status) {
    card.classList.remove('flash'); void card.offsetWidth; card.classList.add('flash');
  }

  async function ensure() {
    if (!O.State.meta) await O.loadMeta();
    await O.loadRecommendations();
  }

  async function mount(container) {
    clear(container);
    container.appendChild(build());
    listEl.appendChild(O.loadingState('Loading recommendations…'));
    try {
      await ensure();
      clear(listEl);
      const recs = O.State.recommendations;
      if (!recs.length) {
        listEl.appendChild(h('div', { class: 'state' }, h('div', { class: 'box' }, [
          h('div', { style: { color: 'var(--ok)', marginBottom: '10px' } }, icon('check', { width: 28, height: 28 })),
          h('h3', null, 'All clear'),
          h('p', null, 'No open recommendations. The engine surfaces a decision card here the moment an anomaly is detected.')
        ])));
        return;
      }
      const grid = h('div', { class: 'anom-grid' });
      recs.forEach(r => grid.appendChild(decisionCard(r)));
      listEl.appendChild(grid);
      if (focusAction) {
        const el = grid.querySelector('[data-action="' + focusAction + '"]');
        if (el) { el.classList.add('focused'); el.scrollTo && el.scrollIntoView; }
        focusAction = null;
      }
    } catch (e) {
      clear(listEl); listEl.appendChild(O.errorState('Could not load recommendations', String(e.message || e), () => mount(container)));
    }
  }
  function setFocus(actionId) { focusAction = actionId; }

  window.OCT.ViewAnomaly = { mount, setFocus };
})();
