# PLAN-0063: Audit-chain verification surface — the trust-dossier read view

**Status:** Complete — all 8 ACs shipped (PR1 #688 backend + PR2 #689 UI, both merged 2026-07-11). Close-out below records the evidence and **two disclosed deferrals** (the merge-commit *local* full-suite run + the Step-5 render check — both blocked on the dev Postgres being down; starting dockerd is a host-state action, CLAUDE.md §8, awaiting Cray go).
**Owner:** both (Claude Code executes; Cray ratifies the surfaced decisions)
**Created:** 2026-07-10
**Related ADRs:** none new — this surfaces an **already-shipped, already-tested**
capability (PLAN-0047 Step 5's `verify_chain`) as a read-only view. **ADR-011 is
explicitly NOT triggered** (the tripwire below — the full audit *framework* stays gated
on real partner data, `services/db/audit_log.py:17-18`).
ADR-016 S2 (RF-1) is cited only to mark the read/write asymmetry in SD-2; ADR-009 D1/D2 +
ADR-012 D4.3 + ADR-013 D1 govern the authoring/commit boundaries of this document itself.
**Related PLANs:** PLAN-0047 (`docs/plans/done/0047-pre-pilot-hardening-authn-gate-audit.md`
— shipped the minimal audit slice + `verify_chain`, SD-3 = yes-minimal); PLAN-0052
(`done/0052-adr016-phase3-oct-monitor.md` — the read-only monitor-GET precedent SD-1
mirrors); PLAN-0054 (`done/0054-control-leg-v1-oct-monitor-operate.md` — the monitor
operate seam + `auth.js` this UI panel composes with); PLAN-0053
(`done/0053-adr016-s2-service-principal-build.md` — the omit-when-None chain evolution the
verifier already honors); PLAN-0059 (`done/0059-hero-demo-kpi-panel.md` — the size/style
calibration analog: small surface over shipped plumbing).

> **Authorship disclosure (ADR-012 D4.3):** drafted by the in-harness `plan-drafter`
> subagent (ADR-013 D1 phased authority). Outline originator: Cray — the session-117
> "governed Decision→Outcome unit" strategic frame (three objects: governed decision
> unit ①, value ledger ②, tamper-evident trust dossier ③) is Cray-ratified per the Code
> dispatch payload, and this PLAN builds the minimum honest surface for object ③.
> Independent review: Code R2 — completed 2026-07-10, every `file:line` citation
> independently re-verified on disk against `main` = `d3cb446` (clean tree); verdict
> accept-with-amendment, applied in place (fact 15 + the SD-2 revision) — + Cray at SD
> ratification and PR merge; Code commits per ADR-009 D2 — the drafter does not git.
> Separation: **INTACT**.

> **This is a build PLAN — no new ADR.** If execution uncovers a design fork that would
> need an ADR, STOP and surface it; do not bake it in.
>
> **Tripwire — the ADR-011 boundary (read twice, then honor it).** The full audit
> **framework** — retention, export/download, external anchoring, PDPA subject-access —
> **stays ADR-011, gated on real partner data** (`services/db/audit_log.py:17-18` — the
> tracked home of the gate). Two refinements recorded in STATUS at drafting time
> (2026-07-10), quoted here because ADR-011 is **not yet minted** and this quote is
> their durable copy: "ADR-011 audit stays gated on a REAL partner conversation (R3:
> SYNTHETIC provenance INFORMS but never TRIGGERS it)", and the trigger =
> "first design-partner data / PDPA review". This PLAN builds a **read-only
> chain-INTEGRITY VERIFICATION view** over the shipped minimal slice and nothing more.
> If any Step starts to look like retention policy, an export/download surface, external
> anchoring, or a PDPA subject-access surface — **STOP and raise; do not build.**

## Goal

Give vero-lite's shipped tamper-evidence a product surface. `verify_chain()`
(`services/db/audit_log.py:185-215`) walks the whole SHA-256 hash chain over `audit_log`
and returns human-readable breaks — detecting in-place mutation (recomputed `row_hash`
mismatch, `:210-213`) and splice/reorder (`prev_hash` linkage break, `:195-198`), "the
tamper-evidence that holds even against an actor strong enough to drop the block
trigger" (`:186-189`). Today it has **zero callers outside tests** (repo grep,
2026-07-10: the definition + its docstring; `tests/services/db/test_audit_log.py:32,94,
129,248`; `tests/services/db/test_audit_service_principal.py:24,80,108`; prose in
`docs/lessons/0028-*` / `done/0053-*` / status-archive — **zero hits in `services/api/`
or `services/api/static/`**). Meanwhile the monitor UI already *claims* the property to
users — "with SoD + a tamper-evident audit actor enforced server-side"
(`services/api/static/assets/view-monitor.js:10-11`) — while rendering only a raw
per-step audit dict behind a "Show audit" toggle (`view-monitor.js:343-355`), never a
verified chain status. This PLAN closes that gap with the minimum honest surface: one
read-only HTTP endpoint that runs `verify_chain` and returns a typed integrity report,
plus a monitor-view panel that renders "chain intact" (or the exact break strings) next
to the claim. Strategic frame (Cray-ratified, session 117, per dispatch): the
tamper-evident **trust dossier (object ③, the auditor's object)** gets its first product
surface; objects ① and ② already have theirs. Deterministic-offline throughout; no
MS-S1, no host-state (§8) surface anywhere.

## Substrate facts (each verified on disk with the Read tool, 2026-07-10, against `main` = `d3cb446`, clean tree; Code R2 independently re-verified every load-bearing citation 2026-07-10. Standing hygiene, not a caveat: the executor re-checks each cited surface before building on it)

1. **The capability exists, tested.** `async def verify_chain(session) -> list[str]`
   (`services/db/audit_log.py:185`); full-table walk
   `sa.select(AuditLog).order_by(AuditLog.audit_id)` → `.scalars().all()` (`:190`);
   linkage-break string names `audit_id=` + 12-char hash prefixes (`:195-198`), mutation
   string likewise (`:210-213`). Chain anchor `GENESIS_HASH = "0" * 64` (`:35`). Model
   `AuditLog` (`:55-83`): `audit_id`, `occurred_at`, `actor_person_id`,
   `actor_service_principal_id`, `action`, `run_id`, `step_id`, `payload`, `prev_hash`,
   `row_hash`.
2. **Empty-chain behavior, derived (not assumed):** with zero rows, `rows` is empty, the
   `for` loop body never executes, and `verify_chain` returns `[]` (`:190-215`) — so
   "empty ⇒ intact" is library truth. `rows_verified` and `head_hash` are **NOT**
   returned by `verify_chain` (it returns only `breaks`); they are **endpoint-side**
   values computed in the same session (SD-3). `head_hash = null` on an empty table is
   therefore an *endpoint* contract, honestly derivable.
3. **Break induction has ONE existing exemplar, not two** *(brief-vs-code note)*: the
   dispatch says to induce breaks "the way `test_audit_log.py` already does" for both
   shapes — the **mutation** break is exemplified
   (`tests/services/db/test_audit_log.py:114-130`: `ALTER TABLE … DISABLE TRIGGER
   audit_log_no_mutation` → raw `UPDATE` → re-enable → assert `"mutated" in breaks[0]`),
   but **no linkage/splice-break induction exists anywhere in the suite** (every other
   call site asserts `== []`). AC-3's test authors the first one, generalizing the same
   disable-trigger pattern (e.g. `UPDATE … SET prev_hash = …` or `DELETE` a middle row
   while the trigger is disabled).
4. **Endpoint patterns to mirror.** Read-only monitor GETs carry **no auth dependency**:
   `GET /runs` (`services/api/routers/runs.py:181`) + `GET /runs/{run_id}` (`:236`),
   header comment "READ-ONLY list + detail endpoints. No mutation, no LLM call, no
   executor — only SELECTs (AC-3)" (`:174-178`); DB session via
   `session: Annotated[AsyncSession, Depends(get_session)]` (`:183`). Consequential
   POSTs require an authenticated human (RF-1, ADR-016 S2): resolve (`:324`, guard
   `:346-353`) + cancel (`:427`, guard `:442-449`) both 403 when `auth.person_id is
   None`. The runs router itself has **no prefix** (`router = APIRouter(tags=["runs"])`,
   `:74`). Router registration: `app.include_router(...)` ×9 at
   `services/api/main.py:204-212` (routers on disk: `actions, admin, demo, intake,
   procedure_draft, procedures, query, runs, whoami` — no `audit.py` exists in
   `routers/` or `models/`).
5. **Auth dependency semantics** (`services/api/auth.py`): fail-closed pilot-grade
   static per-person API keys — SHA-256 digest → `person_id` (`:1-22`);
   `api_auth_enabled=false` ⇒ the dependency is inert, `AuthContext(None, None)`
   (`:71-72`); missing/malformed/unknown credential ⇒ **401** (`:73-81`); an
   authenticated `person_id` unmapped in a principals-shipping vertical ⇒ **403**
   (`:82-93`); a vertical shipping no principals resolves `person=None` with identity
   recorded (`:94`).
6. **Response-model conventions.** `services/api/models/demo.py` — every model
   `BaseModel` + `model_config = ConfigDict(extra="forbid")` + `Field(description=...)`
   on **every** field (exemplar `HeroImpactLedger`, `:32-57`); CLAUDE.md §8 makes the
   `Field(description=...)` rule binding.
7. **`/demo/hero/` is the wrong home.** `services/api/routers/demo.py:17-19`: "**SD-3
   demo guards:** the `/demo/hero/` prefix + the `provisional` flag on every payload +
   this clearly-named demo router make these demo-scoped by construction — never a
   business surface". Chain verification runs over the **real** `audit_log` table — a
   genuine governance capability, not a demo fixture (SD-1 rejects (c) on this fact).
8. **Frontend reality.** No build step: vanilla JS, hand-rolled `h()` hyperscript +
   `window.OCT.*` globals, served by `_StaticFilesWithCSP(directory=_STATIC_DIR,
   html=True)` mounted last (`services/api/main.py:225-230`) — *(brief-vs-code note:
   the mount is the CSP-enforcing subclass, not plain `StaticFiles`; cosmetic)*. The
   monitor view **deliberately bypasses `api.js`** — "DIRECT fetch, NO mock fallback"
   (`view-monitor.js:13-15`), header-less `getJSON()` for reads (`:65-73`),
   `postOperate()` merging `O.Auth.authHeader()` for operate POSTs (`:84-100`)
   — *(brief-vs-code note: the dispatch's likely-shape step "api.js binding" is
   therefore NOT the house idiom for this view; the recommended binding is a
   monitor-local fetch, leaving `api.js` untouched — SD-5)*. Monitor CSS is
   **JS-injected** via `injectStyles()` (`.mon-audit-wrap` at `view-monitor.js:532`,
   inside the `<style>` template ending `:534`) — so a panel style lands in
   `view-monitor.js` itself, no separate CSS file.
9. **Cache-busting is mandatory.** `services/api/static/index.html:9-13` carries the
   rule ("bump the `?v=` token on ANY assets/* edit so a NORMAL browser reload picks up
   the change"). Current tokens (verified): `theme.css?v=c24` (`:14`), `views.css?v=c24`
   (`:15`), `story.css?v=c24` (`:16`), `hero.css?v=c34` (`:17`), `api.js?v=c31` (`:38`),
   `components.js?v=c29` (`:39`), `view-hero.js?v=c34` (`:51`), `auth.js?v=c33` (`:52`),
   **`view-monitor.js?v=c33` (`:53`)**, `app.js?v=c29` (`:54`).
10. **Test conventions.** Endpoint tests live in `tests/api/` —
    `tests/api/test_monitor_runs.py:1-12` (read-only GETs over seeded rows, disposable
    `<db>_test` via `create_test_engine`, skip-without-Postgres) and
    `tests/api/conftest.py:98-122` (`client_with_db`: httpx `ASGITransport` client with
    `get_session` dependency-overridden onto a per-test engine + create_all/drop_all).
    Library-level audit tests: `tests/services/db/test_audit_log.py` (fixture installs
    the frozen block-trigger DDL onto the create_all schema, `:55-70`).
11. **The live AST guard (do not trip).** `tests/services/db/test_load_run_ordering_guard.py`
    statically fails the suite on any `<load_run result>.step_results[...]` subscript
    under `services/`, `tests/`, `verticals/` (scanned packages `:36`; the tree-wide
    enforcement test `test_no_load_run_result_is_read_by_list_position`, `:90-106`).
    Nothing in this PLAN touches `load_run` — stated here as a constraint so no
    executor reaches for it in a test.
12. **Scale reality.** `verify_chain` loads the **entire** `audit_log` table into memory
    and recomputes every row's hash (`audit_log.py:190-208`) — O(n) time and memory,
    unbounded. Fine for pilot/demo data; a real consideration for an open route (SD-2,
    SD-4).
13. **Suite baseline.** Full offline suite at PLAN-0062 close (2026-07-10): **2496
    passed / 7 skipped** (`docs/plans/done/0062-per-vertical-seed-migration.md:421`).
14. **What the monitor already shows per run** (SD-6 guard): `GET /runs/{run_id}`
    returns per-step `audit` dicts (`runs.py:160-171` `_detail_step_views`, field
    `audit=s.audit` at `:168`), rendered behind the "Show audit" toggle
    (`view-monitor.js:343-355`). A per-run audit-row projection would duplicate a
    shipped surface.
15. **Authn default is ON** *(Code R2 finding at review — it changes SD-2's tradeoff)*:
    `api_auth_enabled` defaults to `True` — "Fail-closed default; set false only on a
    local dev/demo box that deliberately wants the pre-authn behavior"
    (`services/api/config.py:53-61`). The unauthenticated path is an explicit
    per-deployment opt-out, NOT the default posture. See SD-2's "default-posture
    consequence".

## Acceptance Criteria

Everything below is **offline and deterministic**, provable under the required CI `gate`
on a fresh PR (CI is PR-only in this repo — prove green via the PR's checks, full suite,
never a named subset). ACs are written to the SD recommendations and re-scope
mechanically if Cray picks otherwise.

- [x] **AC-1 — intact chain verifies over HTTP.** Against a freshly appended, untampered
      chain (seeded via the real `append_audit`, the `test_audit_log.py:73-77` helper
      pattern), the endpoint returns `intact: true`, `breaks: []`, `rows_verified` equal
      to the appended row count, `head_hash` equal to the last row's stored `row_hash`,
      and `genesis_hash: "0"*64` — asserted through the `tests/api/` client (fact 10),
      not by calling the library directly; fetched break-visible per SD-2(d) (a seeded
      credential or `api_auth_enabled=false` — fact 15: the default is authn-ON).
- [x] **AC-2 — in-place mutation is reported, verbatim.** After inducing a mutation the
      shipped way (disable trigger → raw `UPDATE` → re-enable,
      `test_audit_log.py:120-125`), the endpoint returns `intact: false` and a break
      string containing `audit_id=` and `row content mutated` (the library string,
      `audit_log.py:210-213`, echoed verbatim per SD-3 — the endpoint invents no prose;
      fetched break-visible, as AC-1).
- [x] **AC-3 — splice/linkage break is reported, verbatim.** A `prev_hash` linkage break
      (induced with the same disable-trigger pattern — e.g. rewriting a row's
      `prev_hash` or deleting a middle row; **new exemplar**, fact 3) yields
      `intact: false` + the `prev_hash linkage broken` string (`audit_log.py:195-198`);
      fetched break-visible, as AC-1.
- [x] **AC-4 — empty chain is honest.** With zero `audit_log` rows the endpoint returns
      `intact: true`, `rows_verified: 0`, `head_hash: null` — matching the derived
      library behavior (fact 2), not an invented convention.
- [x] **AC-5 — model discipline.** The response model has
      `model_config = ConfigDict(extra="forbid")` and `Field(description=...)` on
      **every** field (fact 6; CLAUDE.md §8), and the route declares
      `response_model=...`.
- [x] **AC-6 — the SD-2 auth posture is pinned by tests.** Per the SD-2(d)
      recommendation, four cases pinned under the DEFAULT authn-on posture (fact 15):
      anonymous (no `Authorization` header) ⇒ **200** verdict-only (`breaks: null`,
      `intact` computed from the real walk); a PRESENTED-but-invalid credential ⇒
      **401** (loud, `auth.py:73-81` — never a silent verdict-only downgrade); a valid
      credential ⇒ the full report with verbatim breaks; `api_auth_enabled=false` ⇒ the
      full report (the explicit opt-out, `auth.py:71-72`). No RF-1-style person-guard
      in any case (this is a read, not a consequential write). Whatever Cray ratifies,
      the matrix re-pins mechanically ((b): the anonymous case becomes 401; (a): every
      case serves the full report) — the posture is never left implicit.
- [x] **AC-7 — the UI panel renders proof beside the claim.** The monitor view gains a
      chain-verification panel (SD-5): on demand it calls the endpoint and renders
      "chain intact · N rows verified" or the verbatim break list. Logged-out under the
      default authn-on posture it still renders the OPEN verdict (SD-2(d)), with an
      honest "log in to see break detail" affordance whenever `breaks` is withheld
      (`null`) — never a fake `intact`, never an empty-list rendering of withheld
      breaks. Every edited asset's `?v=` token is bumped (`view-monitor.js?v=c33` →
      next, `index.html:53`; `api.js` expected untouched per fact 8 — bump only what is
      edited).
- [x] **AC-8 — zero collateral.** No Alembic migration (no schema change — the endpoint
      only SELECTs); `services/db/audit_log.py` is **byte-unchanged** (the 7 pinned
      `verify_chain` test call sites stay green untouched); no
      `load_run …step_results[...]` subscript anywhere new (fact 11); ruff +
      ruff-format + mypy clean; the full offline suite green under CI `gate` (baseline
      2496 passed / 7 skipped, fact 13); no MS-S1 / live-LLM / host-state action
      anywhere.

## Out of Scope

- ❌ **The ADR-011 audit framework — the tripwire.** No retention policy, no
  export/download surface, no external anchoring, no PDPA subject-access surface
  (`audit_log.py:17-18`; the two STATUS refinements are quoted in the tripwire above).
  A Step drifting toward any of the four = STOP and raise.
- ❌ **The heavy hero-demo dossier backlog** — procedure-level KPI/measurement engine
  capability, notification/reporting, questionnaire, kanban. PLAN-0059 already walled
  this off: "That is a heavy engine capability needing its own ADR + PLANs"
  (`done/0059-hero-demo-kpi-panel.md:86-89`, citing the gitignored, **unratified**
  discussion draft `docs/research/private/2026-06-30-hero-demo-design-dossier.md`).
- ❌ **Any schema/migration change to `audit_log`** — the DDL is frozen in
  `alembic/versions/0007_audit_log.py` (a shipped migration must never change;
  `audit_log.py:38-40`).
- ❌ **Any change to `compute_row_hash` / `append_audit` / the hash canonicalisation** —
  touching it silently voids every stored hash
  (`docs/lessons/0028-omit-when-none-evolving-hash-chained-log.md`). This PLAN also
  leaves `verify_chain`'s signature untouched (AC-8): richer return values are composed
  endpoint-side (SD-3), never by widening the library contract.
- ❌ **Scheduled/background verification, alerting, or polling the scan** — the O(n)
  walk runs on demand only (SD-4/SD-5); a verification *schedule* is future work.
- ❌ **Anything under `/demo/hero/`** — fact 7; this is a business/governance surface,
  not a demo fixture.
- ❌ **Any MS-S1 / live-LLM run** (CLAUDE.md §8) — 100% offline + deterministic.
- ❌ Multi-tenancy, the `_action_store` persistence gap, real data adapters.

## Surfaced Decisions

Each SD carries a recommendation + rationale; **Cray ratifies** (AskUserQuestion per
recent practice); none is silently decided. The ACs/Steps are written to the
recommendations and re-scope mechanically otherwise.

- **SD-1 — where the surface lives.**
  *Recommendation:* **(a)** a NEW router `services/api/routers/audit.py`
  (`APIRouter(prefix="/audit", tags=["audit"])`) + `services/api/models/audit.py`,
  registered at `main.py:204-212` (neither file exists today — fact 4).
  *Rationale:* the capability is vertical-agnostic governance, not a runs projection —
  a clearly-named router keeps the trust-dossier surface findable and growable, exactly
  as the demo router's self-describing-name guard argues (fact 7); the runs router is
  prefix-less and scoped to run projections (`runs.py:74`, `:174-178`), so folding in
  (b) would blur two read scopes for zero diff savings.
  *Alternatives:* (b) fold into `runs.py` — smallest file count, but the chain spans ALL
  actions (not only runs; `run_id` is nullable, `audit_log.py:79`), so the home is
  semantically wrong; (c) under `/demo/hero/` — **rejected by fact 7**: demo-scoped by
  construction ≠ a business surface, and chain verification over the real `audit_log`
  is precisely a business surface.
  *Why Cray:* names a new public API namespace — the product taxonomy of object ③ is a
  positioning call, not an implementation detail.
  ✅ *Ratified (Cray, 2026-07-11):* **(a)** — new `services/api/routers/audit.py` +
  `services/api/models/audit.py`, as recommended.
- **SD-2 — auth posture on the endpoint.**
  **The default-posture consequence (Code R2 finding, 2026-07-10).** `api_auth_enabled`
  defaults to `True` (fact 15) — the unauthenticated dev/demo behavior is an explicit
  per-deployment opt-out, not the default. The first draft of this SD claimed the
  `false` escape "keeps the local demo working" under option (b); that was overstated —
  it holds only where someone has already flipped the fail-closed default. Under the
  DEFAULT posture, (b) creates an asymmetry inside one view: `GET /runs` +
  `GET /runs/{run_id}` render open (no auth dependency — fact 4), including the
  per-step "Show audit" dump (fact 14), while the trust panel alone answers 401 → a
  login prompt. The one element whose entire purpose is to make the tamper-evidence
  visible would be the one element hidden in the default demo moment.
  *Recommendation (revised at R2):* **(d) split visibility.** The verification
  **verdict** — `intact`, `rows_verified`, `head_hash`, `genesis_hash`, `verified_at` —
  is served openly, consistent with the read-GET precedent (fact 4); the **verbatim
  break strings** require a credential (they name `audit_id` + 12-char hash prefixes
  and enumerate exactly where the chain was cut — reconnaissance-grade detail an
  anonymous caller does not need). Contract mechanics: `breaks: list[str] | None`,
  `null` = withheld-from-anonymous, `[]` = verified intact; `intact` is ALWAYS computed
  from the real walk (SD-3). Auth mechanics: an optional-credential resolution —
  missing header ⇒ anonymous verdict-only; a PRESENTED-but-invalid credential still
  401s loudly per the `get_current_principal` semantics (`auth.py:73-81`) — degrading a
  bad key silently to verdict-only would mask a misconfigured auditor;
  `api_auth_enabled=false` ⇒ the full report (the deployment explicitly opted out,
  `auth.py:71-72`). Costs, stated honestly: one endpoint branch, a small optional-auth
  dependency variant beside `get_current_principal` (home = OQ-4), the
  nullable-`breaks` wrinkle in SD-3 — and (d) does NOT bound the O(n) scan (fact 12):
  the open verdict half still walks the whole chain, so (b)'s scan-cost argument is
  genuinely given up (accepted at pilot scale per SD-4; narrowing to (b) later is a
  small, compatible change if abuse ever materializes).
  *Drafter's verdict, (d) vs (b):* **(d) beats (b) for v1.** This surface exists to
  make the tamper-evidence *visible*; under the fail-closed default, (b) hides the
  proof behind a login in exactly the partner/demo moment the PLAN is for — and that
  would be discovered at show time. (d) keeps the proof beside the claim (the SD-5
  rationale), puts the credential on the sensitive half, and its give-up — the open
  unbounded scan — is a risk SD-4 already accepts at pilot scale. RF-1 is invoked by
  NONE of the options: its 403-on-no-human exists for *consequential writes*
  (`runs.py:338-353`, `:439-449`); this is a read, so no `person_id is None` guard
  appears in any variant.
  *Alternatives:* **(a)** fully open, mirroring `GET /runs` (fact 4) — simplest and
  precedent-consistent, but exposes break detail AND the unbounded scan on an open
  route. **(b)** require `get_current_principal` outright — honest for a credentialed
  auditor and bounds the scan, but carries the default-posture consequence above.
  Known (b)/(d) edge, stated honestly: with authn on in a principals-shipping vertical
  (procurement is the only one today, `auth.py:13-16`), an unmapped-but-valid key 403s
  at the dependency (`auth.py:82-93`) — acceptable: an auditor credential should be a
  mapped principal. **(c)** unauthenticated + bounded walk — rejected: a bounded
  verify weakens the claim itself (see SD-4).
  *Why Cray:* the visibility/credential split on a partner-facing trust surface — plus
  the acceptance of an open unbounded scan — is a product/security posture call, not a
  drafter default.
  ✅ *Ratified (Cray, 2026-07-11):* **(d) split visibility** — verdict open, verbatim
  break strings credentialed, as recommended (the R2-revised recommendation).
- **SD-3 — response shape.**
  *Recommendation:* `ChainVerificationReport` in `services/api/models/audit.py`:
  `intact: bool` (always computed from the real walk — `len(breaks) == 0` server-side),
  `breaks: list[str] | None` (**verbatim** library strings when visible — they carry
  `audit_id` + 12-char hash prefixes and no payload/PII
  (`audit_log.py:195-198,210-213`); they are the *point* of the surface, and inventing
  parallel prose would drift from the tested truth; under SD-2(d) `null` = withheld
  from an anonymous caller and `[]` = verified intact — a withheld list is NEVER
  serialized as empty), `rows_verified: int`, `head_hash: str | None`,
  `genesis_hash: str`, `verified_at: datetime` (UTC, stamped at verification).
  `extra="forbid"` + `Field(description=...)` everywhere (AC-5).
  Composition note (fact 2): `verify_chain` returns only `breaks`; `rows_verified` +
  `head_hash` come from two cheap endpoint-side SELECTs (count; newest `row_hash`) in
  the **same session** as the walk, so the report is read-consistent —
  `verify_chain`'s signature stays untouched (AC-8).
  *Alternatives:* structured break objects (`{audit_id, kind, detail}`) — richer, but
  requires parsing/duplicating the library's formatted strings or changing the library;
  defer until a consumer needs machine-readable breaks.
  *Why Cray:* this is the auditor-facing contract of object ③ — its field vocabulary is
  a product decision that outlives v1.
  ✅ *Ratified (Cray, 2026-07-11):* the six-field `ChainVerificationReport`,
  `breaks: list[str] | None`, break strings echoed verbatim — as recommended.
- **SD-4 — scale disposition for v1.**
  *Recommendation:* **(a)** accept the full O(n) walk; document the bound in the
  endpoint docstring + this PLAN; record "bounded/incremental verification (e.g.
  checkpointed head, verify-since-anchor)" as an explicit follow-up in the close-out +
  STATUS. Never silently: the docstring says it, the PLAN says it, and the UI invokes
  it on demand only (SD-5). The deeper argument: **a bounded verify weakens the claim**
  — verifying only a suffix proves nothing about the prefix it chains from, so v1
  either walks the whole chain or its "intact" would be dishonest. At pilot scale
  (fact 12: fine for demo/pilot datasets) the whole-chain walk is the honest cheap
  option. Under SD-2(d) the walk is reachable anonymously (the verdict half) — that
  exposure is named in SD-2's costs and in risk 2, not hidden here.
  *Alternatives:* (b) build a bounded/incremental variant now — real engineering
  (anchor storage ≈ external anchoring, which is **ADR-011 tripwire territory**) for a
  scale problem no pilot dataset has.
  *Why Cray:* accepting a documented unbounded scan on a governed surface is a risk
  acceptance, Cray's to sign.
  ✅ *Ratified (Cray, 2026-07-11):* **(a)** — accept the O(n) whole-chain walk; document
  the bound + record the bounded-verification follow-up, as recommended.
- **SD-5 — UI surface.**
  *Recommendation:* **(a)** a panel inside the existing monitor view — the unproven
  "tamper-evident" claim lives exactly there (`view-monitor.js:10-11`), so the proof
  belongs beside the claim; smallest diff. Mechanics per the house idiom (fact 8): a
  monitor-local fetch (the view deliberately bypasses `api.js`, `:13-15` — so **no
  `api.js` edit and no `api.js` `?v=` bump**), merging `O.Auth.authHeader()` when
  logged in (the `postOperate` pattern, `:85`); an explicit **"Verify chain" button**
  rendering the AC-7 states — on demand, NOT on the list/detail poll timers (`:22-23`),
  so the O(n) scan never rides a 3–10s cadence (dovetails SD-4); styles into the
  JS-injected `injectStyles()` block (fact 8); bump `view-monitor.js?v=c33 → c34`
  (`index.html:53`).
  *Alternatives:* **(b)** a new `view-trust.js` + nav tab — the growth path if the
  trust dossier becomes its own screen (more objects than chain status); right when
  that day comes, oversized for one panel today.
  *Why Cray:* where the trust proof appears in the demo narrative is a
  presentation/positioning call Cray owns (the PLAN-0059 SD precedent).
  ✅ *Ratified (Cray, 2026-07-11):* **(a)** — panel inside `view-monitor.js`, on-demand
  "Verify chain" button, off the poll timers, as recommended.
- **SD-6 — scope of "dossier" for v1.**
  *Recommendation:* **(a)** chain-integrity status ONLY — the *trust* half of object ③.
  *Rationale:* the per-run audit rows are already served (`GET /runs/{run_id}` →
  per-step `audit` dicts, `runs.py:160-171`) and already rendered (the "Show audit"
  toggle, `view-monitor.js:343-355`) — option (b) would duplicate a shipped surface
  (fact 14) and start sliding toward the ADR-011 export/reporting tripwire.
  *Alternatives:* (b) also project audit rows through the new `/audit` namespace —
  rejected per fact 14 + the tripwire.
  *Why Cray:* fixes what "trust dossier v1" means to a partner — a scope-of-promise
  decision.
  ✅ *Ratified (Cray, 2026-07-11):* **(a)** — chain-integrity status only for v1, as
  recommended.

## Steps

> **Ratification note (2026-07-11):** all six SDs were ratified **as-recommended**
> (Cray), so the ACs/Steps below already reflect the ratified shape — no re-scope was
> needed; an executor reads this PLAN as directly actionable. OQ-1..OQ-4 stay open as
> build-level questions settled at step review — **OQ-4 (the home of the SD-2(d)
> optional-credential resolution) is now load-bearing and is the first thing Step 2
> settles.**

Recommended split: **two PRs** — PR1 backend contract (Steps 1–3), PR2 UI + close-out
(Steps 4–5). Justification: the endpoint contract is independently reviewable + green
standalone, and the frontend then binds to a *merged* contract (the PLAN-0052 → 0054
layering, one size smaller); a single PR is defensible for a diff this small, but two
keeps each review single-surface (backend vs static assets) and each trivially
revertable. This is a build-sequencing call — Cray may collapse to one PR at
ratification without re-scoping anything.

### Step 1 — response model (`services/api/models/audit.py`, new)
Per SD-3: `ChainVerificationReport` with the six fields (nullable `breaks` per
SD-2(d)), `extra="forbid"`, `Field(description=...)` on every field (the
`models/demo.py:32-57` shape exemplar). Docstring states the O(n) bound (SD-4) and the
ADR-011 boundary (this is the verification view, not the framework).

### Step 2 — router + endpoint + registration
Per SD-1/SD-2: `services/api/routers/audit.py` (new) —
`GET /audit/verify` (final path name = OQ-1), `response_model=ChainVerificationReport`,
`session` via `Depends(get_session)` (`runs.py:183` pattern); credential resolution per
SD-2(d): an optional-auth variant (missing header ⇒ anonymous, verdict-only with
`breaks: null`; a presented-but-invalid credential ⇒ 401 via the
`get_current_principal` semantics, `auth.py:73-81`; `api_auth_enabled=false` ⇒ the full
report) — **no** RF-1-style person-guard (home of the variant = OQ-4). Body:
`breaks = await verify_chain(session)` + the two SD-3 composition SELECTs; read-only by
construction (the `runs.py:174-178` stance: only SELECTs). Register in
`services/api/main.py:204-212` (the 10th `include_router`). Endpoint docstring carries
the O(n) bound + "whole-chain or nothing" honesty note (SD-4).

### Step 3 — endpoint tests (`tests/api/test_audit_verify.py`, new)
The `client_with_db` idiom (`tests/api/conftest.py:98-122`) with the audit block-trigger
DDL installed as in `test_audit_log.py:55-70`. Cases = AC-1 (intact, seeded via
`append_audit`), AC-2 (mutation, the `:120-125` induction), AC-3 (linkage — the NEW
induction exemplar, fact 3), AC-4 (empty), AC-6 (the four-case SD-2(d) posture matrix),
AC-5 (forbid/extra rejection). PR1 boundary: suite + ruff + mypy green
under CI `gate`.

### Step 4 — monitor panel (`services/api/static/assets/view-monitor.js` + `index.html`)
Per SD-5(a): the on-demand "Verify chain" panel — button → monitor-local fetch (merging
`O.Auth.authHeader()` when logged in) → render `intact + rows_verified` (ok state) vs
the verbatim break list (crit state) vs the open verdict + "log in to see break detail"
affordance when `breaks` is withheld (AC-7); styles appended in `injectStyles()`; never
wired to the poll timers. Bump `view-monitor.js?v=c33 → c34` at `index.html:53`; bump
nothing else unless edited (fact 9).

### Step 5 — verify + close-out
Offline: full suite + ruff + mypy green on PR2's required CI `gate` (AC-8; baseline
fact 13). Render: `preview_snapshot` + `preview_eval` DOM assertions against
pre-committed strings (an intact chain renders "chain intact"; pass/fail read fixed
BEFORE the run, Lesson #0026) — **not** `preview_screenshot` (times out in this env,
project memory); cache-busted per fact 9. Record the SD-4 bounded-verification
follow-up in STATUS; STATUS reconcile; `git mv docs/plans/0063-*.md docs/plans/done/`
per CLAUDE.md §6 Plan Flow.

