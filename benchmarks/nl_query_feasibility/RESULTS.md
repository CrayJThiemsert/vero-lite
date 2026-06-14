# NL-query feasibility spike — RESULTS (2026-06-14)

**Run provenance.** Cray-directed (session 58, the T2-vs-T3 roadmap-fork
evidence step). `gpt-oss:20b` @ MS-S1 (`192.168.1.133:11434`), 12 questions
through the **shipped engine-A path** (`services/engine/nl_query.py`:
translate → execute → phrase) over the deterministic energy synthetic data
(`verticals/energy/data_adapter/synthetic.py`). Every number below is verified
against the `--dump-json` records (gitignored at
`.claude/benchmark-results/2026-06-14-nl-query-feasibility.jsonl`). This
reports; it does not gate — the T2 (NL-query) vs T3 (real-data) call is Cray's.

## Headline (two lenses)

| Lens | Score | What it counts |
|---|---|---|
| **Structured-result** (the harness metric) | **8/12** — expressible 5/7, ceiling-rescue 3/5 | the *executed query* returned exactly the gold rows/count |
| **Operator-answer** (what the human reads) | **~10/12** | the *phrased answer* carried the right facts |
| **Anti-hallucination** | **12/12** | **zero invented facts** — every miss was an over-broad set or an honest "no records" |

Latency (translate + phrase = 2 calls/question): **p50 10.9 s · p95 32.2 s · max 32.2 s.**

The gap between the two lenses is the whole story (see Finding 1).

## Per-question

| id | category | ceiling | result | the query it emitted | latency |
|---|---|---|---|---|---|
| nl-01 | filter-enum | – | **wrong** (answer right) | `Asset` **no filter** → all 4 (phrase named the 2 batteries) | 13.1 s |
| nl-02 | count | – | correct | `OperationalEvent count` → 11 | 9.6 s |
| nl-03 | filter-numeric | – | correct | `OperationalEvent measured_value>80` → 2 | 19.9 s |
| nl-04 | filter-enum | – | correct | `OperationalEvent severity=critical` → 1 | 9.2 s |
| nl-05 | count | – | correct | `OperationalEvent severity=warn` → 1 | 9.8 s |
| nl-06 | filter-name | – | correct | `Asset name="Battery Bank A"` → 1 | 10.9 s |
| nl-07 | filter-enum | – | **wrong** (answer right) | `Site` **no filter** → both (phrase named only the microgrid) | 6.7 s |
| nl-08 | superlative | ✓ | correct (rescued) | `OperationalEvent` no filter → all 11; phrase picked max **96.5 °C** | 22.8 s |
| nl-09 | join-count | ✓ | **wrong** (safe) | `OperationalEvent asset_id="Battery Bank A"` → **0** (name used as id) | 19.9 s |
| nl-10 | join-aggregate | ✓ | correct (rescued) | `OperationalEvent type=reading, unit="Celsius"` → 7; phrase averaged **41.3 °C** | 32.2 s |
| nl-11 | entity-superlative | ✓ | **wrong** (safe) | `OperationalEvent type=reading, unit="C"` → **0** (`"C"` ≠ `"celsius"`) | 19.3 s |
| nl-12 | honesty-no-data | ✓ | correct | `Alert status=open` → **0** → honest "No Alert records" | 5.8 s |

## Findings

1. **Filter-omission is the dominant translate failure mode — double-edged.**
   On nl-01 / nl-07 / nl-08 the model emitted an object type with **no filter**
   and returned the whole table. On 11-row toy data the phrase step rescues it
   (nl-01 named exactly the 2 batteries; nl-07 named only the microgrid; nl-08
   picked the max) — so the *answer* is right while the *query* is imprecise.
   This is **harmless here but a real reliability + scale risk:** at partner
   scale the whole-table fetch blows the token budget, hits the
   `_PHRASE_FACT_CAP = 25` truncation (the phrase would then reason over a
   *partial* table and could miss the answer), and dilutes the grounding
   receipt. The structured-result lens (8/12) correctly flags this; the
   operator-answer lens (~10/12) is the toy-data ceiling.

2. **Join-by-name is a hard ceiling, and it fails *safely*.** nl-09 put the
   asset **name** ("Battery Bank A") into an `asset_id` filter; nl-11 used
   `unit="C"` where the data says `"celsius"`. Both matched nothing → the
   deterministic "No records" answer. A single-object-type `StructuredQuery`
   has no way to resolve name→id across types. **Crucially, every such miss
   was an honest no-data answer — never a fabricated one.**

3. **The phrase step rescues superlative/aggregate — but only over a non-empty
   superset.** nl-08 (max) and nl-10 (avg) succeeded because translate returned
   a broad set the phrase could reason over. nl-11 differed from nl-10 by a
   single token (`"C"` vs `"Celsius"`, the latter matching case-insensitively)
   and returned empty → unrescuable. So the rescue is real but **brittle**: it
   hinges on translate not over-specifying the filter into emptiness.

