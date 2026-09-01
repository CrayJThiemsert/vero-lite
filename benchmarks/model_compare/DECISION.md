# Model decision rule — phase 1.5 of the FDE readiness program

> **Written 2026-08-28, BEFORE any comparison run.** Everything below is a
> pre-committed read. If a run produces a result this rule does not cover, the
> honest outcome is INSUFFICIENT-EVIDENCE and a second, differently-designed run
> — never a criterion edited after seeing the numbers.
>
> **Incumbent:** `gpt-oss:20b` — pinned by PLAN-0006 CHECKPOINT-0 after a sweep of
> four model families. It is the default in `services/api/config.py`.
> **Challenger:** `qwen3.8:27b-mtp-q8_0` — the tag as Cray typed it, and
> **asserted-not-verified**: confirm it against the box's own tag list before the
> first run (step 0 below). A wrong-but-plausible model name has bitten this repo
> before, and the log looked fine.

---

## 1. What is being decided

Which local model the **phase-2 dry-run** binds. Nothing else. This is not a
re-pin of the product default: changing `recommender_model` puts the model name
into `audit_metadata` on every record, which reddens the golden-trace oracle and
carries its own two-step discipline (§6). A dry-run binding is reversible; the
default is not free.

## 2. The bars, fixed now

Read them in this order. A bar failed at a lower number stops the comparison —
a later number cannot buy it back.

| # | Bar | Threshold | Why it is a bar and not a preference |
|---|---|---|---|
| B1 | **Tag verified on the box** | exact match in `/api/tags` | Everything below measures a model we cannot name otherwise. |
| B2 | **Structured-output integrity** | judgment errors ≤ incumbent's, in every repeat | A model that drops the schema is unusable here regardless of how well it writes. Qwen3.x is the family Ollama #15260 affects. |
| B3 | **No forbidden handler, ever** | `forbidden_items` empty across all repeats | Worst-case, not averaged. A model that proposes a dangerous handler one run in three is not one-third as dangerous. |
| B4 | **Majority accuracy** | ≥ incumbent's, **and** the gap must exceed both models' flip rates | The repo has already measured that variance dominates single runs. A gap smaller than the noise is not a gap. |
| B5 | **Stability** | flip rate ≤ 0.15 | A model whose own verdict moves between identical runs cannot be demonstrated to a customer. |
| B6 | **Latency** | p95 per LLM call within 2x incumbent's | 27B at q8 is a much larger load; a demo that stalls is a demo that fails. |

**Decision:**

* Challenger clears **every** bar → bind the challenger for the dry-run, and
  record which bar it won on.
* Challenger fails **any** bar → keep `gpt-oss:20b`. This is the default outcome
  and needs no further argument.
* Challenger ties within noise on B4 but wins clearly on B6 (or vice versa) →
  keep the incumbent. A tie does not justify moving a pin that four model
  families were already swept to set.
* Either model shows flip rate > 0.15 → **INSUFFICIENT-EVIDENCE**. Report it as
  such; do not pick a winner from noisy data.

## 3. Cost, before asking for the go

Energy carries **66 items**; each graded item costs two LLM calls. Three repeats
per model over the full set is ~800 calls — too much for a decision this narrow.

🔴 **The runner has no `--vertical` flag** (verified against its `_parse_args`):
it loads **every** dataset in `--dataset-dir`, and `--limit` caps items *per
vertical*. So a bare `--limit 20` would run 20 energy + 20 aquaculture + 20
supply_chain. Point `--dataset-dir` at a directory holding only `energy.yaml`.

**20 energy items × 3 repeats × 2 models ≈ 240 calls**, sequential. Record the
limit in the result file — a number from a 20-item subset must never be quoted as
a 66-item number.

## 4. The run sequence (host-state — needs a typed go from Cray, per CLAUDE.md §8)

Run **sequentially, one model fully warmed and finished before the other**. MS-S1
has ~63.65 GiB usable and a 27B q8 model is a large resident; interleaving pays a
cold load per switch and makes the latency numbers incomparable.