## Verification

**Binding bar:** AC-8 — the full offline suite + ruff + ruff-format + mypy green under
the required CI `gate` on fresh PRs (CI is PR-only; prove main-green via the PR's
checks, full suite, never a named subset), with `services/db/audit_log.py` and
`alembic/versions/` byte-unchanged and the endpoint tests (Step 3) as the contract
oracle — including both break shapes, the empty chain, and the pinned auth posture.
**Confirming evidence (render, not a CI gate):** Step 5's cache-busted
`preview_snapshot` + `preview_eval` with pre-committed expected strings. Nothing in this
PLAN touches MS-S1 or any host-state (§8) surface; the offline oracle is the entire bar.

## Open Questions (build-level; settle at step review — never silently)

- **OQ-1 —** exact route path: `GET /audit/verify` (recommended — verb-ish but honest
  about the on-demand scan) vs `GET /audit/chain`. Cosmetic; settle at Step 2 review.
- **OQ-2 —** panel placement inside the monitor: above the list column vs the detail
  header strip. Presentation detail under SD-5(a); settle at Step 4 review (visual
  check with Cray if taste-sensitive — the PLAN-0059 mockup precedent).
- **OQ-3 —** whether the DB-backed endpoint tests install the block trigger in every
  case or only the induction cases (the trigger is irrelevant to AC-1/AC-4). Test
  hygiene; settle at Step 3 review.
