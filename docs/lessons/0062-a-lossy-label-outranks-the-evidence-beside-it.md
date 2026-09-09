# Lesson #0062 — a lossy label outranks the evidence beside it

**Session:** 290 (2026-09-09) · **Measured on:** `.claude/state/stop-classifier-log.jsonl`,
187 records (2026-09-06 .. 09-09), 0 unparseable · **Status:** advisory (§1 precedence —
promote to ADR if it must bind)

---

## The measurement

The Stop classifier writes each exchange with a categorical
`transport ∈ {ok, timeout, malformed, retry}` **and** a free-text `reason`. The two fields
sat in the same record and disagreed. Session 289 tallied the category; session 290 read
the text.

| | s289 — tallied by `transport` (180 records) | s290 — re-split by full `reason` (187 records) |
|---|---|---|
| the `timeout` bucket | `timeout 50.0%` | 62 × `HTTP Error 500`, 27 × `timed out`, 2 × `WinError 10060` |
| the `malformed` bucket | a wire error | 74 × `Ollama envelope missing message.content` — an HTTP **200** |
| the conclusion drawn | elapsed time / the network is the blocker | 136 of 187 (**72.7%**) = the server answered fast and answered wrong |
| genuine network failure | — | **2 of 187 (1.1%)** |

The tally arithmetic was correct. Nothing was miscounted. **The field was lossy** — and the
action its label implied, widening the timeout, could not have moved a single one of the 136.

> **A category is an interpretation; the text beside it is the measurement.** Tallying by a
> lossy category does not merely lose detail — it *manufactures a cause*, because the
> aggregate is legible and confident and the discarded text is neither.

## Why the category wins by default

`timeout 50.0%` is one number. It sorts, it goes in a table, it reads as a finding. The 187
`reason` strings are unsorted prose that has to be looked at one at a time. Given a legible
aggregate and an illegible field describing the **same events**, the aggregate is what gets
acted on — not because anyone judged it more reliable, but because it is the one already
shaped like an answer.

The confidence is manufactured with it. A percentage over a clean four-valued enum carries
no visible uncertainty: nothing on the face of `timeout 50.0%` says the bucket holds three
different physical events. A cause read off it inherits the precision of the arithmetic and
none of the fidelity of the labelling.

## The caveat was written down, at the definition site, and it still did not stop anyone

This is the uncomfortable half. The deviation was **not** undocumented. It is spelled out at
the constants in `.claude/hooks/_sonnet_classifier.py`, in the file that does the labelling:

```
#: 2. An HTTP error response — including the 500s measured above — arrives as
#:    ``urllib.error.HTTPError``, a subclass of ``URLError``, and so lands in
#:    ``timeout``. That conflates "the server refused" with "the server never
#:    answered", which we have MEASURED to be different causes. No information
#:    is lost: ``reason`` carries the distinguishing text ("HTTP Error 500"
#:    vs "timed out"), so AC-12 can separate them.
```

Every clause of that comment is true, **including the reassurance**. No information *was*
lost — the record still carried the distinguishing text, which is exactly how s290 recovered
it. What was lost was the reader.

> **Documentation of a known lossy mapping does not survive aggregation.** By the time the
> field is a percentage in a report, the caveat is three hops away — record → tally →
> percentage → report — and nobody re-reads the constant's docstring on the way.

"No information is lost, the other field carries it" is a true statement about the *record*
and a false prediction about *practice*. It holds only while someone reads the other field,
and the entire purpose of a category is to stop reading it. If a mapping is known to be
lossy, the note belongs where the aggregation happens — not only where the value is defined.

## What made the re-split trustworthy was a second, independent field

A re-split is not evidence. It is the same records read again by the same reader, who by then
has a hypothesis and is looking for it. What made s290's split believable was a field it had
not touched:

- exactly **27** records say `timed out` in `reason`
- exactly **27** records have `latency_s >= 70`, against a 75 s client timeout

