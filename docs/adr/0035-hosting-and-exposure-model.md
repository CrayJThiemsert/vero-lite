# ADR-0035: Hosting + exposure model — a multi-system portal on MS-S1: one domain, a subdomain per system, published through an edge-gated, outbound-only tunnel (the ADR-002 + ADR-0003 successor)

**Status:** **Accepted** — ratified by Cray, session 200 (2026-08-01). Nine calls were
already LOCKED before drafting (L1–L4 typed s200 round 1; L5–L8 typed s172/s175; L9
typed s200 round 2 — restated below); OQ-1, OQ-2, OQ-3 and OQ-5 were typed by Cray in
the ratification pass and are recorded resolved under §Open Questions. **OQ-4 (the
domain) is deliberately open and non-blocking by construction (L6)** — its trigger is
"the portal repo is stood up".
**Date:** 2026-08-01 (round 2, same day — revised against the session-171/172/174/175
prior art and Cray's portal re-scope; round-1 scope was vero-lite-only)
**Deciders:** Jirachai Thiemsert (Cray). The exposure/gate/retention/tenancy postures
(L1–L4) and the portal shape (L5–L9) are Cray's typed picks; this ADR decides the
design **within** them and surfaces the remaining parameters.
**Related:** ADR-002 (network topology — **amended by D2**, not superseded; its LAN
mechanics stay binding), ADR-0003 (service-port strategy — **its `:105` production-port
deferral is resolved by D1/D2**), ADR-0032 (D1 demo→pilot wedge — the public link exists
to serve it; D5 positioning discipline applies to anything a visitor sees), PLAN-0095
(the hosting-agnostic image; its OQ-1 named this ADR and its trigger FIRED s199 —
`docs/plans/done/0095-docker-image-boot.md:626-629`; the s175 live-API ruling L8 is
recorded in its §Context, `:29-31`), PLAN-0093 (the shipped deterministic/LLM arm
disclosure D5's provisional posture leans on), PLAN-0047 (the fail-closed authn seam
this ADR deliberately does NOT extend, per L1), ADR-007 (approve→execute write gate —
untouched), Lesson #0034 (a deliberate gate outside the scanned surface reads as an
oversight — the dangling-`ADR-NN` failure this ADR closes, now **four** deferrals not
three), ADR-009 D1/D2 + ADR-012 D4.3 + ADR-013 D1 (drafting route + disclosure),
CLAUDE.md §8 (host-state gate; residency; assistive-AI posture). Prior-art handoffs
(on-disk, gitignored): `.claude/handoffs/session-172/2026-07-25-1432-*.md`,
`.claude/handoffs/session-174/2026-07-25-2351-*.md`.

> **Drafting provenance (ADR-012 D4.3 / ADR-013 D1).** Drafted and revised by the
> in-harness `plan-drafter` subagent from two Code-authored session-200 dispatches
> (`.claude/handoffs/session-200/2026-08-01-1114-…-dispatch.md`, round 1;
> `…-1244-…-REVISION-portal-scope-prior-art-dispatch.md`, round 2); the LOCKED calls
> are Cray's typed picks, not drafter inferences. Every round-1 fact and every
> round-2 **on-disk** prior-art fact was re-verified on disk by the drafter; facts
> from the smb-flow live-server docs are **external prior art** — attributed as such
> throughout, never presented as verified in this repo. Independent review: Code (R2)
> at PR; ratification: Cray. Author≠reviewer separation: **INTACT**. Uncommitted
> draft — Code commits per ADR-009 D2.

> **Amendment pass 2026-08-06 (session 208; drafted in-harness by `plan-drafter`
> from a Code dispatch).** Two distinct kinds of marker, inline at each site —
> read the label before treating one as ruled: **(i)** the D4/L5
> connector-ownership reconciliation + the restated D4 acceptance shape —
> **Cray's typed ruling, 2026-08-06, reading (a)**; **(ii)** three factual
> corrections proposed by PLAN-0100 §"ADR amendment owed" — **PLAN-proposed, not
> Cray-typed**, ratified with this amendment's PR. `Status:` is unchanged: this
> is an amendment to an Accepted ADR, not a re-ratification. Author≠reviewer
> separation: **INTACT** (drafter authored; Code R2 + Cray review at PR).

> **Amendment pass 2026-08-11 (drafted in-harness by `plan-drafter` from a
> Code dispatch).** One site: OQ-4's trigger — "the portal repo is created" —
> was ruled out by Cray (typed, s221): **no portal repo will be created** —
> the portal and its landing surface still exist; DNS routes, Access policies
> and the landing surface are configured in the Cloudflare dashboard, each
> published system on its own `oct-<vertical-id>` subdomain label; only a
> separate git repository was ruled out. The inline note at OQ-4 replaces the
> dead trigger with the live condition Cray himself named and records the
> operational answer as the provisional thing it is — **OQ-4 stays
> deliberately open, exactly as ratified**, and the domain itself stays out of
> this repo (D1(3)). `Status:` is unchanged. Author≠reviewer separation:
> **INTACT** (drafter authored; Code R2 + Cray review at PR).

> **Amendment pass 2026-08-11, second of the day (session 222; drafted
> in-harness by `plan-drafter` from a Code dispatch).** Two sites, neither a
> ruling. **(i)** A new open question, **OQ-6**, is added under §Open
> Questions: the apex domain appears at five places in one archived PLAN
> (`docs/plans/done/0100-exposure-published-demo-surface.md`), all written
> **after** this ADR was Accepted, each an evidence record of a measurement or
> incident on the live zone. D1(3)'s narrow runtime clause holds; its broad
> documentary clause is what those writes breached. The corrected factual
> record and Cray's typed s222 remedy (annotate the ADRs; do **not** edit the
> archived PLAN) live in the same-date ADR-0036 amendment; OQ-6 here asks the
> scope question the breach exposes and is **deliberately left open —
> surfaced, not ruled**. **(ii)** One clause of the preceding 2026-08-11
> pass — "the domain itself stays out of this repo (D1(3))" — must be read as
> restating the D1(3) norm, not as a repository inventory fact; the inventory
> fact is the five occurrences above. The preceding note is left as written;
> this note is its correction. `Status:` is unchanged. Author≠reviewer
> separation: **INTACT** (drafter authored; Code R2 + Cray review at PR).

## Context

### Why now

PLAN-0095 shipped a hosting-agnostic artifact: an image that builds, boots in ~2 s
with **no database reachable**, serves the synthetic OCT demo, runs as
`uid=999(vero)`, and takes all configuration through env
(`docs/plans/done/0095-docker-image-boot.md:6`). Its OQ-1 drew a line: deployment
configuration for a specific hosting model — *"exposing the API beyond the LAN,
tenancy for hosted customers, TLS/authn posture, or pointing a deployed image at an
off-LAN LLM endpoint"* — is *"the ADR-002-successor decision and must be its own
ADR"* (`0095:626-629`). In session 199 Cray's stated intent fired the first condition
(`docs/STATUS.md` §'Active TODOs'), and in session 200 Cray **re-scoped the target**: not one
app's demo link but a **multi-system portal** — one domain, a subdomain per system,
vero-lite as the first tenant of an arrangement meant to carry the next system and
the one after that (L9). This ADR is the successor, at that scope.