- **OQ-4 —** home of the SD-2(d) optional-credential resolution: a small
  `get_optional_principal` beside `get_current_principal` in `services/api/auth.py`
  (recommended — one tested home, reuses the fail-closed semantics) vs router-local.
  Settle at Step 2 review.

## Size estimate + risks

**S.** One new model + one new router + one test module + one view panel — larger than
PLAN-0059 (XS, frontend-only: it added zero backend) but well under PLAN-0052 (M: two
endpoints + a whole view). Two contained PRs; blast radius bounded by AC-8's
byte-unchanged pins.

Risks, named:
1. **The ADR-011 misread** — scope creep from "verification view" toward
   retention/export/anchoring/PDPA. Mitigation: the tripwire is first-class (header +
   Out of Scope), and SD-4 explicitly rejects the anchor-storage slope.
2. **The unbounded scan** (fact 12) — under SD-2(d) the verdict half is open, so the
   O(n) walk is NOT credential-bounded. Mitigation: accepted + documented at pilot
   scale (SD-4), on-demand-only in the UI (SD-5, never on the poll timers); if abuse
   materializes, narrowing to (b) is a small compatible change.
3. **`?v=` omission** (fact 9) — a stale `view-monitor.js` makes Step 5's render check a
   false negative against fresh code. Mitigation: AC-7 makes the bump an acceptance
   criterion, and the preview check runs cache-busted.
