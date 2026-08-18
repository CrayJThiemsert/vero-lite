# Local-first, published-parity — the two-machine development standard

> **Ratified by Cray (typed, session 237, 2026-08-18).** The standing procedure for
> any change that will end up serving a published system: develop and verify on
> **Cray-Legion5Pro** first, then deploy to **MS-S1 MAX**. Both machines carry their
> own state, so the sequence is one-way by intent — never edit the live host to make
> a change work and reconcile the repo afterwards.
>
> This is a **convention** (§1 precedence tier 3): a canonical reference you look up
> deliberately. The host-state gate it operates under is the binding rule in
> [`CLAUDE.md`](../../CLAUDE.md) §8 — this file never relaxes it.

---

## Why this exists — the measured failure it prevents

Local-first alone is not enough, and the repo has the evidence.

The intro-video storyboard was built local-first. Every frame in its beat 4 was
verified on a real render, with measured geometry — the work was done properly. It
still targeted a screen the customer cannot reach, because the local process ran the
**dev** profile while the deployed system runs the **published** one:

| | local run as launched | deployed fleet system |
|---|---|---|
| `UI_PROFILE` | `dev` (the default, `services/api/config.py:265`) | `published` |
| tabs served | all ten | six — `A,C,F,H,I,J` |
| Tab **G** (the hero the storyboard filmed) | present | **absent by ruling** (SD-3 s218; ADR-0032 D1.2) |
| personas (the approve beat) | **none** — `resolve_demo_personas` runs only on `published` (`routers/actions.py:226`) | three |
| disclosure bars above the fold | none | two, **80 px**, invalidating every recorded `scrollTop` |

Both halves of that table are failures of the same kind: a local run that is not the
published configuration is **a different system**, and proving something on it proves
nothing about what ships.

The second half of the rule has its own precedent. PLAN-0107's first CI run died on
`ModuleNotFoundError: No module named 'services'` — unreachable locally **by
construction**, because the runtime venv is `--no-install-project` while every local
run used the dev venv. No amount of local care would have found it. The remedy was to
**name the gap and build the condition**, not to reason about it.

---

## The standard — three layers, all three required

### Layer 1 — Local must wear the published profile's configuration

Develop on Legion5Pro, but run it with the **same env the deployed profile declares**,
read from that profile rather than retyped:

- `UI_PROFILE=published`
- the same `UI_PUBLISHED_VIEWS` set
- the same thresholds, direction, entity pins and demo flags

The per-system source of truth is `deploy/published/<system>/published.env`. Secrets
(`API_KEYS`, `UI_DEMO_PERSONA_KEYS`, the database password) are **never** in that file
and are passed from the host environment — provide throwaway local values, never real
ones.

A run under `UI_PROFILE=dev` is a **development** run. It is legitimate for writing
code; it is **not** evidence about the published surface, and a claim resting on it is
recorded as `asserted-not-verified` until re-measured under parity.

### Layer 2 — Name what local cannot prove, in writing, before deploying

Four things are structurally unreachable from Legion5Pro. Enumerate them for the
change at hand and carry the list into the deploy step:

1. **The real LLM backend** — `LLM_BACKEND` defaults to `local` (Ollama on MS-S1). A
   local run pinned to `hosted` reaches nothing (every consumer raises), so it
   exercises the deterministic fallback, not the model path.
2. **The live database's accumulated state** — seeders are idempotent and skip on
   existing rows, so the deployed database holds history a fresh local database never
   reproduces. Frozen timestamps and once-seeded rows live here.
3. **Cloudflare Access** — the auth wall in front of every published host.
4. **DNS + the tunnel** — a committed profile is not a served route. *Committed ≠ live.*

A gap that cannot be closed locally is not a reason to skip the local pass; it is the
content of the post-deploy check.

### Layer 3 — After deploying, verify exactly the Layer-2 list

Not a re-run of the whole suite, and not a glance at the home page. Check the named
items, each against a pass/fail read fixed **before** the deploy, with fresh on-disk or
on-wire evidence. `CLAUDE.md` §6 applies unchanged: a passed check is logged
`confirmed — prior intact`, never as a defect; **no fresh evidence is
INSUFFICIENT-EVIDENCE, not a pass.**

---

## What this standard does not do

- It does not authorise a host-state action. Deploying, warming a model, or altering
  MS-S1 over SSH still needs **explicit Cray go per occasion** (`CLAUDE.md` §8), and
  a go given for one action does not carry to a different one.
- It does not permit fixing the live host directly. If the deployed system is wrong,
  the change lands in the repo, goes through a PR, and is deployed — so the next
  rebuild does not silently revert it.
- It does not make "local passed" into "live passes". It makes the difference
  **enumerated** instead of assumed.

---

## Worked example — session 237

The rule was applied to its own first case, and the first thing it caught was a
directive built on a false premise.

**The ask:** the deployed fleet demo showed pipeline runs dated `16 Aug 2026`, stale
and drifting. The proposed fix was to set `OCT_DEMO_TIME_ANCHOR=true` on MS-S1.

**Layer 1 + 2, before touching the host:** the flag is read at
`services/engine/demo_events.py:100` and shifts the in-memory **synthetic
`OperationalEvent` list** only. The Monitor's run card renders `r.started_at`
(`services/api/static/assets/view-monitor.js:195`) — a `PipelineRun` column in
Postgres. The two never meet.

**The real cause** is Layer-2 item 2: `services/api/main.py:307` skips seeding when
`load_run(session, DEMO_RUN_ID)` finds a row, so the run was written once at bring-up
and frozen. The same skip means a run that is **approved** is never re-seeded either —
consuming the demo's approve beat permanently until the row is deleted.

**Outcome:** setting the flag on MS-S1 would have been a host-state change that fixed
nothing, reported as done. The work moved to the repo instead.

**The transferable shape:** *an inherited premise a decision rests on is a claim, not
context* (`CLAUDE.md` §6). Deploy-time directives inherit premises about the live host
more often than any other kind, because the host is the surface nobody re-reads.

---

## References

- `CLAUDE.md` §8 (host-state gate; command-output-is-evidence), §6 (verification is
  hygiene; inherited premises are claims)
- [`.claude/skills/code-operational-policy/SKILL.md`](../../.claude/skills/code-operational-policy/SKILL.md)
  — the plan-first discipline for costly / host-state / irreversible execution (read
  the result-producing code first; pre-commit the pass/fail read; run once; verify)
- [`docs/lessons/0026-interpret-before-run-pre-commit-outcome-meaning.md`](../lessons/0026-interpret-before-run-pre-commit-outcome-meaning.md)
  — pre-commit what each outcome will mean, before the run that produces it
- [`docs/runbooks/published-demo-redeploy.md`](../runbooks/published-demo-redeploy.md)
  — the deploy mechanics this standard sits in front of
- `deploy/published/<system>/published.env` — the per-system parity source
