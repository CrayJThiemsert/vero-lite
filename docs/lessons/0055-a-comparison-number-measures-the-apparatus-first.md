# Lesson 0055: A model-comparison number measures the apparatus first — rule it out in all three directions

**Status:** Advisory (names a diagnostic order and records the six measurements
behind it; no guard enforces it — the enforcement is the pre-committed pass/fail
read that `CLAUDE.md` §8 already requires)
**Source:** Sessions 220, 259, 261, 262, 263, 264, 266 — every model-comparison
run this repo has made

## The claim

A number produced by comparing two models is a measurement of **the whole
apparatus**: the client's timeouts and token caps, the flags that did or did not
take effect, the build (quantisation) each candidate was loaded as, the directive
each was handed, and the key each was scored against. The model is the last term
in that product, not the first.

**Before attributing a comparison number to a model, rule out the apparatus.**
There is a distinct way to do that for a **low** score, for a **high** score, and
for a **tie** — and this repo has needed all three.

The order is not fastidiousness. It is the measured base rate:

> **Six times, across seven sessions, a number that read as a model difference
> was a property of our own instrument.** Not once did the apparatus check come
> back empty on the first pass of a new configuration.

---

## Direction 1 — a LOW score. Suspect the budget, the flag, the build, the input.

Six measured instances, in the order the checks should run:

| # | The number as it first read | What it actually was |
|---|---|---|
| 1 | **s259 φ1.5**: the challenger failed the structured-output bar with **10 of 20** judgment errors, and the comparison stopped there | **A per-call timeout tuned to the incumbent.** Under a 300 s per-judgment budget the same model produced **zero** transport failures and **zero** schema failures. The cut-task counts matched the error counts exactly — 3/3, 2/2, 0/0 |
| 2 | **s261**: two `gpt-oss` cells differing only in a thinking flag showed a large p95 gap the matrix could not explain | **The flag never took effect.** `gpt-oss:20b` discards a boolean `think` (it takes `"low"`/`"medium"`/`"high"`). A 1-item live run with the flag set came back carrying a **3,105-character reasoning trace**. The two cells were **one request**, and the "gap" was run-to-run variance between two samples of one configuration |
| 3 | **s261**: β low across the whole matrix | **`num_predict` was never set**, so a deadline discarded every token produced. Bounded afterwards |
| 4 | **s263 §10**: `qwen` trailed `gpt-oss` by five items on the handler probe | **~60% of the gap was the quantisation, not the model.** An 8-bit build of the same weights corrected **exactly the five items** the 4-bit build got wrong. α-canonical and consistency each moved **+3 items**; β did not move at all |
| 5 | **s263 §11**: `qwen` withheld routing decisions and looked like it could not follow the rule | **The defect was in our own procedure goal.** It told the model to check a gate that the engine evaluates deterministically downstream with no LLM, and withheld the gate's threshold. The invitation was live on **11 of 14** graded items; the rule it points at fires on **one**. Rewriting that single clause moved the model **85.7% → 100%** on β and α, and **12/14 → 14/14** on consistency |
| 6 | **s220** (archived): the headline run looked ready to score | A pre-run smoke against the live model surfaced that **the harness, not the model, was mis-measuring**. Four measurement-correctness fixes were ratified **before** the scored run, none of them moving the acceptance bar |

**The order matters** because each check is cheaper than the one after it and
invalidates everything below it:

1. **Did every candidate get the same budget?** Timeout, token cap, retry
   allowance. A budget tuned to the incumbent is the classic shape — it is not
   visible as a bias, it reads as a fair setting.
2. **Did the flag you set actually take effect?** Not "was it sent" — was it
   *honoured*. This needs an artifact, not an assumption: instance 2 was
   invisible until the run captured the reasoning trace. Nothing in the log said
   the flag was ignored.
