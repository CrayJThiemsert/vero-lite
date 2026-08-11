# ADR-0036: Vertical-as-system — the multi-vertical demo portal: one published system per deployed vertical instance (extends ADR-0035 L9/D4; zero engine change)

**Status:** Accepted
**Date:** 2026-08-06 (ratified 2026-08-09, session 218)
**Deciders:** Jirachai Thiemsert (Cray). Five calls were LOCKED (typed by Cray,
2026-08-06) before drafting — restated below, not re-litigated. This ADR decides
the design **within** them and surfaces the remaining parameters.
**Related:** ADR-0035 (hosting + exposure model — **extended, not amended**: every
decision here works inside its D1–D4, including the 2026-08-06 reading-(a)
connector-ownership amendment), PLAN-0100 (the exposure PLAN — its Step 8
`deploy/published/` artifact is this ADR's per-system template; its owed
`OCT_VERTICAL` pin is discharged by D4 below), PLAN-0095 (the hosting-agnostic
image every system boots), ADR-0032 (D1.2 — a governed hero is bespoke per design
partner; D5 positioning discipline), ADR-0023 (registry auto-discovery — why the
engine already *contains* every vertical while each process *serves* one),
CLAUDE.md §1 (the three OCT features; Rule of Three), §8 (host-state gate),
ADR-009 D1/D2 + ADR-012 D4.3 + ADR-013 D1 (drafting route + disclosure).

> **Drafting provenance (ADR-012 D4.3 / ADR-013 D1).** Drafted by the in-harness
> `plan-drafter` subagent from a Code-authored dispatch (2026-08-06); the LOCKED
> calls are Cray's typed picks, not drafter inferences. Every `file:line` fact
> below was re-verified on disk by the drafter this session; the one fact that
> cannot be verified from this repo (whether the portal repo has been stood up)
> is handled by construction, never assumed (D6). Independent review: Code (R2)
> at PR; ratification: Cray. Author≠reviewer separation: **INTACT**. Uncommitted
> draft — Code commits per ADR-009 D2.

> **Amendment pass 2026-08-11 (session 222; drafted in-harness by `plan-drafter`
> from a Code dispatch).** One site: the D2 subdomain-label paragraph's factual
> claim that the apex domain "appears nowhere in this repo" was **false at
> ratification** and is corrected by the inline note there — the domain appears
> at five places in one archived PLAN, all written after ADR-0035's rule was
> live. The label convention, the `_`→`-` mapping, and the single-place-binding
> rule are unchanged; no decision is reopened. Remedy per Cray (typed, s222):
> annotate the ADRs; do **not** edit the archived PLAN. The underlying
> collision — ADR-0035 D1(3)'s broad clause vs the evidence discipline — is
> surfaced as **ADR-0035 OQ-6, open, not ruled**. `Status:` is unchanged.
> Author≠reviewer separation: **INTACT** (drafter authored; Code R2 + Cray
> review at PR).

## Context

### Why now — the requirement ADR-0035 does not cover

Cray's requirement: **open the demo and pick which vertical to view** —
procurement / energy / fleet_maintenance. ADR-0035 built a **multi-SYSTEM**
portal: one domain, a subdomain per system, each system its own compose project
(`-p`) and Docker network (L9, `0035:237-250`); "vero-lite (`oct.`) is the first
system" — **singular**. Its D1–D4 are "portal-level and permanent"
(`0035:254-257`). Nowhere does it address multiple **VERTICALS** of one codebase
being separately viewable. That gap is architectural, not operational: whether a
deployed vertical instance counts as a "system" determines whether the answer is
N compose projects (config) or an engine re-architecture (code).

### The measured fact base — one process serves exactly one vertical

All facts re-verified on the working tree this session (2026-08-06):

