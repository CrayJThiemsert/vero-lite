# 2026-08-22 (session 246) — PLAN-0112 Step 7: fleet redeploy + the live visitor walk

**Host-state gate:** Cray typed an advance go for Step 7 this session, and then a
second typed go for Phase D specifically — asked **after** §2's reads showed the host
was a week stale and the demo `CONSUMED`, because the advance go was given before
either of us knew that. `DEPLOY.md` §0 requires the go **per occasion** and **per
phase**; both were satisfied in that order, and this paragraph is the record.

**Result:** the published fleet system runs `ee41b55`. The accepted-quote ingress row
is live, a visitor's acceptance fires a governed run end to end, and the demo reads
`PRISTINE` with that visitor run parked alongside it.

---

## §2 pre-flight (read-only) — and the two findings that reshaped the deploy

| read | result |
|---|---|
| `hostname` | `CRAY-MS-S1-MAX`, key auth proven with `-o BatchMode=yes` |
| `docker ps` | fleet app `b23992b244c8`, image **`sha256:63c5ec37…`**, Up 3 days (healthy) — the do-no-harm baseline |
| `docker compose ls` | `oct-fleet-maintenance` `running(3)` **present**; **no `vero-published`** project (the stop condition) |
| host checkout | `205ba4b` — **2026-08-15, a week behind `main`** |
| demo state | 🔴 **`DEMO-STATE: CONSUMED`** |

**Finding 1 — the host had never received Step 5.** Diffing only the two files the
host actually reads (`docker-compose.yml`, `cloudflared/`) showed
`cloudflared/config.yml` changed: the `^/api/cases/[^/]+/accepted-quote$` row was NOT
on the live system. Step 5's whole promise was unreachable in production. That made a
host `git pull` **and** `--force-recreate cloudflared` both necessary rather than
optional.

**Finding 2 — the demo was spent.** `CONSUMED` routes through `DEMO-RESET.md`, whose
ordering constraint (**reset first, boot second**) changes the sequence. The §2a
bootstrap exception did **not** apply: `demo_run_reset.py` is unchanged in this ship,
proven by the tool running and printing its token on the OLD container.

## §3 the sequence, with the pass read fixed before each command

| # | step | measured |
|---|---|---|
| 1 | host `git pull --ff-only` | `205ba4b..ee41b55`, checkout verified clean **before** the pull; host HEAD then `== ` local HEAD |
| 2 | build on the dev box | `Built`. Never on the host — its credential helper needs an interactive desktop session |
| 3 | §2a content check | **6/6 file hashes identical, line for line**, image vs working tree (`runs.py`, `config.py`, `cases.py`, `view-case.js`, `demo_run_reset.py`, `procedures.yaml`) |
| 4 | tag `:prev` | resolved to **`sha256:63c5ec37…`** — exactly the §2 baseline id. The rollback point |
| 5 | `docker save │ ssh … docker load` | `Loaded image`, pipeline status read under `set -o pipefail` |
| 6 | id equality across machines | **`sha256:0fc679cf…` on both** — the guarantee |
| 7 | `config --quiet` | **zero bytes** — both required host secrets interpolate |
| 8 | reset `--execute` | deleted **2** `pipeline_runs`, **2** `repair_case`, **6** `repair_case_run_link`, **12** `step_results` |
| 9 | `up -d` | **only `app` Recreated**; postgres and cloudflared stayed `Running` |
| 10 | `up -d --force-recreate cloudflared` | only cloudflared recreated |
| 11 | demo state | 🔴 **`DEMO-STATE: PRISTINE`** |

**§4 against the baseline, not against memory:** app on `sha256:0fc679cf…` (new),
cloudflared recreated on its unchanged image, **postgres still `Up 3 days`** — untouched.

🔴 **The reset's own numbers corroborated a lab finding.** Six link rows were deleted
for two demo runs. A demo run cannot produce three link rows each by itself; the excess
is rows that **visitor-fired runs** wrote against demo case ids, which the reset reaches
through its `case_id` branch. That is the PLAN-0112 AC-7(i) finding — measured
independently in `tests/api/test_fleet_demo_reset_coexistence_scenario.py` earlier the
same session — showing up in production data.

## The live walk (evidence, never the gate)

Signed in through Cloudflare Access as personas. Case `case-9a52c518ffaf` (truck-01),
three quotes: 58,000 / 62,000 / 59,500.

- **non-cheapest accept → 422, and the reason box is scoped to that quote**, rendered
  under that row rather than as a page-level banner. Server text:
  `quote 'quote-3761caae4934' at 62000.00 is not the lowest on file (58000.00) — a
  reason is required when the cheapest quote is not accepted`
- **reason submitted → the run fired**: `governed_repair_approval@cbc5677f9fdef75a`,
  `trigger: event`, `waiting_human`, 15:16 UTC
- **Tab H moved as claimed**: runs **2 → 3**, badge **`1 WAITING ON YOU` → `2`**
- **the run is about the visitor's own case** — the gate reasons on
  *"Spend 62000.0 THB"*, an amount that exists nowhere in the seed data
- 🔴 **"3 candidates reached this gate"** — `intake` read 7 events → 3 trucks → 3
  breaches. The fleet-wide scan, live. This is the second production confirmation of
  the AC-7(i) finding: one gate resolution writes one link row **per decided case**,
  not one per run
- **SoD held**: *"the requester cannot approve their own requisition"*; the DOA ladder
  resolved 62,000 THB to tier `เจ้าของกิจการ` → `appr-owner`, so the approval was made
  as เฮีย, not as ต้อม
- **approve resolved** → audit line *"gate resolved by principal 'appr-owner' — the
  approving human recorded for the principal-SoD run-check (ADR-0026 D3, OQ-2)"*, badge
  `✓ approved by appr-owner`, and the run **parked again at `fulfill`** — the terminal
  step is itself gated, exactly the state AC-7(i)'s test asserts
- **`quote_gate`**: 1 compliance rule over 3 candidates, 0 blocked, non-waivable
- **the ฿ facet emits**: `Economic impact (overpay_avoided)` lines in the trace
- 🔴 **coexistence, the Step 7 check**: with the visitor run parked at `fulfill`, the
  demo still reads **`DEMO-STATE: PRISTINE`** — a visitor's governed run does not
  consume the beat the next visitor needs

## UX defects confirmed in production (the s245 chip findings, unfixed)

Recorded because they were measured on the live system, not inferred:

1. **a case row has no interactive affordance** — it does not appear in the
   accessibility tree at all and had to be clicked by coordinate (chip 1)
2. **the accept button is visibly smaller than the routine add-quote button** (chip 2)
3. **the result message renders far from the button pressed**, and the panel scroll
   jumps after a submit — enough to make a follow-up click land on the wrong element
   (chip 3)
4. **the 422 is English inside an otherwise Thai UI** (chip 4)

The success toast names *"แท็บ Monitor"*, and Tab H **is** labelled `Monitor` — so that
message is correct as it stands. Recorded because the s245 close-out described a toast
naming a tab that does not exist; either it refers to a different string or the
description needs narrowing. **Not re-verified further here.**

## Left as it stands

The visitor run is **parked at `fulfill`** — deliberately. It is the exact state the
coexistence test asserts, and SD-7(a)+(c) rules that visitor runs are retained and
cancelled manually by an operator, never swept. Nothing needs doing to it.

**Rollback, if ever needed:** `oct-fleet-maintenance-app:prev` on the host is
`sha256:63c5ec37…`.
