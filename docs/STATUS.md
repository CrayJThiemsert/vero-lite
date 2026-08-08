---
last_updated: 2026-08-08T13:58:23+07:00
session: 215
current_batch: "s215 — four PRs (#1084–#1087), 0 open: PLAN-0100 Step 11 RAN live against the published demo. Four defects found, three fixed, redeployed and re-verified live the same session."
current_actor: code
blocked_on: "Nothing is blocked. PLAN-0100 stays Draft — AC-6(c) has not been re-scored against the D-3 fix, and P4(i)'s T_edge is UNMEASURED (bound: >= 54 s)."
next_action: "Judge whether PLAN-0100 Step 11 is closeable — re-score AC-6(c), decide T_edge. Non-gating: D-4's direction, a cache-purge step in the redeploy runbook, AC-12, ADR-0036."
head_commit: 94fac66
recent_commits: [94fac66, 825eec0, 00ddca0, 6660165, 1ddcde3, 77e94bf, b279056, b0f26e6, a8033f9, bef5d66]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 215, 2026-08-08 (head_commit `a5ae3cd` → `94fac66`) — four PRs merged
> (#1084–#1087), 0 open. Theme: PLAN-0100 Step 11 — the Cray-gated live run against
> the published demo — was executed end to end; it found four defects, three of which
> were fixed, redeployed and re-verified live in the same session.**
>
> **The run.** Driven through the ratified Cloudflare Access gate with a cookie from a
> real one-time-PIN login (the s214 route), under Cray's typed §8 go, with the
> unauthenticated control re-run alongside (302/302/302). **Cases 0, 2, 3, 4, 6, 8
> CLOSE.** **Case 1 closes 19/21 on its own read** — the two misses were the font
> content-types, and two further failures were probes the runner added, not rows the
> case asks for. **Case 5 FAILED, was fixed, and re-verified PASS.** **P5 PASS**;
> **P4(ii) PASS** twice independently; **P4(i)'s exact `T_edge` is UNMEASURED** —
> recorded as INSUFFICIENT-EVIDENCE with a measured lower bound (`T_edge ≥ 54 s`)
> that excludes the clause's own FAIL condition of `< 40 s`.
>
> 🔴 **Four defects, none catchable offline.** **D-1 — 90+ published `POST /query`
> wrote ZERO prompt-log rows.** The image never created the volume mount point, so
> Docker made it root-owned while the runtime is uid 999; `prompt_log.record` swallows
> `OSError` **by design**, so it failed silently and ADR-0035 D6's whole regime (RoPA,
> 90-day retention, the purge command, the DSR path) described a file that did not
> exist. **D-2** — the prompt log named a model that never ran
> (`ollama_default_model` / `gemma4:26b` recorded while the engine ran
> `recommender_model` / `gpt-oss:20b`). **D-3** — bundled `.woff2` fonts served as
> `text/plain`: the slim image ships no `/etc/mime.types` and Python's built-in table
> has no `.woff2`. **D-4**, narrowed after a second measurement: **only** the
> `group_by` verified_query fails — `count` aggregation works, and the second query's
> empty result is the **correct** answer (the dataset holds no `feeder` asset). Left
> open, direction undecided. **Also:** the demo pinned no `keep_alive`, so the first
> visitor after an idle spell waited the full 25 s timeout and got a degraded,
> ungrounded answer; fixed by sending the existing `ollama_keep_alive` on every chat
> call.
>
> **The finding worth carrying forward:** `deploy.py`'s seven green checks prove the
> **container** runs the new image; they do **not** prove a **visitor** receives it.
> D-3 read as still-broken after redeploy because Cloudflare was serving a
> `text/plain` copy cached while the defect was live (`cf-cache-status: HIT`,
> `max-age=14400`), closed by a manual **Purge Everything** (Cray). Nothing in the
> pipeline purges the edge, and the repo's `?v=cNN` convention does not reach fonts
> (referenced from inside CSS with no version parameter). A purge step or versioned
> font URLs belongs in the redeploy runbook — **not done**.
>
> **Twelve instrument faults** were caught and are listed in the PLAN record. The two
> most consequential: the probe matrix first scored **0/43 against a completely
> healthy demo**, because Cloudflare's Browser Integrity Check rejects a
> `Python-urllib` User-Agent *before* Access is consulted; and a `/query` oracle
> passed on the string *"I couldn't translate that question into a query over the
> operational data."* Common root: **checking a proxy for the thing rather than the
> thing.** **No AC was ticked — PLAN-0100 stays `Draft` at 10 of 13.** _[STATUS's
> frontmatter had stalled at `1384278`; s214 in fact closed at `a5ae3cd`, so the
> commits between them are s214's later merges, reconciled here rather than
> restated.]_