| # | Fact | Grounding |
|---|---|---|
| F1 | **No route accepts a vertical parameter.** Fifteen router call sites read the process-wide `settings.oct_vertical` directly: `query.py:52,58` · `insights.py:134,185,214,296` · `actions.py:183,204,217,275` · `runs.py:230,283,384,453` · `demo.py:149`. The code states it: *"Runs are scoped by the single active vertical (`settings.oct_vertical`)"* | `services/api/routers/runs.py:279` + the census |
| F2 | **Auth is vertical-scoped — the hardest blocker to in-process serving, and ADR-level.** The principal index resolves from `settings.oct_vertical` (`auth.py:82`); an authenticated subject with no `Person` in the active vertical is 403'd by name (`auth.py:85-92`). Two verticals in one process = two DOA/SoD rosters live at once — a question about *who can approve what*, not a routing detail | `services/api/auth.py:82-92` |
| F3 | **Executors are active-vertical-only.** The lifespan registers the procedure-executor factory for the `OCT_VERTICAL`-selected vertical alone; a run on any other vertical 409s at gate-resolve | `services/api/main.py:300-302` |
| F4 | **`/meta` cannot feed a picker** — `OntologyMeta.vertical: str`, singular; there is no "available verticals" list on the UI's boot fetch | `services/engine/ontology_meta.py:145` |
| F5 | **The registry already holds everything.** `discover_and_register()` registers adapters + handlers for **all** discovered verticals at boot; the single-vertical limit lives in the routers, not the registry | `services/api/main.py:282-289` |
| F6 | **One surface is already multi-vertical:** `GET /procedures` iterates `registry.verticals()` and projects every discovered vertical — breadth is visible today on exactly one read-only tab | `services/api/routers/procedures.py:102-121` |
| F7 | **Hero coupling.** `_HERO_BUILDERS` carries only `procurement` + `fleet_maintenance` (`demo.py:132-135`); `_FALLBACK_VERTICAL = "procurement"` (`:61`); the fallback resolves at **request** time (`:142-149`). A published `OCT_VERTICAL=energy` process would therefore serve procurement's Fastenal hero under an energy banner. Fleet's hero is offline-only by design — `live=true` is refused, not faked (`demo.py:108-117`) | `services/api/routers/demo.py` |
| F8 | **One-process-per-vertical is already the practice.** Cray's local launch file carries seven configs, four of them `OCT_VERTICAL`-pinned to distinct verticals on distinct ports (8098 supply_chain, 8101 procurement, 8102 building_materials, 8103 fleet_maintenance). Untracked working file — empirical corroboration, not a governed artifact | `.claude/launch.json` |
| F9 | **The per-system template exists in flight.** PLAN-0100 Step 8 builds `deploy/published/`: a committed compose project of exactly `app` + `cloudflared`, no `ports:` keys, a committed anchored-regex ingress allowlist ending in the catch-all `http_status:404`, a pinned env file — and it still owes its `OCT_VERTICAL` pin (*"§Pinned values, still UNPINNED"*). The DB-less boot guarantee was verified for `energy` only | `docs/plans/0100-exposure-published-demo-surface.md:856-915`, `:867`, `:897-899` |

### The scope question that must be answered first

ADR-0035 D4 assigns the portal repo's files to the portal repo: *"The portal
repo's scaffolding is **out of scope here by dispatch** — this ADR fixes the
arrangement's shape, not its files"* (`0035:424-430`), and D1(3) makes vero-lite
domain-ignorant: the domain appears in exactly one layer — the portal repo's
ingress map + DNS — *"nothing in this repo may reference the portal domain"*
(`0035:280-285`). L5 (Cray, typed, s172) says the portal is not built inside
vero-lite. So a vero-lite artifact "standing up the portal repo" collides with
the Accepted ADR that created the portal — unless the collision is resolved
explicitly. D1 below resolves it.

## LOCKED (Cray, typed 2026-08-06 — restated, not re-litigated)