```bash
# 0. Verify the tag EXISTS. warm.sh takes the model as a POSITIONAL argument and is
#    fail-closed by design: on an unknown tag it prints the full tag list and ABORTS
#    rather than warming something else. That refusal IS the verification step.
bash .claude/skills/ms-s1-ollama/warm.sh qwen3.8:27b-mtp-q8_0

# 0b. Energy-only dataset dir (no --vertical flag exists).
mkdir -p /tmp/mc-dataset && cp benchmarks/procedure_baseline/dataset/energy.yaml /tmp/mc-dataset/

# 1. Incumbent — warm once, then three repeats.
uv run python -m benchmarks.procedure_baseline.run_benchmark \
  --dataset-dir /tmp/mc-dataset --limit 20 --model gpt-oss:20b --warm \
  --dump-json .claude/benchmark-results/s259-mc-gptoss-1.jsonl | tee /tmp/mc-gptoss-1.log
# repeat for -2 and -3 WITHOUT --warm

# 2. Challenger — warm once, then three repeats.
uv run python -m benchmarks.procedure_baseline.run_benchmark \
  --dataset-dir /tmp/mc-dataset --limit 20 --model qwen3.8:27b-mtp-q8_0 --warm \
  --dump-json .claude/benchmark-results/s259-mc-qwen-1.jsonl | tee /tmp/mc-qwen-1.log
# repeat for -2 and -3 WITHOUT --warm

# 3. Join — offline, no model contact.
uv run python -m benchmarks.model_compare.compare \
  --run gpt-oss:20b=.claude/benchmark-results/s259-mc-gptoss-1.jsonl \
  --run gpt-oss:20b=.claude/benchmark-results/s259-mc-gptoss-2.jsonl \
  --run gpt-oss:20b=.claude/benchmark-results/s259-mc-gptoss-3.jsonl \
  --run qwen3.8:27b-mtp-q8_0=.claude/benchmark-results/s259-mc-qwen-1.jsonl \
  --run qwen3.8:27b-mtp-q8_0=.claude/benchmark-results/s259-mc-qwen-2.jsonl \
  --run qwen3.8:27b-mtp-q8_0=.claude/benchmark-results/s259-mc-qwen-3.jsonl \
  --json .claude/benchmark-results/s259-mc-report.json
```

⚠️ **Latency is printed to the console, not written into the dump** — hence the
`tee`. A comparison whose B6 evidence was never captured is missing a bar, not
passing it.

⚠️ `.claude/benchmark-results/` is untracked **and unignored**: the raw evidence
lives only in the working tree unless it is deliberately copied somewhere durable.
That has already cost this repo one set of dumps.

## 5. The one dimension this instrument cannot measure

The procedure-baseline dataset is English. **Thai brief quality — the actual job
in case 1 — is not measured by any number above.** It is a separate, smaller step
and must be reported separately, never folded into the bars:

1. Pull the `judgment` blobs for the same 20 items out of both models' repeat-1
   dumps.
2. Strip the model names, shuffle, and present pairs.
3. Score each on a 3-point rubric **written before reading any output**:
   *(a)* names the right entity and number, *(b)* an operator could act on it
   without asking a follow-up question, *(c)* reads as Thai a manager would send
   on, not as translated English.
4. Report as a preference count with the n, e.g. "13 of 20 preferred B" — never
   as a percentage accuracy.

If the bars pick one model and the blind read prefers the other, that is a real
conflict and it goes to Cray. It is **not** resolved by re-weighting the bars.

### 5a. The rubric at the GATE-ADVISORY position — ruled (Cray, typed, 2026-09-01, session 267)

§5's three criteria are unchanged and stay as written. This adds the rubric for a
**different surface**: the `llm_assist` gate draft (`gate_advisory.py`), which
sessions 267+ prioritised alongside the recommender path. §5 was written for the
procedure-baseline corpus and could not have anticipated this position, because
this position supplies the model far less than that corpus does.

**What the approver already sees, deterministically, without the model.**
`GateAdvisoryBuilder._entry` puts `reasons`, `tier`, `approver_role`,
`resolved_approver_id` and `sod_required` in front of the human on every run. The
amount, the band, the tier, the required role, the specific approver and the SoD
requirement are all **already on the screen**.

**What the shipped prompt already asks the model for**, verbatim: *"You brief a
human approver in 2 short sentences. Explain why this requisition needs THEIR
level of authority, from the facts given. No numbers you were not given, no
confidence scores, no recommendation to approve or reject."*

So two things a reader might expect to rule on are **already settled by the
code**: brevity is specified (2 sentences), and restating figures is forbidden.

🔴 **The ruling: score the CAUSAL LINK, not completeness.** The narrative earns
its place only by connecting the facts into *why this lands on THIS approver's
desk* — amount → band → your authority. A brief that repeats facts the sidecar
already shows scores **low even when it is complete**; a short brief that makes
the link scores well. "Is there a link?" is the question, not "is it thorough?".

⚠️ **Consequence for the benchmark's fourth axis, stated so it is not assumed to
transfer.** `names_approver` — the one axis that separates the two models on the
procedure benchmark (§13, and §14 across reasoning modes) — asks whether the
prose names a human role. At **this** position the role is sourced
deterministically, so naming it adds nothing a reader did not already have.
**That axis is not a proxy for gate-draft quality**, and a panel scoring this
surface must not reuse it. Whether it transfers to the recommender path is a
separate question: that path has no equivalent deterministic sidecar, and it has
not been checked here.