3. **Is the difference a build difference?** Two quantisations of one set of
   weights are two different deployable things. A claim about "qwen" that does
   not name the quantisation is unfalsifiable (s263's own ruling).
4. **Is the input identical and correct for everyone?** The directive, the
   prompt, the key. Instance 5 is the sharpest: the benchmark was working
   perfectly and grading a model against a directive that contradicted itself.
5. **Only now: the model.**

---

## Direction 2 — a HIGH score. Suspect non-engagement.

Nobody audits a 100%. This is the direction with no natural tripwire, and it
produced the single most useful finding in the matrix.

`gpt-oss:20b` scored **100% β / 100% α (14/0/0/0) / 14-of-14 consistency** on
`fleet` under the **defective** goal of instance 5 above — the same directive
that had cost the other model two items. Then the goal was repaired, and its
scores came back **identical, every one of them**.

That invariance is the signal. The mechanism count says why:

| items whose reasoning mentions the sourcing gate | old goal | fixed goal |
|---|---|---|
| `qwen` | **17 of 17** | 14 of 17 (**15** now naming it as downstream) |
| `gpt-oss` | **1 of 17** | 0 of 17 |

**It never engaged with the clause at all.** A directive a model does not read
cannot mislead it, and repairing that directive cannot help it. Its 100% was
compliance-by-omission, not comprehension — and three scored axes were blind to
the difference.

The corroboration came from a fourth axis added later: under the fixed goal,
`gpt-oss` names **no** human approval role on **any** of its fourteen items,
though the goal supplies all three phrases verbatim, at a mean rationale length
of **116 characters** against the other model's **289**.

### The test, stated so it is reusable

> **A score that does not move when you fix a defect in the subject's input is
> evidence the input was not read.**

⚠️ **Not proof on its own.** An invariant score fits two stories — *"already
handled it correctly"* and *"never looked at it"* — and they are opposite in
what they say about the model. **A mechanism count separates them**, and it must
be counted over the same runs, not inferred: 1-of-17 against 17-of-17 is the
evidence; the identical scores are only the reason to go looking.

---

## Direction 3 — a TIE, or an identical failure. The subject is provably shared.

When two independent candidates produce the **same wrong output**, the defect is
located in whatever they share, and this is the strongest attribution evidence
available — it needs no repeats and no variance estimate.

Measured on the NL-query gold set, case `fl-10` (*which vendor has no accounting
code?*): both models emitted the **byte-identical** wrong filter — an equality
comparison of the property against an empty string — which matched zero rows.

**That is not a model difference of any size.** The query language has no way to
express *"this property is absent"*, so an absence question is forced through an
equality filter and both models are pushed into the same wall. Nothing about
either model's judgment is measurable on that case.

The sibling shape, same gold set, case `fl-09`: the weaker model moved from
*"could not translate this at all"* to emitting a valid query comparing one
property to another — which the filter language also cannot express. A **better
failure**, and still a language limit rather than a model limit.

**Corollary:** an identical failure is *worth authoring a case for*. Two of the
three ceiling failures on that vertical are now known to be language limits with
named fixes, which is a far more actionable result than a percentage.

---

## What this does NOT say

- **Not "the model is never the cause."** Two model-level results in this repo
  survived every apparatus check and stand: the quantisation effect of instance
  4 is a real, measured difference between two deployable builds; and the
  rationale axis separates the two candidates in **every cell with no overlap**
  (4–8/14 against 0–1/14) under one harness, one goal-derived vocabulary, and on
  both sides of the goal fix. Ruling out the apparatus is what makes those two
  claims worth stating.
- **Not "prove the apparatus before measuring anything."** That halts all work.
  The rule governs **attribution** — what you are allowed to say the number is
  *about* — not whether the run is worth making. Instance 5 was found *by*
  running the matrix.
- **Not a claim that any of the six was careless.** Each was an honest reading of
  what could then be seen; instances 2 and 3 were only checkable because a later
  run started capturing the artifact that revealed them. They are recorded as
  **superseded by new info**, not as errors (`CLAUDE.md` §6).
- **Not limited to LLMs.** Direction 3 in particular is a general debugging
  result: two independent implementations returning the identical wrong answer
  localise the defect to their shared dependency.

## Where this fires

- Any model, prompt, quantisation, or reasoning-mode comparison — before the
  verdict is written, not after it is questioned.
- Any candidate that fails a bar **badly**. A large gap is the least likely thing
  to be a genuine model difference and the most likely to be a configuration one.
- Any candidate that passes a bar **perfectly**, especially on an input known to
  be imperfect. Direction 2 exists because that case has no natural reviewer.
- Choosing what to run next. Four of the six instances were found **offline**,
  from dumps already on disk — the apparatus checks are mostly free, and running
  a fresh live cell before making them buys a number nobody can attribute.

## References

- `benchmarks/model_compare/RESULTS.md` — instance 1 as first written (the
  verdict it produced was later superseded, and the file says so).
- `benchmarks/model_compare/RESULTS-1.6.md` — §2 (instance 1 resolved), §4's
  superseded note (instance 2), §10 (instance 4), §11 (instance 5), §12
  (direction 2, with the mechanism counts), §13 (the surviving model-level
  separation).
- `benchmarks/nl_query_feasibility/RESULTS.md` — the s265/s266 fleet addenda
  (direction 3, `fl-09` and `fl-10`).
- `docs/status-archive/2026-h1c-current-focus.md` — instance 6, the earliest and
  the one that survives only in an archive.
- Lesson #0042 (a remembered baseline is not evidence) — the same discipline
  applied to a number carried in memory rather than to one just measured.
- Lesson #0048 (repeat sampling establishes a rate, not a cause) — why repeats
  do not substitute for any check above.
- Lesson #0051 (a saturated benchmark may be missing an axis) — the companion
  for when the apparatus is sound and the number still says nothing.

*AI-assisted (Claude Code, session 267); no `Co-Authored-By` per CLAUDE.md §7.*