1. **Deployment-level portal is the direction** — one compose project per
   vertical. In-process multi-vertical serving (one process, per-request
   vertical, a UI picker) is **not** being built now.
2. **`OCT_VERTICAL=energy` is system #1**; procurement follows as system #2.
3. **`/demo/hero/*` is dropped from the energy system's route allowlist** — each
   system tells ONE clean story: the energy system = the three OCT features
   (ontology map · NL query · anomaly + suggested action — CLAUDE.md §1); the
   procurement system = the governed hero (bespoke per design partner, ADR-0032
   D1.2).
4. **ADR-0035 D1–D4 are portal-level and permanent** (`0035:254-257`) — this ADR
   works inside them; any amendment would need explicit argument and citation
   (none is made: D2 below shows none is needed).
5. **Only Code commits** — this draft lands via Code's PR (ADR-009 D2).

## Decision

Six decisions. D1 rules the scope question; D2 is the architectural core; D3–D5
apply it; D6 names the follow-on work without drafting it.

### D1 — Scope ruling: this decision enters vero-lite as an ADR extending ADR-0035; the portal repo's files stay out (SD-1 = option (a))

**Ruling: (a).** This document is a new ADR in vero-lite that extends ADR-0035's
L9/D4 vocabulary; once Accepted, a vero-lite PLAN for **vero-lite's side** of the
multi-vertical arrangement becomes legitimate. The portal repo's own files —
the cross-system ingress map, the Access policies, the `portal.` landing
surface, its connector — remain the portal repo's property, exactly per
ADR-0035 D4 as amended (`0035:432-456`). Nothing in this ADR or its follow-on
PLAN creates, names, or assumes those files.

Why not **(b)** — a vero-lite PLAN directly: the requirement rests on an
unresolved architectural question (is a vertical a system?). A PLAN that assumed
the answer would smuggle an architecture decision past the ADR discipline
(CLAUDE.md §8: ADRs merge before related implementation); a PLAN that decided it
would be the wrong artifact class. D4's "out of scope here by dispatch" was a
scoping of ADR-0035's own drafting, not a standing prohibition on ever deciding
portal-adjacent questions — but the *first* artifact after it must be the one
that says what the arrangement **is**, and that is an ADR.

Why not **(c)** — everything in the portal repo, vero-lite gets a pointer: the
vertical-as-system ruling is a reading of **vero-lite's** architecture (what one
`OCT_VERTICAL` process is — F1–F7), and under ADR-0035 D4-as-amended each
system's connector service, committed route-allowlist config, and tunnel
credentials are **that system's property, in that system's repo**
(`0035:432-456`). Every vero-lite vertical-system's home is this repo, so
vero-lite owns real work here — N published profiles, N allowlists, the energy
hero-drop — not a pointer. The portal repo cannot rule what a vero-lite vertical
is, and this repo cannot even verify that the portal repo exists yet (D6).

### D2 — A deployed vertical instance IS a system under L9/D4 (SD-2 = yes)

**Ruling: yes.** ADR-0035 never defines "system" intensionally; it defines it
**operationally**, by what a system owns: one subdomain, one Access policy, one
compose project on its own Docker network — containing its own connector, its
committed route-allowlist config, and its secret-held tunnel credentials (the
restated D4 acceptance shape, `0035:478-493`). A deployed vertical instance —
the PLAN-0095 image + `OCT_VERTICAL=<v>` + the Step 8 compose shape — satisfies
every clause with **zero engine change**: the process already serves exactly one
vertical (F1–F3), and the deployment unit is already the practice (F8). The L9
sketch's `oct.` label (`0035:243-250`) was the single-system illustration, not a
constraint; L9's substance — one domain, subdomain per system, per-system
isolation — is *multiplied*, not modified.