The governance record has been dangling on this question in **four** places, always
deferring to an unnumbered future ADR: ADR-002's PDPA claim
(`docs/adr/0002-network-topology.md:76`), its LAN-trust bullet (`0002:86`), its
Tailscale alternative (`0002:113-116`), and — found at round-2 R2 — ADR-0003's
production-port deferral (*"Production port selection … deferred to a future ADR when
production deployment is on the roadmap"*, `docs/adr/0003-service-port-strategy.md:105`).
Lesson #0034's rule applies: a decision NOT to act needs the same recording
discipline as an action. The `ADR-NN` those four lines point at is **this document**.

### Round 2 — the prior art the first draft was written without

Stated plainly, per the revision dispatch: the round-1 fact-pack was assembled from
the `vero-lite` repo alone. It was accurate and incomplete. A four-specialist
analysis of this exact question already existed (session 172), a correction to it
existed (session 174), Cray had already typed scope rulings (sessions 172/175), and a
Cloudflare Tunnel + MS-S1 stack has been **running in production since ~2026-03 on
the same physical host**. Round 1's own residual — "the tunnel-vendor claims are
training knowledge I could not verify" — was correct, and this is why.

> **Amended 2026-08-02 — currency correction (Cray-ratified scope):** as of
> 2026-08-02 the smb-flow tunnel **process is not running** on MS-S1 (Cray's
> statement — a host-state fact this repo cannot verify; CLAUDE.md §8). The
> sentence above was accurate when this ADR was drafted; read it now as a **track
> record**: roughly five months of production operation on the same physical
> host, plus a still-provisioned substrate — the P1 amendment beneath the
> prior-art table carries the full re-dating. No decision in this ADR turns on
> the process being live at the moment of reading, and the exposure PLAN
> re-confirms every `[ext]` fact on first touch (D1(5)).

Two source classes feed this revision, handled differently:

- **On-disk in this repo, re-verified by the drafter at the cited paths** (marked
  `[disk]` below): the s172 four-specialist findings and s174 corrections, ADR-0003's
  deferral, and the config/route facts.
- **External to this repo** (marked `[ext]`): the smb-flow live-server docs
  (`docs/deployment/live-server-blueprint.md`,
  `documents/context_ms_s1_max_live_server.md` — another repo, not openable here).
  These are attributed as **external prior art with session-200 dispatch provenance**;
  nothing below treats them as verified facts of this repo, and anything load-bearing
  that rests on them is re-confirmed by the exposure PLAN's Cray-gated live evidence.

The prior-art facts this revision builds on:

| # | Fact | Source |
|---|---|---|
| P1 | A Cloudflare Tunnel + MS-S1 stack has run in production since ~2026-03: free tier, Zero Trust account provisioned, a domain already on Cloudflare nameservers, `cloudflared` as a compose service with **no `ports:` key at all**, outbound-only | `[ext]` smb-flow blueprint |
| P2 | Four specialists (s172) recommended **Cloudflare Access + one-time-PIN email allowlist** for phase-1 auth — *deny-by-default, zero app changes, free*; phase 2 adds an IdP and validates `Cf-Access-Jwt-Assertion` in a FastAPI dependency | `[disk]` s172 handoff `:279-281` |
| P3 | s172 ingress recommendation: **no published host ports at all** — `cloudflared` reaches containers by name over the Docker network; port-collision risk zero, *"better than reserving a range"* | `[disk]` s172 `:282-284` |
| P4 | **Timeout collision:** `llm_request_timeout_s=120` × `llm_retry_budget=3` (defaults verified: `services/api/config.py:106-118`) vs a fixed ~125 s Cloudflare proxy read timeout ⇒ a slow-but-reachable MS-S1 returns a Cloudflare 524, not vero-lite's graceful degrade | `[disk]` s172 `:274-276` + `config.py`; the exact edge ceiling is vendor-side — measured by the exposure PLAN |
| P5 | **Ollama on that box is zero-sum, and the failure mode is EVICTION:** smb-flow warms `groomflow-unified`; loading a second model evicts it. A public NL-query would evict another project's **production** model | `[disk]` s172 `:271-273` (mechanism recorded there from smb-flow's own repo) |
| P6/P7 | s174 **corrected** s172: ADR-0032's `on-prem` is not the blocker; ADR-002's LAN trust model is. The tree hung on one Cray call — static-only vs live API — ruled **live API** (s175, = L8); the consequence ("live API makes the container boot the long pole") is **discharged** by PLAN-0095 (s177) | `[disk]` s174 handoff `:180-185`; `0095:29-31` |
| P8 | The fourth dangling deferral: ADR-0003 `:105` (production ports). **P3 dissolves it** — "no published host ports" answers the production-port question by removing it | `[disk]` `docs/adr/0003-service-port-strategy.md:105` |
| P9 | MS-S1 is **already a 24/7 server**: Docker Desktop (WSL2), BIOS AC-loss = Always On, Sleep = Never, Autologon, a self-hosted GitHub Actions runner. Round 1's OQ-4 overstated the §8 cost — the container runtime is not being introduced; adding a stack is still a host-state change needing Cray's explicit go | `[ext]` smb-flow blueprint §1, §5 |
| P10 | `settings.ollama_host` defaults to `http://ms-s1-max:11434` — a dev-box `/etc/hosts` name (`services/api/config.py:79-82` `[disk]`). For a container **on** MS-S1 reaching the native Windows Ollama, the working value is `http://host.docker.internal:11434` (Ollama already listens `0.0.0.0` — ADR-002's own decided binding, `0002:64-66`) | `[disk]` config + ADR-002; mechanism `[ext]` smb-flow trap table |
| P11 | The box currently runs `API_AUTH_ENABLED=false` (s172 `:277-278` `[disk]`), and `/warm` + `/sleep` are **`GET`** routes with side effects. Precision (re-verified): both DO carry `get_current_principal` (`admin.py:174-177`, `:222-223`) — the hazard is that `api_auth_enabled=false` renders the dependency inert (`auth.py:71-72`), at which point a browser prefetch of a `GET` link can unload the model mid-demo | `[disk]` |
| P12 | **The A-before-B warning (s172):** the public instance's LLM posture was never settled because vero-lite must run a **deterministic arm and an LLM arm side by side**; doing the website first "forces you to guess the LLM posture with no model of 'an arm' to guess from, then revise." The D5 route allowlist is exactly that guess — ruled on explicitly in D5 | `[disk]` s172 `:294-302` |

> **Amended 2026-08-02 — P1 currency correction (Cray-ratified scope; placed below
> the table because an amendment cannot sit inside a row).** As of 2026-08-02 the
> smb-flow tunnel **process is not running** on MS-S1 (Cray's statement — a
> host-state fact this repo cannot verify; CLAUDE.md §8). Read P1's "has run in
> production since ~2026-03" as a **track record** — roughly five months of
> production operation up to this ADR's drafting — which stopping the process does
> not un-prove. The durable substrate P1 lists remains provisioned: the Zero Trust
> account, the domain on Cloudflare nameservers, and a known-working outbound-only
> config, which Cray states a fresh vero-lite tunnel may reuse. Everything this ADR
> builds on P1 stands (the D1(1) pattern evidence, the D3(5) substrate); only the
> running-process reading is corrected — and D1(5)'s rule that the exposure PLAN
> re-confirms `[ext]` facts on first touch already anticipated exactly this drift.

> **Amended 2026-08-02 — P5 currency correction (Cray-ratified scope).** The
> eviction **mechanism** — Ollama on that box is zero-sum; loading a second model
> evicts the resident one — is a property of the host, unaffected by the tunnel
> stopping. What is now **unverified either way** is whether `groomflow-unified`
> is currently resident in Ollama on MS-S1: checking would touch MS-S1 (CLAUDE.md
> §8 — not authorized), so this ADR asserts **no residency claim in either
> direction**. The hazard model stands regardless — the neighboring stack can be
> restarted and re-warmed at any time — and D5(3)'s pre-publication caps and
> eviction-coexistence check remain required (see the D5(3) amendment).

**Withdrawn, with lineage kept (CLAUDE.md §6 classification):** s172 also claimed
ADR-0032 states `on-prem` at two irreconcilable scopes and that this ADR must
adjudicate (s172 `:257-263`). s174's verified finding refuted it: MS-S1 *is* on-prem
and all three ADR-0032 occurrences are **data-scoped** (s174 `:180-183`). The claim is
classified **superseded by new info**, not an error — recorded here so no future
reader re-adds the adjudication. This ADR contains none; its own "on-prem" usages are
data-scoped, consistent with s174.

### The frontier — no longer one app's demo link

The system's authn was designed around **accountability**: *who approved this
action*. `services/api/auth.py` carries exactly two dependencies —
`get_current_principal` (fail-closed: 401 on missing/malformed/unknown key, 403 when
the authenticated `person_id` has no `Person` in the active vertical's principal
set — `auth.py:63-94`) and `get_optional_principal` (anonymous ⇒ reduced view;
consumed by exactly one route, `services/api/routers/audit.py:31,43`). What it has
never been asked is the **resource** question — *who is paying for this GPU cycle* —
and the prior art sharpens that question twice over: the GPU is not merely Cray's
budget, it is **shared with another project's production model** (P5), and the host
is not a dev box, it is **a machine already carrying production traffic** (P1/P9).

> **Amended 2026-08-02 — currency correction (Cray-ratified scope):** "a machine
> already carrying production traffic" is re-dated, not retracted — as of
> 2026-08-02 the neighboring tunnel process is not running (Cray's statement; see
> the P1 amendment above). The resource question this paragraph sharpens is
> unchanged: the GPU is still shared with a neighbor whose stack can be restarted
> and re-warmed at any time (its model's residency is unverified either way — the
> P5 amendment), and the 24/7-server posture is a separate claim (P9 `[ext]`)
> that the tunnel stopping neither proves nor refutes. The framing stands; only
> the present tense is corrected.

The genuinely new hard part after the re-scope (L9) is separation: what is
**portal-level and permanent** (ingress, gate, subdomain convention, per-system
isolation, domain portability) versus what is **vero-lite-specific and disposable**
(its route allowlist, its prompt-log regime, its tenant key). The Decision section is
structured on exactly that line.

### The fact base — round-1 fact-pack F1–F10, re-verified on disk

All ten were re-checked against the working tree at `main` = `164197c`. Eight held
exactly; **F2 needed a path correction, F3 an undercount correction, and F7 an
extension** (each marked ▲; F7's census was corrected again at round-2 R2).

| # | Fact (re-verified) | Grounding |
|---|---|---|
| F1 | Authn split is "writes governed state → key": two dependencies, fail-closed + optional; the principal index resolves from the **process-wide** `settings.oct_vertical` | `services/api/auth.py:63-94`, `:97-116`, `:82` |
| F2 ▲ | **Exactly seven** POST routes carry no auth dependency (full `@router.post` census cross-checked against every `Depends(get_current_principal)` site): `POST /query`, `POST /procedures/draft/{classify,build,instantiate}`, `POST /insights/query`, `POST /demo/hero/event` *(round-1 dispatch said `/demo/event` — the router prefix is `/demo/hero`)*, `POST /intake/extract`. Every other POST is keyed | `query.py:38` · `procedure_draft.py:233,271,315` · `insights.py:57,278` · `demo.py:52,180` · `intake.py:153`; keyed counter-examples `intake.py:198`, `runs.py:375,427,542`, `cases.py:187-748`, `actions.py:227,248`, `pm.py:117,221` |
| F3 ▲ | **FIVE of the seven reach MS-S1 inference, not three**: `/query` (`answer_question`), `/procedures/draft/classify` (`_chat_client` + `classify_narrative`), **`/procedures/draft/build`** (`_chat_client` + `build_skeleton` — missed by the round-1 dispatch), `/intake/extract` (`extract_package`, MS-S1 named in its docstring), and **`/insights/query`** (translate stage *"wired to the local model"*; phrase stage builds a chat client — also missed). Only `/procedures/draft/instantiate` (deterministic, zero-LLM) and `/demo/hero/event` (DB write, no LLM) do not | `query.py:38-42` · `procedure_draft.py:240-247`, `:286-301`, `:315-328` · `intake.py:155-172` · `insights.py:227-235`, `:265-275` |
| F4 | `POST /demo/hero/event` **writes the database with no credential** — docstring: *"A **POST**, not a param on the read-only GET: it WRITES/persists a governed run"*; depends on `get_session` only; procurement-only, so the DB-less demo image cannot serve it — but a pilot with real Postgres can | `demo.py:180-199` |
| F5 | **No HTTP rate limiting anywhere in `services/`** — `rate.?limit\|slowapi\|throttl` matches only LINE *notification* throttling and a `motion.js` comment | `services/notify/line.py:133,294-330` · `static/assets/motion.js:69` |
| F6 | **No tenancy concept at all** — `tenant\|Tenant\|organization_id\|org_id\|customer_id` over `services/` = zero matches. Isolation unit = `settings.oct_vertical`, process-wide env; executor factories are hand-wired per vertical in `main.py` | `config.py:179-185` · `auth.py:82` · `main.py:103-156` |
| F7 ▲ | Only two namespaces have **generated** committed ORMs (`energy` → `services/db/models.py`, `core` → `services/db/person.py` — 7 tables). **Extension + round-2 R2 fix:** the committed table surface also includes the hand-written runtime spine — `pipeline_runs` + `step_results`, **`schedule_states`** (missed in round 1), `audit_log`, `action_identity`, `pm_import_row`, and the eight `repair_case*` tables — **21 tables across 12 modules** (the only other `__tablename__` occurrence in `services/` is the generator's emitter itself). One additive Alembic revision covers it (D7) | `code_generator.py:871-874` · `services/engine/procedures/runs.py:84,122` · `services/engine/procedures/schedules.py:35` · `services/db/`: `audit_log.py:63`, `identity.py:29`, `pm_import.py:71`, `models.py:14-85`, `person.py:11`, `repair_case*.py` |
| F8 | ADR-002's three self-deferrals, verbatim, all to an unnumbered `ADR-NN`. The PDPA sentence (*"All LLM traffic stays on-prem LAN; never traverses public internet"*) **survives intact under L2/B1a** — an argument *for* B1a, made explicitly in D1 | `docs/adr/0002-network-topology.md:76`, `:86`, `:113-116` |
| F9 | PLAN-0095 OQ-1's four trigger conditions + "must be its own ADR", verbatim | `docs/plans/done/0095-docker-image-boot.md:626-629` |
| F10 | The demo data is synthetic: PLAN-0095's Goal serves *"the synthetic OCT demo with no database"*; the fleet adapter is `data_adapter/synthetic.py` and its principals are role-nicknames (ต้อม / วิรัช / เฮีย) with `person_id`/`name`/`roles` only — no contact or identity fields. **The PDPA surface under L3 is therefore visitor-typed input, not seeded data** — an inversion no prior document states | `0095:11-12` · `verticals/fleet_maintenance/data_adapter/synthetic.py:1`, `__init__.py:1` · `procedures.yaml:102-111` |

One consequence of the F3 correction deserves its own sentence, because P5 raises its
stakes: `/insights/query` runs its LLM translate stage **before** its first database
read (`insights.py:297-298`; the session engine is lazy — `services/db/session.py:3-5`
per PLAN-0095), so even the DB-less demo image lets an anonymous caller drive MS-S1
inference through it — and under P5, every such call is a potential **eviction of
another project's production model**, not merely a burned GPU cycle. "DB-less" bounds
the *write* surface, not the *inference* surface.

## LOCKED (Cray, typed — restated, not re-litigated)

Round 1 (s200):

1. **L1 — Edge gate, not per-route authn (A1).** One gate for the whole published
   surface, enforced at the edge; no new `Depends(...)` on individual routes, no
   per-visitor key lifecycle. *(Which mechanism honors this is re-decided in D3 on
   the P2 evidence; the letter-vs-intent reading is surfaced as OQ-1.)*
2. **L2 — App runs ON the LAN, published outward through a tunnel (B1a).** No
   inbound ports opened; MS-S1 stays LAN-only; LLM traffic never traverses the
   public internet. Refines the earlier "B1 lean" (`docs/STATUS.md` §'Active TODOs').
3. **L3 — Prompt logs ARE retained.** Seeded data stays synthetic; visitor-typed
   free text is stored for analysis, obligations named (D6).
4. **L4 — Tenant column now, single-tenant deployment still (T2-light).** 1 customer
   = 1 process = 1 deployment; explicitly NOT "one process serves many tenants".

Rounds s172/s175/s200-r2 (carried into this revision):

5. **L5 — Separate new repo.** The portal is NOT built inside `vero-lite` (s172).
6. **L6 — Domain undecided, but design so it can MOVE.** No hardcoded domain
   anywhere, in any layer (s172).
7. **L7 — Phase 1 combines all three scope options** — portal + vero-lite + infra
   proven together (s172).
8. **L8 — Live-API shape, not static-only** (s175; recorded at `0095:29-31`). This
   is the ruling s174 said would collapse the blocker tree — it did (P6/P7).
9. **L9 — Multi-system portal** (s200, typed): one domain, **a subdomain per
   system**, each system its own compose project (`-p`) and its own Docker network.
   vero-lite (`oct.`) is the first system, a `portal.` landing surface the second,
   and the arrangement must accept an unnamed third without redesign. Shape sketch
   (s171, recalled by Cray):

   ```
                    <one domain>
          portal.  │  oct.  │  <next system>.     ← subdomain per system
             │         │          │
          ┌──▼───┐ ┌───▼──────┐ ┌─▼───┐
          │portal│ │ vero-api │ │ ... │   ← compose project (-p) + network, per system
          │static│ │+postgres │ │     │
   ```

## Decision

Eight decisions in two parts. **D1–D4 are portal-level and permanent** — they outlive
vero-lite's demo and govern every system the portal ever fronts. **D5–D8 are
vero-lite-specific** — the first tenant's own posture, disposable or revisable
without touching the portal.

### Part I — portal-level decisions (permanent)

#### D1 — The exposure model: one outbound-only tunnel on MS-S1, one domain, a subdomain per system, no published ports anywhere

The portal obeys five constraints, stated as architecture (violating any of them
reopens this ADR):

1. **No inbound port is opened on any LAN device, and no container publishes a host
   port.** Publication happens through an **outbound-only connector** (`cloudflared`)
   dialing out from MS-S1; the connector reaches each system's containers **by name
   over that system's Docker network** — no `ports:` keys at all (P3; the pattern is
   production-proven on this host, P1 `[ext]`). This does more than preserve
   ADR-002's firewall posture (`0002:52-62`): it **dissolves ADR-0003's deferred
   production-port question** (`0003:105`) — in production there are no published
   ports to select. Port strategy remains a *dev-compose* concern only, exactly
   where ADR-0003 already governs it.
2. **MS-S1's LLM endpoint stays LAN-only.** Ollama (`192.168.1.133:11434`,
   Private/Domain firewall profiles) is never published, proxied, or tunneled.
   App↔MS-S1 traffic remains on-prem — ADR-002's PDPA bullet (`0002:76`) survives
   **by construction**, the strongest argument for B1a and why D2 amends rather than
   retracts it.
3. **One domain, subdomains per system (L9), movable by design (L6).** The domain
   appears in exactly one layer — the portal repo's tunnel-ingress map (+ DNS at the
   vendor) — and **never** in any system's application code, image, compose file, or
   env contract. vero-lite specifically remains domain-ignorant: nothing in this
   repo may reference the portal domain. Moving domains = re-pointing DNS + editing
   the ingress map; zero application changes.

   > **Annotated 2026-08-11 (s222).** This item's two clauses have different
   > scope, and only one has a recorded breach. The **narrow runtime clause**
   > (never in "application code, image, compose file, or env contract")
   > holds — no runtime surface references the domain, and portability by
   > DNS re-point is intact. The **broad documentary clause** ("nothing in
   > this repo may reference the portal domain") has a recorded breach: five
   > references in one archived PLAN, all post-ratification evidence records
   > (count, file, dating, and Cray's typed s222 remedy — annotate, don't
   > delete — are recorded in the ADR-0036 amendment of the same date).
   > Whether this clause governs evidence records at all, or only the runtime
   > surfaces the narrow clause enumerates, is **OQ-6 — open**. The rule's
   > text above is left exactly as ratified.

4. **Honest data-path statement** (feeds D6's notice): *visitor* traffic — including
   every prompt a visitor types — traverses the public internet and the tunnel
   vendor's edge over HTTPS; TLS terminates at that edge before re-encryption to the
   origin. "LLM traffic stays on-prem" is a claim about the app↔model hop, not about
   visitor-typed content. The two must never be conflated in partner-facing material
   (ADR-0032 D5 discipline).
5. **The serving host is MS-S1** — decided, no longer an open question. Round 1
   deferred this (its OQ-4) on the assumption that a container runtime would have to
   be introduced under the §8 host-state gate; the prior art corrects the cost
   picture: MS-S1 already runs Docker Desktop 24/7 with always-on BIOS/autologon
   posture and carries a production tunnel stack (P9/P1 — both `[ext]`, so the
   exposure PLAN re-confirms on first touch). **Adding the portal stack is still a
   host-state change**: explicit Cray go before any command runs on MS-S1, per
   CLAUDE.md §8 — P9 lowers the *surprise*, not the gate. A standing portal duty
   attaches: **do no harm to co-tenant systems** — the host carries another
   project's production traffic, and every portal-side change is planned around that
   fact (P5's eviction hazard is the sharpest instance; D5 owns vero-lite's side of
   it).

   > **Amended 2026-08-02 — currency correction (Cray-ratified scope):** two
   > present-state phrases above are re-dated, not retracted. As of 2026-08-02 the
   > smb-flow tunnel **process is not running** on MS-S1 (Cray's statement), so
   > read "carries a production tunnel stack" as: carried one for roughly five
   > months and retains the provisioned substrate — account, domain, known-working
   > config (the P1 amendment, Context); and read "the host carries another
   > project's production traffic" as a **standing co-tenancy property, not a
   > moment-in-time claim** — the neighboring stack's assets remain on the host and
   > it can be restarted at any time (whether its model is currently resident is
   > unverified either way — the P5 amendment, Context). Nothing in this item
   > changes: MS-S1 remains the serving host, the §8 gate and the do-no-harm duty
   > stand, and this item's own rule — the exposure PLAN re-confirms `[ext]` facts
   > on first touch — is the mechanism that absorbs exactly this drift.

**Only properties PLAN-0095 actually demonstrated are claimed** for the vero-lite
image (its OQ-2/OQ-3 evidence boundary): builds, boots DB-less in ~2 s, serves the
demo, runs nonroot with a passing healthcheck, migrates in-image against a live
Postgres (`0095:6`). No tunnel behavior of *this* system has been demonstrated yet —
that evidence belongs to the exposure PLAN's Cray-gated live step. The five months of
production tunnel operation are the *neighboring stack's* evidence (`[ext]`): strong
prior art for the pattern, not a demonstrated property of this deployment.

#### D2 — The dangling record: ADR-002 amended in place (three lines) + ADR-0003 amended in place (one line); neither superseded

ADR-002's *mechanics* — the `/etc/hosts` convention, the firewall rule, the
`OLLAMA_HOST=0.0.0.0` binding, the `ms-s1-max` service-discovery rule — remain the
binding truth of the dev LAN and are untouched. ADR-0003's `${VAR:-default}`
port-fallback pattern remains the binding truth of the dev compose file. What
changes is exactly the four deferral lines (Context):

- `0002:76` (Positive → PDPA-aligned): the claim is **re-affirmed for the app↔LLM
  hop by ADR-0035 D1(2)** and re-scoped — visitor traffic is governed by ADR-0035
  D1(4)/D6.
- `0002:86` (Neutral → LAN trust): the deferred re-evaluation is **performed — the
  `ADR-NN` is ADR-0035**.
- `0002:113-116` (Alternative 3, Tailscale): the reconsideration happened in
  ADR-0035 D3/Alternatives.
- `0003:105` (Neutral → production ports): the deferred production-port ADR is
  **ADR-0035, and its answer is dissolution** — D1(1)'s no-published-ports ingress
  means production selects no host ports at all.

Mechanics: Code applies the four pointer lines **in the same PR that lands this ADR
after Cray ratifies** — Accepted-body edits under the G1 gate, lifted by that
in-context approval (house rule: never flip-then-edit; the amendments are part of
the ratified scope, mirroring the ADR-0034 in-place precedent).

#### D3 — The portal gate: Cloudflare Access with a one-time-PIN email allowlist, enforced at the vendor edge, one policy pattern for every subdomain

Round 1 chose a shared HTTP Basic Auth credential at an on-LAN proxy and **rejected
Cloudflare Access as having "no shared-password shape"** — a correct answer to L1's
*letter* on a smaller fact base. The four-specialist s172 analysis (P2, re-verified
`[disk]`) recommends Access for exactly L1's *intent* — deny-by-default, **zero app
changes**, free — and the revision dispatch re-opened the comparison. Re-decided,
**for Access**, on five grounds:

1. **Enforcement point.** Access denies at the vendor edge, *before* traffic enters
   the tunnel; an unauthenticated request never reaches the LAN. Basic-auth at an
   on-LAN proxy admits every anonymous request through the tunnel to LAN
   infrastructure first. On a host carrying another project's production traffic
   (D1(5)), keeping unauthenticated load off the box entirely is worth more than it
   was in round 1's one-app picture.

   > **Amended 2026-08-02 — currency correction (rides with the D1(5) amendment):**
   > "a host carrying another project's production traffic" is a standing
   > co-tenancy property, not a moment-in-time claim — as of 2026-08-02 the
   > neighboring tunnel process is not running, but its stack can return at any
   > time (see the D1(5) amendment). The enforcement-point argument survives on
   > grounds that do not depend on the neighbor being live right now: keeping
   > unauthenticated load off the box also protects Cray's own compute and the
   > demo's responsiveness. This ground's conclusion is unchanged.
2. **No secret we mint.** There is no shared password to distribute, store, rotate,
   or leak — round 1's own top-listed negative ("a leak is invisible until the GPU
   bill says otherwise") is *eliminated* rather than mitigated. Revocation is
   per-person (remove an email); the s172 recipe's audit trail is per-identity at
   the vendor.
3. **L1's ban on a per-visitor key lifecycle is honored in substance:** vero-lite
   issues nothing per visitor — the allowlist entry is an email address, and the
   "credential" is the visitor's own inbox (one-time PIN per visit). Managing an
   email list is audience curation, which the wedge motion does anyway (ADR-0032
   D1: hand-picked partners). This *is* however a departure from L1's literal "one
   shared credential" — surfaced honestly as **OQ-1**, not silently widened.
4. **Portal fit (L9).** One Access policy pattern covers every subdomain uniformly;
   per-system audiences are per-subdomain allowlists — config-only, and system N+1
   inherits the gate by adding a policy, not by inventing an auth story.
5. **Substrate already in production** (P1 `[ext]`): the Zero Trust account and
   Cloudflare-managed domain exist; the marginal setup is a policy, not a stack.

   > **Amended 2026-08-02 — currency note (Cray-ratified scope; deliberately
   > lighter than its siblings):** the body of this ground is about the
   > **substrate**, and that claim stands — the Zero Trust account and the
   > Cloudflare-managed domain remain provisioned (P1 amendment, Context). Only
   > the heading's "already in production" framing is re-dated: as of 2026-08-02
   > the tunnel process that used this substrate is not running (Cray's
   > statement). The ground's force is unchanged — the marginal setup being "a
   > policy, not a stack" never depended on the neighbor's process being live.

Costs, stated honestly: a one-time-PIN fetch adds friction to first entry (for a
hand-picked demo audience, acceptable — arguably a professionalism signal); visitor
**email addresses become personal data processed at the vendor** (named in D6's
notice and RoPA instance); the free tier has seat limits (well above demo-audience
scale — a vendor-side figure the exposure PLAN confirms, not asserted here). Phase 2
of the s172 recipe (IdP + validating `Cf-Access-Jwt-Assertion` in a FastAPI
dependency) is **app code and therefore out of L1's phase-1 posture** — named as a
pilot-era option in D8, not built.

Revocation and tear-down (surviving round 1, mechanism-adjusted): access is revoked
per-person by allowlist edit; the whole link dies by deleting the tunnel route /
stopping the connector — one command at the vendor edge, no listening socket left
behind (D1(1)). Visitor anonymity *inside the app* is unchanged: no app-level
identity exists for gate-passers, nothing in the audit trail may claim one, and the
governed write surface still demands real API keys (D5/D8).

#### D4 — Per-system isolation, and the repo boundary

- **One compose project (`-p`) and one Docker network per system** (L9). No
  cross-system network sharing; the connector joins each system's network to reach
  its containers by name (P3). A misbehaving or compromised system cannot address
  its neighbors' containers; a system is added or removed without touching another
  system's stack.
- **The portal lives in a separate new repo** (L5): the connector config, the
  ingress map (the only place subdomain→service bindings exist), the Access
  policies, and the `portal.` landing surface are its property. vero-lite
  contributes **only** its image (PLAN-0095) and its own compose project; this repo
  stays domain-ignorant (D1(3)) and portal-ignorant. The portal repo's scaffolding
  is **out of scope here by dispatch** — this ADR fixes the arrangement's shape, not
  its files.

  > **Amended 2026-08-06 — connector-ownership reconciliation (Cray's typed
  > ruling, session 208: reading (a)).** This bullet and Implementation Note 1
  > gave the connector config *and* the ingress map to the portal repo — while
  > Implementation Note 2 was already assigning the **route allowlist** to
  > vero-lite's exposure PLAN. Those two assignments were in tension from
  > ratification day; the exposure PLAN (PLAN-0100,
  > `docs/plans/0100-exposure-published-demo-surface.md`) made it concrete when
  > its SD-3 ruling (Cray, 2026-08-05, §Surfaced decisions: enforce the
  > allowlist at the `cloudflared` edge — ingress allowlist + catch-all
  > `http_status:404`, config committed in this repo, **no** `nginx`) left a
  > connector as the only edge vero-lite owns. **Ruling (a), Cray, typed,
  > 2026-08-06: vero-lite's `cloudflared` IS this system's connector, declared
  > in vero-lite's own compose project; the portal repo owns the ingress map
  > *across systems*, while each system owns its *own* route allowlist.**
  > Reading (b) — relocate the ingress allowlist to the portal repo, vero-lite
  > shipping only the allow *table* as a contract — was **rejected** (it voids
  > PLAN-0100 AC-6(a)'s offline set-equality and re-opens SD-3). This is the ADR
  > reconciled with itself, not a reversal. The split, restated:
  > **portal repo** = the **cross-system** ingress map — this bullet's
  > parenthetical narrows to "the only place *subdomain→system* bindings exist"
  > (still the only domain-bearing layer, D1(3)) — plus the Access policies, the
  > `portal.` landing surface, and its own connector for it. **Each system** =
  > its own connector service + its own committed, path-scoped route-allowlist
  > config + its own tunnel credentials (secret-held, **never committed** —
  > CLAUDE.md §8), all ordinary members of its own compose project.
  > "Contributes **only** its image and its own compose project" survives
  > verbatim — the connector now lives *inside* that compose project; what
  > vero-lite still never contributes is domain knowledge, Access policy, or
  > cross-system routing, so D1(3)/L6 domain-ignorance still binds: the
  > committed ingress config must stay domain-free (mechanics = PLAN-0100
  > Step 8). Singular "the connector" — the first bullet above and D1(1) — now
  > reads **distributively**: each system's own connector joins that system's
  > network (P3's by-name, no-ports mechanism is unchanged). Isolation is
  > strengthened, not weakened: one compose project + one network per system, no
  > cross-system sharing, a system cannot address its neighbours' containers —
  > and no single shared connector holds membership in every system's network
  > any more, so a compromised connector reaches exactly one system. Corollary
  > (binding — PLAN-0100 SD-3 review finding 3): **no other system's connector
  > may ever join this system's network** — a foreign connector on the network
  > reaches the app by name and bypasses the route allowlist entirely.

- **Acceptance shape for L9's "no redesign" clause:** admitting system N+1 =
  one subdomain (DNS/ingress entry) + one Access policy + one compose project on its
  own network. If a future system needs more than that, the arrangement has drifted
  and this ADR is reopened.

  > **Amended 2026-08-06 — acceptance shape RESTATED (rides with the
  > reading-(a) ruling above; Cray, session 208).** Restated so the drift
  > trigger cannot fire on the very arrangement just ruled — the pre-amendment
  > sentence silently counted the connector as portal-side furniture, so under
  > reading (a) a literal reading would have tripped it. The shape is now:
  > admitting system N+1 = **one subdomain (DNS/ingress entry, portal-side) +
  > one Access policy (portal-side) + one compose project on its own network —
  > which, under reading (a), contains that system's own connector, its
  > committed route-allowlist config, and its secret-held tunnel credentials as
  > ordinary members**. The portal-side cost of a new system is unchanged at
  > exactly two artifacts; everything else the system brings rides inside the
  > one compose project it was always required to bring. The trigger keeps its
  > teeth for real drift: a system that needs a **per-system change in the
  > portal repo**, a second Access policy, a shared network, or any portal-side
  > artifact beyond the two named ⇒ the arrangement has drifted and this ADR is
  > reopened.

### Part II — vero-lite-specific decisions (the first tenant)

#### D5 — vero-lite's published surface and resource posture: allowlist (provisional by design), pre-publication rate + concurrency caps, and an edge-compatible timeout profile

F2/F3/F5 mean the gate is the only thing between the internet and MS-S1's GPU — and
P5 re-classifies the risk: an anonymous LLM call does not merely spend Cray's
compute, it can **evict another project's warmed production model**. Ruling, in
layers (all config, zero app code, per L1):

> **Amended 2026-08-06 — factual correction (PLAN-proposed by PLAN-0100 §"ADR
> amendment owed"; NOT Cray-typed — it records Cray's s202 ownership ruling and
> is ratified with this amendment's PR).** "All config, zero app code"
> overstates. L1's ban is on per-route **authn** code, and it remains honored —
> zero new `Depends(...)` — but it was never a ban on UI-coherence or cap code:
> item 2's exclusions require **published-UI-profile code** to hide the excluded
> controls, and item 3's in-flight cap is **app code** (no substrate existed —
> F5). Both are owned by PLAN-0100, per Cray's s202 ruling. Same correction at
> item 5's "Env only — no code."

1. **The gate (D3)** — first layer.
2. **A default-deny route allowlist at vero-lite's edge** — the published surface
   contains **only** the routes the demo script exercises. This is the round-1
   elimination, kept: `POST /demo/hero/event` (the unauthenticated DB write, F4),
   the `/intake/*` scaffolding wizard, and the `/warm`+`/sleep` admin surface
   (P11) do not exist on the published surface — not "exist but are patched".
3. **Rate + concurrency caps on the published LLM routes — required BEFORE
   PUBLISHING AT ALL.** Round 1 ruled a rate limit "required before wide sharing";
   P5 moves it: the exposure victim is a *third party's production system*, so the
   cap is a pre-publication requirement even for a single hand-picked visitor
   (defense against a shared link, a prefetching browser, or an automated crawler
   that acquires the URL). Recommended defaults for the exposure PLAN to pin: per-IP
   10 LLM-requests/min, burst 20, **and a global cap of 1 in-flight LLM request**
   with fast-fail to the deterministic degrade (which already exists and discloses
   itself — PLAN-0093). The exposure PLAN's live evidence must include an
   **eviction-coexistence check** (observe the neighboring model's residency during
   a vero-lite LLM call — Cray-gated, §8).

   > **Amended 2026-08-02 — currency correction (Cray-ratified scope): the premise
   > is re-grounded; the requirement is unchanged.** "The exposure victim is a
   > *third party's production system*" was written while the neighboring tunnel
   > stack was running; as of 2026-08-02 that process is stopped, and whether
   > `groomflow-unified` is currently resident in Ollama is **unverified either
   > way** (checking touches MS-S1 — CLAUDE.md §8, not authorized; see the P5
   > amendment, Context). The caps remain a **pre-publication requirement** on
   > grounds independent of the neighbor being live right now: (i) a shared link, a
   > prefetching browser, or a crawler acquiring the URL; (ii) the caps also
   > protect Cray's own compute and the demo's responsiveness; (iii) the neighbor
   > can be restarted at any time — a cap that must be added back later is a cap
   > that should never have been removed. The **eviction-coexistence check**
   > (Cray-gated, §8) remains required — it is precisely the step that converts the
   > unverified residency into live evidence.
4. **An edge-compatible LLM timeout profile (P4).** Defaults verified on disk:
   `llm_request_timeout_s=120.0` × `llm_retry_budget=3` (`config.py:106-118`) — a
   worst case of minutes, far beyond the tunnel edge's fixed proxy read ceiling
   (~125 s per the s172 finding; the exact vendor figure is confirmed by the
   exposure PLAN's live measurement, not asserted here). Published-profile env must
   bring the app's **graceful degrade inside the edge window** — recommended:
   `LLM_REQUEST_TIMEOUT_S=25`, `LLM_RETRY_BUDGET=1` for the published deployment —
   so a slow MS-S1 yields vero-lite's own disclosed degrade (PLAN-0093), never a
   vendor 524 in front of exactly the audience the wedge exists to impress.
5. **Published configuration facts (P10/P11):** the published compose project sets
   `API_AUTH_ENABLED=true` (the box's current `false` state is a LAN-era
   convenience; with it, the auth dependency on `/warm`/`/sleep` goes inert —
   `auth.py:71-72` — and a browser prefetch of those `GET`s can unload the model
   mid-demo) and overrides `OLLAMA_HOST=http://host.docker.internal:11434` (the
   default `http://ms-s1-max:11434`, `config.py:79-82`, is a dev-box hosts-file
   name; the container-on-MS-S1 mechanism is external prior art, verified live by
   the exposure PLAN; Ollama's `0.0.0.0` listen is already ADR-002's own binding,
   `0002:64-66`). Env only — no code.

   > **Amended 2026-08-06 — factual correction (PLAN-proposed by PLAN-0100
   > §"ADR amendment owed"; NOT Cray-typed — ratified with this amendment's
   > PR).** The two settings above are env-only, but the published surface's
   > **full** diff is not code-free: item 2's exclusions require the published
   > UI profile to hide the excluded controls, and item 3's in-flight cap is app
   > code (no substrate existed, F5) — both owned by PLAN-0100, per Cray's s202
   > ruling. See the matching correction under this D5's preamble.

**The P12 ruling — the allowlist is a labelled provisional, by design.** s172's
sharpest warning: publishing before the arm model exists forces a guess at the LLM
posture, then a revision. Partially discharged since: L8 settled live-API, and the
arm *vocabulary* has shipped (PLAN-0093's `phrased_by` / degrade disclosure rides
every NL answer — `query.py:29-34`, `insights.py:265-275`). What remains genuinely
unsettled is per-route: *which published routes run the LLM arm for anonymous
visitors, and which pin the deterministic arm*. Therefore: the exposure PLAN's
allowlist must **declare an arm posture (`deterministic` | `assisted`) per published
route**, the list is explicitly labelled PROVISIONAL in that PLAN, and the first
live measurement (P4 timeout + P5 eviction behavior) may revise it **without
reopening this ADR**. That converts s172's "guess then revise" from a silent hazard
into a declared, bounded iteration.

#### D6 — The prompt-log regime (L3), with numbers and names

What L3 creates is a personal-data processing activity where none existed: the
seeded data is synthetic (F10), so **the only PII surface of the demo is what
visitors type** — free text may carry embedded PII regardless of what the notice
asks. The regime, stated as numbers and names:

- **What is stored, per request to a published LLM route:** UTC timestamp, route,
  active vertical, the visitor-typed free-text field(s) verbatim, model name,
  outcome state (`match`/`degraded`/`abstain`/grounded flag), and the phrasing arm.
  **Not stored:** IP address, headers, any gate identity. (The vendor edge keeps its
  own access-log metadata — and under D3 the gate itself processes **visitor email
  addresses** at the vendor — both named in the notice, neither copied into our
  log.)
- **Where:** an append-only JSONL file per day under a named volume on the serving
  host (`prompt-log` volume). LAN-only at rest; never committed; never leaves the
  host except for Cray's local analysis.
- **Retention: 90 days rolling.** Rotation deletes files older than 90 days. (30
  days would drop slow-burn outreach-campaign signal; indefinite is unbounded PDPA
  liability — rejected in Alternatives.)
- **Who may read: Cray (Jirachai Thiemsert) only** — sole operator, controller of
  this dataset.
- **Deletion path:** (i) automatic rotation at 90 days; (ii) a documented manual
  purge command in the exposure PLAN's runbook section; (iii) a data-subject
  deletion request honored within **30 days** (for gate emails: allowlist removal +
  a vendor-side deletion request, named in the RoPA instance).
- **Processing record:** a **populated instance of the existing RoPA-lite template**
  (`docs/conventions/partner-ropa-lite.md`) — its §6 retention/erasure and §8 DSR
  slots fit this dataset exactly, so no new artifact class is invented. Two
  postures stated in the instance: the template's trial roles are
  partner=controller / vero-lite=processor (`partner-ropa-lite.md:22-23`); for the
  public demo **vero-lite is the controller**, and **Cloudflare is a named
  recipient/processor** (gate emails + edge transit).
- **Consent capture:** an **in-app persistent notice is REQUIRED** on the published
  demo UI regardless of gate choice. Round 1's structural finding stands and
  generalizes: a Basic Auth prompt cannot render text at all, and while the D3
  Access login page may carry short text, that is vendor-side capability this repo
  cannot verify — so the in-app notice is the load-bearing capture point, with any
  gate-page text additive. The notice states: what is retained (typed text), for
  how long (90 days), who reads it (the operator), that the gate processes the
  visitor's email via Cloudflare, that traffic transits the vendor's edge (D1(4)),
  and that the demo is synthetic and **no real personal data should be entered**.
  The exposure PLAN owns the banner; its text is reviewed against ADR-0032 D5's
  vocabulary rules.

#### D7 — The tenant key (L4): a customer-organisation column, stamped per deployment

- **What the tenant key IS:** a **customer organisation** — `tenant_id` (Text, NOT
  NULL), a stable slug. Not a deployment (two deployments for one customer — e.g. a
  re-hosted pilot — must keep one key; a deployment id can be added later as a
  separate label), and not a vertical instance (the vertical is already
  `settings.oct_vertical`, and conflating them breaks the moment one customer runs
  two verticals).
- **Where its value comes from:** `settings.tenant_id` (env `TENANT_ID`),
  defaulting to `"default"` so every existing dev/test flow is untouched; the
  public demo deployment sets `TENANT_ID=demo`. Stamped at the write path from
  settings — **process-wide, exactly like `oct_vertical`** (`config.py:179-185`),
  which is what keeps L4 "light": per-request tenancy would collide with the
  process-scoped vertical (`auth.py:82`) and the hand-wired executor factories
  (`main.py:103-156`). It is a plain settings field, **not** part of the governance
  pin — it must never enter the resolved-procedures hash.
- **Which tables carry it: every committed persistence table — 21 tables across 12
  modules** (F7 ▲, corrected census): the two generated ORM modules
  (`services/db/models.py` — asset, site, operational_event, alert,
  recommended_action, alert_event_link; `services/db/person.py` — person) **and**
  the hand-written runtime spine — `pipeline_runs` + `step_results`
  (`services/engine/procedures/runs.py:84,122`), **`schedule_states`**
  (`services/engine/procedures/schedules.py:35`), `audit_log` (`audit_log.py:63`),
  `action_identity` (`identity.py:29`), `pm_import_row` (`pm_import.py:71`), and
  the eight `repair_case*` tables. A rows-in-one-DB table that omitted the key
  would be exactly the query-written-wrongly trap L4 exists to prevent.
- **The migration itself is a separate PLAN** (the tenant-key PLAN — Implementation
  Notes), and so it is not silently dropped, that PLAN must: (i) teach the
  generator to emit the column for the committed ORMs and update the
  reproducibility guard; (ii) add the column to the hand-written models; (iii) ship
  one Alembic revision in the measured-safe shape — add nullable → backfill
  `'default'` → NOT NULL; (iv) stamp writes from `settings.tenant_id` at the
  session/repository seam; (v) add a set-equality guard test asserting every
  `__tablename__` model carries `tenant_id` (a new table cannot silently opt out);
  (vi) **rule on every natural-key unique constraint that a tenant column
  re-scopes** — concretely `uq_schedule_states_vertical_procedure` on
  `(vertical, procedure_id)` (`schedules.py:36-38`): under one-DB-per-deployment it
  is unaffected, but the PLAN must decide (not discover) whether `tenant_id` joins
  such keys, and `uq_step_results_seq` (`runs.py:125`) gets the same review;
  (vii) build **no** per-request tenant resolution, no row-level security, no
  tenant-scoped authn — those are T2-full and are explicitly not this decision.
- **Non-goal, verbatim per L4:** one process never serves two tenants under this
  ADR. Multi-tenant serving is a future ADR with its own trigger (a second
  concurrently-hosted customer).

#### D8 — Demo posture ≠ pilot posture (binding; the F4 consequence)

The security posture this ADR authorizes is **the demo's**, and it does not carry
over:

- **Data:** the demo is synthetic end-to-end (F10) — the PDPA surface is visitor
  input plus gate emails (D6). A pilot serves a real partner's data; the
  partner-controller RoPA-lite record and the DPA govern, not D6's demo record.
- **Database:** the demo image is DB-less, so the unauthenticated write route
  `POST /demo/hero/event` (F4) *cannot* persist anything — the write surface is
  bounded by construction, not by control. A pilot deployment with real Postgres
  **re-activates it**. Therefore, binding: **before any pilot-shaped deployment is
  published through this (or any) tunnel, the unauthenticated-write surface must be
  re-postured** — at minimum excluded by the D5 allowlist permanently, with the
  real decision (per-route `Depends` vs permanent edge exclusion vs route removal
  from published builds) taken by the pilot's own governance artifact. It may not
  ride in on demo precedent.
- **Identity:** the pilot era is where the s172 phase-2 recipe belongs — an IdP
  behind Access with `Cf-Access-Jwt-Assertion` validated in a FastAPI dependency
  (P2) — because a pilot's users are *known principals*, not anonymous visitors.
  That is app code and a per-route decision: out of L1's phase-1 posture, named
  here so it is neither forgotten nor smuggled in early.
- **Inference:** the demo's D5 layers assume synthetic stakes on a shared box. A
  pilot's inference over real operational data raises the residency question
  again — and D1(2) (MS-S1 LAN-only) plus PLAN-0095 OQ-1's fourth condition
  ("pointing a deployed image at an off-LAN LLM endpoint") make any off-LAN LLM
  endpoint a **new ADR-level decision**, not a config change.
- **Authn:** `api_auth_enabled=true` + provisioned per-person keys on any published
  deployment (D5(5)); the demo's read+ask surface needs no keys, the governed loop
  always does.

In one sentence, for every future reader: **this ADR publishes the synthetic demo
through the portal; it authorizes nothing about publishing a pilot.**

## Consequences

### Positive

- **Four** dangling governance deferrals resolve to a numbered, session-visible
  successor (ADR-002's three + ADR-0003's production-port line — Lesson #0034
  closed for this surface), and ADR-002's PDPA sentence survives with its scope
  stated honestly.
- The ADR-0032 D1 wedge gets a shareable, always-on demo link on a host that is
  **already a proven 24/7 server**, with **zero authn code changes** in `services/`
  (L1 honored: vero-lite's exposure diff is env + edge config + a log writer + a
  banner, all owned by the exposure PLAN).

  > **Amended 2026-08-06 — factual correction (PLAN-proposed by PLAN-0100 §"ADR
  > amendment owed"; NOT Cray-typed — ratified with this amendment's PR).** The
  > enumeration is two items short: the exposure diff is env + edge config + a
  > log writer + a banner **+ the published UI profile + the in-flight cap**
  > (D5(2)/D5(3) as corrected there). "Zero authn code changes" stands — L1's
  > ban is on per-route authn code, which remains honored.
- The portal is permanent infrastructure: system N+1 costs one subdomain + one
  Access policy + one compose project (D4) — the arrangement, not the demo, is the
  durable asset (L9).
- No minted secret exists anywhere in the gate path (D3) — the round-1 design's
  worst failure mode (an invisible shared-password leak) is structurally removed.
- The resource exposure is stated at its true size (five inference routes, F3 ▲)
  and at its true stakes (a co-tenant *production* model, P5), and every layer of
  the answer is verifiable config.
- The tenant retrofit trap is closed at its cheapest point: one additive revision
  over 21 tables now versus a backfill across live pilot data later.

### Negative (the honest costs)

- **Vendor concentration.** DNS, TLS, tunnel, and gate all sit on one vendor's
  free tier. Mitigations: L6 (movable domain, one-layer binding), the gate being
  policy-not-code, and the app's own fail-closed authn seam remaining intact
  underneath — but an edge outage or policy change takes the portal down, and an
  exit costs re-fronting work. This is the price of "no inbound ports"; the
  alternatives (B1b VM, port-forward) were judged worse.
- **The demo now coexists with another project's production.** Both directions: a
  vero-lite LLM call can evict their warmed model (bounded by D5(3), verified by
  the coexistence check), and their stack's reboots or changes can take the demo
  down — the portal has no SLA and should not imply one. The D1(5) do-no-harm duty
  makes every portal change a §8-planned act, which is friction by design.
- **Gate friction and a new (small) PDPA surface.** One-time-PIN entry costs a
  visitor an inbox round-trip, and visitor emails are processed at the vendor —
  named in the notice and RoPA instance (D6). L3's retained free text remains a
  real obligation D6 bounds but cannot remove.
- **The P4 timeout profile trades depth for reliability.** `LLM_REQUEST_TIMEOUT_S=25`
  / budget 1 on the published profile means a genuinely slow model answer degrades
  deterministically where the LAN demo would have waited — the honest cost of never
  showing a vendor 524 to a partner.
- **The tenant column touches generated code**, so the generator and its
  reproducibility guard move together (D7 (i)) — a coordination cost the tenant-key
  PLAN must sequence, not discover.

### Neutral

- ADR-002's LAN mechanics, ADR-0003's dev-compose port pattern, ADR-007's
  approve→execute write gate, and the PLAN-0047 authn seam are all untouched. F5
  stays true in `services/` — rate limiting lives at the edge.
- The demo remains the PLAN-0095 image, byte-identical; exposure is composition
  around it — which is exactly what "hosting-agnostic by construction" was for.
- The smb-flow production stack is not modified by this ADR; the portal only adds
  alongside it, each addition behind Cray's explicit §8 go.

## Open Questions — RESOLVED at ratification (Cray, typed, session 200)

Four of five were answered in the ratification pass; each was typed by Cray against
the recommendation stated, and each is now binding. **OQ-4 stays open by design.**
_[2026-08-11 (s222): a sixth question, **OQ-6**, was surfaced post-ratification
and is **open** — it was not part of the ratification pass.]_

- **OQ-1 — D3's reading of L1 (letter → intent): RATIFIED as drafted → Cloudflare
  Access + one-time-PIN email allowlist.** L1's letter said "one shared credential";
  D3 reads it for intent (one gate, no app code) and Cray confirmed that reading.
  The literal-letter fallback — shared Basic Auth at an on-LAN proxy — is **not
  taken**, and survives as Alternative 1 for the record. Every other decision was
  independent of this choice and is unaffected. *(This was the one question a
  drafter may not settle alone, because it re-reads a LOCKED ruling's wording.)*
- **OQ-2 — the D6 numbers: RATIFIED as drafted.** 90-day rolling retention ·
  Cray-only reader · 30-day DSR honor · no IP address in our log. The 30-day and
  180-day variants were both offered and declined.
- **OQ-3 — the tenant-key semantic (D7): RATIFIED as drafted → customer
  organisation**, not deployment. A re-hosted or re-deployed pilot for the same
  customer keeps one key; a deployment id may be added later as a separate label.
- **OQ-4 — the domain: DELIBERATELY OPEN, and non-blocking by construction (L6).**
  Every layer treats the domain as movable, so no work is gated on it. Cray picks
  the name — and confirms whether the portal shares the existing Zero Trust account
  or gets its own — when the portal repo is stood up. **This is a recorded gate, not
  an oversight** (Lesson #0034): the trigger is "the portal repo is created", and it
  is restated in the exposure PLAN's first step rather than left only here.
  _[Amended 2026-08-11 (the amendment-pass note above) — **the trigger is
  replaced; the openness is not.** (i) The recorded trigger will never fire:
  Cray ruled (typed, s221) that **no portal repo will be created** — the
  portal and its landing surface still exist; DNS routes, Access policies and
  the landing surface are configured in the **Cloudflare dashboard**, each
  published system on its own `oct-<vertical-id>` subdomain label; **only a
  separate git repository was ruled out**
  (`docs/logs/2026-08-10-plan0103-step8b-portal-assembly-request.md`; the
  two-artifact-per-system price of ADR-0036 D2 is unchanged, paid as
  dashboard configuration). (ii) An operational answer to the name exists and
  is **live**: Cray named the domain in sessions 206/212 — deliberately not
  written here, per D1(3) — and it has carried DNS since session 213. That
  answer was **explicitly provisional** ("revisit the name after a full life
  cycle" — Cray's words, recorded in the same log), and this amendment does
  not convert it into a settled one: this ADR was not wrong, and the pick is
  still Cray's. (iii) The live trigger that replaces the dead one: Cray
  revisits the name **after a full life cycle has run** — the condition Cray
  himself named. The account half of this question (shared Zero Trust account
  vs its own) was gated on the same dead trigger and moves to the same live
  one; the dashboard has carried the Access policies since s213 as an
  operational reality, and no typed confirmation of the account choice is on
  the record or manufactured here. Non-blocking by construction (L6) is
  unchanged; PLAN-0103 Step 1 carries the same s221 ruling on the PLAN
  side.]_
- **OQ-5 — D6's consent reading: RATIFIED as drafted → the in-app banner is
  REQUIRED.** It is load-bearing regardless of which gate is deployed: a Basic Auth
  prompt renders no text at all, and the Access login page's text capability is
  vendor-side and unverified from this repo. The banner does not depend on either.
- **OQ-6 — the scope of D1(3)'s broad clause vs the evidence discipline:
  SURFACED 2026-08-11 (s222) — OPEN, deliberately not ruled.** The fact that
  surfaced it: three commits, each **after** this ADR was Accepted — 2026-08-05
  (`36221a8`) and 2026-08-08 (`5934f1a`, `c3c7b8c`), vs this ADR landing
  2026-08-01 (`234c40f`) — wrote the apex domain into the exposure PLAN (now
  `docs/plans/done/0100-exposure-published-demo-surface.md`; five occurrences,
  working-tree lines 1101, 1702, 1719, 1726, 1967 at this pass). Each
  occurrence is an evidence record that arguably cannot do its job without the
  name: the rate-limiting rule as deployed names its zone (`:1101`); the s216
  Safe-Browsing incident record pins the exact flagged callback URL (`:1702`),
  states a name-collision theory in which the domain string itself is the
  evidence (`:1719`), and records the Search Console recovery step, which
  takes the domain as its input (`:1726`); the 2026-08-05 zone-quota reading
  names the zone it measured (`:1967`). Three independent sessions resolved
  the collision the same way without anyone noticing there was one — evidence
  of a real tension, not of three lapses: a PLAN recording a measurement taken
  against a real zone has to name the zone or the evidence stops being
  checkable, and the project's own evidence discipline (CLAUDE.md §8: command
  output is evidence; fresh on-disk evidence) pushes hard in that direction.
  **The question, Cray's to rule:** does the broad clause ("nothing in this
  repo may reference the portal domain") govern operational / evidence
  documents (`docs/plans/`, `docs/logs/`) at all, or only the runtime surfaces
  the narrow clause enumerates (application code, image, compose file, env
  contract)? And if it governs both, what does an evidence record cite instead
  so the measurement stays checkable? Options, stated neutrally — none
  recommended here, none ruled:
  **(a) narrow scope** — the broad clause is read as protecting the runtime
  surfaces; evidence records may name the zone when the measurement requires
  it (cost: the string recurs in tracked documents, and L6 portability rests
  on the narrow clause alone);
  **(b) categorical scope + indirection** — evidence records say "the portal
  zone" (the OQ-4 operational answer) without the string (cost: re-checking a
  measurement requires resolving the indirection out-of-band — dashboard or
  Cray — so the record is no longer independently checkable from the repo);
  **(c) categorical scope + two-artifact evidence** — the domain-bearing
  detail lives in a gitignored companion and the tracked record cites its
  path, the PLAN-004 v2 D6 two-artifact model `docs/logs/` already uses
  (cost: the checkable half is unversioned and can be lost).
  Whichever way Cray rules, D1(3)'s wording takes a scoping amendment
  **then** — not now, and not by this note. Interim posture is only what s222
  already ruled: the five existing occurrences stay (the repository is public
  and git history retains the string regardless — deleting a working-file copy
  buys the feeling of cleanliness, not the fact of it), ADR-0036 no longer
  asserts their absence, and whether **new** evidence records may add
  occurrences is exactly this question — unruled.

## Alternatives Considered

### Alternative 1: Shared Basic Auth credential at an on-LAN proxy (round 1's D3)
- Pros: honors L1's *letter* exactly (one shared credential); no visitor emails
  processed anywhere; browser-native prompt with no dependence on the vendor's
  auth product.
- Cons: mints a secret whose leak is invisible and whose rotation is manual;
  admits unauthenticated traffic through the tunnel onto a production-carrying
  host before denying it; per-system credentials multiply under the portal scope
  (L9); no per-visitor revocation or audit.
- Why rejected: **superseded by new info** — the round-1 pick was sound on the
  round-1 fact base (and its "Access has no shared-password shape" objection was
  literally true); P1/P2's evidence plus the portal re-scope invert the comparison
  (D3). Retained as OQ-1's named fallback.

### Alternative 2: Per-route authn for the seven open POSTs (A2 — against L1)
- Pros — the honest counter-case to L1: per-visitor keys would give the prompt log
  an identity, make a leak revocable per-person, and reuse the shipped fail-closed
  seam (`auth.py:63-94`).
- Cons: a key-issuance lifecycle for an audience of anonymous prospects; seven
  `Depends` edits to read+ask routes; the accountability it buys is worthless on
  synthetic data — and D3's Access gives per-visitor revocation without app code.
- Why rejected: L1 (Cray, typed). The pilot posture (D8) is where per-route
  identity genuinely belongs, via the s172 phase-2 JWT recipe.

### Alternative 3: Open link + rate limit only (A3)
- Pros: zero credential friction.
- Cons: hands the open internet metered-but-free MS-S1 inference (five routes,
  F3 ▲) on a box where every call can evict a co-tenant's production model (P5);
  indexes the demo for crawlers.
- Why rejected: L1; P5 hardens the rejection — a rate limit bounds burn rate, not
  audience, and the audience is hand-picked by the wedge anyway (ADR-0032 D1).

### Alternative 4: Static-only public site (no live API)
- Pros: near-zero exposure surface; no GPU path at all; trivial hosting.
- Cons: cannot show the live governed loop, NL-query, or the arm disclosure — the
  exact substance the wedge demos; s174 showed the whole decision tree hung on
  this fork.
- Why rejected: **L8 (Cray, typed, s175)** — live-API shape. Recorded here so the
  fork's closure is visible in the ADR that inherited it.

### Alternative 5: Cloud VM calling home to MS-S1 (B1b) / cloud without MS-S1 (B1c)
- Pros: a serving host off the home uplink; no tunnel vendor.
- Cons: B1b requires a standing internet→LAN channel for LLM traffic — killing
  ADR-002's PDPA sentence instead of preserving it (F8) — plus a VM to operate and
  pay for; B1c swaps MS-S1 for a hosted LLM, violating the §8 residency default
  and the on-prem story the wedge sells (ADR-0032 D1(5)). P9 also removes B1b's
  main selling point: the LAN host already *is* an always-on server.
- Why rejected: L2 = B1a (Cray, typed); F8 makes B1a the only option under which
  ADR-002's strongest claim survives by construction.

### Alternative 6: Zero prompt retention (against L3)
- Pros — the honest counter-case to L3: no stored visitor text, no processing
  record, no DSR path, no breach surface; strictly simpler.
- Cons: throws away the only behavioral signal a demo campaign produces (what
  prospects actually ask) — the D6-bounded value L3 buys.
- Why rejected: L3 (Cray, typed, obligations named). Reversal is cheap if the
  obligations ever outweigh the signal: a one-line regime change plus a log purge.

### Alternative 7: No tenant column (T0) / full multi-tenancy (T2-full — both against L4)
- T0 pros: pure YAGNI — single-tenant deployments with per-deployment databases
  never *need* the column. Cons: the retrofit lands exactly when it is most
  expensive (live pilot data, per-customer backfill semantics), and every query
  written until then is written wrong for the consolidated case. Rejected: L4.
- T2-full pros: real hosted multi-tenancy. Cons: collides head-on with the
  process-wide isolation unit (`config.py:179-185`, `auth.py:82`) and hand-wired
  factories (`main.py:103-156`) — an engine re-architecture disguised as a column.
  Rejected: L4's light reading is the point; D7(vii) makes the boundary explicit.

### Alternative 8: Supersede ADR-002 / ADR-0003 wholesale
- Pros: one clean successor document.
- Cons: both ADRs' mechanics are still binding truth (hosts convention, firewall,
  `OLLAMA_HOST` binding, service discovery; `${VAR:-default}` dev-port pattern) —
  superseding orphans valid decisions to fix four sentences.
- Why rejected: D2's amend-in-place closes the dangling deferrals at minimal blast
  radius, per the ADR-0034 in-place precedent.

### Alternative 9: Build the portal inside the vero-lite repo
- Pros: one repo to manage; the first tenant is here anyway.
- Cons: the portal outlives and out-scopes any one system (L9); its config would
  couple every future system to this repo's history, reviews, and gates; the repo
  boundary is itself an isolation mechanism (a portal change can never be smuggled
  into an app PR, and vice versa).
- Why rejected: **L5 (Cray, typed, s172)**.

### Alternative 10: A separate domain per system (vs one domain + subdomains)
- Pros: per-system branding; blast-radius isolation at the DNS level.
- Cons: N domains to buy, renew, and front; N times the gate/policy setup; nothing
  the subdomain convention + per-system isolation (D4) does not already provide.
- Why rejected: **L9's** one-domain-many-subdomains shape (Cray, typed), with L6
  guaranteeing the one domain is never load-bearing.

### Alternative 11: ngrok / Tailscale Funnel as the tunnel
- ngrok: native basic-auth on the tunnel, but an ephemeral free-tier URL + an
  interstitial page in front of partners, a paid tier for stability, and no
  production track record on this host. Funnel: publishes with **no visitor gate
  at all** (fails L1 without an added component; its access model targets tailnet
  members, not demo guests) — and ADR-002's Alternative 3 already deferred
  Tailscale once. Both lose to a pattern already running in production on the
  target host for five months (P1 `[ext]`).

> **Amended 2026-08-02 — currency correction (Cray-ratified scope):** as of
> 2026-08-02 the smb-flow tunnel process is not running (see the P1 amendment,
> Context), so read "already running in production … for five months" as a
> **track record**: roughly five months of production operation on the target
> host, plus a still-provisioned substrate (Zero Trust account, domain,
> known-working config). Stopping the process does not un-prove the pattern, and
> neither competitor gains ground from it: ngrok still has no production track
> record on this host, and Funnel still publishes with no visitor gate. The
> rejection stands.

## References

- Dispatches:
  `.claude/handoffs/session-200/2026-08-01-1114-code-plan-drafter-adr0035-hosting-exposure-dispatch.md`
  (round 1 — LOCKED L1–L4; fact-pack corrected in Context) ·
  `.claude/handoffs/session-200/2026-08-01-1244-code-plan-drafter-adr0035-REVISION-portal-scope-prior-art-dispatch.md`
  (round 2 — L5–L9, P1–P12, the withdrawal, the R2 defects)
- Prior art (on-disk, re-verified):
  `.claude/handoffs/session-172/2026-07-25-1432-code-session172-CLOSE-plan0093-COMPLETE.md:255-302`
  (four-specialist findings; the A-before-B warning; the on-prem claim later
  superseded) ·
  `.claude/handoffs/session-174/2026-07-25-2351-code-session174-CLOSE-ms-s1-ssh-and-plan0094-step1.md:180-185`
  (the corrected diagnosis; the one-decision collapse)
- Prior art (external — smb-flow repo, attributed, not verifiable here):
  `docs/deployment/live-server-blueprint.md`,
  `documents/context_ms_s1_max_live_server.md` (P1, P9, P10's mechanism);
  re-confirmed on first touch by the exposure PLAN's Cray-gated live evidence
- Trigger record: `docs/STATUS.md` §'Active TODOs' (trigger FIRED; the B1 lean L2
  refines); `docs/STATUS.md` §'Active TODOs' (nav-bar overflow measurement — `scrollWidth
  1825` vs `clientWidth 1382`, all 24 overflowing elements in the global nav, s197)
- ADR-002 `docs/adr/0002-network-topology.md:76,86,113-116,64-66` · ADR-0003
  `docs/adr/0003-service-port-strategy.md:105` (the four deferrals D2 resolves)
- PLAN-0095 `docs/plans/done/0095-docker-image-boot.md:6,11-12,29-31,626-629`
  (the artifact, its evidence boundary, the L8 record, and OQ-1's trigger)
- Code (all re-verified this session at the working tree, `main`=`164197c`):
  `services/api/auth.py:63-94,97-116,71-72,82` ·
  `services/api/routers/{query.py:29-42, procedure_draft.py:233-328,
  insights.py:57,227-235,265-275,278-298, demo.py:52,180-199, intake.py:153-198,
  audit.py:31,43, admin.py:174-177,222-223}` ·
  `services/api/config.py:53-61,79-82,106-118,179-185` ·
  `services/api/main.py:103-156` · `services/engine/code_generator.py:871-874` ·
  `services/engine/procedures/runs.py:81-128` ·
  `services/engine/procedures/schedules.py:35-38` · `services/db/` table census
  (`__tablename__`: **21 model tables across 12 modules**; the 22nd occurrence is
  the generator's emitter) ·
  `services/notify/line.py:133,294-330` (the only "throttle" matches) ·
  `verticals/fleet_maintenance/{procedures.yaml:102-111,
  data_adapter/synthetic.py:1}`
- `docs/conventions/partner-ropa-lite.md` (§6 retention/erasure, §8 DSR, the roles
  posture D6 inverts for the demo instance) · Lesson #0034 · ADR-0032 D1/D5 ·
  CLAUDE.md §8

## Implementation Notes

Three follow-on artifacts are **named but not drafted here** (CLAUDE.md §8: this
ADR merges before implementation starts):

1. **The portal repo bootstrap (L5 — a separate new repo, out of scope here).**
   Owns: the `cloudflared` connector + ingress map (the only domain-bearing layer,
   D1(3)), the Access policies (D3), the `portal.` landing surface, and the
   per-system compose/network conventions (D4). Every step that touches MS-S1 is a
   host-state change — explicit Cray go before any command runs (§8; P9 lowers the
   surprise, not the gate), planned under the D1(5) do-no-harm duty to the
   co-tenant production stack.

   > **Amended 2026-08-06 — connector-ownership reconciliation (Cray's typed
   > ruling, session 208, reading (a) — full text at D4).** "The `cloudflared`
   > connector + ingress map" narrows to: the **cross-system** ingress map
   > (subdomain→system bindings — still the only domain-bearing layer, D1(3))
   > plus the portal's **own** connector for `portal.`. Each system's connector
   > service, committed route-allowlist config, and secret-held tunnel
   > credentials are that system's property, inside its own compose project —
   > for vero-lite, owned by the exposure PLAN (note 2).
2. **The vero-lite exposure PLAN (this repo).** Owns: the published compose
   project's env profile (`API_AUTH_ENABLED=true`, the `OLLAMA_HOST` override, the
   P4 timeout/retry profile — D5(4)/(5)), the route allowlist **with a declared
   per-route arm posture, explicitly labelled PROVISIONAL** (D5's P12 ruling), the
   pre-publication rate + concurrency caps (D5(3)), the prompt-log writer +
   rotation + the populated RoPA-lite instance + the in-app notice banner (D6),
   and its Cray-gated live evidence step — the first demonstrated tunnel behavior
   for *this* system: the edge-timeout measurement (P4) and the
   eviction-coexistence check (P5). **The nav-bar overflow fix is a blocking
   acceptance criterion of this PLAN before any link is shared** (ruling: IN the
   exposure PLAN's critical path, OUT of this ADR's decision set — the measurement
   is real, `docs/STATUS.md` §'Active TODOs', and a public link is a first-impression
   surface, but a CSS fix is not an architecture decision).

   > **Amended 2026-08-06 — rides with the reading-(a) ruling (Cray, session
   > 208).** The exposure PLAN is PLAN-0100
   > (`docs/plans/0100-exposure-published-demo-surface.md`). The route allowlist
   > this note already assigned to vero-lite is now explicitly **edge-shaped**:
   > the PLAN also owns vero-lite's own `cloudflared` connector service and its
   > committed, path-scoped, domain-ignorant ingress config (allowlist +
   > catch-all 404 — the SD-3 ruling), plus the tunnel credentials (secret-held,
   > never committed — CLAUDE.md §8). This note and note 1 were the two halves
   > of the tension the D4 amendment reconciles: the route allowlist was
   > vero-lite's from ratification day — only the connector's address changed.
3. **The tenant-key PLAN (this repo).** Owns D7 (i)–(vii) exactly as enumerated.

Deployment configuration files, the Alembic migration, the CSS fix, and the portal
repo's own scaffolding are all **out of this ADR by dispatch** — this document
decides postures and names owners.

**Ratified by Cray, session 200 (2026-08-01)** — OQ-1, OQ-2, OQ-3 and OQ-5 each typed
against the stated recommendation and each confirmed as drafted; OQ-4 (the domain) left
deliberately open and non-blocking per L6. Status is therefore **Accepted**. Code applies
the D2 pointer amendments to ADR-002 (three lines) and ADR-0003 (one line) in the landing
PR, and commits via a `docs/*` branch + PR (ADR-009 D2). AI-assisted drafting (in-harness
`plan-drafter`, two rounds), reviewed by Code (R2) before landing; no `Co-Authored-By`
(CLAUDE.md §7).
