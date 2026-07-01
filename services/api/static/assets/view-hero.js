/* ============================================================
   OCT — Hero governance-moment view (PLAN-0045 Step 2).

   The read-only demo screen for the hero beat: a governed emergency-sourcing
   run hitting the AT-2 gate. Binds the THREE shipped A1b structured fields
   DIRECTLY, no reshape (SD-2): doa_tier · PrincipalSoDVerdict · governed_decision,
   from GET /demo/hero/governance; plus the ฿-impact ledger from
   GET /demo/hero/impact. Per SD-2 it reuses view-procedures.js's decomposition
   PATTERN (a pure joiner → a render model → static cards) with a thin
   purpose-built `governanceMoment(audit)` joiner over the three fields.

   governed ≠ generated: the tier / SoD / control ties are the DETERMINISTIC
   engine's output (no LLM) — the render just draws the audit → control →
   principal join the engine already resolved. ALL ฿ FIGURES DEMO-GRADE.
   ============================================================ */
(function () {
  'use strict';
  const O = window.OCT;
  const { h, clear, icon } = O;

  /* ---- formatting ---- */
  function thb(value) {
    // value is a Decimal-as-string ("288000") or a number; format ฿ with separators.
    const n = Number(value);
    return '฿' + (Number.isFinite(n) ? n.toLocaleString('en-US') : String(value));
  }
  function thbM(value) {
    const n = Number(value);
    return Number.isFinite(n) ? '฿' + (n / 1e6).toFixed(2) + 'M' : String(value);
  }

  /* ---- THE JOINER (SD-2): the shipped audit → a render model, join resolved ----
     Pure decomposition over the three fields; verifies the exact shipped join keys
     (control_ref.id == resolved_tier_id; sod constraint_id; principal_id == Person PK). */
  function governanceMoment(poAudit) {
    const doa = (poAudit.doa_tier && poAudit.doa_tier[0]) || {};
    const sod = poAudit.sod || {};
    const gds = poAudit.governed_decision || [];
    const doaTie = gds.find((g) => g.control_ref && g.control_ref.kind === 'doa_tier') || null;
    const sodTie = gds.find((g) => g.control_ref && g.control_ref.kind === 'sod') || null;
    return {
      po: poAudit.po_id,
      amount: doa.amount || { value: '0', currency: 'THB' },
      band: doa.band || { min: null, max: null },
      role: doa.resolved_tier_id, // the approver ROLE (e.g. CONTROLLER), NOT the CSV tier_id
      declaredTier: poAudit.declared_tier_id, // the CSV label (TIER-CTRL) — display only
      approverId: doa.resolved_approver_id,
      sodRequired: doa.sod_required,
      offAvl: poAudit.is_off_avl_override,
      sod: sod,
      doaTie: doaTie && {
        controlId: doaTie.control_ref.id,
        principalId: doaTie.principal_id,
        joins: doaTie.control_ref.id === doa.resolved_tier_id
      },
      sodTie: sodTie && {
        controlId: sodTie.control_ref.id,
        principalId: sodTie.principal_id,
        joins: sodTie.control_ref.id === sod.constraint_id
      }
    };
  }

  /* ---- small DOM helpers (the pv-* idiom, hero-scoped) ---- */
  function kv(label, value, cls) {
    return h('div', { class: 'hero-kv' }, [
      h('span', { class: 'hero-k mono' }, label),
      h('span', { class: 'hero-v ' + (cls || '') }, value)
    ]);
  }
  function badge(text, cls) {
    return h('span', { class: 'hero-badge ' + (cls || '') }, text);
  }
  function card(title, sub, children) {
    return h('div', { class: 'hero-card' }, [
      h('div', { class: 'hero-card-head' }, [
        h('div', { class: 'hero-card-title' }, title),
        sub ? h('div', { class: 'hero-card-sub faint' }, sub) : null
      ]),
      h('div', { class: 'hero-card-body' }, children)
    ]);
  }

  /* ---- the DOA gate card (AC-3): ฿ crosses the Manager ceiling → CONTROLLER ---- */
  function renderDoaCard(m) {
    // the Manager ceiling = one baht below the Controller floor (half-open band min)
    const ceiling = Number(m.band.min) - 1;
    return card('DOA tier — the ฿ decides who signs', 'audit["doa_tier"] · deterministic, no LLM', [
      h('div', { class: 'hero-amount' }, [
        h('span', { class: 'hero-amount-val' }, thb(m.amount.value)),
        badge('OFF-AVL EMERGENCY', m.offAvl ? 's-warn' : 's-neutral')
      ]),
      h('div', { class: 'hero-cross' }, [
        h('span', null, thb(m.amount.value)),
        h('span', { class: 'hero-arrow' }, icon('flow', { width: 14, height: 14 })),
        h('span', { class: 'faint' }, 'crosses the ' + thb(ceiling) + ' Manager ceiling →'),
        h('span', { class: 'hero-role s-crit' }, m.role)
      ]),
      h('div', { class: 'hero-grid' }, [
        kv('resolved_tier_id', m.role, 'mono s-crit'),
        kv('required_role', m.role, 'mono'),
        kv('band', '[' + m.band.min + ', ' + (m.band.max == null ? '∞' : m.band.max) + ')', 'mono'),
        kv('sod_required', String(m.sodRequired), 'mono'),
        kv('resolved_approver_id', m.approverId || '—', 'mono'),
        kv('tier label (CSV)', m.declaredTier + ' — display only', 'mono faint')
      ])
    ]);
  }

  /* ---- the SoD card (AC-4): requester ≠ approver → governed ---- */
  function renderSodCard(m) {
    const sod = m.sod;
    const req = sod.requester || {};
    const appr = sod.approver || {};
    return card('Separation of Duties — the requester cannot self-approve',
      'PrincipalSoDVerdict · fail-closed run-check', [
        h('div', { class: 'hero-sod-row' }, [
          h('div', { class: 'hero-principal' }, [
            h('div', { class: 'hero-p-role mono' }, 'requester'),
            h('div', { class: 'hero-p-name' }, req.name || req.person_id || '—'),
            h('div', { class: 'hero-p-id mono faint' }, req.person_id || '')
          ]),
          h('div', { class: 'hero-neq ' + (sod.governed ? 's-ok' : 's-crit') }, sod.governed ? '≠' : '='),
          h('div', { class: 'hero-principal' }, [
            h('div', { class: 'hero-p-role mono' }, 'approver'),
            h('div', { class: 'hero-p-name' }, appr.name || appr.person_id || '—'),
            h('div', { class: 'hero-p-id mono faint' }, appr.person_id || '')
          ])
        ]),
        h('div', { class: 'hero-sod-verdict' }, [
          badge(sod.governed ? 'GOVERNED — distinct principals' : 'BLOCKED — collapse', sod.governed ? 's-ok' : 's-crit'),
          kv('constraint_id', sod.constraint_id || '—', 'mono')
        ])
      ]);
  }

  /* ---- the join card (AC-5): audit → control → principal, on the shipped keys ---- */
  function renderJoinCard(m) {
    const ties = [];
    if (m.doaTie) ties.push(joinRow('doa_tier', m.doaTie, m.role, 'resolved_tier_id'));
    if (m.sodTie) ties.push(joinRow('sod', m.sodTie, m.sod.constraint_id, 'constraint_id'));
    return card('governed_decision — every decision tied to the control that governed it',
      'audit["governed_decision"] · join keys resolved, no fuzzy match', ties);
  }
  function joinRow(kind, tie, expectId, keyName) {
    return h('div', { class: 'hero-join' }, [
      h('span', { class: 'hero-join-kind mono' }, kind),
      h('span', { class: 'hero-chip mono' }, 'control_ref.id = ' + tie.controlId),
      h('span', { class: 'hero-arrow' }, '⇄'),
      h('span', { class: 'hero-chip mono' }, keyName + ' = ' + expectId),
      tie.joins ? badge('JOINS', 's-ok') : badge('MISMATCH', 's-crit'),
      h('span', { class: 'hero-arrow' }, '→'),
      h('span', { class: 'hero-chip mono' }, 'principal_id = ' + tie.principalId)
    ]);
  }

  /* ---- the contrast card (AC-7): ฿99k stays at MANAGER, no escalation ---- */
  function renderContrast(cm) {
    return h('div', { class: 'hero-contrast' }, [
      h('span', { class: 'hero-contrast-lbl faint' }, 'Contrast · ' + cm.po + ' ' + thb(cm.amount.value) + ' emergency →'),
      h('span', { class: 'hero-role s-info' }, cm.role),
      h('span', { class: 'faint' }, '— no Controller escalation. The gate is data-driven, not hardcoded.')
    ]);
  }

  /* ---- the ฿-impact ledger (AC-6): baseline → governed ---- */
  function renderLedger(led) {
    const b = led.baseline, g = led.governed;
    return card('฿-impact — governed sourcing turned a line-stop into a decision',
      'GET /demo/hero/impact · server-computed', [
        h('div', { class: 'hero-ledger' }, [
          ledgerSide('Baseline — wait on-AVL', b, 's-crit', led.currency),
          h('div', { class: 'hero-ledger-arrow' }, icon('flow', { width: 18, height: 18 })),
          ledgerSide('Governed — off-AVL emergency', g, 's-ok', led.currency)
        ]),
        h('div', { class: 'hero-ledger-foot' }, [
          kv('expedite premium (price of speed)', thb(led.expedite_premium_thb), 's-warn'),
          kv('avoided downtime', thbM(led.avoided_downtime_thb), 's-ok'),
          kv('net benefit', thbM(led.net_benefit_thb), 's-ok')
        ])
      ]);
  }
  function ledgerSide(title, side, cls, currency) {
    return h('div', { class: 'hero-ledger-side' }, [
      h('div', { class: 'hero-ledger-title ' + cls }, title),
      h('div', { class: 'hero-ledger-big ' + cls }, thbM(side.exposure_thb)),
      h('div', { class: 'hero-ledger-detail faint mono' }, [
        h('div', null, side.supplier_id + ' · ' + side.lead_time_days + 'd lead'),
        h('div', null, 'downtime ' + thb(side.downtime_thb)),
        h('div', null, 'part ' + thb(side.part_cost_thb))
      ])
    ]);
  }

  function render(container, gov, ledger) {
    clear(container);
    const hero = governanceMoment(gov.hero);
    const contrast = governanceMoment(gov.contrast);

    const head = h('div', { class: 'hero-head' }, [
      h('div', { class: 'hero-title' }, [
        icon('receipt', { width: 18, height: 18 }),
        h('b', null, 'Governance Moment'),
        h('span', { class: 'faint' }, '· Emergency Sourcing (Fastenal)')
      ]),
      h('div', { class: 'hero-badges' }, [
        badge(gov.source === 'offline-fixture' ? 'OFFLINE FIXTURE' : 'LIVE · MS-S1', 's-info'),
        badge('DEMO-GRADE · PROVISIONAL', 's-warn')
      ])
    ]);

    const scenario = h('div', { class: 'hero-scenario faint' },
      'A CNC machining center (' + ledger.asset_id + ') is DOWN → needs a critical spindle bearing set ('
      + ledger.part_id + ') → the only fast-enough source is an off-AVL emergency supplier ('
      + hero.sod.approver.person_id + ' approves) at ' + thb(hero.amount.value) + '.');

    container.appendChild(head);
    container.appendChild(scenario);
    container.appendChild(renderDoaCard(hero));
    container.appendChild(renderSodCard(hero));
    container.appendChild(renderJoinCard(hero));
    container.appendChild(renderContrast(contrast));
    container.appendChild(renderLedger(ledger));
  }

  async function mount(container) {
    clear(container);
    const body = h('div', { class: 'hero-view' });
    container.appendChild(body);
    body.appendChild(O.loadingState ? O.loadingState('Loading the governance moment…') : h('div', null, 'Loading…'));
    try {
      const [gov, ledger] = await Promise.all([O.Hero.governance(), O.Hero.impact()]);
      render(body, gov, ledger);
    } catch (e) {
      clear(body);
      const msg = String((e && e.message) || e) +
        ' — the hero-demo endpoints (/demo/hero/*) require the live backend (no embedded demo).';
      body.appendChild(O.errorState
        ? O.errorState('Could not load the governance moment', msg, () => mount(container))
        : h('div', { class: 'hero-err' }, msg));
    }
  }

  window.OCT.ViewHero = { mount, governanceMoment };
})();