**Drift check, explicitly:** admitting the energy system, then the procurement
system, costs the portal side exactly the two artifacts the restated acceptance
shape allows — one subdomain (DNS/ingress entry) + one Access policy — with
everything else riding inside the one compose project each system was always
required to bring (`0035:478-493`). The D4 reopening trigger does **not** fire.
This is why LOCKED-4 needs no amendment: the ruling is an application of D4, not
a change to it.

**Subdomain-label convention.** Each vero-lite vertical-system takes the label
`oct-<vertical-id>`, with `_` mapped to `-` (DNS labels forbid underscores):
`oct-energy.` · `oct-procurement.` · `oct-fleet-maintenance.`. Labels only — the
apex domain appears nowhere in this repo, per D1(3) (`0035:280-285`); the
label→system binding is written in exactly one place, the portal repo's
cross-system ingress map (`0035:432-456`).

> **Amended 2026-08-11 (session 222) — factual correction; the convention
> stands.** "The apex domain appears nowhere in this repo" was false when this
> ADR was ratified (2026-08-09, s218). A repo-wide search finds the apex domain
> at **five places in one tracked file** —
> `docs/plans/done/0100-exposure-published-demo-surface.md`, working-tree lines
> 1101, 1702, 1719, 1726, 1967 at this amendment (the string itself is
> deliberately not reproduced here, per the very clause under discussion; the
> `0035:280-285` citation above has since drifted — cite it stably as
> **ADR-0035 D1 item 3, "One domain, subdomains per system (L9), movable by
> design (L6)"**, by item number and title rather than line range, because a
> line range rots as its file grows: this one rotted twice within two weeks,
> the second time inside this very amendment pass, whose own ADR-0035 header
> note moved D1(3) again — the same fix PLAN-0103 Step 7's s220 correction
> adopted, citing by branch/symbol so the reference cannot rot the same way
> again). All five are evidence records of work
> against the live zone: the rate-limiting rule as deployed (s215), the s216
> Safe-Browsing incident — the flagged login-callback URL, the name-collision
> theory in which the domain string itself is the evidence, and the Search
> Console recovery step that takes the domain as its input — and the
> 2026-08-05 zone-quota reading. The dating matters: ADR-0035 landed
> 2026-08-01 (`234c40f`); the references entered in three commits **after**
> the rule was live — 2026-08-05 (`36221a8`) and 2026-08-08 (`5934f1a`,
> `c3c7b8c`) — so this is not pre-rule residue that nobody swept, and all
> three predate this ADR's ratification. Say the breach precisely: ADR-0035
> D1(3) has two clauses of different scope. Its **narrow runtime clause** —
> the domain never in "any system's application code, image, compose file, or
> env contract" — **holds**: the runtime is domain-ignorant, and moving
> domains is still re-pointing DNS with zero application change. What is
> breached is the **broad documentary clause** ("nothing in this repo may
> reference the portal domain"), five times in one file. **Remedy (Cray,
> typed, s222): do NOT edit the archived PLAN; correct this ADR so it stops
> asserting something false.** The repository is public (CLAUDE.md §1/§8) and
> the string is in git history regardless — deleting it from a working file
> would buy the feeling of cleanliness rather than the fact of it, while an
> ADR that asserts a false fact about its own repository actively misleads the
> next reader into not checking. The dangerous artifact is the false claim,
> not the leaked string. Whether the broad clause should govern evidence
> records at all is **ADR-0035 OQ-6 — surfaced the same day, open, Cray's to
> rule.** Everything else in this paragraph — labels only, `_`→`-`, the
> label→system binding written in exactly one place — is correct and
> unchanged.

**How the `portal.` landing surface learns the list.** From the cross-system
ingress map — the one place subdomain→system bindings exist — by whatever
mechanism the portal repo chooses (generated page, config read; its concern).
Binding constraint from this side: **no second registry of systems may exist
anywhere, and vero-lite contributes nothing to the list** — this repo stays
portal-ignorant (ADR-0035 D4). A vero-lite file that enumerated the published
systems would be a shadow ingress map and a D1(3) leak waiting to happen.

