# s256 — MS-S1 read-only deploy census, and what is merged but not live

**Session:** 256 · **Date:** 2026-08-26 · **Author:** Claude Code (Tier 2)

> **The go.** `CLAUDE.md` §8 and `published-demo-redeploy.md` §0 gate *every* command
> that reaches the deploy host, read-only included. Cray's typed go, 2026-08-26:
> **"เอา และเตรียมแผน deploy ด้วย"** — inspect read-only, and prepare a deploy plan.
> Recorded here **before** the commands ran, per §0.
>
> **What actually ran:** one `.ps1` piped over `ssh -o BatchMode=yes ms-s1
> 'powershell -NoProfile -Command -'`. It executed `git -C … rev-parse/status/log`,
> `docker compose ls`, `docker ps`, `docker ps -a`, and `docker image inspect`.
> **No `pull`, no `build`, no `up`, no service or task touch, and no Ollama contact
> of any kind.** The script printed a terminal `DONE-READONLY` token, which is what
> the completeness claim below rests on — not an exit code (Lesson #0007).

## §1 — What is live, measured

| | fleet | procurement | energy |
|---|---|---|---|
| compose project | `oct-fleet-maintenance` running(3) | `oct-procurement` running(2) | `oct-energy` running(2) |
| app image | `sha256:0fc679cf…` | `sha256:bc95aa04…` | `sha256:f2c3717b…` |
| image built | **2026-08-22** | 2026-08-11 | 2026-08-10 |
| app container | Up 2 days (healthy) | Up 2 days (healthy) | Up 2 days (healthy) |

- **Host checkout `C:\projects\vero-lite` is at `ee41b55`, branch `main`, tree clean.**
- ✅ **The one-time STOP condition is CLEAR** — `docker compose ls --all` lists no
  project named `vero-published`. The PLAN-0103 Step 4b rename is fully settled on
  this host; the redeploy runbook §0b no longer applies.
- Cross-check that makes this more than a snapshot: the fleet image id
  `sha256:0fc679cf…` is **byte-identical to the id recorded in
  `docs/logs/2026-08-22-s246-…md` step 6**. The deploy log and the host agree, so the
  log is a trustworthy record of what shipped.
- The unrelated `smb-prod` / `smb-staging` projects are `exited(9)`, untouched, and
  4 weeks cold. Noted only so a future reader does not mistake them for OCT drift.

## §2 — Merged but NOT live

`ee41b55..origin/main` restricted to `services/ verticals/ ontology/ deploy/
pyproject.toml docker-compose.yml` — four commits, nine files:

| PR | What | Live impact if deployed |
|---|---|---|
| [#1275](https://github.com/CrayJThiemsert/vero-lite/pull/1275) [#1277](https://github.com/CrayJThiemsert/vero-lite/pull/1277) [#1279](https://github.com/CrayJThiemsert/vero-lite/pull/1279) | **PLAN-0113 Steps 1–3** — `scope_by`/`when_absent` grammar, `trigger_context` wired into `query_step`, the fleet scope clause | 🔴 **Visitor-visible.** An event-fired run scopes to its firing case instead of sweeping the fleet |
| [#1287](https://github.com/CrayJThiemsert/vero-lite/pull/1287) | **PLAN-0114 Step 1** — the `continue_no_decision_run` chokepoint | None. Library-only; no route reaches it |
| [#1267](https://github.com/CrayJThiemsert/vero-lite/pull/1267) | `config.py` docstring correction | None |

Files: `spec.py`, `query_step.py`, `persistence.py`, `draft.py`, `governance_pin.py`,
`config.py`, `trace-kinds.js`, `index.html`,
`verticals/fleet_maintenance/procedures.yaml`.

**Also relevant and NOT yet merged:** PLAN-0114 Step 2 (PR #1298) and Step 3.

## §3 — 🔴 The sequencing finding: 0113 must not ship alone

**PLAN-0113 Step 3 is what CREATES the empty-gate dead end**, and PLAN-0114 exists to
close it. Scoping an event-fired run to its firing case is exactly what makes a
sub-ceiling acceptance (฿4,500, under every truck's ฿5,001 ceiling) park at `approve`
with an **empty** proposal set — a state that was unreachable before, because `intake`
swept the fleet and the fixture always carried a breaching truck.

So:

- Deploying **0113 alone** puts a visitor-reachable dead end on the live fleet demo:
  accept a sub-ceiling quote → a parked run `/gate/resolve` refuses (409, nothing to
  resolve) whose only exit is `/cancel`, which records **abandonment** for a case that
  was checked and cleared.
- The host is currently safe from this **by accident, not by plan** — 0113 was never
  deployed. PLAN-0113 **AC-9 (live evidence on MS-S1) is archived CARRIED-OPEN** for
  the same reason: the go was never held, so MS-S1 received no contact.

**Therefore the deploy unit is `0113 + 0114 (Steps 1–3) together`, never 0113 alone.**

## §4 — A live-only gap Step 3 found, that the offline suite would have shipped

`deploy/published/oct-fleet-maintenance/cloudflared/config.yml` is a **default-deny**
ingress allowlist. `^/runs/[^/]+/continue$` was not on it, so the acknowledge button
would have **404'd at the Cloudflare edge** on the live demo while passing every local
test. It was caught by `test_ac6b_every_route_the_ui_references_is_classified` — the
tripwire reddening exactly as designed on a new UI fetch to an unlisted route.

Fixed in Step 3, in three places (the config row 4b, the profiles test's fleet set,
and the compose test's two census tables), each with a written basis per that file's
convention. ⚠️ **This admits a new write route to a published surface.** It is
strictly less privileged than the `gate/resolve` row already published — the
chokepoint 409s any gate holding a decidable proposal, so it can never approve — but
it is a publishing decision and is flagged for Cray at the PR rather than treated as
mechanical.

## §5 — Deploy plan (prepared, NOT executed)

Nothing below has run. It needs its own typed go **per occasion and per phase**
(§0 / `oct-fleet-maintenance/DEPLOY.md` §0), and it should not run until PLAN-0114
Steps 2+3 are merged.

1. **Precondition:** PR #1298 (Step 2) and the Step 3 PR merged to `main`; CI green at
   the merge sha; `main` pulled locally.
2. **Scope:** `oct-fleet-maintenance` only. Energy and procurement are on older images
   and neither publishes Tab H, so neither needs 0113/0114 to be correct — redeploying
   them is a separate decision with its own risk, not a free ride-along.
3. Follow `docs/runbooks/published-demo-redeploy.md`. §0b's STOP condition is already
   measured CLEAR (§1 above) — re-measure anyway, per the runbook's "every time".
4. The three host-reaching phases, each needing its own go: **(a)** `git -C
   C:/projects/vero-lite pull --ff-only` — note the compose file, `published.env` and
   `cloudflared/config.yml` are read from the **host checkout**, so the new ingress row
   arrives with this pull, not with the image; **(b)** build on the workstation, `docker
   save | ssh … docker load`, assert the image id is equal on both machines; **(c)**
   `compose up -d`, then assert an **effect**, not step success (runbook §1 fact 3).
5. **Tag `:prev` before the load** — the rollback point. Current rollback target is
   `sha256:0fc679cf…`.
6. **Then, and only then, PLAN-0113 AC-9's live walk** — accept a mid-band quote
   (single-proposal gate) *and* a sub-ceiling quote (empty gate → the new Acknowledge
   button → run completes), plus the demo reset reading `PRISTINE`. That walk closes
   0113 AC-9 and PLAN-0114 AC-5's live half in one pass, which is why they belong in
   the same occasion.

---

*Read-only inspection only. No host state was changed. MS-S1 received no Ollama
contact. AI-assisted (Claude Code).*
