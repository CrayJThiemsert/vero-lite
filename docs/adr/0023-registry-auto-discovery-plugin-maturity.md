# ADR-0023: Registry auto-discovery — vertical plugin maturity L1→L2 (amends ADR-006 D3)

**Status:** Accepted (ratified 2026-06-18 — **SD-A = a new ADR-0023** that amends ADR-006 D3 [not an in-place edit] · **SD-C = import-scan** over `verticals/*` [Python entry-points = the L3 future seam])
**Date:** 2026-06-18 (drafted Proposed) · 2026-06-18 (ratified Accepted)
**Deciders:** Jirachai Thiemsert (founder) — ratified the construct AND resolved SD-A (framing) + SD-C (mechanism) in-session 2026-06-18
**Related:** ADR-006 (vertical plugin architecture — **this ADR amends D3** [template maturity L1/L2] and is gated by D4 [Rule of Three]); ADR-007 (OCT engine contracts — D1 "plugin discovery" mechanism left unpinned, see OQ-6); ADR-008 (YAML ontology — each vertical declares its objects/adapters); PLAN-0005 (§6.4 OQ-6 "explicit registration, no import-scan discovery"; §8.1 deferred-foundational register; R5 registry-reset fixture); PLAN-0016 / PLAN-0017 (new-vertical scaffold + live co-creation intake — the flows that currently *edit* `main.py`); CLAUDE.md §1 (vertical plugin architecture = part of the moat), §3 (Action layer registers at runtime), §6 (Decision Flow); ADR-009 D1/D2 (Cowork drafts, Code commits); ADR-012 D4.3 (author≠reviewer disclosure); ADR-013 (phased autonomy relocation — Cowork = advisory governance drafter)