### D3 — Selection is deployment-level; in-process multi-vertical serving is a recorded non-goal (LOCKED-1)

The "pick a vertical" experience is the `portal.` landing surface linking to N
vertical-systems — selection by navigation, not by application state. In-process
multi-vertical serving (one process, per-request vertical, an in-app picker) is
**not built now**, and this ADR records the measured blocker list so a future
proposal starts from evidence, not archaeology:

- **The authority blocker (ADR-level):** the principal index is resolved from
  the process-wide vertical (`auth.py:82`); per-request verticals would put two
  DOA/SoD rosters live in one process, and an API key's identity would become
  request-dependent (`auth.py:85-92`). This is a governance-model question, not
  a refactor.
- **The executor blocker:** factories register for the active vertical only
  (`main.py:300-302`) — every other vertical's runs 409.
- **The breadth of the seam:** fifteen call sites across five routers read
  `settings.oct_vertical` (F1), and `/meta` is singular (F4).

If in-process serving is ever wanted, it is **its own ADR** with the authority
question at its center. Nothing here forecloses it; everything here makes it
unnecessary for the demo.

### D4 — System #1 is energy, system #2 is procurement; one story per system (LOCKED-2, LOCKED-3)

- **System #1 = `OCT_VERTICAL=energy`** (Cray, typed). This **discharges
  PLAN-0100 Step 8's owed `OCT_VERTICAL` pin** (`0100:867`) — the pin's value is
  now governance-recorded, and energy is the one vertical whose DB-less boot was
  verified (`0100:897-899`). PLAN-0100 completes as scoped, for system #1; this
  ADR does not reopen it.
- **The energy system's allowlist drops `/demo/hero/*`** (Cray, typed). This
  removes the two Tab G read rows PLAN-0100's PROVISIONAL table carries
  (`/demo/hero/governance`, `/demo/hero/impact` — `0100:163`). Legal by
  construction: ADR-0035 D5's P12 ruling made the allowlist a labelled
  provisional revisable *"without reopening this ADR"* (`0035:573-584`). The
  reason is F7: energy has no hero, and the request-time fallback
  (`demo.py:149`) would serve procurement's Fastenal story under an energy
  banner — the edge exclusion is the **binding control** against that. App-side
  hardening (refusing the fallback for hero-less verticals) is optional
  defense-in-depth for the follow-on PLAN to consider, not required here.
  **UI corollary, so it is not silently missed:** the energy system's published
  UI profile must not render Tab G at all — a visible tab whose fetches edge-404
  is a broken first impression on exactly the surface the wedge shares
  (ADR-0032 D5).
- **System #2 = procurement**: the governed hero *is* its story (`Tab G` +
  the governed loop). Its own allowlist and arm postures are declared by the
  follow-on PLAN under the same P12 provisional regime, per system.
- **fleet_maintenance is system #3 when Cray triggers it**, same shape; its
  hero is deterministic/offline by design (`demo.py:108-117`), which suits a
  published surface as-is.

### D5 — Per-vertical published profiles: vero-lite owns N committed {allowlist + env} pairs, parameterized from the Step 8 template (SD-3)

**Ruling: vero-lite owns every vertical-system's profile.** Under ADR-0035
D4-as-amended, each system owns its connector service, its committed
route-allowlist config, and its tunnel credentials (`0035:432-456`) — and each
vero-lite vertical-system's repo is this one. Concretely:

- The follow-on PLAN **parameterizes PLAN-0100 Step 8's `deploy/published/`**
  into per-vertical-system profiles (recommended shape, PLAN's to finalize: one
  compose template + one committed `{ingress config, env file}` pair per
  system) — it builds **on** the Step 8 artifact, never replaces it.