> **Session 214, 2026-08-07→08 (head_commit `07e9603` → `1384278`) — six PRs merged
> (#1073–#1078), 0 open. Theme: the published demo got a repeatable deploy
> procedure, and the procedure found three defects in itself before it was allowed
> to touch the host.**
>
> **#1074 — the redeploy pipeline.** `deploy/published/deploy.py` + a runbook +
> **18 guard/scenario tests**. Bring-up was a one-time procedure; nothing covered
> "main moved, make the demo be that". It asserts an **effect** — the running
> container's `.Image` equals the id just loaded — not a step count, because
> `compose up` decides for itself whether a container is stale and that decision
> appears in no command's output. Also: `:prev` tagged before the load overwrites
> `:latest` (rollback), and force-recreate of the connector **only** when the
> bind-mounted ingress config changed.
>
> 🔴 **#1076 — every remote `--format={{…}}` was unrunnable.** The deploy host's ssh
> shell is **PowerShell** (`echo %COMSPEC%` comes back unexpanded), which reads
> `{…}` as a script block: docker gets `unknown shorthand flag: 'e' in
> -encodedCommand`. Fixed by asking for plain JSON and parsing locally; `scp` and
> the `C:\vero-staging` path dropped for `docker load` on stdin. **The guard written
> one PR earlier to catch exactly this went GREEN over it** — its hazard set listed
> quotes, `$` and separators but not braces, because it came from what was
> imagined, not measured. **#1075:** a plan reported `PASS` for checks it never ran
> and closed "2 checks, 0 FAIL" at exit 0, found by running it and reading the
> output. **#1077:** the build could not interpolate its own compose file (`compose
> config` exits 1 without `CLOUDFLARED_CREDENTIALS_FILE`) while the code's own
> comment said so and passed nothing — the **third** instance in one session of
> *comment states the rule, adjacent code breaks it*. **#1073** reconciled s213's
> STATUS (never done) and discharged a stale 🔴 "Step 8 must not start" marker in
> PLAN-0100, cleared by #1057 on 2026-08-05; **#1078** folds in the corrections from
> the real run.
>
> **THE DEPLOY RAN, under Cray's typed §8 go (2026-08-08).** The demo now serves the
> image built from `d0a2808`; it had been on s213's image for 10 hours. `8 checks,
> 0 FAIL` — and every pre-committed read was verified **independently of the
> script's own ledger** by reading the host: container `11b0fb7201be…` →
> `45f6440a2d48…` (genuinely new — `Up 45 seconds` vs `Up 10 hours`), `.Image`
> `4c88145c8653…` → `153324a2995c…`, `:prev` now holds `4c88145c8653…` so rollback
> is live, host checkout `9601f068` → `d0a28080`, `/health` and `/` both **302** at
> the edge. The connector was correctly **not** recreated (none of the 14 changed
> files was `cloudflared/config.yml`).
>
> **The finding worth carrying:** none of the three pipeline defects was catchable
> by the offline suite — **3977 tests green over a script whose first command failed
> on contact with the host**. Same shape as s213's #1071 (3943 green over a
> container that could not boot), one layer up. What caught them was a read-only
> recon phase with a pass/fail read fixed **before** the run, and a rule that a
> failed phase means no deploy. Gate at CI scope on every merge: `ruff format
> --check` clean (614 files) · `mypy services/` clean (133) · **3977 passed /
> 8 skipped / 0 failed**.

> **Session 213, 2026-08-07 (head_commit `a22ff8e` → `07e9603`) — four PRs merged
> (#1069, #1070, #1071, #1072), 0 open. Theme: the session that stood the published
> demo up for real — and NOT ONE of the four defects came from a failing test.**
>
> **The demo is LIVE** at the `oct-energy` subdomain behind Cloudflare Access
> (one-time-PIN email allowlist), verified end-to-end in a browser by Cray. Every
> defect was found by touching a layer of reality nobody had touched before —
> docs → config → image → deploy host → edge.
>
> 🔴 **#1071 — `python-multipart` is a RUNTIME dependency, and the shipped image
> could not boot; it had not been able to since 2026-07-28.** It reached the dev
> venv only via `mcp` (a **dev** extra); the image installs `--no-dev`. FastAPI
> resolves multipart routes at *import* time, so `import services.api.main` raised.
> **3943 tests were green over a container that could not start.** The fix ships
> **a CI step that reproduces the image's dependency set and imports the entry
> module** — it guards the *class*, not the instance.
>
> **#1069 — `API_KEYS` had no way into the container.** `env_file` loads
> `published.env` and nothing else, and compose does not forward the host
> environment, so the secret the README told operators to provision was silently
> dropped: the demo was unloginable no matter what the host exported. Bare
> pass-through added, deliberately optional. **#1070** adds the bring-up runbook +
> `verify_tunnel_credentials.py` and fixes **7** `docker compose -p vero-oct`
> invocations in the operations runbook — the project is `vero-published`, so **all
> three PDPA deletion paths were unexecutable**. **#1072** folds in 7 corrections
> from executing the runbook for real, plus **13 tests for the verifier** (it
> shipped with none).
>
> **Step 11 is BLOCKED on a governance ruling nobody knew was needed — SURFACED,
> NOT RULED.** PLAN-0100 Step 11's case list asserts exact statuses (`/health` →
> 200, keyless `/whoami` → *exactly* 401 — which the PLAN calls the only thing that
> catches `API_AUTH_ENABLED=false` in the running container); through the ratified
> Access gate **every path returns 302** (measured on seven paths; the redirect
> metadata carries `"service_token_status": false`). The remedy is a service token,
> which Cloudflare requires be a **second Access policy** — and ADR-0035's
> acceptance shape names "a second Access policy" as a drift trigger. **ADR-0035 D3
> and the case list are each correct and were written at different times — a
> composition problem, not a defect in either.** **PLAN-0100 stays 10 of 13; AC-6
> unticked** ((c)'s "allowed → served" clause is still unproven).
>
> Verification: the full offline gate at CI scope **four times**, once per PR; final
> `ruff format --check` clean (612 files) · `mypy services/` clean (133) ·
> **3956 passed / 8 skipped / 0 failed**, the count pre-committed before every run.
> Non-vacuity demonstrated for all **9** guards added (mutations restored from
> `/tmp` copies, never `git checkout`). The shipped image proven identical across
> machines via `docker image inspect` after `save`/`scp`/`load`.

> **Session 212, 2026-08-06 (head_commit `8bd331d` → `a22ff8e`) — one PR merged
> (#1067), 0 open. Theme: the run that could not run still told the truth — and all
> three defects it found were in the instructions for running it.**
>
> **PLAN-0100 Step 9 ran as its OWN sanctioned offline fallback, not as the smoke.**
> Probed first: the box has `docker` and `curl` but **no `cloudflared` binary**, no
> `CLOUDFLARED_CREDENTIALS_FILE`, no `~/.cloudflared`; the compose declares that
> variable required-with-no-default, so `up` cannot start the project and **case 0 —
> which gates every other case — is unreachable**. A real tunnel needs a Cloudflare
> account action plus a domain ADR-0035 D1(3) places in the portal repo, which does
> not exist. Against the pass/fail read fixed **before** the run: **case 2 PASS**
> (24/24 excluded routes → `http_status:404`; 11/11 allowed → `http://app:8000`) and
> **case 7 PASS** (`cloudflared 2025.8.1`, committed config validates `OK`) — both
> install-free through the image the compose project already pins. **Cases 0, 1, 3,
> 4, 5, 6, 8 are NOT COVERED**, recorded and inherited by **Step 11**.
>
> **Non-vacuity DEMONSTRATED, not asserted.** Re-run against a **copy** of
> `config.yml` in `/tmp` with the `^…$` anchors stripped, the excluded
> `/insights/query` **flipped** from `http_status:404` to `http://app:8000` — so the
> 35 PASS rows prove the probe discriminates, not merely that it ran; the committed
> file was never mutated and both states are in the transcript.
>
> **AC-6 stays unticked; PLAN-0100 stays 10 of 13.** (c) has two clauses and only one
> is met — "excluded → 404 at the edge" is proven against the real `cloudflared`
> matcher, "allowed → served" is not, because **nothing was ever served**. Case 2
> likewise closes in its **rule-resolution form only**: its positive control (an
> allowed request must appear in `docker compose logs app`) has no app log to read,
> so that half rides to Step 11 with case 1.
>
> **Three COMMITTED defects found and fixed in the same PR; each would have scored a
> false verdict.** (1) The case list still called three `/demo/hero/*` GETs **served
> (200)** — Step 8 excluded that surface the day after v2 was written, so an operator
> reading it literally would have logged **three FAILs against an edge behaving
> exactly as intended**. (2) The sanctioned fallback was written `tunnel ingress
> validate --config F` in the PLAN and twice in `deploy/published/README.md`; the
> flag belongs on `tunnel`, and the wrong form prints `Incorrect Usage`, validates
> **nothing**, and **still exits 0** — a silent false pass for anyone scoring on
> `$?`. (3) It assumed a host `cloudflared`; the README now documents the
> install-free image invocation, installing one being a host-state change under
> `CLAUDE.md` §8.
>
> Gate at CI scope: ruff-format clean (610 files), `mypy services/` clean (133
> files), `tests/` **3938 passed / 8 skipped / 0 failed**, matching the count
> pre-committed before the run. _[Numbering: 209 → 212 is not a slip — parallel
> sessions consumed 210 and the 211 handoff directory, and the merged Step 9 run
> record says "session 212", so STATUS agrees with it.]_

## Prior focus (archived)

PLAN-003, PLAN-0005, PLAN-0006, PLAN-0007 and PLAN-0008 are all merged
and archived to `docs/plans/done/`; the Cowork-as-Tier-1 trial concluded
and was ratified permanently by **ADR-009** (Cowork = merged Tier 0 +
Tier 1 workspace; commits stay Code-exclusive). Full detail lives in
`docs/plans/done/`, the Recent Decisions table below, and git history.
_[Corrected s169, `was an error`: this paragraph claimed PLAN-004's
"Phase B/C remain deferred", which both the Next Steps section and the
Active TODO refute — **Phase A + B are COMPLETE (s35)** and only the
optional Phase C polish is deferred. The stale sentence is dropped rather
than restated: the Active TODO owns that status.]_

## Recent Decisions (last 10)

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-08-08 | **s215 — PLAN-0100 Step 11 RAN live against the published demo (#1084–#1087): cases 0, 2, 3, 4, 6, 8 CLOSE; case 5 FAILED → fixed → re-verified PASS; case 1 19/21.** Four defects, none catchable offline — **90+ published `POST /query` wrote ZERO prompt-log rows** (mount point root-owned vs runtime uid 999; `record` swallows `OSError` **by design**, so ADR-0035 D6's whole regime described a file that did not exist), a prompt log naming a model that never ran, `.woff2` served as `text/plain`, and a `group_by` verified_query (**D-4, left open**). `T_edge` **UNMEASURED** (bound `≥ 54 s`). **The edge cache masked the redeploy** — `deploy.py` proves the container, not the visitor. **`Draft`, still 10 of 13** | `94fac66` (head_commit) / [#1086](https://github.com/CrayJThiemsert/vero-lite/pull/1086) / [#1087](https://github.com/CrayJThiemsert/vero-lite/pull/1087) / `docs/plans/done/0100-exposure-published-demo-surface.md` |
| 2026-08-08 | **s214 — the published demo has a REPEATABLE deploy procedure, and it RAN under Cray's typed §8 go (#1073–#1078).** Script + runbook + **18 guard/scenario tests**; it asserts an **effect** (the container's `.Image` == the id just loaded), not a step count. Three defects, none catchable offline — **3977 green over a script whose first remote command failed on the host**: its ssh shell is **PowerShell**, so every `--format={{…}}` died at `unknown shorthand flag: 'e' in -encodedCommand`, **and the guard written one PR earlier went GREEN over it**. Demo now on `d0a2808`'s image; `:prev` holds the old, rollback live. **PLAN-0100 unchanged at 10 of 13** | `1384278` (head_commit) / [#1076](https://github.com/CrayJThiemsert/vero-lite/pull/1076) / `deploy/published/deploy.py` / `docs/runbooks/published-demo-redeploy.md` |
| 2026-08-07 | **s213 — the published OCT demo is LIVE behind Cloudflare Access (#1069–#1072); PLAN-0100 Step 11 is now BLOCKED on an unruled composition question.** `python-multipart` was a RUNTIME dep absent from the shipped image, which could not boot since 2026-07-28 while **3943 tests stayed green**; the fix adds a CI step that rebuilds the image's dependency set and imports the entry module. Step 11's exact-status cases cannot hold when Access returns **302 on every path**; the service-token remedy needs a **second Access policy** — ADR-0035's acceptance shape names that a drift trigger. **SURFACED, unruled; still 10 of 13** | `fe1d018` ([#1072](https://github.com/CrayJThiemsert/vero-lite/pull/1072)) / `6e6563a` ([#1071](https://github.com/CrayJThiemsert/vero-lite/pull/1071)) / `docs/plans/done/0100-exposure-published-demo-surface.md` |
| 2026-08-06 | **s212 — PLAN-0100 Step 9 RAN as its own sanctioned OFFLINE FALLBACK (#1067): cases 2 + 7 PASS, cases 0/1/3–6/8 NOT COVERED → inherited by Step 11.** No `cloudflared` binary, no credentials, and case 0 gates all the others. **Non-vacuity DEMONSTRATED** — anchors stripped on a `/tmp` copy flipped the excluded `/insights/query` to `http://app:8000`. **AC-6 unticked, still 10 of 13**: (c)'s "allowed → served" half is unproven, nothing was ever served. Three committed defects fixed — a stale served-200 case list, a `tunnel ingress validate` flag order that exits **0** validating nothing, a host-install assumption | `4a88f37` ([#1067](https://github.com/CrayJThiemsert/vero-lite/pull/1067)) / `docs/plans/done/0100-exposure-published-demo-surface.md` |
| 2026-08-06 | **s209 cont. — PLAN-0100 Step 8 SHIPPED (#1063): AC-4/5/6(a)(b) CLOSED, 8 → 10 of 13.** Greenfield `deploy/published/` + `tests/deploy/` (**69 tests**); Tab G dropped on the published profile (`?v=c48`). **`OCT_VERTICAL` pinned `energy` (Cray typed)** — the DB posture was **not** the discriminator: `FastenalCsvAdapter.stream_events` is an **empty async iterator by design**, so procurement's `GET /recommendations` returns `[]` on both profiles and Tab A lands blank. AC-6 stays unticked on purpose ((c) = Step 9). A non-vacuity probe caught a **vacuous test inside the change itself** | `1557141` ([#1063](https://github.com/CrayJThiemsert/vero-lite/pull/1063)) / `deploy/published/` / `docs/plans/done/0100-exposure-published-demo-surface.md` |
| 2026-08-06 | **s209 cont. — ADR-0036 DRAFTED `Proposed` (#1065): a deployed vertical instance IS a "system" under ADR-0035 L9/D4.** ADR-0035 defines "system" by what one owns (`0035:478-493`), and a vertical instance satisfies every clause with **zero engine change** ⇒ the multi-vertical demo is N systems + a `portal.` picker, and **D4's reopening trigger does not fire**; in-process multi-vertical serving is a recorded **non-goal** (`auth.py:82`). ⚠️ Ratifying `Proposed → Accepted` **must remove `0036` from `test_the_non_accepted_adrs_are_exactly_the_expected_set` in the same edit** | `8bd331d` (head_commit) / [#1065](https://github.com/CrayJThiemsert/vero-lite/pull/1065) / `docs/adr/0036-vertical-as-system-multi-vertical-demo-portal.md` |
| 2026-08-06 | **#1062 + #1064 (session 210, a PARALLEL session — NOT s209's work).** #1062 adds the `.claude/skills/stream-status/` skill (a 4-work-stream progress readout); #1064 gives `next-work-analyst/SKILL.md` a 4-stream lens (stream tag, stream column, per-stream view, balance note). s210 closed without reconciling STATUS, so this row is its only record here. ⚠️ Its closing notice asserted the skill's registry table is **canonical** and must be updated in the same PR as a carrier change — **recorded as an OPEN QUESTION for Cray** (In-Flight Discussions), not as a decision | `05d672f` ([#1062](https://github.com/CrayJThiemsert/vero-lite/pull/1062)) / `efaaeb3` ([#1064](https://github.com/CrayJThiemsert/vero-lite/pull/1064)) / `.claude/skills/stream-status/SKILL.md` |
| 2026-08-06 | **s209 — PLAN-0100 OI-1 RULED (Cray, typed): option (b), as a PRINCIPLE not a one-route patch (#1060).** On the `published` profile an LLM call the visitor did not initiate is **no longer made** — `arm_policy.py` (the principle + one predicate); `recommend(..., visitor_initiated=False)` is **keyword-only, fail-closed**. **฿ facet kept** (`build_economic_steps` is deterministic, never raises). New `_disclose_rule_by_design` — a **third** state, because the degrade wording would claim degraded while working as designed; trace step `arm-pin-disclosure` reuses the CI-pinned `rule_check` kind ⇒ **no UI label, no `?v=` bump**. Non-vacuity 3 of 5 RED. **No AC ticked — still 8 of 13**; Step 8 now fully unblocked | `0c067de` (head_commit) / [#1060](https://github.com/CrayJThiemsert/vero-lite/pull/1060) / `services/engine/llm/arm_policy.py` |
| 2026-08-06 | **s208 — PLAN-0100 AC-7/8/9/10 CLOSED (#1058): 4 of 13 → 8 of 13.** The work shipped in s206; the table was never ticked (the s207 handoff said "10 of 13", the checkboxes read **4**). Independent refuting review returned **two of four NOT-CLOSEABLE**: AC-7 had two **unassertable** clauses (**amended on Cray's typed ruling**) plus a third genuinely unmet and now built — a prompt-log assertion under the cap, non-vacuity proven by a hardcoded `arm="llm"` mutation; **AC-9's ADR-0032 D5 wording review had never been run** (done, PASS). AC-10 fixed a purge glob (`prompts-*` vs `prompt-`) matching **0** files at **exit 0** | `c0f08b8` (head_commit) / [#1058](https://github.com/CrayJThiemsert/vero-lite/pull/1058) / `docs/plans/done/0100-exposure-published-demo-surface.md` |
| 2026-08-06 | **s208 — ADR-0035 D4/L5 AMENDED (#1057): PLAN-0100 Step 8's ADR blocker is CLEARED.** **Cray typed reading (a)** — vero-lite's `cloudflared` **is** this system's connector in its own compose project; the portal owns the ingress map *across* systems; each system owns its *own* route allowlist. (b) rejected: voids AC-6(a), re-opens SD-3. Two drafter SDs also typed: **SD-1** restate D4's acceptance to count each system's own connector; **SD-2** keep "no other system's connector may join this system's network". Same PR renumbered **81 line numbers / 45 citations** — no guard test covers ADR line cites | `a8e04c3` ([#1057](https://github.com/CrayJThiemsert/vero-lite/pull/1057)) / `docs/adr/0035-hosting-and-exposure-model.md` |

## In-Flight Discussions

- **OPEN QUESTION for Cray — does a skill's registry table *bind*? (raised by s210's closing notice, recorded here s209 cont.; Code's observation, NOT a ruling and NOT a defect.)** The notice asserted that the four-work-stream registry table in `.claude/skills/stream-status/SKILL.md` (#1062) is **canonical**, and that a carrier-artifact change must update it **in the same PR**. The registry as *reference* is unobjectionable; the **same-PR obligation** is the part that would have to live in `CLAUDE.md` or an ADR to bind — `CLAUDE.md` §1 places `.claude/skills/` at **Tier 2.6, derived, carrying no independent precedence (ADR-0017 D6)**, and §4 draws the bright line that *"a binding rule never moves into a skill (a skill that fails to trigger would silently drop it)"*. Cray's call: promote the obligation into a canonical, or keep the table advisory.
- **PLAN-0096 — COMPLETE 12/12 and ARCHIVED (s193); FOUR RESIDUAL RISKS OUTLIVE IT** (which is why this entry is a pointer and not a deletion): **RR-1** (per-baht approver→case attribution is INFERENCE, not data — silently wrong the day two approvers share a gate resolution), **RR-3** (concurrency-race coverage — both named gaps CLOSED s195 by #995), **ศูนย์ต้นทุน ships EMPTY** (partner granularity unanswered — also an open Active TODO below), and **`latest_per`** still collapsing two open cases on one truck (**Cray typed (ค) defer** — the older case reports as *ungoverned*, indistinguishable from a governance failure). Read the archived PLAN, not a restatement: `docs/plans/done/0096-fleet-flow-completion-phase1.md` (§Verification preamble + §Acceptance Criteria for RR-1 / RR-3 / ศูนย์ต้นทุน; §Step 8 for `latest_per`).
- **COMPLETE-and-ARCHIVED, no live remainder here — read the archived PLAN, never a restatement:** **PLAN-0095** (Docker image boot, s177 — its OQ-1 hosting model CLOSED by ADR-0035) · **PLAN-0094** (L1 loop-detect restructure, s183 — its OQ-4 is ANSWERED; see the PLAN-0102 row in Active TODOs) · **PLAN-0093** (LLM-arm degrade disclosure, s172 — **no follow-on owed**) · **PLAN-0091** (narrative→vertical scaffolder, s168 — two named follow-ons, **neither scheduled**, both greenfield/human-call) · **PLAN-0088** (cross-run read substrate + the four run-insight readers, s171 — **three AC-WORDING debts, none a code defect**) · **PLAN-0036 + PLAN-0037** (Fastenal procurement vertical Stage 1 + the Stage-2 facet retrofit, s76 — `Status: Done`; demo target = Fastenal Thailand, **pitch = asset-ontology-triggered governed sourcing**, NOT the commoditized "governed"/"cross-vertical" claims). Each record is in `docs/plans/done/`; the s168→s193 retrospectives these bullets used to carry are rotated to `docs/status-archive/`.
- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13; verdict **continue-with-adjustments**. Runs 1 (energy, s93) + 2 (supply-chain, s94) both COMPLETE, all S-checks PASS against pre-committed oracles, no R-PS trigger fired; C-1..C-3 CONFIRMED → **no open partner-sim debt**. ADR-011's audit stays gated on a REAL partner conversation (R3: SYNTHETIC provenance INFORMS but never TRIGGERS it). Full record: `docs/adr/0020-*.md` + the gitignored run packages under `docs/research/private/`.
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm — **not yet drafted**, and it needs a fresh ADR number. _[The old "≥ ADR-014" floor recorded here was **moot** — see the Active TODO below, corrected s141: ADRs now run past 0032 and `0014-WITHDRAWN.md` exists. Kept as one pointer rather than two divergent copies.]_
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **The autonomy fork — Stop-hook misfires: CLOSED s167.** Resolved by **option A′** (Cray, typed) and shipped the same session — the `dispatch` verdict is a **suggestion, not an order** (#870/#871). Final ledger: **14 misfires / 0 valid fires**. **The whole argument is settled history in `docs/plans/done/0092-stop-hook-dispatch-arm-demotion-to-suggestion.md` — do not restate it here.** Live remainder: only **option (e)** (flip the classifier backend from local Ollama `gpt-oss:20b` to Sonnet), **deferred**, its API-key/org fail-closed probe unrun.

## Active TODOs

- [x] **PLAN-0100 — the ADR-0035 exposure PLAN. COMPLETE 13/13 and ARCHIVED (s216).** The demo is LIVE, REDEPLOYABLE and DRIVEN. Step 11 ran end to end through the ratified Cloudflare Access gate under Cray's typed §8 go, and every pass/fail read is discharged. Closed in s216: **AC-6(c)** by re-scoring case 1 against the D-3 fix (its only two misses were the `.woff2` content-types, fixed and live-verified on a `cf-cache-status: MISS` — proven to reach a *visitor*, not merely the container); **AC-11** by measuring **`T_edge` = 125 s (HTTP 524)** after s215 could only bound it, Cray having ruled that a bound is not the number the clause asks for; **AC-12** by *verifying* rather than dispatching — its three "unrouted" ADR-0035 amendments had already landed on 2026-08-06 in `06e2b84` and only the tick was missing. **Read the archived PLAN, never a restatement:** `docs/plans/done/0100-exposure-published-demo-surface.md` (§"Step 11 closure verdict" for the closeout; §"Defects the live run found" for D-1..D-5; §Instrument failures for the twelve faults). **Five residual items OUTLIVE it, which is why this is a pointer and not a deletion:** **D-4**'s direction (teach the translator `group_by` vs. correct the ontology's advertised set — the two move the product in opposite directions, which is why Code did not pick) · a **cache-purge step or versioned font URLs** in the redeploy runbook — nothing in the pipeline purges the edge, and the `?v=cNN` convention does not reach fonts · **D-5**, a *transient* Safe Browsing phishing flag on the Access login callback (lifted within ~30 min, no security posture involved, cause UNDETERMINED — Google Search Console is the only source that reports why, if it recurs) · **ADR-0036** ratification (+ its 3 OQs; ⚠️ the ratifying edit must also remove `0036` from `tests/handoffs/test_pretooluse_governance_gate_deny.py`'s set-equality assertion) · **`published.env` pins no `OLLAMA_KEEP_ALIVE`**, so the published surface silently inherits the code default of 30m.
- [ ] **Assembly-cost axis — MEASURE it before an ADR argues it (Cray typed s197); nothing built, no PLAN drafted.** Build the tripwire that puts a number on assembly cost first, *then* draft the ADR on top of that number — the ordering is the ruling. **The series measured so far is banked HERE because it is banked NOWHERE ELSE in the repo — no test, no doc, no PLAN holds it:** churn per vertical went **1:1.8 → 1:6 → 1:1.1**, i.e. **spiky, not falling**, which is the shape any ADR on this axis has to argue against. Left unbanked it survives only in session memory and dies at the next context reset; a tripwire that recomputes it is what makes it evidence rather than a recollection.
- [ ] **Seam-scoped mutation-testing CI — a PLAN candidate, NOT built.** Surfaced s188 as the one CHECKABLE variant the scenario-test hook rejection does not cover; **rehomed here s191** when its parent `[x]` row was pruned, because STATUS was its only home. A CI job that requires the scenario suite to REDDEN under a seam mutation: ritual compliance cannot fake it, since an empty or stubbed scenario suite stays green under mutation — exactly what a file-existence hook would miss. Rationale: `CLAUDE.md` §8's scenario-test bullet.
- [ ] **PLAN-0096 partner round-2 — ANSWERED s189; five of seven closed, one non-blocking follow-up open.** A1 → Step 6 built (#965); A3 → `pm_due` built (#968); **A4 + A7 confirmed values already shipped** (flat ฿5,000 ceiling, `"30001"` inclusive floors); A5 **parked** — no real Wialon export exists yet. **A2 is answered and consumed by Step 8** (no longer a gate). **Open, NON-blocking: cost-center (ศูนย์ต้นทุน) granularity — per truck or per company?** Ship the column, fill the rule when it lands. A6 is answered but is a Step 9 *runbook* item. Detail: `docs/plans/done/0096-fleet-flow-completion-phase1.md`.
- [ ] **The AT-2 extraction — only the F-FACTORY half remains, owned by PLAN-0076 T1.** The criterion-vocabulary half SHIPPED as PLAN-0087 (COMPLETE 8/8, ARCHIVED — #840/#841); ADR-0025 D7's generator deferral was CANCELLED at N=4 (Cray-ratified, typed); SD-1 = (a) keeps the procedure-aware `ExecutorFactory` half with PLAN-0076 T1, guard `test_at2_extraction_obligation_is_owned` ARMED. Full detail: `docs/plans/done/0087-gate-seam-declared-criterion-vocabulary.md` + `docs/plans/0076-*.md` §A.
- [ ] **PLAN-0075 follow-ons — homed by PLAN-0076 (`Status: Tracking`, #752, s133).** T1 (ADR-0031 D3 gate-plugin seam, F-FACTORY) is PARTIALLY discharged — the criterion-vocabulary half shipped as PLAN-0087; the procedure-aware-`ExecutorFactory` half stays OPEN here. T2's F-PIN remainder CLOSED s143 (#784), but **F-PIN itself stays OPEN**, so PLAN-0076 does NOT archive and its AC-6 presence guard stays ARMED. Full detail: `docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md` §A.
- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2) — open ONLY for the O-2 residue.** Every other leg is DONE + archived (PLAN-0046/0048/0061/0062/0066–0068/0070/0071/0073 → `done/`). **The one OPEN residue:** procurement's `intake` migrated only **PARTIALLY** — the derived fields ALREADY moved to declared `transform` ✔ (PLAN-0078 PR-1 #762, AC-2 ticked), so what is left is **only the cardinality-changing `candidate_quotes` nest**, which is explicitly Out-of-Scope there. *[Corrected s175 by the #921 grounding sweep, `was an error`: this entry said production execution stays `_SeedQuery` "for derived fields" — it does not; the derived fields are migrated and the reshape is the sole residue.]* Full detail: `docs/plans/done/0062-per-vertical-seed-migration.md` §SD-C (the co-exist decision + its STOP-and-surface tripwire) + `done/0078-*.md` §L-3 and its Out-of-Scope, where the residue is walled in.
- [ ] **Bounded/incremental chain verification (PLAN-0063 SD-4 follow-up, s118).** `GET /audit/verify` walks the WHOLE chain O(n) on demand — accepted at pilot scale. Future work = a checkpointed head / verify-since-anchor design; anchor storage ≈ external anchoring — **do not build without re-reading the tripwire** in `docs/plans/done/0063-audit-chain-verification-surface.md` + the `services/api/routers/audit.py` module docstring (SD-4). _[Note: the docstring's "ADR-011 boundary" is an EARMARK — `docs/adr/` jumps 0010 → 0012.]_ *(#688/#690)*
- [ ] **Rock 4 — s84 deep research DELIVERED → O-sequence locked.** Cray locked **O-1 → O-3 → O-2 → O-4**. **O-1** (Box-4 ฿ pitch) **DONE** · **O-3 = ADR-0025 Accepted** · **O-4 = PARK** (agent-interop; `docs/adr/0032-*.md` D4 — option-only, un-park = a counterparty's *written* pull). **Remaining: O-2 only** (economic-impact facet + Q3 data-binding = Rock 3). Full detail: `docs/adr/0025-at2-managerial-layer.md` (O-sequence + Box-3 fit + the **evidence-asymmetry** finding rehomed s142). *(s84 Cray ask)*
- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten. **Full table (all six rows + their triggers + where each lands): `docs/plans/done/0005-oct-engine-runtime-layer.md` §8.1** — which itself instructs this STATUS entry to be a pointer. *(per Cray note 2026-05-21)*
- [ ] **PLAN-004 Phase C — OPTIONAL POLISH (forward-declared; "may never land"):** HTML/markdown handoff dashboard under `docs/` + references-graph (mermaid dispatch chains) + `render_transcript.py` unified session export (PLAN-0004 §"Phase C"). *(Phase A + B both COMPLETE — session 35; the prior TODO's validator **warning-swallow bug was FIXED #312**, s58. Minor never-formally-scoped sub-ideas — README/`_rename-map` walk-exclusion, Cat G `references_*` autofix, OQ-2 effective-vs-authored `status:` dashboard flag — fold in only if Phase C lands. Reconciled 2026-06-16 s65 audit.)*
- [ ] **Custom Postgres image with extensions (pgvector / AGE / pg_trgm) — needs a fresh ADR number + a PLAN; neither drafted.** *[Corrected s141: **PLAN-002 does not exist** ("NOT yet drafted", `docs/plans/done/0005-oct-engine-runtime-layer.md`), and the old "≥ ADR-014" floor is **moot** — ADRs now run to 0032 and `0014-WITHDRAWN.md` exists.]* Context: **`docs/adr/0013-autonomy-axis-relocation.md`** (the floor-bump note) + **`docs/plans/done/0005-*.md`** (trigger: semantic + graph features).
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] **CLAUDE.md follow-up extraction pass (s181 option b): new Cowork dispatch; target < 20 KB (~18 KB / ~225–235 line floor).** Candidates (Cowork fresh-eyes, s181 completion §6): §11 ¶3 restates the §6 E2 rule → one-line pointer; §10 skills-row annotation duplicates §4's Tier-2.6 row (in-file ADR-0017 D6 drift); §10 docs/logs row's PLAN-004 parenthetical; §9 halves; §3 folds into §1. Materials: `.claude/handoffs/session-181/` (gitignored). **PARKED s183 by Cray — the dispatch stays UNSENT until two things are settled, and s183 grounded both.** (1) **The unit of `< 20 KB` is load-bearing and unpinned:** `CLAUDE.md` measures **21,524 B / 261 lines**, so the target needs **1,044 B** cut against 20 KiB but **1,524 B** against decimal 20,000 — Cray was asked and declined to rule for now. (2) **The five named candidates cannot reach either target:** measured at **~930–1,000 B** combined, and the row's own "~225–235 line floor" needs **26–36 lines** removed where the five move **~7** (candidates 1–3 are in-line trims that shorten bytes without deleting lines). The genuinely large blocks — `CLAUDE.md:112` (~1,100 B), `:153` (~700 B), `:73` (~800 B) — are **not on the list**. Sending this dispatch as written would repeat the s181 failure of a target that is arithmetically unreachable in scope. ~~Batch the two standing CLAUDE.md defects into whatever dispatch eventually goes out~~ — **DISCHARGED s188**: both rows below are closed, batched into the s188 three-edit Cowork round-trip. _[s188 — **the arithmetic moved AGAINST the target and the row must not be read at its old numbers.** `CLAUDE.md` is now **22,424 B** (+900 B: the §8 scenario-test rule +569, the §6 gate-claim correction +261, the §7 link resolution +70), so the cut needed is **1,944 B** against 20 KiB or **2,424 B** against decimal 20,000 — roughly **double** what this row was written against, while the five named candidates still measure only ~930–1,000 B. Note also that `:112`, one of the three "genuinely large blocks" this row says are **not** on the candidate list, is now ~260 B larger. The growth is Cray-ratified binding-rule substance, not padding — which is the point: **the target and the constitution are pulling in opposite directions, and that is the decision this row is actually parked on**, not the unit question alone.]_
- [ ] **PLAN-0102 — retire L1 loop-detect. OQ-4 ANSWERED s205 (NO; Cray typed RETIRE, 2026-08-04); the PLAN is DRAFTED and UNARCHIVED, so this row tracks execution only.** The measurement, the s180 "0 denies" correction (**≥ 56**, a floor), and the ADR-013-never-backed-L1 finding are all recorded elsewhere — read them, not a restatement: `docs/plans/0102-retire-l1-loop-detect.md` §Context + [`docs/lessons/0035-negative-measurement-needs-a-positive-control.md`](docs/lessons/0035-negative-measurement-needs-a-positive-control.md).
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)

## Next Steps

1. **PLAN-0005 §8.1 revisit register** — remaining deferred-foundational simplifications at their batch boundaries (audit framework, mapping layer, ORM emitter, base-Postgres → the custom-Postgres image, registry discovery). _[Corrected s153: dropped the stale "→ ADR-011+" and "→ PLAN-002 (≥ADR-014)" pointers — **ADR-011 does not exist** (earmark only, per the Active TODO above) and **PLAN-002 was never drafted** with its ADR floor moot; each item's corrected status lives in Active TODOs.]_
2. **Partner-trial readiness gaps** — `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` awaits a dedicated Cray discussion.
3. **Deferred (backlog)** — PLAN-004 Phase C only (optional polish: handoff dashboard / references-graph / unified export — Phase B complete s35, warning-swallow fixed #312); the custom Postgres image (needs a fresh ADR number + a PLAN — neither drafted; see the Active TODO for the corrected framing).
4. **Ongoing** — Continue exercising the file-based handoff mechanism (Chat ↔ Code ↔ Cowork) across batches.

## Update Workflow

**Rehomed 2026-07-24 (session-171).** The update mechanism and the Q4
`head_commit` semantics are *procedure*, not *state*, so they now live in
[`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md)
section "STATUS.md Update Workflow" (ADR-0017 D5 knowledge placement). Moved
verbatim; nothing was rewritten.