4. **Anti-hallucination held perfectly (12/12).** The grounded-execute +
   "empty → fixed no-data answer" design (PLAN-0013 AC-nlquery) meant zero
   invented facts across every failure mode. This is the strongest positive for
   operator trust — an operator who's been burned by confident-wrong vendors
   sees "I don't have that" instead of a fabrication.

5. **Latency is usable but not snappy.** p50 ~11 s, and the aggregate/superlative
   questions ran 20–32 s (the 2-call translate+phrase design). Fine for a
   considered query; not instant.

## Read → the T2-vs-T3 fork (reports, does not decide)

**Verdict: MIXED, leaning "T2 viable for a scoped demo."**

- Simple operational questions — lookup, numeric/enum filter, count,
  named-asset — **work, grounded and honest.** A "wow" demo *scoped to this
  envelope* would land.
- The **filter-omission** and **join-by-name** gaps would surface on harder
  questions; a live demo must either stay in the working envelope or invest in
  two concrete, cheap fixes (below).
- **Anti-hallucination is a trust asset**, not a caveat.

So **T2 is a real option** — not weak, not flawless. The wedge choice (T2 vs
T3) is therefore **genuinely open** and should be made on partner psychology
(the GTM framing), not blocked on feasibility.

**Concrete T2 improvements this spike surfaced (each small):**
- Tighten the translate prompt to **require the filter** the question implies
  (the no-filter whole-table emission is the #1 error) + enum/value grounding
  ("celsius" not "C").
- Add a **name→id resolve** pre-step (or expose a name filter on events) so
  cross-type questions ("events for Battery Bank A") work.
- Consider an explicit **"fetch-broad + phrase-aggregate" mode** for
  superlative/average — the phrase rescue already works when fed a superset.

## text-to-SQL comparison arm (the architecture-vs-discipline answer)

Same 12 questions, same model, run as **NL→SQL** — the LLM writes a read-only
SQLite SELECT over the same synthetic data, which is executed and scored
(`text_to_sql.py` + `run_text_to_sql.py`; in-memory DB built from the same
`synthetic.py`, so the arms are directly comparable). Recorded at
`.claude/benchmark-results/2026-06-14-nl-query-text-to-sql.jsonl`.

**Result: 11/12 correct · latency p50 5.6 s / p95 12.1 s** (one call, no phrase step).

| dimension | engine-A (NL→StructuredQuery) | text-to-SQL |
|---|---|---|
| accuracy | 8/12 structured (~10/12 answer) | **11/12** |
| ceiling: joins / aggregates | fails or brittle phrase-rescue | **clears natively** (JOIN, AVG, MAX) |
| filter-omission (whole-table fetch) | present | **absent** — wrote `WHERE` every time |
| **anti-hallucination** | **12/12 (perfect)** | **11/12 — LOST IT** (nl-12) |
| latency | p50 11 s / p95 32 s (2 calls) | **p50 5.6 s / p95 12 s (1 call)** |
| attack surface | bounded (no free-form SQL) | arbitrary SQL (here behind a SELECT-only guard) |

**The answer this arm was for:**
- **The ceiling is ARCHITECTURE, not the model.** text-to-SQL cleared every
  join/aggregate the StructuredQuery layer couldn't express — incl. the two
  engine-A *failed* (nl-09 join-count, nl-11 entity-superlative). → enriching
  `StructuredQuery` with join + aggregate ops closes the ceiling; the local
  model is capable.
- **The filter-omission is PROMPT, not the model.** Under the SQL framing the
  same model applied a `WHERE` on every expressible question (incl. nl-01 /
  nl-07, the two engine-A botched). → engine-A's whole-table fetch is a
  translate-prompt fix, not a capability wall.

**But text-to-SQL paid for it in safety (the load-bearing caveat).** On nl-12
("list all open alerts" — no alert data), engine-A returned the honest
deterministic "No Alert records" (grounded=false); text-to-SQL **improvised**
`SELECT * FROM operational_event WHERE event_type='alarm'` and handed back an
*alarm* event as if it were the requested *alert* — a quiet
hallucination-by-substitution. Raw NL→SQL has no grounded-execute guard, so the
model fills the gap by confidently answering a *different* question.

## Read → the refined T2 verdict

The two arms together say **T2 is more viable than the engine-A run alone
showed**, and they point at the right architecture:

- engine-A's weaknesses (ceiling, filter-omission) are **both fixable** —
  architecture (add join/aggregate ops to `StructuredQuery`) + prompt (require
  the filter) — not model limits.
- text-to-SQL's expressiveness is **not worth its safety cost** for an
  operational tool: an operator who's been burned wants "I don't have that,"
  not a confident answer to a question they didn't ask.
- **The target T2 = engine-A's grounded-execute safety + a richer
  `StructuredQuery`** (joins + aggregates), NOT a switch to raw text-to-SQL —
  keeping the 12/12 anti-hallucination *and* clearing the ceiling.

So for the **T2-vs-T3 fork**: T2 is a real, de-riskable option with a clear,
bounded build path. The wedge call stays Cray's (partner psychology); the
engineering half is now evidence-backed — **viable, with a known architecture.**

*AI-assisted (Claude Code, session 58); no `Co-Authored-By` per CLAUDE.md §7.*