`latency_s` is written by different code and means a different thing; nothing forces it to
agree with a substring of `reason`. **Two unrelated fields landing on the same 27 records is
the evidence. One field re-read is not** — cf.
[#0053](0053-two-sessions-agreeing-through-one-instrument-is-one-measurement.md), where two
sessions agreeing through one instrument was still one measurement.

## No tally over this schema could have found it

Root cause, later confirmed from MS-S1's own `server.log`: `gpt-oss:20b` emitted harmony tool
calls for tools the request never declared, and Ollama's parser then failed ~half as a 500
and ~half as a 200 with empty content.

**One fault, recorded by the schema as two unrelated categories** — 62 of it in `timeout`,
74 of it in `malformed`. The enum's job is to hold those two apart, so no aggregation over it
could ever have put them back together. Grouping them required reading the strings and
noticing they described the same server misbehaving in the same way.

## The same shape, twice more in the same session

**1 — a label the instrument invented.** A grep for `OOM` over MS-S1's server log returned 8
hits, and those 8 were reported as OOM evidence. The needle had matched the `oom` inside
*"making room for prompt cache"*. The count was real; the category was not. The instrument
was **fresh** — newly drafted for this question — while the hypothesis was inherited, so the
new thing in the room was the draft, not the theory
([#0056](0056-suspect-the-instrument-before-the-artifact.md)). Its s286 rule applies
verbatim: when the needle is short and the corpus is prose, anchor or word-bound it before
believing the count.

**2 — a join that scored 0 and was read as a verdict.** A timestamp join of the classifier
log against MS-S1's server log matched **0 of 62**, and was read as *"these are different
events."* They were the same events: MS-S1's clock runs ~165 s ahead, and one log is UTC
while the other is +07:00.

🔴 **Widening the tolerance would have manufactured neighbour matches** — a tolerance wide
enough to bridge the offset is wide enough to pair each event with the ones either side of
it, and the join would have come back green and wrong. The fix was to join on something the
clock cannot corrupt: two shape-based signals, the **inter-event gap sequences** (identical)
and the **durations** (agreeing to a tenth of a second). Repair by derivation, never by
relaxation (CLAUDE.md §8) — and, as in
[#0058](0058-an-assertion-that-moves-with-the-mutation-has-no-witness.md), anchor on
something the fault cannot follow.

## The practice

1. **Before acting on a distribution over a categorical field, read the raw text of a sample
   from each bucket and confirm the bucket means one thing.** Sample *every* bucket, not only
   the suspect one — `malformed` was not under suspicion and it held the single largest
   group, 74 records of a 200 response.
2. **Prefer a second, independent field as corroboration before believing a re-split.** Name
   which field, and why it cannot move with the first. The `27 timed out` / `27 latency_s >=
   70` pair is the shape to aim for; a second reading of the same field is not.
3. **Put the lossy-mapping caveat where the aggregation happens, not only at the
   definition.** A note at the constant survives one hop. A note in the report that prints
   the percentage survives to the person acting on it.
4. **An extreme reading is an instrument claim first** — `0 of 62`, a bucket at exactly
   `50.0%`, 8 hits for a three-letter needle. Go to the artifact before it becomes a finding
   ([#0046](0046-when-a-check-and-a-claim-disagree-go-to-the-artifact.md)).

## The one-line version

> The category was written by whoever chose the enum; the text was written by the event.
> s289 acted on the enum and got a cause that did not exist — while the distinguishing string
> sat in the same record the whole time, and a comment at the definition site said so.

---

*Related: [`0035`](0035-negative-measurement-needs-a-positive-control.md) (a zero needs a
positive control — the 0/62 join),
[`0048`](0048-repeat-sampling-establishes-a-rate-not-a-cause.md) (a rate is not a cause),
[`0056`](0056-suspect-the-instrument-before-the-artifact.md),
[`0061`](0061-an-acceptance-criterion-is-not-a-spec.md) (where this enum came from —
PLAN-0122 §4.3, and the deviation note it produced).*