4. **Library-contract drift** — widening `verify_chain` would break 7 pinned call sites
   and brush against Lesson #0028's hash-chain caution. Mitigation: AC-8 pins
   `audit_log.py` byte-unchanged; SD-3 composes endpoint-side.

## Close-out (2026-07-11, session 118)

**Shipped.** PR1 #688 (`b41e3f5` → merge `9d02686`) = Steps 1–3: `services/api/models/audit.py`
(`ChainVerificationReport`, six SD-3 fields, `extra="forbid"`, `Field(description=...)` on
every field), `services/api/routers/audit.py` (`GET /audit/verify`,
`response_model=ChainVerificationReport`, SD-2(d) split visibility —
`reveal_breaks = (not settings.api_auth_enabled) or (auth.person_id is not None)`;
`intact` always from the real walk), registration as the 10th `include_router`
(`main.py:208`), and `tests/api/test_audit_verify.py` (AC-1 intact / AC-2 mutation /
AC-3 linkage — the suite's **first** linkage-break induction, generalizing the
disable-trigger pattern per fact 3 / AC-4 empty / AC-5 model discipline / AC-6 the
four-leg posture matrix). PR2 #689 (`ceee552` → merge `360007a`) = Step 4: the on-demand
"Verify chain" panel in `view-monitor.js` (`fetchVerify`/`loadTrust`/`trustResult`,
three states — intact badge / verbatim break list / withheld → "Log in above to see
where the chain was cut." — off the poll timers per SD-5), `index.html`
`view-monitor.js?v=c33 → c34` with no other token touched (fact 9).

**Build-level OQ resolutions (settled at step review, per the header note).**
OQ-1 = **`GET /audit/verify`** (the recommended path). OQ-2 = panel placement settled
at Step-4 review as built (inside the monitor view, on-demand button). OQ-3 = the
block-trigger DDL installs via the shared test fixture across all cases. OQ-4 =
**`get_optional_principal` in `services/api/auth.py`** (the recommended one-tested-home;
missing credential ⇒ anonymous, a PRESENTED credential still delegates to
`get_current_principal` so a bad key 401s loudly).

**Verification evidence.** Both PRs green through the required CI `gate` — and per
`.github/workflows/ci.yml` (SD-4 of the CI PLAN, 2026-07-03) that gate provisions a
`postgres:16-alpine` service, so the green runs **include the DB-backed
`test_audit_verify.py` contract oracle**, plus `ruff check` / `ruff format --check` /
`mypy --strict services/` / migrations-on-a-fresh-DB. AC-8 pins re-verified at close on
`main = 360007a`: `git diff d3cb446..360007a -- services/db/audit_log.py alembic/` is
**empty** (byte-unchanged), the full diff is confined to the 8 expected files, and local
`ruff` + `ruff format --check` + `mypy --strict services/` are clean on the merge
commit.

**Two deferrals, disclosed — not softened (CLAUDE.md §6: no fresh evidence = not a
pass).**
1. **Merge-commit local full suite.** CI here is PR-only (never tests a merge commit);
   the local re-run on `360007a` degraded to **2391 passed / 123 skipped** because the
   dev Postgres is DOWN (dockerd not running) — every DB-backed test skipped. That run
   is recorded as what it is: NOT the bar. The close-out PR's own required `gate` (full
   suite + Postgres service) runs on code identical to `main = 360007a` and stands in as
   the merge-commit-equivalent evidence.