**The pre-commitment holds.** No output from this position exists to tune a
rubric to: all four call sites construct `GateAdvisoryBuilder()` with no
arguments, i.e. `client_factory=None`, the deterministic arm. The live arm is a
seam that has never been wired. This rubric is therefore fixed **before** any
narrative has ever been generated, which is the property §5 exists to protect.

**Recorded as intent, not built (Cray, same ruling):** this belongs long-term in
**system preferences**, adjustable by an administrator per deployment, rather
than as one rubric hard-coded for every operator. The ruling above is what the
panel scores against *now* so the work can proceed; it is not a claim that one
answer suits every customer.

---

🔴 **Post-ruling caveat — the rubric's reward set may be near-empty. Found by
Code at the session-267 reconcile, re-verified session-268; this is NOT Cray
reversing the ruling.**

The paragraph above records what the approver already sees as a list of *field
names* — `reasons`, `tier`, `approver_role`, `resolved_approver_id`,
`sod_required`. It never records what `reasons[0]` **says**. Read at
`services/engine/procedures/gate_advisory.py:69` (`_reasons`), that first element
is appended **unconditionally**, on every run, and reads:

> *"Spend {amount} {currency} lands in tier '{tier}' (band {band}), **so**
> approver role '{role}' must sign"*

That is the causal link — amount → band → *your* authority — already rendered
verbatim before any model is called. A rubric that asks *"is there a link?"*
therefore rewards **paraphrasing a sentence already on the screen**, and the set
of narratives it can score above the deterministic baseline may be empty.

**Do not score a panel against §5a until this is resolved.** The rule the ruling
was protecting still holds — it is fixed before any narrative exists — but a
pre-committed rubric with an empty reward set is not a usable one.

**The resolution route, ruled by Cray in the same session — the GATE EXISTENCE
TEST.** It is designed to *dissolve* the question rather than re-rule it, and it
runs entirely offline:

1. Read the deterministic sidecar **alone**, item by item.
2. For each, write down the ONE question still open in the approver's head, plus
   what an answer must name — **fixed before seeing any narrative**, which is the
   same pre-commitment §5 exists to protect.
3. Then check whether any 2-sentence narrative under the shipped prompt can
   answer it.

**If none can → do not wire the live arm at this position at all.** The
measurement problem disappears instead of needing a better rubric, and this
caveat closes with it. Nothing is lost on that outcome: the live arm has never
been wired, so no shipped behaviour changes either way. Sequencing and the rest
of the ruled work order are state, and live in `docs/STATUS.md` Active TODOs.

⚠️ **A position fact, so it is not assumed even (measured session-268).** This
ruling covers ONE position. Of the two whose next consumer is **code**, only one
is measured at all: the NL-query position runs its real consumer
(`answer_question`) under `benchmarks/nl_query_feasibility/`, while **intake
extraction has no benchmark of any kind** — `benchmarks/` holds five suites
(`model_compare`, `nl_query_feasibility`, `procedure_baseline`,
`procedure_comparison`, `stop_classifier`) and `grep -rn -i intake benchmarks/`
over `*.py`, `*.md` and `*.yaml` returns **zero hits**, against a shipped engine
seam at `services/engine/llm/intake.py`. This is a **negative claim with a
date** — true of the tree at the session-268 reconcile, falsified the moment a
suite lands. Re-measure it rather than citing it.

## 6. If the challenger wins — what it costs to actually switch

Binding it for the dry-run is a per-run `--model` / `RECOMMENDER_MODEL` override.
Changing the product default is a different act:

* the model name travels into `audit_metadata` on every record, so the
  golden-trace oracle goes red;
* the fix is `python -m tools.golden_trace refresh` **and reading the diff as part
  of the change** — refreshing without reading it accepts a regression as the new
  expectation, which is the one way that oracle can be defeated;
* `client.py`'s CHECKPOINT-0 caller contract (never `think=False` with
  `response_format`) was written against a Qwen3.x failure. Re-verify it holds
  for this specific MTP tag rather than assuming the existing guard covers it.

## 7. Provenance of this instrument

`compare.py` is offline and reads files only. Its 17 tests drive the **shipped**
`run_benchmark._item_record` into the joiner, so the dump contract is never
hand-copied. Probe battery `run-53f8778f`: **PASS**, 12/12 probes, **8 witnessed
RED + 4 declared-GREEN controls**, coverage COMPLETE over 30 claims with 0 gaps,
tree restored. The two absence claims (`forbidden_items == []`,
`disagreements(...) == []`) each carry a positive control that reddens them under
an over-firing mutation — an empty list satisfies an absence assert by
construction, so without those controls they would prove nothing.

*(One probe was repaired mid-battery: blinding `if not path.is_file():` made
`read_text` raise `FileNotFoundError`, a non-assertion exception the driver
correctly refused to credit. The mutation was changed to return an empty list —
the actual false-pass shape — which fails as `DID NOT RAISE`. The instrument was
repaired; the criterion was not touched.)*
