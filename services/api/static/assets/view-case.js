/* ============================================================
   OCT — View I: Open a Case (PLAN-0096 Step 2 / AC-3).

   The minute-1 surface. Every other view in this app is built for someone sitting
   at a desk looking at a fleet; this one is built for น้องเมย์ on a phone with a
   driver still on the line, and for ต้อม standing next to a broken truck on the
   hard shoulder. That difference drives every choice below:

   * ONE required input — the truck. Description is optional, the photo is optional,
     and nothing else is asked. AC-3's "zero further required typing" is a promise
     about a human's hands, so the form must be submittable after a single tap.
   * The photo input carries `capture="environment"`, so a phone opens the CAMERA
     rather than a file browser. On desktop the same input is an ordinary file pick.
   * Big touch targets and a single column. No hover affordances — there is no
     cursor on the device this is for.
   * Failures are stated in Thai, in the operator's own terms, and the form KEEPS
     what was typed. Losing a roadside case to an error toast is how a tool teaches
     people to go back to LINE.

   Photo upload is a SECOND request after the case exists (POST /api/cases, then
   POST /api/cases/{id}/photos). Deliberate: the case — who, which truck, when — is
   the record that must survive, and a failed or slow photo on a hard-shoulder
   connection must never take it down with it. A case with a missing photo is
   recoverable; a photo with no case is nothing.

   DIRECT fetch, no mock fallback (the view-monitor precedent): this view WRITES,
   and api.js request()'s mock path would fake a stored case. An honest error is
   correct.
   ============================================================ */
