# PLAN-0032: Registry auto-discovery — vertical plugin maturity (Group B / B2)

**Status:** Draft *(implementation PR **gated on ADR-0023 Accepted** — CLAUDE.md §8 ADR-Accepted-before-impl)*
**Owner:** both (Cowork/Tier-1 authors this PLAN; Code commits + executes per ADR-009 D1/D2)
**Created:** 2026-06-18
**Related ADRs:** **ADR-0023** (registry auto-discovery / L1→L2 plugin maturity — **THIS PLAN builds it**; the impl-PR is gated on ADR-0023 Accepted; the mechanism follows ADR-0023 D2 / SD-C); ADR-006 (D3 maturity — amended by ADR-0023; D4 Rule of Three); ADR-007 (D1 plugin-discovery mechanism, unpinned/OQ-6)
**Related Plans:** PLAN-0005 (§6.4 OQ-6 explicit registration; §8.1 register "explicit registry → ADR-006 D3 L2"; **R5 registry-reset fixture**); PLAN-0016 (new-vertical scaffold) / PLAN-0017 (live co-creation intake) — the flows that currently **edit `main.py`**; PLAN-0031 (B1 ORM emitter — the **other** Group-B half, independent)

> **Disclosure (ADR-012 D4.3).** Originated by **Code's** session-67 dispatch
> (`.claude/handoffs/session-67/2026-06-18-1453-code-dispatch-groupb-foundation.md`)
> on Cray's Group-B trigger decision, and by **ADR-0023** (drafted same session by
> Cowork from that dispatch). Drafted (uncommitted) by **Cowork** (Tier-1, ADR-009
> D1). The construct + mechanism were **originated in Code's dispatch + ADR-0023**,
> not in a Cowork free-form self-deliberation — **not** an ADR-012 D4.3
> self-deliberation case. **Author-overlap note:** Cowork also drafted ADR-0023, so
> the same author wrote the governing ADR and this build PLAN; the
> **independent-deliberation check is Cray's ratification of ADR-0023 + Cray/Code's
> PLAN review** (the remaining checks). Cowork re-verified every cited code line /
> file / symbol against the live repo this session (fact-pack-first, Tier-1 rule #4).

> **Gate (CLAUDE.md §8).** The implementation PR is gated on **ADR-0023 Accepted**.
> The PLAN is drafted **around import-scan** (ADR-0023 D2 recommendation); **if Cray
> selects entry-points at ADR-0023 ratification (SD-C), Step 1/Step 2 re-point** to
> the packaging-metadata mechanism — the Goal, ACs, and the back-compat/reset
> invariants are mechanism-agnostic and hold either way.

---

## Goal

Implement **runtime registry auto-discovery** (ADR-0023 D1) so a vertical that
lives under `verticals/<ns>/` and exposes the conventional registration entry
functions (`register_<ns>_adapter` / `register_<ns>_handlers`) is **discovered and
registered without a hand edit to `services/api/main.py`** — the ADR-006 D3
**L1→L2** plugin-maturity move. Discovery is **additive** (explicit
`register_adapter` / `register_handler` stay valid — ADR-0023 D3),
**test-resettable** (the `_reset_registry` fixture still fully wipes discovered
state — ADR-0023 D4 / PLAN-0005 R5), and it **removes the per-vertical `main.py`
edit** from the scaffold/intake onboarding path (ADR-0023 D5).

## The gap + the anchors (live code, re-verified session 67)

- `services/engine/registry.py` — process-global `registry`; explicit
  `register_adapter` (`:47`) / `register_handler` (`:55`); docstring (`:4-6`) *"no
  entry-point packaging, no import-scan discovery"* (OQ-6); duplicate guard
  `RegistryError` (`:51-52`); `reset()` (`:92`).
- The **conventional entry functions** every vertical exposes (and the scaffold
  generates — `scaffold.py:774`/`:802`): `register_<ns>_adapter()` in
  `verticals/<ns>/data_adapter/__init__.py` (energy `:109`, aquaculture `:96`),
  `register_<ns>_handlers()` in `verticals/<ns>/handlers.py` (energy `:59`,
  aquaculture `:64`, supply_chain `:60`).
- The **manual wiring** today — `services/api/main.py:20-25` (imports) + `:40-42`
  (the `name → (adapter_fn, handler_fn)` map for energy / supply_chain /
  aquaculture).
- The **onboarding-edits-core** coupling — `tests/api/test_intake_routes.py:256`
  asserts the scaffold/intake flow inserts a new vertical's tuple into `main.py`.
- The **reset invariant** — `tests/conftest.py:13` autouse `_reset_registry`
  (PLAN-0005 R5).
- Existing **explicit call sites** that must keep working (back-compat): e.g.
  `tests/api/conftest.py:83-84`, `benchmarks/procedure_baseline/run_benchmark.py:55-60`,
  `benchmarks/nl_query_feasibility/run_benchmark.py:89`, the per-vertical adapter
  tests (`tests/verticals/.../test_*_adapter.py`).

## Acceptance Criteria

- [ ] **AC-1 — Discovery registers verticals at runtime.** A discovery entry point
      (e.g. `discover_and_register(registry)` in `services/engine/registry.py` or a
      new `services/engine/discovery.py`) walks `verticals/*` (import-scan,
      `pkgutil`/`importlib`), and for each vertical exposing the conventional entry
      functions, imports + invokes them against the registry. Discovery order is
      **deterministic**. After discovery, the 3 active verticals (energy /
      supply_chain / aquaculture) are all registered.
- [ ] **AC-2 — Idempotent / guarded (ADR-0023 D3).** Discovery does **not**
      double-register (no `RegistryError` from a vertical already registered);
      discovery and explicit `register_*` of the same vertical coexist safely (skip
      if already present, or own registration and migrate callers — Step 1 fixes
      the policy).
- [ ] **AC-3 — Failure isolation.** A broken / partial vertical package (import
      error, missing entry function) is **skipped with a clear, logged error** and
      does **not** abort discovery of the other verticals.
- [ ] **AC-4 — Test-resettable (ADR-0023 D4 / PLAN-0005 R5).** `_reset_registry`
      still fully wipes discovered state between tests; discovery is **re-runnable
      after `registry.reset()`** (no import-time-only side effect that survives a
      reset and cannot be re-triggered).
- [ ] **AC-5 — `main.py` uses discovery; the onboarding edit is removed (ADR-0023
      D5).** `services/api/main.py` registers verticals via discovery instead of
      the hand-wired `:40-42` map (the map is replaced); the scaffold/intake flow
      no longer edits `main.py`, and `tests/api/test_intake_routes.py:256` (the
      edit assertion) is **updated/retired** accordingly — a tested change, not a
      silent removal.
- [ ] **AC-6 — Back-compat (ADR-0023 D3).** Existing explicit `register_*` call
      sites (tests + benchmarks listed above) keep working — via the AC-2 guard or
      a deliberate migration; the `register_adapter` / `register_handler` public
      API is **unchanged**.
- [ ] **AC-7 — Quality bar (CLAUDE.md §8), offline.** Type hints + tests + **ruff
      clean + `mypy --strict` clean**; fully **offline** (no host-state); the full
      `uv run pytest -q` suite stays green (baseline stated at execution — STATUS
      records 1608 passed / 22 skipped).

## Out of Scope

- ❌ **Python entry-points / packaging metadata** — the ADR-0023 SD-C entry-points
  branch + the L3 future seam (unless Cray selects it at ratification, in which
  case Step 1/2 re-point and this line moves to In-Scope).
- ❌ **B1 ORM emitter** — separate, independent PLAN-0031.
- ❌ **Removing the explicit `register_*` APIs** — they stay (ADR-0023 D3);
  discovery is additive.
- ❌ **Editing ADR-006 in place** — the L1→L2 amendment is recorded in ADR-0023.
- ❌ **The Phase-C intake UI / "user context → new vertical" UX** — PLAN-0032
  delivers the **discovery seam** that Phase C builds on; the UI itself is Phase C.
- ❌ **New vertical (#4), NL-query, partner data, host-state.**

## Steps

> Mechanism below = **import-scan** (ADR-0023 D2 recommendation). If ADR-0023
> ratifies **entry-points** (SD-C), Steps 1–2 re-point to packaging-metadata
> discovery; Steps 3–6 are mechanism-agnostic.

### Step 1 — The discovery function (import-scan + isolation + idempotency)

Add `discover_and_register(registry)` (in `registry.py` or a new
`services/engine/discovery.py`): enumerate `verticals/*` packages
(`pkgutil.iter_modules` over the `verticals` package path; skip `_template` and any
parked/non-conforming package), import each vertical's `data_adapter` +
`handlers`, and call its `register_<ns>_adapter` / `register_<ns>_handlers` if
present. Wrap each vertical in `try/except` (AC-3, log + continue). Guard against
duplicates (check `registry.verticals()` / catch the duplicate `RegistryError`) so
discovery is idempotent (AC-2). Deterministic order (sorted) (AC-1).

### Step 2 — Wire `main.py` to discovery; drop the onboarding edit (D5)

Replace the `main.py:40-42` hand-wired map with a `discover_and_register(registry)`
call at startup. Update the scaffold/intake flow (PLAN-0016/0017) to stop editing
`main.py`, and update `tests/api/test_intake_routes.py:256` to assert the new
behaviour (no `main.py` edit; the new vertical is discovered) (AC-5).

### Step 3 — Reset + back-compat reconciliation (D3/D4)

Confirm `_reset_registry` wipes discovered state and discovery is re-runnable after
reset (AC-4); reconcile the explicit `register_*` call sites (tests/benchmarks) so
they coexist with discovery (AC-2/AC-6) — keep them as the explicit-API regression
coverage.

### Step 4 — Tests

Offline tests: discovery registers all 3 verticals (AC-1); idempotency — discovery
after an explicit register does not raise (AC-2); failure-isolation — a stub broken
vertical is skipped, others still register (AC-3); reset-then-rediscover (AC-4);
explicit-registration back-compat unchanged (AC-6).

### Step 5 — Gate

`ruff` + `mypy --strict` clean; `uv run pytest -q` green vs baseline (AC-7).

### Step 6 — Handback → Code commits + executes (gated)

Hand the uncommitted draft back to Code. Code reviews, commits this PLAN via a
`docs(plans):` chore PR (ADR-009 D2). **Implementation waits on ADR-0023 Accepted**
(CLAUDE.md §8); then Code implements on a `feat/*` branch + PR (offline-only),
reconciles `docs/STATUS.md`, and on completion `git mv docs/plans/0032-*.md
docs/plans/done/`.

## Verification

- **Discovery (AC-1/AC-3):** offline tests show all 3 verticals registered via
  discovery, deterministic order, and a broken vertical skipped without aborting
  the rest.
- **Idempotency + back-compat (AC-2/AC-6):** discovery + explicit registration
  coexist with no `RegistryError`; the explicit API is unchanged + still covered.
- **Reset (AC-4):** `_reset_registry` + re-discover round-trips cleanly.
- **Onboarding (AC-5):** a scaffolded vertical is discovered with **no** `main.py`
  edit; the updated `test_intake_routes` asserts it.
- **Gate (AC-7):** `ruff` + `mypy --strict` clean; suite green.
- **No host-state at any point** — engine-internal, offline build + tests.

## Dependency / surfaced

- **Gated on ADR-0023 Accepted** (the construct + SD-A framing + SD-C mechanism).
  This PLAN does **not** re-decide the mechanism — it builds the ratified branch
  (drafted around import-scan; re-points to entry-points if Cray selects that).
- **Couples with PLAN-0031 only loosely** — both are Group B, but B1 (ORM emitter)
  carries no ADR gate and can land first; B2 (this PLAN) waits on ADR-0023. (SD-B
  in the completion handoff records the split rationale.)

## References

- **The construct:** `docs/adr/0023-registry-auto-discovery-plugin-maturity.md`
  (D1 the L1→L2 move; D2/SD-C the mechanism; D3 back-compat; D4 reset invariant;
  D5 remove the `main.py` edit).
- **Code anchors (live, re-verified this session):** `services/engine/registry.py`
  (`:4-6` docstring, `:47`/`:55` register, `:51-52` duplicate guard, `:92` reset);
  `services/api/main.py:20-25`/`:40-42` (imports + the manual map);
  `services/engine/scaffold.py:774`/`:802` (generated entry functions);
  `verticals/<ns>/data_adapter/__init__.py` + `verticals/<ns>/handlers.py`
  (energy/supply_chain/aquaculture entry functions); `tests/conftest.py:13`
  (`_reset_registry`); `tests/api/test_intake_routes.py:256` (the `main.py`-edit
  assertion); the explicit call sites in `tests/api/conftest.py` +
  `benchmarks/*/run_benchmark.py`.
- **Governance / triggers:** ADR-006 D3 (maturity, amended by ADR-0023) + D4 (Rule
  of Three); ADR-007 D1 (discovery unpinned/OQ-6); PLAN-0005 §6.4 OQ-6, §8.1
  register, R5 (reset fixture); CLAUDE.md §1/§3/§6/§8; ADR-009 D1/D2; ADR-012 D4.3.
- **Dispatch + roadmap:**
  `.claude/handoffs/session-67/2026-06-18-1453-code-dispatch-groupb-foundation.md` §2;
  `.claude/handoffs/session-67/2026-06-18-0938-code-session67-roadmap-sequencing-handoff.md`
  §"Phase B / B2".

---

*PLAN-0032, registry auto-discovery (Group B / B2 — the ADR-006 D3 L1→L2 plugin
maturity move). Builds ADR-0023; implementation gated on ADR-0023 Accepted. Drafted
by Cowork (Tier-1, ADR-009 D1); Code reviews, commits (ADR-009 D2), and executes;
Cray ratifies ADR-0023. Engine-internal; offline-only build (no host-state);
explicit registration + the `_reset_registry` invariant preserved. AI-assisted
(Claude, Cowork session); no `Co-Authored-By` per CLAUDE.md §7.*
