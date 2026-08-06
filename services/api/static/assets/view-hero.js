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
  function tile(label, value, cls, sublabel) {
    const kids = [
      h('div', { class: 'hero-kpi-label' }, label),
      h('div', { class: 'hero-kpi-value ' + (cls || '') }, value)
    ];
    if (sublabel) kids.push(h('div', { class: 'hero-kpi-sub faint' }, sublabel));
    return h('div', { class: 'hero-kpi-tile' }, kids);
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

  /* ---- PLAN-0073 (SD-3): the typed Box-4 economic-impact PROVENANCE strip. Coexists UNDER
     the ledger (ADR-0030 D2 — the ledger card is unchanged); the ฿ figure EQUALS the ledger's,
     so this adds the audit-grade WHY (kind · assumptions · basis_refs), not a new number. An
     always-visible PROVISIONAL badge (s74 trust-shape) + a "show provenance" toggle reusing the
     reasoning-trace toggle idiom (the detail starts hidden). ---- */
  function renderEconomicProvenance(impact) {
    if (!impact) return null;
    const detail = h('div', { class: 'hero-econ-detail faint mono' });
    detail.hidden = true;
    (impact.assumptions || []).forEach(function (a) {
      detail.appendChild(h('div', { class: 'hero-econ-line' }, '• ' + a));
    });
    (impact.basis_refs || []).forEach(function (r) {
      detail.appendChild(h('div', { class: 'hero-econ-line' }, 'basis · ' + r));
    });
    const toggle = h('button', { class: 'hero-badge hero-toggle', type: 'button' }, 'show provenance');
    toggle.addEventListener('click', function () {
      detail.hidden = !detail.hidden;
      toggle.textContent = detail.hidden ? 'show provenance' : 'hide provenance';
    });
    return h('div', { class: 'hero-econ' }, [
      h('div', { class: 'hero-econ-head' }, [
        badge(impact.kind, 's-info'),
        badge('PROVISIONAL', 's-warn'),
        h('span', { class: 'faint' },
          'Box-4 economic impact · net benefit ' + thbM(impact.net_benefit_thb) + ' · audit-grade provenance'),
        toggle
      ]),
      detail
    ]);
  }

  /* ---- the ฿-impact ledger (AC-6): baseline → governed ---- */
  function renderLedger(led) {
    const b = led.baseline, g = led.governed;
    const body = [
      h('div', { class: 'hero-ledger' }, [
        ledgerSide('Baseline — wait on-AVL', b, 's-crit', led.currency),
        h('div', { class: 'hero-ledger-arrow' }, icon('flow', { width: 18, height: 18 })),
        ledgerSide('Governed — off-AVL emergency', g, 's-ok', led.currency)
      ]),
      h('div', { class: 'hero-ledger-foot' }, [
        tile('expedite premium', thb(led.expedite_premium_thb), 's-warn', 'price of speed'),
        tile('avoided downtime', thbM(led.avoided_downtime_thb), 's-ok'),
        tile('net benefit', thbM(led.net_benefit_thb), 's-ok',
          'exposure ' + thbM(b.exposure_thb) + ' → ' + thbM(g.exposure_thb))
      ])
    ];
    // PLAN-0073 (SD-3 coexist): the typed facet provenance strip under the ledger, when present.
    const prov = renderEconomicProvenance(led.economic_impact);
    if (prov) body.push(prov);
    return card('฿-impact — governed sourcing turned a line-stop into a decision',
      'GET /demo/hero/impact · server-computed', body);
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

  /* ---- PLAN-0057 (AC-3b): the beat-1 "sense" cue — the event that auto-fired the run.
     Reuses the hero-scenario line idiom + a warning badge; no new CSS. ---- */
  function renderSenseCue(trigger) {
    const t = trigger || {};
    const entity = (t.entity_ids && t.entity_ids[0]) || '—';
    return h('div', { class: 'hero-scenario' }, [
      badge('SENSED · event', 's-warn'),
      h('span', { class: 'faint' }, ' asset-failure on '),
      h('span', { class: 'mono' }, entity),
      h('span', { class: 'faint' }, ' → auto-classified '),
      h('span', { class: 'mono' }, t.event_kind || '—'),
      h('span', { class: 'faint' }, ' → auto-fired the governed run · detected '),
      h('span', { class: 'mono faint' }, t.detected_at || '—')
    ]);
  }

  /* ---- PLAN-0072 (beat 3): the "act" panel GENUINELY resolves the parked DOA gate.
     SD-A(b): drives the REAL production POST /runs/{id}/gate/resolve (authenticated approver,
     RF-1); SD-B(b): approve AND reject as real affordances; SD-D(a): inline login here — the
     approver authenticates, THEN signs. The render binds to the PERSISTED GateResolveResponse
     (run_status), never a client literal; a reject renders the honest shipped semantics (no PO
     issued, decision recorded, run completed — reject = continue+record, not a rejected terminal). ---- */
  function renderActPanel(hero, host, runId) {
    const apprId = (hero.sod && hero.sod.approver && hero.sod.approver.person_id) || 'appr-pm';
    const reqId = (hero.sod && hero.sod.requester && hero.sod.requester.person_id) || 'req-planner';
    const auth = O.Auth;
    const body = h('div', { class: 'hero-badges' }, []);

    function addReplay() {
      const replay = h('button', { class: 'hero-badge hero-toggle', type: 'button' }, '↺ Replay');
      replay.addEventListener('click', function () { mount(host, { mode: 'event' }); });
      body.appendChild(replay);
    }

    function renderLogin() {
      clear(body);
      if (!auth) {
        body.appendChild(h('span', { class: 'faint' }, 'Operate unavailable — auth module not loaded.'));
        return;
      }
      const keyIn = h('input', { class: 'mon-auth-in mono', type: 'password', autocomplete: 'off', placeholder: 'operator API key' });
      const idIn = h('input', { class: 'mon-auth-in', type: 'text', autocomplete: 'off', placeholder: 'identity (e.g. ' + apprId + ')' });
      const err = h('span', { class: 'mon-auth-err', role: 'status', 'aria-live': 'polite' });
      const doLogin = async function () {
        try { await auth.login(keyIn.value, idIn.value); renderActions(); }
        catch (e) { err.textContent = String((e && e.message) || e); }
      };
      keyIn.addEventListener('keydown', function (e) { if (e.key === 'Enter') doLogin(); });
      idIn.addEventListener('keydown', function (e) { if (e.key === 'Enter') doLogin(); });
      const loginBtn = h('button', { class: 'hero-badge hero-toggle', type: 'button' }, 'Log in');
      loginBtn.addEventListener('click', doLogin);
      body.appendChild(h('span', { class: 'faint' }, 'Log in to sign the gate: '));
      body.appendChild(keyIn);
      body.appendChild(idIn);
      body.appendChild(loginBtn);
      body.appendChild(err);
    }

    function renderActions() {
      clear(body);
      body.appendChild(h('span', { class: 'faint' }, 'Signed in as ' + (auth.identity() || apprId) + ' · '));
      const approve = h('button', { class: 'hero-badge hero-toggle', type: 'button' }, icon('check', { width: 14, height: 14 }));
      approve.appendChild(document.createTextNode(' Approve'));
      approve.addEventListener('click', function () { decide('approve'); });
      const reject = h('button', { class: 'hero-badge hero-toggle', type: 'button' }, '✗ Reject');
      reject.addEventListener('click', function () { decide('reject'); });
      const logout = h('button', { class: 'hero-badge hero-toggle', type: 'button' }, 'Log out');
      logout.addEventListener('click', function () { auth.logout(); renderLogin(); });
      body.appendChild(approve);
      body.appendChild(reject);
      body.appendChild(logout);
    }

    async function decide(kind) {
      clear(body);
      body.appendChild(badge('resolving…', 's-info'));  // OQ-3: optimistic paint = a loading state only
      try {
        const detail = await O.Hero.runDetail(runId);
        const decisions = {};
        (detail.proposals || []).forEach(function (p) { decisions[p.action_id] = kind; });
        const out = await O.Hero.resolve(runId, detail.suspended_step, decisions);
        renderOutcome(kind, out);
      } catch (e) { renderError(e); }
    }

    function renderOutcome(kind, out) {
      clear(body);
      const who = auth.identity() || apprId;
      const status = (out && out.run_status) || 'completed';
      if (kind === 'approve') {
        body.appendChild(badge('✓ COMPLETED · approved by ' + who, 's-ok'));
        body.appendChild(h('span', { class: 'faint' },
          ' gate resolved → run ' + status + ' · SoD governed (' + reqId + ' ≠ ' + who + ')'));
      } else {
        body.appendChild(badge('✗ REJECTED · by ' + who, 's-warn'));
        body.appendChild(h('span', { class: 'faint' },
          ' no PO created (handler never fired) · decision recorded on the audit trace · run ' + status));
      }
      addReplay();
    }

    function renderError(e) {
      clear(body);
      const st = e && e.status;
      let msg = String((e && e.message) || e);
      if (st === 401) msg = 'Not authenticated — log in as the approver (' + apprId + ') first.';
      else if (st === 403) msg = 'Refused — SoD: the requester (' + reqId + ') cannot also approve.';
      body.appendChild(badge('resolve failed', 's-warn'));
      body.appendChild(h('span', { class: 'faint' }, ' ' + msg + ' '));
      const retry = h('button', { class: 'hero-badge hero-toggle', type: 'button' }, '↺ Try again');
      retry.addEventListener('click', function () {
        if (auth && auth.isLoggedIn()) renderActions(); else renderLogin();
      });
      body.appendChild(retry);
    }

    if (auth && auth.isLoggedIn()) renderActions(); else renderLogin();
    return card('Act — the human DOA gate', 'a distinct approver authenticates, then signs · SoD (RF-3)', [body]);
  }

  /* ---- FLEET-BRANCH-START · PLAN-0098 Step 5 (fleet_maintenance View G) --------------
     Keyed on the impact payload's `vertical` discriminant. FleetHeroImpact carries it;
     HeroImpactLedger cannot (ADR-0030 D2 forbids editing that model), so procurement is
     the ABSENCE case — never a second literal to keep in sync.

     STATED DEVIATION from the PLAN's D-D. D-D reads: "the joiner (:35-62) binds only
     doa_tier / sod / governed_decision, all of which fleet produces". Measured, that is
     not so — governanceMoment also binds po_id (:42), declared_tier_id (:46) and
     is_off_avl_override (:49), none of which fleet's audit emits. Reusing it verbatim
     would print "undefined — display only" in the DOA card and "Contrast · undefined"
     in the contrast line. Hence fleetMoment below. The SoD card and the join card ARE
     reused verbatim — those two really do read only the shared fields.

     SD-2 (Cray, 2026-07-31): the assumptions strip renders ALWAYS VISIBLE here, never
     behind the donor's provenance toggle. Fleet's entire governed delta is
     assumption-derived, so hiding the assumption hides the number's nature.

     SD-3(c) (Cray, 2026-07-31): lead with the MEASURED quote, show the modelled recovery
     labelled as understated, AND carry the owner's origin story as NARRATIVE COPY ONLY.
     No money figure is written as a literal anywhere below — every rendered amount flows
     from the payload through thb(). AC-9 is the lexical fence that keeps it that way.

     No new CSS class is introduced: every class used here already carries a rule in
     hero.css, so the PLAN-0099-era class contract (tests/api/test_css_class_contract.py)
     needs no allowlist edit and hero.css is untouched.
     ---------------------------------------------------------------------------------- */

  function fleetMoment(audit) {
    const doa = (audit.doa_tier && audit.doa_tier[0]) || {};
    const sod = audit.sod || {};
    const gds = audit.governed_decision || [];
    const doaTie = gds.find((g) => g.control_ref && g.control_ref.kind === 'doa_tier') || null;
    const sodTie = gds.find((g) => g.control_ref && g.control_ref.kind === 'sod') || null;
    return {
      truck: audit.truck_id,
      caseId: audit.case_id,
      severity: audit.severity,
      amount: audit.amount || { value: null, currency: 'THB' },
      band: doa.band || { min: null, max: null },
      role: doa.resolved_tier_id,
      approverId: doa.resolved_approver_id,
      sodRequired: doa.sod_required,
      sod: sod,
      ruleGate: audit.three_quote || null,
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

  /* the fleet DOA card — the quote decides who signs; no OFF-AVL / CSV-tier nouns */
  function renderFleetDoaCard(m) {
    return card('DOA tier — the repair quote decides who signs',
      'audit["doa_tier"] · deterministic, no LLM', [
        h('div', { class: 'hero-amount' }, [
          h('span', { class: 'hero-amount-val' }, thb(m.amount.value)),
          badge('REPAIR QUOTE · MEASURED', 's-info')
        ]),
        h('div', { class: 'hero-cross' }, [
          h('span', null, thb(m.amount.value)),
          h('span', { class: 'hero-arrow' }, icon('flow', { width: 14, height: 14 })),
          h('span', { class: 'faint' }, 'clears the ' + thb(m.band.min) + ' rung →'),
          h('span', { class: 'hero-role s-crit' }, m.role)
        ]),
        h('div', { class: 'hero-grid' }, [
          kv('truck_id', m.truck || '—', 'mono'),
          kv('case_id', m.caseId || '—', 'mono'),
          kv('resolved_tier_id', m.role, 'mono s-crit'),
          kv('band', '[' + m.band.min + ', ' + (m.band.max == null ? '∞' : m.band.max) + ')', 'mono'),
          kv('sod_required', String(m.sodRequired), 'mono'),
          kv('resolved_approver_id', m.approverId || '—', 'mono')
        ])
      ]);
  }

  /* the fleet-only third card: the three-quote rule gate, with its STAMPED basis.
     Both repairs pass the signal; only the basis says whether the pass was earned by
     collecting quotes or granted because the rule never applied. A card showing the
     boolean alone would render those two as the same thing. */
  function renderFleetRuleGate(hero, contrast) {
    function gateRow(label, gate) {
      if (!gate) return h('div', { class: 'hero-join' }, h('span', { class: 'faint' }, label + ' · no rule-gate verdict'));
      return h('div', { class: 'hero-join' }, [
        h('span', { class: 'hero-join-kind mono' }, label),
        badge(gate.signal ? 'PASS' : 'BLOCKED', gate.signal ? 's-ok' : 's-crit'),
        h('span', { class: 'hero-arrow' }, '←'),
        h('span', { class: 'hero-chip mono' }, 'basis = ' + (gate.basis || '—')),
        h('span', { class: 'faint' },
          gate.basis === 'three_quotes'
            ? 'earned — the quotes were actually collected'
            : 'granted — the rule never applied to this repair')
      ]);
    }
    const g = hero.ruleGate;
    return card('three_quote — the partner’s own กฎเหล็ก, run as a rule gate',
      'audit["three_quote"] · basis stamped at write time, not recomputed', [
        gateRow('hero', hero.ruleGate),
        gateRow('contrast', contrast.ruleGate),
        h('div', { class: 'hero-grid' }, [
          kv('criterion', (g && g.criterion) || '—', 'mono'),
          kv('blocks_po', String(g && g.blocks_po), 'mono')
        ]),
        // The authored rule is a sentence, not a value. Measured in the hero-kv grid it
        // rendered right-aligned across 54px against a 19px row — prose wearing a
        // key-value slot. It reads as what it is on its own full-width line.
        h('div', { class: 'hero-card-sub faint' }, 'authored rule · ' + ((g && g.spec) || '—'))
      ]);
  }

  function renderFleetContrast(cm) {
    return h('div', { class: 'hero-contrast' }, [
      h('span', { class: 'hero-contrast-lbl faint' },
        'Contrast · ' + (cm.caseId || cm.truck || '') + ' ' + thb(cm.amount.value) + ' repair →'),
      h('span', { class: 'hero-role s-info' }, cm.role),
      h('span', { class: 'faint' }, '— no escalation to the owner. The gate is data-driven, not hardcoded.')
    ]);
  }

  /* SD-2: the assumptions strip, ALWAYS VISIBLE (no toggle, never hidden). */
  function renderFleetAssumptions(impact) {
    const detail = h('div', { class: 'hero-econ-detail faint mono' });
    (impact.assumptions || []).forEach(function (a) {
      detail.appendChild(h('div', { class: 'hero-econ-line' }, '• ' + a));
    });
    (impact.basis_refs || []).forEach(function (r) {
      detail.appendChild(h('div', { class: 'hero-econ-line' }, 'basis · ' + r));
    });
    return h('div', { class: 'hero-econ' }, [
      h('div', { class: 'hero-econ-head' }, [
        badge(impact.kind, 's-info'),
        badge('MODELLED · PROVISIONAL', 's-warn'),
        h('span', { class: 'faint' },
          'every figure below the quote is derived — these are the inputs it was derived from')
      ]),
      detail
    ]);
  }

  function fleetExposureSide(title, side, cls) {
    const rows = [h('div', null, side.label || '')];
    const comps = side.components || {};
    Object.keys(comps).forEach(function (key) {
      rows.push(h('div', null, key.replace(/_thb$/, '').replace(/_/g, ' ') + ' · ' + thb(comps[key])));
    });
    return h('div', { class: 'hero-ledger-side' }, [
      h('div', { class: 'hero-ledger-title ' + cls }, title),
      h('div', { class: 'hero-ledger-big ' + cls }, thb(side.exposure_thb)),
      h('div', { class: 'hero-ledger-detail faint mono' }, rows)
    ]);
  }

  /* SD-3(c): the measured quote LEADS; the modelled recovery follows, labelled
     understated. Two different kinds of number, and the screen says which is which. */
  function renderFleetMoney(led) {
    const impact = led.impact;
    return card('฿-impact — the quote that arrived, and what comparison recovered',
      'GET /demo/hero/impact · measured quote + modelled recovery, kept apart', [
        h('div', { class: 'hero-ledger-foot' }, [
          tile('quoted repair', thb(led.quoted_repair_thb), 's-info', 'MEASURED · off the event itself'),
          tile('recovered by comparison', thb(impact.net_benefit_thb), 's-ok',
            'MODELLED · deliberately understated'),
          tile('governed exposure', thb(impact.governed.exposure_thb), 's-ok',
            'what the governed path is modelled to cost')
        ]),
        h('div', { class: 'hero-ledger' }, [
          fleetExposureSide('Baseline — pay the quote as sent', impact.baseline, 's-crit'),
          h('div', { class: 'hero-ledger-arrow' }, icon('flow', { width: 18, height: 18 })),
          fleetExposureSide('Governed — quote compared before approval', impact.governed, 's-ok')
        ]),
        renderFleetAssumptions(impact)
      ]);
  }

  /* SD-3(c): the origin story, as NARRATIVE COPY ONLY — the owner's own words, stated
     unprompted (procedures.yaml). It carries no numeral by construction, so the story
     cannot smuggle in a figure the payload never supplied. AC-9 fences that edge. */
  function renderFleetOrigin() {
    return h('div', { class: 'hero-scenario faint' }, [
      h('span', null, 'Why this rule exists — the owner’s own words, unprompted: '),
      h('span', { class: 'mono' }, '“เคยโดนช่างโกงอะไหล่ไปเป็นแสน”'),
      h('span', null, ' — the loss that wrote the three-quote rule. Narrative only: no figure on this screen is derived from it.')
    ]);
  }

  function renderFleet(container, gov, led) {
    clear(container);
    const hero = fleetMoment(gov.hero);
    const contrast = fleetMoment(gov.contrast);

    const head = h('div', { class: 'hero-head' }, [
      h('div', { class: 'hero-title' }, [
        icon('receipt', { width: 18, height: 18 }),
        h('b', null, 'Governance Moment'),
        h('span', { class: 'faint' }, '· Governed Repair Approval (fleet)')
      ]),
      h('div', { class: 'hero-badges' }, [
        badge(gov.source === 'offline-fixture' ? 'OFFLINE FIXTURE' : String(gov.source),
          gov.source === 'offline-fixture' ? 's-info' : 's-ok'),
        badge('DEMO-GRADE · PROVISIONAL', 's-warn')
      ])
    ]);

    const scenario = h('div', { class: 'hero-scenario faint' },
      'A truck (' + hero.truck + ') is off the road on a ' + (hero.severity || 'critical')
      + ' fault → the roadside garage sends a repair quote of ' + thb(hero.amount.value)
      + ' → it clears the owner’s ceiling, so the claim cannot be signed by whoever filed it.');

    container.appendChild(head);
    container.appendChild(scenario);
    container.appendChild(renderFleetOrigin());
    container.appendChild(renderFleetDoaCard(hero));
    container.appendChild(renderSodCard(hero));
    container.appendChild(renderFleetRuleGate(hero, contrast));
    container.appendChild(renderJoinCard(hero));
    container.appendChild(renderFleetContrast(contrast));
    container.appendChild(renderFleetMoney(led));
  }
  /* ---- FLEET-BRANCH-END ------------------------------------------------------------ */

  function render(container, gov, ledger, host, live, mode) {
    // The typed discriminant (FleetHeroImpact.vertical). Procurement is the absence case.
    if (ledger && ledger.vertical === 'fleet_maintenance') {
      renderFleet(container, gov, ledger);
      return;
    }
    clear(container);
    const hero = governanceMoment(gov.hero);
    const contrast = governanceMoment(gov.contrast);

    const srcLabel = gov.source === 'event-fired'
      ? 'EVENT-FIRED'
      : (gov.source === 'offline-fixture'
        ? 'OFFLINE FIXTURE'
        : (gov.source === 'live-ms-s1' ? 'LIVE · MS-S1' : 'LIVE · RUN'));
    const srcCls = gov.source === 'offline-fixture' ? 's-info' : 's-ok';

    // PLAN-0057 (AC-3): the manual ↔ event opener toggle.
    // PLAN-0100 Step 3: not rendered on the published profile — event mode fires
    // POST /demo/hero/event, the unauthenticated DB write D5(2) excludes (F4).
    const published = O.isPublished();
    let modeToggle = null;
    if (!published) {
      modeToggle = h('button', { class: 'hero-badge hero-toggle', type: 'button' },
        mode === 'event' ? '↩ Manual opener' : '⚡ Event opener');
      modeToggle.addEventListener('click', function () {
        mount(host, { mode: mode === 'event' ? 'manual' : 'event' });
      });
    }
    // The offline/live toggle applies to the manual opener only.
    // PLAN-0100 Step 3, BEYOND the PLAN's drafted Step-3 list — added s207 after an
    // adversarial review of the Step 9 read flagged it. "▶ Run live" drives
    // GET /demo/hero/governance?live=true, i.e. a full live procedure run that
    // raises ProcedureError (run.py:387) when the gate does not suspend; with no
    // global exception handler in services/api/ that is an unhandled 500 in front
    // of a design partner. It is also an anonymous, uncapped, unlogged MS-S1 call.
    // The default (offline fixture) already renders the whole narrative, so hiding
    // the toggle costs the demo nothing.
    let liveToggle = null;
    if (mode !== 'event' && !published) {
      liveToggle = h('button', { class: 'hero-badge hero-toggle', type: 'button' },
        live ? '↺ Offline fixture' : '▶ Run live');
      liveToggle.addEventListener('click', function () { mount(host, { mode: 'manual', live: !live }); });
    }

    const head = h('div', { class: 'hero-head' }, [
      h('div', { class: 'hero-title' }, [
        icon('receipt', { width: 18, height: 18 }),
        h('b', null, 'Governance Moment'),
        h('span', { class: 'faint' }, '· Emergency Sourcing (Fastenal)')
      ]),
      h('div', { class: 'hero-badges' }, [
        badge(srcLabel, srcCls),
        badge('DEMO-GRADE · PROVISIONAL', 's-warn'),
        modeToggle,
        liveToggle
      ])
    ]);

    const scenario = h('div', { class: 'hero-scenario faint' },
      'A CNC machining center (' + ledger.asset_id + ') is DOWN → needs a critical spindle bearing set ('
      + ledger.part_id + ') → the only fast-enough source is an off-AVL emergency supplier ('
      + hero.sod.approver.person_id + ' approves) at ' + thb(hero.amount.value) + '.');

    container.appendChild(head);
    if (mode === 'event') container.appendChild(renderSenseCue(gov.hero.trigger));
    container.appendChild(scenario);
    container.appendChild(renderDoaCard(hero));
    container.appendChild(renderSodCard(hero));
    if (mode === 'event') container.appendChild(renderActPanel(hero, host, gov.hero && gov.hero.run_id));
    container.appendChild(renderJoinCard(hero));
    container.appendChild(renderContrast(contrast));
    container.appendChild(renderLedger(ledger));
  }

  async function mount(container, opts) {
    const mode = (opts && opts.mode) || 'manual';
    const live = !!(opts && opts.live);
    clear(container);
    const body = h('div', { class: 'hero-view' });
    container.appendChild(body);
    const loadMsg = mode === 'event'
      ? 'Firing the event-triggered governance moment…'
      : (live ? 'Running the governance moment live…' : 'Loading the governance moment…');
    body.appendChild(O.loadingState ? O.loadingState(loadMsg) : h('div', null, 'Loading…'));
    try {
      const govCall = mode === 'event' ? O.Hero.event() : O.Hero.governance(live);
      const [gov, ledger] = await Promise.all([govCall, O.Hero.impact()]);
      render(body, gov, ledger, container, live, mode);
    } catch (e) {
      clear(body);
      const msg = String((e && e.message) || e) +
        ' — the hero-demo endpoints (/demo/hero/*) require the live backend (no embedded demo).';
      body.appendChild(O.errorState
        ? O.errorState('Could not load the governance moment', msg, () => mount(container, { live: live, mode: mode }))
        : h('div', { class: 'hero-err' }, msg));
    }
  }

  window.OCT.ViewHero = { mount, governanceMoment, fleetMoment };
})();