> **Authoring disclosure (ADR-012 D4.3).** Drafted (uncommitted) by Cowork
> (Tier-1, ADR-009 D1) from Code's session-67 dispatch
> (`.claude/handoffs/session-67/2026-06-18-1453-code-dispatch-groupb-foundation.md`).
> The trigger (Rule-of-Three met), the L1→L2 framing, the gap evidence, and the
> mechanism axis were **originated in Code's dispatch + Cray's Group-B trigger
> decision**, not in a Cowork free-form self-deliberation — so this is **not** an
> ADR-012 D4.3 self-deliberation case (no Cowork opinion is silently promoted).
> The drafter is Cowork; the **independent reviewers are Cray at ratification +
> Code at PR review**. Separation drafter↔reviewer is **intact**. Cowork
> re-verified every cited code line / file / symbol against the live repo this
> session (fact-pack-first, ADR-009 D1 Tier-1 rule #4).

> **Why a new ADR rather than an in-place edit of ADR-006 (SD-A).** ADRs are
> immutable decision records; the repo convention is **new-ADR-amends-old**
> (ADR-0021 amended ADR-008 D3 via a new ADR, not an in-place rewrite), and
> editing an Accepted ADR in place is the **G1 trap** the dispatch routing flags.
> This ADR therefore **records the L1→L2 amendment to ADR-006 D3** as a standalone
> decision and cross-links both ways. **SD-A was surfaced, not silently chosen —
> Cray selected the new-ADR framing at ratification (2026-06-18; see
> §"Surfaced decisions").**

> **Ratification — RESOLVED (2026-06-18).** Cray ratified this ADR Proposed →
> Accepted in-session, resolving the two surfaced decisions: **SD-A = a new
> ADR-0023** that amends ADR-006 D3 (not an in-place edit) · **SD-C = import-scan**
> over `verticals/*` as the discovery mechanism (Python entry-points recorded as
> the L3 / commercial future seam). The construct (D1–D5) is **unchanged** from the
> Proposed draft — only the ratification outcome is recorded. The §"Surfaced
> decisions" tables are retained as the record of what was weighed, with the
> selected branch marked **← SELECTED**. PLAN-0032 (B2) implementation is now
> unblocked (impl-gate ADR-0023 Accepted satisfied).

## Context

### What ADR-006 D3 set, and why discovery was deferred

ADR-006 **D3** set the Phase-1 template-maturity target at **L1 Scaffolded**
(skeleton + how-to guide; 3–5 days to spin up a vertical) and named **L2** as the
*CLI generator* (`vero-lite new-vertical <name>`, Phase 2). **Registry discovery
rides L2.** Consistent with that, PLAN-0005 **§6.4 (OQ-6, Cray 2026-05-21)**
resolved Phase-2 registration to be **explicit** —
`register_adapter` / `register_handler` calls, *"not entry-point packaging or
import-scan discovery"* — an intentional "do the simple thing first." That
simplification was logged in PLAN-0005 **§8.1** as a deferred-foundational item:

> *Explicit registry (OQ-6) — trigger: vertical #2/#3, or the `new-vertical`
> generator → **ADR-006 D3 L2**.*

### The live state today (re-verified this session)

- `services/engine/registry.py` — a process-global `registry` singleton; explicit
  `register_adapter` (`:47`) / `register_handler` (`:55`); module docstring
  (`:4-6`) states *"no entry-point packaging, no import-scan discovery"* (OQ-6).
- Each active vertical exposes **conventional entry functions**:
  `register_<ns>_adapter()` in `verticals/<ns>/data_adapter/__init__.py`
  (energy `:109`, aquaculture `:96`) and `register_<ns>_handlers()` in
  `verticals/<ns>/handlers.py` (energy `:59`, aquaculture `:64`,
  supply_chain `:60`). `services/engine/scaffold.py` **generates** these same two
  functions for a new vertical (`register_<ns>_adapter()` `:774`,
  `register_<ns>_handlers()` `:802`).
- They are **hand-wired** in `services/api/main.py:40-42` via a name→callables map:

  ```python
  "energy": (register_energy_adapter, register_energy_handlers),
  "supply_chain": (register_supply_chain_adapter, register_supply_chain_handlers),
  "aquaculture": (register_aquaculture_adapter, register_aquaculture_handlers),
  ```

- The new-vertical **scaffold / intake** flow (PLAN-0016 / PLAN-0017) currently
  **edits `main.py`** to insert each new vertical's tuple —
  `tests/api/test_intake_routes.py:256` asserts the inserted line
  (`'"cold_room": (register_cold_room_adapter, register_cold_room_handlers),'`).
- `tests/conftest.py:13` — the autouse `_reset_registry` fixture wipes the
  process-global registry between tests (PLAN-0005 R5).

### Why the trigger has fired

Rule of Three (ADR-006 **D4**; CLAUDE.md §1) requires **3 working verticals**
before extracting an abstraction. **energy + supply_chain + aquaculture** now
satisfy it. Both PLAN-0005 §8.1 triggers ("vertical #2/#3" *and* "the
`new-vertical` generator") have occurred. The deferred "simple thing first" is now
the bottleneck: **every new vertical requires a manual `main.py` edit** (or
codegen that edits `main.py`) — not a true plugin, doesn't scale, and is the
exact **L1→L2 maturity move** ADR-006 D3 anticipated.

## Decision

### D1: Adopt registry auto-discovery as the ADR-006 D3 L1→L2 maturity move (amends ADR-006 D3)

A vertical that lives under `verticals/<ns>/` and exposes the conventional
registration entry functions is **discovered and registered at runtime** without a
hand edit to `services/api/main.py`. **This ADR amends ADR-006 D3**: the **L2**
maturity level now explicitly includes **runtime registry discovery** of
verticals — the registry no longer requires hand-wiring per vertical. (ADR-006 D3
L1/L2/L3 levels are otherwise unchanged; L3 web-UI self-service is untouched.)

### D2: Discovery mechanism — import-scan over `verticals/*` (SD-C: RESOLVED 2026-06-18 — import-scan ← SELECTED)

> *Cray selected **import-scan** at ratification (2026-06-18); Python entry-points
> are recorded as the L3 future seam. The §"Surfaced decisions" SD-C table is
> retained as the record of what was weighed (import-scan ← SELECTED).*

Discovery walks the `verticals/` package, and for each vertical package that
exposes the conventional entry points (`register_<ns>_adapter` in
`data_adapter`, `register_<ns>_handlers` in `handlers`), imports and invokes them
against the process-global `registry`. Rationale for import-scan over Python
entry-points:

- **Monorepo posture.** ADR-006 Alternative 2 *rejected* verticals-as-separate-
  packages for Phase 1; verticals are in-tree, so packaging-metadata entry-points
  buy nothing yet.
- **Dependency-conservative.** The project is deliberately dep-light
  (`code_generator.py` docstring); import-scan is stdlib (`importlib` +
  `pkgutil`), no packaging build step.
- **The seam already exists.** All three verticals *and* the scaffold generator
  already emit the conventional `register_<ns>_*` functions — discovery rides the
  naming convention already in place.

**Entry-points (packaging metadata) are named as the L3 / commercial future
seam** — when verticals become separately installable/versioned (ADR-006 L3 web
self-service; the Alternative-2 "independent release cadence" revisit) — not now.

### D3: Back-compat — explicit registration stays valid (additive, not a replacement)

Discovery is **additive**. `register_adapter` / `register_handler` remain valid
and unchanged; discovery simply calls the same registry methods on the caller's
behalf. Because `register_adapter` raises `RegistryError` on a **duplicate**
(`registry.py:51-52`), discovery and explicit registration of the *same* vertical
must not both run — discovery must be **idempotent / guarded** (skip an
already-registered vertical, or own registration entirely so callers stop
double-registering). The build PLAN (PLAN-0032) specifies the exact guard.

### D4: Test-resettability invariant retained (PLAN-0005 R5)

The autouse `_reset_registry` fixture (`tests/conftest.py:13`) must continue to
fully wipe discovered state between tests, and discovery must be **re-runnable
after a reset** — i.e. discovery must not rely on import-time-only side effects
that survive `registry.reset()` and cannot be re-triggered. Discovery is a
callable the test harness (and `main.py` startup) can invoke deterministically,
not a one-shot import side effect.

### D5: Remove the per-vertical `main.py` edit from the onboarding path

Auto-discovery removes the need for the scaffold / intake flow (PLAN-0016 /
PLAN-0017) to **edit `main.py`** to register a new vertical. The registration map
(`main.py:40-42`) and the test asserting the edit
(`tests/api/test_intake_routes.py:256`) are **updated or retired** by the B2 build
(PLAN-0032) — a deliberate, tested change, not a silent removal. This closes the
"onboarding edits core" fragility that makes a new vertical a non-plugin today.

## Surfaced decisions (RESOLVED at ratification 2026-06-18)

> Both axes were drafted as un-decided options; **Cray resolved them at
> ratification (2026-06-18)** — the **← SELECTED** markers below record each chosen
> branch (the full option tables are retained as the record of what was weighed).

### SD-A — Record the L1→L2 amendment as a NEW ADR vs an in-place edit of ADR-006 D3. *(Cowork recommended: new ADR — this one. **Cray selected new-ADR at ratification, 2026-06-18.**)*

| Option | Shape | Trade-off |
|---|---|---|
| **New ADR-0023 (recommended) ← SELECTED** | A standalone decision record that amends ADR-006 D3 + cross-links. | Matches repo convention (ADR-0021 amended ADR-008 D3 via a new ADR); preserves ADR-006 as an immutable historical record; clean own-ratification; avoids the G1 in-place-edit-of-Accepted-ADR trap. Slight cost: the plugin-architecture story spans ADR-006 + ADR-0023 (mitigated by explicit cross-links both ways). |
| **Amend ADR-006 D3 in place** | Edit the Accepted ADR-006 D3 table/text directly. | One citation anchor for the whole plugin story. But rewrites an Accepted decision record (loses immutability), and in-place edits of an Accepted ADR are the **G1 trap** the dispatch routing flags. |

*Cray selected the new-ADR form at ratification (2026-06-18)* — this file stands as
the standalone ADR amending ADR-006 D3; the in-place-edit option was weighed and not
taken.

### SD-C — Discovery mechanism: import-scan vs Python entry-points (D2). *(Cowork recommended: import-scan. **Cray selected import-scan at ratification, 2026-06-18.**)*

| Branch | Mechanism | Trade-off |
|---|---|---|
| **import-scan (recommended) ← SELECTED** | `importlib`/`pkgutil` walk of `verticals/*`; invoke each vertical's conventional `register_<ns>_*` entry functions. | Simplest; stdlib-only; no packaging change; rides the naming convention already emitted by every vertical + the scaffold. Needs a per-vertical **import-failure-isolation** story (a broken vertical must not crash discovery for the others). |
| **Python entry-points** | Declare each vertical as a packaging entry-point; discover via importlib.metadata. | The "real" plugin seam for *separately installed* verticals; but adds packaging metadata + a build step, and ADR-006 Alt-2 rejected separate vertical packages for Phase 1 → premature. |

*Cray selected import-scan at ratification (2026-06-18).* PLAN-0032's
mechanism-specific steps follow the selected branch (import-scan); Python
entry-points stay reserved for the L3 future seam.

## Consequences

### Positive

- **True plugin onboarding (ADR-006 D3 L2).** Drop a vertical under `verticals/`
  with the conventional entry functions → it is found and registered. No core
  edit. Directly advances the CLAUDE.md §1 vertical-plugin-architecture moat and
  unblocks the Phase-C "user context → new vertical" flow end-to-end.
- **Removes the "onboarding edits core" fragility.** The scaffold/intake flow no
  longer rewrites `main.py`; one fewer brittle codegen-edit seam.
- **Rule-of-Three-honest.** The abstraction is extracted *after* 3 verticals
  validate the registration pattern (ADR-006 D4), not before.

### Negative

- **Discovery needs a failure-isolation + ordering policy.** Under import-scan, a
  broken/partial vertical package must be skipped with a clear error, not crash
  startup; discovery order must be deterministic. A real, bounded design cost
  carried into PLAN-0032.
- **A subtle duplicate-registration footgun** (D3): mixing discovery with leftover
  explicit `register_*` calls trips `RegistryError`. Requires a guard + a
  migration of existing call sites (tests/benchmarks that call `register_*`).
- **Blast radius on the intake/scaffold tests** (D5): `main.py:40-42` +
  `test_intake_routes.py:256` change — tested, not silent, but real surface area.

### Neutral

- **The deterministic/explicit path is untouched** as an API — `register_adapter`/
  `register_handler` stay valid (D3); discovery is a convenience layer on top.
- **No ontology / engine-contract change.** This is a registration-wiring maturity
  move; ADR-007 D2 envelopes and ADR-008 ontology are unaffected.

## Alternatives Considered

### Alternative 1: Keep explicit registration (status quo)

- **Pros:** zero work; simplest possible; OQ-6's deliberate Phase-2 choice.
- **Cons:** **this is the gap** — every vertical is a manual `main.py` edit; not a
  plugin; doesn't scale; blocks Phase-C end-to-end onboarding.
- **Why rejected:** the PLAN-0005 §8.1 trigger has fired (Rule of Three met +
  the `new-vertical` generator exists). Deferring further contradicts ADR-006 D3.

### Alternative 2: Python entry-points now (instead of import-scan)

- **Pros:** the canonical plugin seam; supports separately-installed verticals.
- **Cons:** packaging-metadata overhead + a build step for in-tree verticals;
  ADR-006 Alt-2 rejected separate vertical packages for Phase 1.
- **Why not now:** recorded as fork branch **SD-C / entry-points**; reserved for
  L3 when verticals are independently versioned/installed.

### Alternative 3: Edit ADR-006 D3 in place (instead of a new ADR)

- **Pros:** single citation anchor for the plugin architecture.
- **Cons:** rewrites an Accepted decision record (immutability loss); the G1
  in-place-edit trap.
- **Why not chosen:** recorded as **SD-A / in-place**; **Cray selected the new-ADR
  form at ratification (2026-06-18).** The new-ADR form (this file) is the
  convention-aligned outcome.

## References

- **ADR being amended:** `docs/adr/0006-vertical-plugin-architecture.md` (D3
  template maturity L1/L2/L3 `:46-52`; D4 Rule of Three `:56-60`; §5 pattern #2/#3
  "register at runtime").
- **The deferred-foundational decision + trigger:**
  `docs/plans/done/0005-oct-engine-runtime-layer.md` §6.4 (OQ-6 explicit
  registration), §8.1 register (explicit-registry row → "ADR-006 D3 L2"), R5
  (registry-reset fixture).
- **Live code (re-verified this session):** `services/engine/registry.py:4-6`
  (the "no discovery" docstring), `:47`/`:55` (`register_adapter`/`register_handler`),
  `:51-52` (duplicate `RegistryError`), `:92` (`reset`); `services/api/main.py:20-25`
  (imports), `:40-42` (the manual registration map);
  `services/engine/scaffold.py:774`/`:802` (generated `register_<ns>_adapter`/
  `register_<ns>_handlers`); `verticals/energy/data_adapter/__init__.py:109`,
  `verticals/aquaculture/data_adapter/__init__.py:96`, `verticals/energy/handlers.py:59`,
  `verticals/aquaculture/handlers.py:64`, `verticals/supply_chain/handlers.py:60`
  (the conventional entry functions); `tests/conftest.py:13` (`_reset_registry`);
  `tests/api/test_intake_routes.py:256` (the `main.py`-edit assertion).
- **Governance:** `docs/adr/0000-template.md`; CLAUDE.md §1/§3/§6; ADR-007 D1
  (plugin discovery unpinned); ADR-009 D1/D2; ADR-012 D4.3; ADR-013;
  `docs/adr/0021-metric-kind-typed-ontology-semantics.md` (the new-ADR-amends-old
  precedent for SD-A).
- **Build PLAN:** `docs/plans/0032-registry-auto-discovery.md` (PLAN-0032 builds
  this once Accepted; impl-PR gated on this ADR Accepted, CLAUDE.md §6/§8).

## Implementation Notes

- **Number:** `0023` confirmed free at authoring — highest used = ADR-0022;
  ADR-0014 is WITHDRAWN; no `0023` file exists (Glob of `docs/adr/` this session).
  Code confirms at commit.
- **Routing + ratification flow (mirror ADR-0022 exactly):**
  1. **Cowork** authors this draft (**Proposed**) — framing + SD-A/SD-C surfaced +
     the author≠reviewer disclosure. *(done)*
  2. **Code** commits it **Proposed** via a `docs(adr):` chore PR (ADR-009 D2).
  3. **Cray** ratifies **Proposed → Accepted**, resolving **SD-A** (amend-framing)
     + **SD-C** (mechanism). Cowork authored, so **Cray is the independent
     reviewer** (ADR-012 D4.3 independent-deliberation check). **✓ done
     (2026-06-18, session 67: SD-A = new ADR-0023 amends ADR-006 D3; SD-C =
     import-scan; Python entry-points = L3 future seam).**
  4. **Then** PLAN-0032 builds B2 (the entity gate: this ADR Accepted, CLAUDE.md
     §6 Decision/Plan Flow + §8 ADR-Accepted-before-impl). **✓ gate satisfied.**
- **B1 is independent of this ADR.** The ORM emitter (PLAN-0031) is an additive
  generator artifact with **no** ADR gate; it had no dependency on this ADR's
  ratification and may land independently (see SD-B in the completion handoff).
- Drafted by Cowork (Tier-1, ADR-009 D1); uncommitted. Code reviews + commits.
  AI-assisted (Claude); no `Co-Authored-By` per CLAUDE.md §7.