- **N near-identical allowlists are accepted at N ≤ 3.** Yes, the energy and
  procurement allowlists will differ by a handful of rows (the hero delta,
  D4). That duplication is taken deliberately under the Rule of Three
  (CLAUDE.md §1): a shared allowlist *source* (generator or include mechanism)
  is extracted only when a third live system demonstrates drift pain, not
  before. Each system's file stays independently readable — which is what the
  AC-6(a)-style set-equality + anchoring guard needs; that guard extends **per
  instance** (one committed config, one guard target, per system).
- **Binding isolation note:** N instances of the compose template must **not**
  share a Docker network. Step 8's single-system network (`vero_oct`,
  `0100:907`) must not become a fixed shared `name:` across projects — a shared
  network would let one system's connector reach another system's `app` by
  name, bypassing its allowlist entirely, which ADR-0035's corollary forbids
  outright (*"no other system's connector may ever join this system's
  network"*, `0035:469-471`). Per-project network uniqueness is an acceptance
  criterion of the follow-on PLAN, not a hope.
- **Aggregate inference posture:** ADR-0035 D5(3)'s in-flight LLM cap is
  per-process; N systems multiply it (N × 1 in-flight against one shared
  Ollama, with P5's eviction hazard unchanged). The follow-on PLAN must state
  the aggregate posture explicitly. Recommendation: keep 1 in-flight per
  system and note that today at most one published system (`oct-energy.`)
  carries an `assisted` route at all — procurement's hero surface is
  deterministic/offline — so the aggregate is not a present hazard; revisit at
  the first observed contention.

### D6 — The follow-on PLAN: named, not drafted (ADR-0035's own pattern)

One vero-lite PLAN (next free number at drafting: PLAN-0103 — a convenience
note, not binding) owns:

1. **First step — confirm and branch:** whether the portal repo has been stood
   up is *unverifiable from this repo* and is **not assumed** in either
   direction. If it exists, coordinate the two portal-side artifacts per system
   (ingress entry + Access policy — requests to the portal repo, not files
   here); if not, that standing-up is the portal repo's own bootstrap
   (ADR-0035 Implementation Note 1, `0035:962-977`), it triggers OQ-4 (Cray
   picks the domain then — `0035:793-798`), and this PLAN proceeds on
   everything host-side and repo-side that does not require it.
2. The **per-vertical published profiles** (D5), starting with
   `oct-energy` (system #1, hero rows dropped — D4) and `oct-procurement`
   (system #2).
3. An **MS-S1 headroom measurement before N systems publish** — RAM/CPU for N
   concurrent app containers is unmeasured and **no number is assumed here**;
   measuring it is an explicit step with its own recorded result.
4. **§8 discipline:** every system brought up on MS-S1 is a host-state change —
   explicit Cray go per addition, do-no-harm duty to co-tenant stacks
   (ADR-0035 D1(5)).
5. The **UI-profile corollary** for hero-less systems (D4) and any optional
   fallback hardening (D4, optional).

What the PLAN does **not** own, restated so no future reader widens it: the
ingress map, the Access policies, the `portal.` landing surface, the domain —
portal-repo property, per ADR-0035 D4/L5, reaffirmed by D1 above.

## Consequences

### Positive

- **The multi-vertical demo costs zero engine change.** The picker is the
  portal's landing surface; every blocker in F1–F7 is routed *around*, not
  through. The demo-selection requirement is met by composition — exactly what
  PLAN-0095's hosting-agnostic image and ADR-0035's per-system isolation were
  built to make cheap.
- **Each system tells one clean story** (LOCKED-3): the energy system shows the
  three OCT features with no Fastenal bleed-through (the F7 fallback is edge-
  excluded); the procurement system leads with the governed hero. Positioning
  stays legible per ADR-0032 D5.
- ADR-0035's arrangement is *exercised*, not amended: system N+1 still costs
  the portal exactly two artifacts (`0035:478-493`), which is the strongest
  evidence L9's "no redesign" clause holds.
- PLAN-0100 is unblocked on its owed pin (`OCT_VERTICAL=energy`, D4) rather
  than reopened.

### Negative (the honest costs)

- **N compose projects to operate on one shared host.** Headroom is unmeasured
  (D6.3 measures before assuming), every addition is a §8-gated host-state
  change, and the do-no-harm duty applies N times.
- **Near-duplicate allowlists are a drift surface** until the Rule-of-Three
  extraction point (D5) — accepted deliberately, with per-instance guards as
  the mitigation.
- **Cross-system GPU contention among vero-lite's own instances is new**: N
  published systems share one Ollama, and ADR-0035's caps are per-process. D5
  bounds it today (one `assisted` system) and names the follow-on posture, but
  the aggregate story is thinner than the single-system one.
- The bare `oct.` label ADR-0035 sketched becomes ambiguous under per-vertical
  labels (OQ-1) — a small naming debt this ADR surfaces rather than silently
  resolves.

### Neutral

- ADR-0035 D1–D4 are untouched (LOCKED-4 honored without exception). D1(3)
  domain-ignorance now covers N label bindings instead of one, all still living
  only in the portal repo's ingress map.
- The tenant key is orthogonal: every demo vertical-system stamps
  `TENANT_ID=demo` (ADR-0035 D7 — tenant = customer organisation, explicitly
  *not* a vertical instance), so N systems for one demo audience remain one
  tenant. Vertical-as-system and tenant-as-organisation compose without
  collision — the case ADR-0035 D7 anticipated ("one customer runs two
  verticals").
- `GET /procedures` (F6) keeps showing engine breadth inside any one system —
  unaffected and unchanged.

## Open Questions

- **OQ-1 — the bare `oct.` label:** retire it, or keep it as a portal-side
  alias/redirect to system #1? Recommendation: **retire** — the sketch label
  was illustrative, and an alias is a second binding to maintain. Portal-side,
  non-blocking (nothing in this repo references any label binding); Cray picks
  when the ingress entries are created — the OQ-4 pattern (`0035:793-798`).
- **OQ-2 — the aggregate in-flight LLM posture across N vero-lite systems:**
  recommendation in D5 (keep 1 per system; today only one published system is
  `assisted`); the follow-on PLAN pins it as a named value.
- **OQ-3 — when fleet_maintenance becomes system #3:** Cray's trigger, not a
  schedule. The shape is fixed by D2/D5; only the go is open.

## Alternatives Considered

### Alternative 1: In-process multi-vertical serving (one process, per-request vertical, UI picker)
- Pros: one deployment; a true in-app picker; no per-system portal artifacts.
- Cons: collides with the measured seam at fifteen call sites (F1), the
  active-vertical executor wiring (F3), the singular `/meta` (F4) — and above
  all the vertical-scoped authority roster (F2), which makes it an ADR-level
  governance question, not a refactor.
- Why rejected: **LOCKED-1 (Cray, typed)**; the blocker record in D3 is kept so
  a future proposal starts honest.

### Alternative 2: A third concept between "system" and "vertical"
- Pros: preserves a reading where "system" means only whole products.
- Cons: everything such a concept would own — subdomain, policy, compose
  project, network, allowlist, credentials — is already exactly what ADR-0035
  D4 gives a *system* (`0035:478-493`). A middle concept would hold no
  property; empty abstractions are how vocabularies rot.
- Why rejected: D2's drift check shows the existing concept fits without
  amendment; the Rule of Three cuts against minting concepts ahead of need.

### Alternative 3: One subdomain with path-based vertical routing (`/energy/*`, `/procurement/*`)
- Pros: one ingress entry; one Access policy.
- Cons: either one process serves all paths (= Alternative 1, rejected) or the
  edge rewrites paths into N backends — which puts *vertical* knowledge into
  the ingress layer, makes every app URL vertical-prefixed (a change PLAN-0095's
  image does not support), and dissolves the per-system isolation unit D4
  builds on (one policy, one network, shared blast radius).
- Why rejected: it re-architects two layers to avoid two config artifacts per
  system that ADR-0035 already prices as acceptable (`0035:478-493`).

### Alternative 4: One shared allowlist source generating all systems' configs, now
- Pros: no near-duplicate files; single point of edit.
- Cons: a generator built for N=2 is speculative abstraction; the committed
  per-system config is what the offline set-equality guard closes on
  (`0100:870-876`), and an indirection layer weakens exactly that check today.
- Why rejected for now: Rule of Three (CLAUDE.md §1) — extract at the third
  system's demonstrated drift pain, not before (D5).

### Alternative 5: Rule and plan all of this in the portal repo; vero-lite gets a pointer (dispatch option (c))
- Pros: keeps vero-lite maximally portal-ignorant.
- Cons: the core ruling is about what a **vero-lite process** is (F1–F7) — the
  portal repo has no standing to rule it and no visibility into this code; and
  D4-as-amended places each system's profile *in the system's own repo*
  (`0035:432-456`), so the follow-on work is mostly here regardless. The
  portal repo may not even exist yet — unverifiable from here.
- Why rejected: D1's ruling (a); the boundary (c) wanted is preserved anyway —
  portal files stay out of vero-lite.

## References

- ADR-0035 `docs/adr/0035-hosting-and-exposure-model.md` — L9 `:237-250` · the
  permanence line `:254-257` · D1(3) `:280-285` · D4 + reading-(a) amendment
  `:424-471` · the restated acceptance shape `:478-493` · D5's P12 provisional
  ruling `:573-584` · D7 (tenant ≠ vertical instance) `:631-640` · OQ-4
  `:793-798` · Implementation Notes 1–2 `:957-1002`
- PLAN-0100 `docs/plans/0100-exposure-published-demo-surface.md` — Step 8 spec
  `:856-915` (owed `OCT_VERTICAL` pin `:867`; energy-only DB-less verification
  `:897-899`; network + no-ports `:907`; committed-ingress rationale
  `:870-876`) · the PROVISIONAL table's hero rows `:163` · the Tab G
  event-mode UI gating precedent `:174`
- Code (all re-verified this session): `services/api/auth.py:82-92` ·
  `services/api/main.py:282-302` · `services/api/routers/runs.py:279` ·
  `services/api/routers/demo.py:61,108-117,132-149` ·
  `services/api/routers/procedures.py:102-121` ·
  `services/engine/ontology_meta.py:145` · the 15-site
  `settings.oct_vertical` router census (F1)
- `.claude/launch.json` (untracked; empirical corroboration only, F8)
- ADR-0032 D1.2/D5 · ADR-0023 · PLAN-0095 (`docs/plans/done/0095-docker-image-boot.md`) ·
  CLAUDE.md §1 (Rule of Three), §8 (host-state gate)

## Implementation Notes

Two follow-on artifacts are **named but not drafted here**:

1. **The multi-vertical published-profile PLAN (this repo)** — scope fixed by
   D6; it builds on PLAN-0100 Step 8's `deploy/published/` artifact and starts
   with the confirm-and-branch step on the portal repo's existence.
2. **The portal repo's own additions** (ingress entries, Access policies,
   landing-surface listing) — portal-repo property per ADR-0035 D4/L5,
   coordinated by request, never by files in this repo.

PLAN-0100 itself continues unmodified: D4 supplies its owed `OCT_VERTICAL` pin
(`energy`) and the hero-row drop rides the allowlist's own PROVISIONAL regime
(ADR-0035 D5 P12) — no step of PLAN-0100 is reopened by this ADR.

**Ratification ask (Cray):** the D1 scope ruling, the D2 vertical-as-system
ruling + label convention, the D5 ownership/duplication posture, and OQ-1's
recommendation. LOCKED-1/2/3 are restated, already typed, and not re-asked.
