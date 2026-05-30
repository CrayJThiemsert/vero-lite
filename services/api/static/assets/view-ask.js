/* ============================================================
   View C — Ask (natural-language operational query)
   Chat transcript + grounding receipt: structured query, source ids,
   grounded vs. not-found (anti-hallucination) state made visible.
   ============================================================ */
(function () {
  'use strict';
  const O = window.OCT;
  const { h, clear, icon, badge } = O;

  let root, transcriptEl, inputEl, sendBtn;
  let busy = false;

  const EXAMPLES = [
    'How many assets are we running?',
    'Which sites do we operate?',
    'Any readings above 90 °C?',
    'Which assets are active right now?',
    "What's currently in maintenance?"
  ];

  function build() {
    root = h('div', { class: 'view-inner askview' });
    root.appendChild(h('div', { class: 'view-head' }, [
      h('div', null, [
        h('div', { class: 'eyebrow', style: { marginBottom: '4px' } }, 'View C · Ask'),
        h('h1', null, 'Ask in plain language — see the records behind the answer')
      ])
    ]));

    const panel = h('div', { class: 'ask-panel card' });
    transcriptEl = h('div', { class: 'ask-transcript scroll' });
    panel.appendChild(transcriptEl);

    // composer
    inputEl = h('input', { class: 'ask-input', type: 'text', placeholder: 'Ask about ' + (O.State.meta ? O.State.meta.object_types.map(t => t.name).join(', ') : 'your operation') + '…', autocomplete: 'off' });
    inputEl.addEventListener('keydown', (e) => { if (e.key === 'Enter') submit(); });
    sendBtn = h('button', { class: 'btn primary ask-send', onClick: submit }, [icon('arrow'), 'Ask']);
    panel.appendChild(h('div', { class: 'ask-composer' }, [
      h('div', { class: 'ask-input-wrap' }, [icon('ask', { width: 16, height: 16, class: 'ask-input-ic' }), inputEl]),
      sendBtn
    ]));

    root.appendChild(panel);
    return root;
  }

  function welcome() {
    transcriptEl.appendChild(h('div', { class: 'ask-welcome' }, [
      h('div', { class: 'aw-icon' }, icon('spark', { width: 22, height: 22 })),
      h('div', { class: 'aw-title' }, 'Grounded answers only'),
      h('div', { class: 'aw-sub muted' }, 'Every answer shows the structured query it ran and the exact records it came from. When nothing matches, you get an explicit “no data” — never an invention.'),
      h('div', { class: 'aw-chips' }, EXAMPLES.map(q =>
        h('button', { class: 'q-chip', onClick: () => { inputEl.value = q; submit(); } }, q)
      ))
    ]));
  }

  function userBubble(text) {
    return h('div', { class: 'msg msg-user' }, [
      h('div', { class: 'msg-role' }, 'You'),
      h('div', { class: 'bubble' }, text)
    ]);
  }

  function pendingBubble() {
    return h('div', { class: 'msg msg-sys' }, [
      h('div', { class: 'msg-role' }, 'OCT'),
      h('div', { class: 'bubble' }, h('div', { class: 'typing' }, [h('i'), h('i'), h('i')]))
    ]);
  }

  function answerBubble(res) {
    const grounded = !!res.grounded;
    const bubble = h('div', { class: 'bubble answer' }, [
      h('div', { class: 'answer-text' }, res.answer),
      groundingReceipt(res)
    ]);
    return h('div', { class: 'msg msg-sys' }, [
      h('div', { class: 'msg-role' }, 'OCT'),
      bubble
    ]);
  }

  function groundingReceipt(res) {
    const grounded = !!res.grounded;
    const sq = res.structured_query;
    const receipt = h('div', { class: 'grounding' + (grounded ? '' : ' not-found') });

    // header / open by default
    const head = h('button', { class: 'grounding-head', onClick: (e) => {
      receipt.classList.toggle('collapsed');
    } }, [
      h('span', { class: 'gh-left' }, [
        icon('receipt', { width: 14, height: 14 }),
        h('span', { class: 'eyebrow' }, 'Grounding receipt')
      ]),
      grounded
        ? O.badge('grounded', { solid: false })
        : h('span', { class: 'badge s-warn', style: { textTransform: 'none' } }, [h('span', { class: 'led' }), 'No matching records — not invented']),
      h('span', { class: 'gh-chev' }, icon('chevron', { width: 14, height: 14 }))
    ]);
    receipt.appendChild(head);

    const body = h('div', { class: 'grounding-body' });

    // structured query
    if (sq) {
      const filters = (sq.filters || []);
      body.appendChild(h('div', { class: 'gq' }, [
        h('div', { class: 'gq-label eyebrow' }, 'Structured query executed'),
        h('div', { class: 'gq-pill mono' }, [
          h('span', { class: 'gq-op' }, (sq.operation || 'list').toUpperCase()),
          h('span', { class: 'gq-type' }, sq.object_type),
          filters.length
            ? h('span', { class: 'gq-where' }, ['WHERE ', filters.map((f, i) =>
                h('span', { class: 'gq-filter' }, [
                  h('span', { class: 'gqf-p' }, f.property), ' ',
                  h('span', { class: 'gqf-o' }, opSym(f.op)), ' ',
                  h('span', { class: 'gqf-v' }, String(f.value)),
                  i < filters.length - 1 ? h('span', { class: 'faint' }, ' AND ') : null
                ])
              )])
            : h('span', { class: 'faint' }, '— no filters —')
        ])
      ]));
    }

    // result count + source ids
    const ids = res.source_object_ids || [];
    body.appendChild(h('div', { class: 'gsrc' }, [
      h('div', { class: 'gsrc-top' }, [
        h('span', { class: 'eyebrow' }, grounded ? 'Answered from these records' : 'Records matched'),
        h('span', { class: 'gsrc-count mono' }, res.result_count + ' result' + (res.result_count === 1 ? '' : 's'))
      ]),
      ids.length
        ? h('div', { class: 'gsrc-ids' }, ids.map(id =>
            h('button', { class: 'src-chip mono', title: 'Open ' + id, onClick: () => openSource(res.source_object_type, id) }, [
              icon('link', { width: 11, height: 11 }), id
            ])
          ))
        : h('div', { class: 'no-records' }, [
            icon('db', { width: 15, height: 15 }),
            h('span', null, 'Zero records returned. The system reports the empty result rather than fabricating an answer.')
          ])
    ]));

    receipt.appendChild(body);
    return receipt;
  }

  function opSym(op) { return { eq: '=', gt: '>', lt: '<', gte: '≥', lte: '≤', neq: '≠' }[op] || op; }

  function openSource(type, id) {
    if (!type) return;
    document.dispatchEvent(new CustomEvent('oct:navobj', { detail: { type, id } }));
  }

  async function submit() {
    const q = (inputEl.value || '').trim();
    if (!q || busy) return;
    busy = true; sendBtn.disabled = true; inputEl.value = '';
    // remove welcome on first ask
    const wel = transcriptEl.querySelector('.ask-welcome'); if (wel) wel.remove();
    transcriptEl.appendChild(userBubble(q));
    const pending = pendingBubble();
    transcriptEl.appendChild(pending);
    transcriptEl.scrollTop = transcriptEl.scrollHeight;
    try {
      const res = await O.API.query(q);
      pending.replaceWith(answerBubble(res));
    } catch (e) {
      pending.replaceWith(h('div', { class: 'msg msg-sys' }, [
        h('div', { class: 'msg-role' }, 'OCT'),
        h('div', { class: 'bubble answer' }, h('div', { class: 'dc-err' }, 'Query failed: ' + (e.message || e)))
      ]));
    } finally {
      busy = false; sendBtn.disabled = false;
      transcriptEl.scrollTop = transcriptEl.scrollHeight;
      inputEl.focus();
    }
  }

  async function mount(container) {
    clear(container);
    if (!O.State.meta) { try { await O.loadMeta(); } catch (e) {} }
    if (Object.keys(O.State.objects).length < (O.State.meta ? O.State.meta.object_types.length : 99)) { try { await O.loadAllObjects(); } catch (e) {} }
    container.appendChild(build());
    welcome();
    setTimeout(() => inputEl && inputEl.focus(), 50);
  }
  function ask(q) { if (inputEl) { inputEl.value = q; submit(); } }

  window.OCT.ViewAsk = { mount, ask };
})();
