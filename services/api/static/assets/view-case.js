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

    (pack.quotes || []).forEach(q => {
      children.push(h('div', { class: 'pack-quote' }, [
        h('span', null, q.vendor),
        // Always two decimals. The stored value is exact Decimal; a display that
        // renders 45500.50 as "45,500.5" makes เมย์ second-guess it against the
        // paper in her hand, which is the opposite of what this panel is for.
        h('b', { class: 'mono' }, Number(q.amount_thb).toLocaleString('th-TH', {
          minimumFractionDigits: 2, maximumFractionDigits: 2
        })),
        h('span', { class: 'pack-doc' }, q.attachment ? 'มีเอกสาร' : 'ยังไม่มีเอกสาร')
      ]));
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

    container.appendChild(h('div', { class: 'case-wrap' }, [
      h('div', { class: 'case-head' }, [
        h('h2', null, 'เปิดเคสซ่อม'),
        h('p', { class: 'case-sub' },
          'บันทึกตั้งแต่นาทีแรก — เลือกรถอย่างเดียวก็พอ ที่เหลือใส่ทีหลังได้')
      ]),
      form,
      h('div', { class: 'case-head' }, [h('h3', null, 'เคสล่าสุด')]),
      list
    ]));

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