2. **The Step-5 render check** (`preview_eval` DOM assertions against the pre-committed
   strings — "chain intact" / the withheld affordance) was **NOT RUN**: `/audit/verify`
   500s without Postgres (`ConnectionRefusedError`, verified live on the preview
   server), and starting dockerd is a **host-state action outside the worktree
   (CLAUDE.md §8) awaiting explicit Cray go**. The panel code paths, exact strings, and
   the `?v=c34` bump are verified on disk (and `?v=c34` observed served by the live
   preview server); the browser E2E render is deferred to the docker go —
   **erratum-if-fail** on that run, per the PLAN-0062 errata precedent.

**SD-4 follow-up (recorded in STATUS at this close):** bounded/incremental chain
verification (checkpointed head / verify-since-anchor) stays explicit future work —
anchor storage ≈ external anchoring = **ADR-011 tripwire territory**; do not build
without re-reading the tripwire.

---

*PLAN-0063 drafted by the in-harness `plan-drafter` subagent (2026-07-10), ADR-013 D1
phased governance authoring (ADR-009 D1). It surfaces the shipped PLAN-0047 Step 5
capability behind a read-only view — no ratified fork is reopened, ADR-011 stays gated
(the tripwire); six build-level forks are surfaced (SD-1..SD-6) with recommendations,
none silently decided. Amended at Code R2 review (2026-07-10, accept-with-amendment):
fact 15 added and SD-2 revised to recommendation (d) after R2's default-posture finding
(`api_auth_enabled` defaults to `True`, `services/api/config.py:53-61`);
AC-1..AC-3/AC-6/AC-7, SD-3/SD-4, Steps 1–4, OQ-4 and risk 2 re-scoped to match.
Author≠reviewer (ADR-012 D4.3): drafter = plan-drafter; reviewers = Code R2 (every
load-bearing citation independently re-verified on disk against `main` = `d3cb446`,
clean tree, 2026-07-10) + Cray at SD ratification and PR merge — separation INTACT.
Drafted uncommitted; Code commits via a `docs/*` PR (ADR-009 D2); the drafter does not
git. AI-assisted (plan-drafter); no `Co-Authored-By` per CLAUDE.md §7.*