(function () {
  'use strict';
  const O = window.OCT;
  const { h, clear, icon } = O;

  const state = {
    trucks: [],
    cases: [],
    listError: null,   // set when the LIST could not be read — never shown as 'empty'
    selected: null,    // case_id whose evidence pack is expanded (Step 3)
    pack: null,        // the fetched evidence pack, or {error}
    packMsg: null,     // {kind, text} for the quote form
    // PLAN-0112 Step 5 — the accept control. `reasonFor` holds the quote_id the
    // SERVER has demanded a reason for; null the rest of the time. It is set from a
    // 422 and never from a client-side comparison — see acceptQuote().
    reasonFor: null,
    accepting: null,   // quote_id of an in-flight acceptance; disables the buttons
    busy: false,
    msg: null,        // {kind:'ok'|'err', text}
    els: null
  };

  function authHeader() {
    return (O.Auth && O.Auth.authHeader) ? O.Auth.authHeader() : {};
  }

  async function loadTrucks() {
    // Best-effort: the picker degrades to free text if the objects route is
    // unavailable, because a truck the operator can NAME must still be reportable.
    try {
      const res = await fetch('/objects/Truck', { headers: authHeader() });
      if (!res.ok) return [];
      const body = await res.json();
      return (body.objects || body || []).map(t => ({
        id: t.truck_id, label: t.plate ? `${t.plate} (${t.truck_id})` : t.truck_id
      }));
    } catch (_) { return []; }
  }

  /* Returns {ok:true, cases} or {ok:false, why} — NEVER a bare empty list.
     "ยังไม่มีเคสในระบบ" and "อ่านรายการไม่ได้" are different facts, and collapsing
     the second into the first tells น้องเมย์ her colleague never opened a case when
     the truth is that the store is unreachable. On a surface whose entire purpose is
     an evidence trail, a reassuring empty state is the worst possible lie. */
  async function loadCases() {
    try {
      const res = await fetch('/api/cases?limit=20', { headers: authHeader() });
      if (!res.ok) return { ok: false, why: `อ่านรายการเคสไม่ได้ (HTTP ${res.status})` };
      return { ok: true, cases: (await res.json()).cases || [] };
    } catch (_) {
      return { ok: false, why: 'ต่อกับระบบไม่ได้ — รายการเคสอาจไม่ครบ' };
    }
  }

  async function submit(ev) {
    ev.preventDefault();
    if (state.busy) return;
    const { truck, desc, photo } = state.els;
    const truckId = (truck.value || '').trim();
    if (!truckId) {
      setMsg('err', 'เลือกรถก่อนนะครับ — เป็นข้อมูลเดียวที่จำเป็น');
      return;
    }

    setBusy(true);
    setMsg(null);
    try {
      const res = await fetch('/api/cases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeader() },
        body: JSON.stringify({ truck_id: truckId, description: (desc.value || '').trim() || null })
      });
      if (!res.ok) throw new Error(`เปิดเคสไม่สำเร็จ (HTTP ${res.status})`);
      const created = await res.json();

      let photoNote = '';
      if (photo.files && photo.files.length) {
        // The case is already saved. A photo failure downgrades the message; it
        // never discards the case or the operator's typing.
        try {
          const form = new FormData();
          form.append('file', photo.files[0]);
          const up = await fetch(`/api/cases/${encodeURIComponent(created.case_id)}/photos`, {
            method: 'POST', headers: authHeader(), body: form
          });
          if (!up.ok) {
            photoNote = up.status === 413
              ? ' — แต่รูปใหญ่เกินไป ลองถ่ายใหม่แล้วแนบเพิ่มได้'
              : ' — แต่แนบรูปไม่สำเร็จ ลองแนบใหม่ได้';
          }
        } catch (_) {
          photoNote = ' — แต่แนบรูปไม่สำเร็จ (สัญญาณอาจไม่ดี) เคสถูกบันทึกแล้ว';
        }
      }

      setMsg('ok', `เปิดเคสแล้ว: ${created.case_id}${photoNote}`);
      desc.value = ''; photo.value = '';
      await refreshCases();
    } catch (err) {
      setMsg('err', String(err.message || err));
    } finally {
      setBusy(false);
    }
  }

  function setBusy(v) {
    state.busy = v;
    if (state.els && state.els.submit) {
      state.els.submit.disabled = v;
      state.els.submit.textContent = v ? 'กำลังบันทึก…' : 'เปิดเคส';
    }
  }

  function setMsg(kind, text) {
    state.msg = text ? { kind, text } : null;
    if (!state.els) return;
    const el = state.els.msg;
    clear(el);
    if (!text) { el.className = 'case-msg'; return; }
    el.className = 'case-msg ' + (kind === 'ok' ? 'is-ok' : 'is-err');
    el.appendChild(h('span', null, text));
  }

  async function refreshCases() {
    const result = await loadCases();
    state.listError = result.ok ? null : result.why;
    state.cases = result.ok ? result.cases : [];
    renderCases();
  }

  function renderCases() {
    const el = state.els.list;
    clear(el);
    if (state.listError) {
      el.appendChild(h('div', { class: 'case-empty is-err' }, state.listError));
      return;
    }
    if (!state.cases.length) {
      el.appendChild(h('div', { class: 'case-empty' }, 'ยังไม่มีเคสในระบบ'));
      return;
    }
    state.cases.forEach(c => {
      const row = h('div', { class: 'case-row', onClick: () => selectCase(c.case_id) }, [
        h('div', { class: 'case-row-main' }, [
          h('b', { class: 'mono' }, c.truck_id),
          h('span', { class: 'case-desc' }, c.description || 'ไม่มีรายละเอียด')
        ]),
        h('div', { class: 'case-row-meta' }, [
          h('span', { class: 'mono' }, c.case_id),
          h('span', null, `${(c.photos || []).length} รูป`),
          h('span', { class: 'case-status' }, c.status)
        ])
      ]);
      if (c.case_id === state.selected) row.classList.add('is-selected');
      el.appendChild(row);
      if (c.case_id === state.selected) el.appendChild(renderEvidence());
    });
  }

  /* ---- PLAN-0096 Step 3: the quote evidence pack -------------------------
     This is what replaces "3-quote compare = scrolling LINE, sometimes lost" (Q5).
     เมย์ types the amount (Q15 — OCR is assistive at most) and attaches whatever
     arrived: PDF, LINE-exported photo, photographed paper.

     The panel shows `quote_count` AND `distinct_vendor_count` side by side, because
     three quotes from one garage is not a price comparison and the operator is the
     one who can see that at a glance. It shows counts only — no pass/fail badge —
     since the rule that judges them lands in Step 4 and inventing a verdict here
     would be a second, drifting copy of it.
     ---------------------------------------------------------------------- */
  async function selectCase(caseId) {
    state.selected = state.selected === caseId ? null : caseId;
    state.pack = null;
    // A pack message belongs to the pack that produced it. Measured in the browser
    // (s245): press ตกลงใบนี้ with no persona -> the "ยังไม่ได้เลือกบทบาท" refusal; pick a
    // persona; re-open the case -> the refusal was STILL on screen, telling a
    // now-authenticated operator they are not signed in. The same applies to a
    // reason box left open for a quote on a case nobody is looking at any more.
    // Callers that want a message AFTER a refetch set it after awaiting this.
    state.packMsg = null;
    state.reasonFor = null;
    renderCases();
    if (!state.selected) return;
    try {
      const res = await fetch(`/api/cases/${encodeURIComponent(caseId)}/evidence`,
        { headers: authHeader() });
      state.pack = res.ok ? await res.json() : { error: `อ่านหลักฐานไม่ได้ (HTTP ${res.status})` };
    } catch (_) {
      state.pack = { error: 'ต่อกับระบบไม่ได้' };
    }
    renderCases();
  }

  async function addQuote(ev) {
    ev.preventDefault();
    ev.stopPropagation();
    const form = ev.target;
    const vendor = form.querySelector('[name=vendor]').value.trim();
    const amount = form.querySelector('[name=amount]').value.trim();
    const fileEl = form.querySelector('[name=qfile]');
    if (!vendor || !amount) { setPackMsg('err', 'ใส่ชื่อร้านและยอดเงินด้วยครับ'); return; }

    const body = new FormData();
    body.append('vendor', vendor);
    body.append('amount_thb', amount);
    if (fileEl.files && fileEl.files.length) body.append('file', fileEl.files[0]);
    try {
      const res = await fetch(`/api/cases/${encodeURIComponent(state.selected)}/quotes`,
        { method: 'POST', headers: authHeader(), body });
      if (!res.ok) { setPackMsg('err', `บันทึกใบเสนอราคาไม่สำเร็จ (HTTP ${res.status})`); return; }
      const id = state.selected;
      state.selected = null;
      await selectCase(id);           // refetch the pack so the counts are the server's
    } catch (_) {
      setPackMsg('err', 'ต่อกับระบบไม่ได้');
    }
  }

  function setPackMsg(kind, text) {
    state.packMsg = { kind, text };
    renderCases();
  }

  /* ---- PLAN-0112 Step 5: ตกลงใบนี้ — the governable moment ----------------
     Quoting is not a decision; ACCEPTING is. This is the only control in Tab I
     that starts a governed run: the server's accept handler fires it (SD-5(b)),
     so the visitor never touches `POST /procedures/{id}/run`, which stays off the
     allowlist under every ruling.

     🔴 THE NON-LOWEST REASON IS THE SERVER'S RULE, ASKED FOR ONLY WHEN THE SERVER
     ASKS. `accept_quote` refuses a non-lowest acceptance without a written reason
     (422). This view does NOT re-derive that rule: it posts, and if the server
     refuses it surfaces the server's own message and opens a reason box for THAT
     quote. The alternative — comparing amounts here and pre-emptively demanding a
     reason — is a second copy of a rule that already exists, exactly what the
     quote panel above refuses to do with the three-quote verdict. A drifting copy
     would either nag for a reason nobody owed or, worse, stay silent when the
     server would have demanded one and hand เมย์ an unexplained 422.

     Re-accepting is deliberate and supported: the acceptance table is append-only,
     and a DIFFERENT quote accepted mints a new governed run (SD-2(b)), while the
     SAME quote re-accepted does not (the event key carries case + quote, G-14).
     ---------------------------------------------------------------------- */
  async function acceptQuote(quoteId, reason) {
    if (state.accepting) return;
    state.accepting = quoteId;
    state.packMsg = null;
    renderCases();
    const body = { quote_id: quoteId };
    if (reason) body.reason = reason;
    try {
      const res = await fetch(
        `/api/cases/${encodeURIComponent(state.selected)}/accepted-quote`,
        {
          method: 'POST',
          headers: Object.assign({ 'Content-Type': 'application/json' }, authHeader()),
          body: JSON.stringify(body)
        }
      );
      if (res.status === 422) {
        // The server demanded a reason (or refused the quote id). Show ITS words —
        // it names the two figures, which is what makes the demand answerable.
        //
        // `detail` is a STRING for the two HTTPExceptions this route raises, but a
        // LIST of error objects when FastAPI's own request validation rejects the
        // body. Rendering a list would print "[object Object]" at the operator, so
        // only a string is trusted and anything else falls back.
        let detail = 'ระบบขอเหตุผลก่อนบันทึก';
        try {
          const got = (await res.json()).detail;
          if (typeof got === 'string' && got) detail = got;
        } catch (_) { /* keep default */ }
        state.reasonFor = quoteId;
        state.accepting = null;
        setPackMsg('err', detail);
        return;
      }
      if (res.status === 401 || res.status === 403) {
        // Fail-closed authn: the accept route resolves a real principal. On the
        // published profile that means "pick a persona first", which is a fixable
        // situation and must not read as a system fault.
        state.accepting = null;
        // 🔴 Names the picker by the noun IT uses and says where it is. Measured in
        // the browser (s245): the control on Tab H calls itself
        // "เลือกบทบาทเพื่อดำเนินการ" (view-monitor.js), and Tab I has no persona
        // control at all — so "เลือกตัวตน" with no location left ต้อม, on the hard
        // shoulder, refused and with nowhere to go.
        setPackMsg('err', 'ยังไม่ได้เลือกบทบาท — ไปเลือกที่แท็บ Monitor แล้วกลับมากดใหม่ (ระบบต้องลงชื่อคนที่เคาะราคา)');
        return;
      }
      if (!res.ok) {
        state.accepting = null;
        setPackMsg('err', `บันทึกใบที่ตกลงไม่สำเร็จ (HTTP ${res.status})`);
        return;
      }
      const caseId = state.selected;
      state.reasonFor = null;
      state.accepting = null;
      state.selected = null;
      await selectCase(caseId);       // refetch: the pack is the server's answer
      // 🔴 Says a ROUND RAN, never "it is awaiting approval". A sub-ceiling
      // acceptance fires the run and is then dropped before the gate
      // (`test_a_sub_ceiling_acceptance_fires_but_never_reaches_the_gate`), so
      // promising an approval here would be false for exactly the cases the ฿5,000
      // ceiling is meant to keep OUT of the chain — the same over-claim card-copy.md
      // was corrected for.
      // 🔴 "แท็บ Monitor", not "หน้าติดตามงาน". Measured in the browser (s245): all
      // six published tab labels are ENGLISH — Operational Map / Ask / Procedures /
      // Monitor / Open a Case / Month-End KPI — so the Thai name pointed at a tab
      // that does not exist on screen, on the one string that hands the operator
      // from the acceptance to the payoff. card-copy.md carried the same false name
      // and is corrected in this commit.
      setPackMsg('ok', 'บันทึกใบที่ตกลงแล้ว — ระบบเดินรอบตรวจให้แล้ว ดูรอบนี้ได้ที่แท็บ Monitor');
    } catch (_) {
      state.accepting = null;
      setPackMsg('err', 'ต่อกับระบบไม่ได้');
    }
  }

  function submitReason(ev) {
    ev.preventDefault();
    ev.stopPropagation();
    const quoteId = state.reasonFor;
    const reason = ev.target.querySelector('[name=areason]').value.trim();
    if (!reason) { setPackMsg('err', 'ใส่เหตุผลด้วยครับ ระบบต้องบันทึกว่าทำไมไม่เอาใบที่ถูกที่สุด'); return; }
    acceptQuote(quoteId, reason);
  }

  function renderEvidence() {
    const pack = state.pack;
    if (!pack) return h('div', { class: 'case-pack' }, 'กำลังโหลดหลักฐาน…');
    if (pack.error) return h('div', { class: 'case-pack is-err' }, pack.error);

    const quoteForm = h('form', { class: 'pack-form', onSubmit: addQuote }, [
      h('input', { class: 'case-input', name: 'vendor', placeholder: 'ร้าน / อู่' }),
      h('input', { class: 'case-input', name: 'amount', type: 'text',
                   inputmode: 'decimal', placeholder: 'ยอดเงิน (บาท)' }),
      h('input', { class: 'case-input', name: 'qfile', type: 'file',
                   accept: 'image/*,application/pdf', capture: 'environment' }),
      h('button', { class: 'case-submit', type: 'submit' }, 'เพิ่มใบเสนอราคา')
    ]);

    const children = [
      h('div', { class: 'pack-counts' }, [
        h('span', null, [h('b', null, String(pack.quote_count)), ' ใบเสนอราคา']),
        h('span', null, [h('b', null, String(pack.distinct_vendor_count)), ' ร้าน']),
        h('span', null, `${pack.attachment_count} เอกสารแนบ`),
        pack.has_sole_source_justification
          ? h('span', { class: 'pack-flag' }, 'มีเหตุผลซื้อร้านเดียว')
          : null
      ].filter(Boolean))
    ];

    // ใบที่ตกลง, read from the SERVER's pack — never from what this view just
    // posted. `accepted_quote_id` is the latest acceptance on an append-only table.
    const acceptedId = pack.accepted_quote_id || null;
    if (acceptedId) {
      children.push(h('div', { class: 'pack-accepted' }, [
        h('span', null, 'ใบที่ตกลง'),
        h('b', null, pack.accepted_vendor || acceptedId),
        h('b', { class: 'mono' }, Number(pack.accepted_amount_thb || 0).toLocaleString('th-TH', {
          minimumFractionDigits: 2, maximumFractionDigits: 2
        })),
        // Present only when the cheapest was NOT taken — the write path refuses a
        // non-lowest acceptance without one, so showing it is showing a record.
        pack.accepted_reason ? h('span', { class: 'pack-reason' }, pack.accepted_reason) : null
      ].filter(Boolean)));
    }

    (pack.quotes || []).forEach(q => {
      const isAccepted = acceptedId && q.quote_id === acceptedId;
      children.push(h('div', { class: 'pack-quote' }, [
        h('span', null, q.vendor),
        // Always two decimals. The stored value is exact Decimal; a display that
        // renders 45500.50 as "45,500.5" makes เมย์ second-guess it against the
        // paper in her hand, which is the opposite of what this panel is for.
        h('b', { class: 'mono' }, Number(q.amount_thb).toLocaleString('th-TH', {
          minimumFractionDigits: 2, maximumFractionDigits: 2
        })),
        h('span', { class: 'pack-doc' }, q.attachment ? 'มีเอกสาร' : 'ยังไม่มีเอกสาร'),
        // The accepted quote shows a STATE, not a disabled button: re-accepting the
        // same quote is a no-op the server dedups (G-14), so offering it would
        // promise an action that produces nothing.
        isAccepted
          ? h('span', { class: 'pack-agreed' }, 'ตกลงใบนี้แล้ว')
          : h('button', {
              class: 'pack-accept',
              type: 'button',
              disabled: state.accepting ? 'disabled' : null,
              onClick: (e) => { e.stopPropagation(); acceptQuote(q.quote_id, null); }
            }, state.accepting === q.quote_id ? 'กำลังบันทึก…' : 'ตกลงใบนี้')
      ]));

      // The reason box appears under the quote the SERVER refused, and only there.
      if (state.reasonFor === q.quote_id) {
        children.push(h('form', { class: 'pack-form', onSubmit: submitReason }, [
          h('input', {
            class: 'case-input', name: 'areason',
            placeholder: 'ทำไมไม่เอาใบที่ถูกที่สุด (เช่น รออะไหล่ไม่ได้)'
          }),
          h('button', { class: 'case-submit', type: 'submit' }, 'ยืนยันตกลงใบนี้')
        ]));
      }
    });

    if (state.packMsg) {
      children.push(h('div', {
        class: 'case-msg ' + (state.packMsg.kind === 'ok' ? 'is-ok' : 'is-err')
      }, state.packMsg.text));
    }
    children.push(quoteForm);
    return h('div', { class: 'case-pack', onClick: (e) => e.stopPropagation() }, children);
  }

  async function mount(container) {
    clear(container);

    const truck = h('select', { class: 'case-input', id: 'caseTruck' });
    const desc = h('textarea', {
      class: 'case-input', id: 'caseDesc', rows: 3,
      placeholder: 'อาการ / ที่เกิดเหตุ (ไม่ใส่ก็ได้)'
    });
    const photo = h('input', {
      class: 'case-input', id: 'casePhoto', type: 'file',
      accept: 'image/*,application/pdf', capture: 'environment'
    });
    const submitBtn = h('button', { class: 'case-submit', type: 'submit' }, 'เปิดเคส');
    const msg = h('div', { class: 'case-msg' });
    const list = h('div', { class: 'case-list' });

    state.els = { truck, desc, photo, submit: submitBtn, msg, list };

    const form = h('form', { class: 'case-form', onSubmit: submit }, [
      h('label', { class: 'case-label', for: 'caseTruck' }, 'คันไหน *'),
      truck,
      h('label', { class: 'case-label', for: 'caseDesc' }, 'เกิดอะไรขึ้น'),
      desc,
      h('label', { class: 'case-label', for: 'casePhoto' }, 'รูป / ใบเสนอราคา'),
      photo,
      submitBtn,
      msg
    ]);

    // ---- D2.4 case-persistence disclosure, AT THE POINT OF CAPTURE ----
    // PLAN-0106 (ADR-0037 D2.4). SD-2 ruled BOTH surfaces and made THIS one
    // load-bearing: it sits between the heading and the first input, so it is
    // read by the person about to type rather than by whoever scrolled past a
    // banner. Published profile only — on the dev console every claim below is
    // false, and AC-4 asserts its absence there.
    //
    // 🔴 This is NOT the D6 banner and must never be folded into it. ADR-0037 D3
    // refuses to widen D6, which is the prompt-log regime; this covers the CASE
    // dataset, whose reader set is far wider. The two 90-day numbers are an
    // INDEPENDENT coincidence by ruling (PLAN-0105 LOCKED-1) and the code guards
    // that independence — one merged sentence would fuse in prose exactly what
    // the tests keep apart.
    //
    // The synthetic line is RESTATED here deliberately (SD-1 sub-question 1,
    // Cray typed s232), duplicating the persistent banner's lead. That is the
    // accepted cost of the point-of-capture principle: the banner may be
    // scrolled away or banner-blind by minute 1, and this is the riskiest input
    // on the whole published surface.
    const wrapKids = [
      h('div', { class: 'case-head' }, [
        h('h2', null, 'เปิดเคสซ่อม'),
        h('p', { class: 'case-sub' },
          'บันทึกตั้งแต่นาทีแรก — เลือกรถอย่างเดียวก็พอ ที่เหลือใส่ทีหลังได้')
      ])
    ];
    if (O.isPublished()) {
      wrapKids.push(h('div', { class: 'case-notice', role: 'note' }, [
        h('b', null, 'ข้อมูลสาธิตเป็นข้อมูลสังเคราะห์ — กรุณาอย่ากรอกข้อมูลส่วนบุคคลจริง'),
        ' ',
        h('span', null,
          'ข้อความและรูปถ่ายที่กรอกในใบแจ้งซ่อมจะถูกบันทึกในฐานข้อมูลของระบบนี้ ' +
          'และถูกลบภายใน 90 วัน — ข้อความในใบแจ้งซ่อม ผู้เข้าชมทุกคนของระบบนี้อ่านได้ ' +
          'ไม่ใช่เฉพาะผู้ดูแลระบบ')
      ]));
    }
    wrapKids.push(
      form,
      h('div', { class: 'case-head' }, [h('h3', null, 'เคสล่าสุด')]),
      list
    );

    container.appendChild(h('div', { class: 'case-wrap' }, wrapKids));

    state.trucks = await loadTrucks();
    clear(truck);
    truck.appendChild(h('option', { value: '' }, '— เลือกรถ —'));
    state.trucks.forEach(t => truck.appendChild(h('option', { value: t.id }, t.label)));
    if (!state.trucks.length) {
      // No roster reachable: never block the report — let them type the id.
      const manual = h('input', {
        class: 'case-input', id: 'caseTruck', type: 'text',
        placeholder: 'รหัส/ทะเบียนรถ'
      });
      truck.replaceWith(manual);
      state.els.truck = manual;
    }

    await refreshCases();
    if (state.msg) setMsg(state.msg.kind, state.msg.text);
  }

  O.ViewCase = { mount };
})();
