# Intro video — production rulings and filming constraints

> **What this file is: a RECORD, not a rule.** It carries the decisions Cray typed
> about the introductory video, and the filming constraints that follow from them, so
> that they survive outside a gitignored working file. It creates no new obligation and
> holds **no precedence tier** (`CLAUDE.md` §1) — where it appears to conflict with an
> ADR, `CLAUDE.md`, or a convention, the canonical wins and this file is corrected.
>
> **Superseding a ruling here needs Cray.** A session may record that a ruling's
> *mechanics* were overtaken by a measurement (§4 does exactly that, twice) — it may not
> reverse the ruling's *intent* on its own.
>
> **Scope note:** the storyboard, the VO script, and the shot list live in
> `docs/strategy/private/` and are **gitignored by design** (ADR-006 D2 — see
> [`README.md`](README.md)). This file deliberately carries only the rulings and
> constraints, at the abstraction the public split allows. It is an index into that
> work, not a copy of it.

---

## 1. Why this file exists

R1–R7 were typed by Cray across three sessions and lived in exactly two places, **both
gitignored**: `docs/strategy/private/2026-08-10-intro-video-STORYBOARD-v2.md` and a session
handoff. (**R8 is the exception** — it was ruled at session 239 and recorded here first,
which is what this file being tracked now makes possible.) A carve-out check run at session
239 confirmed the gap by measurement rather than by memory — `git grep -i` over
`docs/ deploy/ services/ tests/ verticals/` returned:

| Probe | Tracked hits before this file |
|---|---|
| `reply to this email` (the CTA ruling) | **0** |
| `access code` | **0** |
| `barely say` | **0** |
| `verify-chain` | **0** |
| `founder on camera` | **0** |

Handoffs are gitignored working notes. One `/clear` and the video could not have been
shot from anything the repository holds.

**What was already tracked, and is not repeated here:** the *pivot itself* — why the
storyboard's beat 4 targeted a screen the customer cannot reach — is recorded in
[`docs/conventions/local-first-published-parity.md`](../../conventions/local-first-published-parity.md),
which is the standing convention that failure produced. Read that for the **why**; read
§4 below for the **replacement**.

---

## 2. Cray's typed rulings

Eight rulings across three dates. Each row names where it was typed, because the count
has been mis-carried before: the four rulings of **2026-08-12** sit in the storyboard's
own ruling table, while the **2026-08-10** ruling was recorded inline in the beat it
governs. Every summary written afterwards inherited the table and dropped the fifth.

### 2.1 Content and framing

| # | Ruling | Typed | Consequence folded in |
|---|---|---|---|
| R1 | **Beat 2.5 carries the vendor-documentation sentence ONLY — no numbers on camera.** Beat 2.5 cites the model vendor's own documentation that determinism is not guaranteed, and cites nothing else. Reserve evidence stays off-camera for the live demo if challenged | 2026-08-10 | Enforced by the storyboard's own risk register, whose failure condition reads *"a number enters beat 2.5 or 4"* |
| R2 | **~140 s runtime, with objections IN the video** | 2026-08-12 | Creates **beat 4.5**. ⚠️ Ruled **against** the drafted recommendation (~110 s, objections travelling in the attached one-pager). The dissent is recorded in the storyboard and **closed** — do not re-litigate |
| R3 | **"Barely say AI"** | 2026-08-12 | Beat 1 dismisses it once; beat 2.5 pivots |
| R4 | **Beat 4 gains the Verify-chain shot (Tab H)** | 2026-08-12 | Originally "4 shots, not 3". ⚠️ **The shot count is superseded — see §4.** The ruling's intent (the Verify chain must appear on camera) stands unchanged |
| R5 | **Founder on camera for BOTH beats 1 and 5** | 2026-08-12 | Two camera setups |

### 2.2 Where it is shot, and what it asks for

| # | Ruling | Typed | Consequence folded in |
|---|---|---|---|
| R6 | **Option (A): shoot beat 4 on the PUBLISHED profile.** Tab G is dropped from the video | 2026-08-18 | The beat-4 remap in §4. Tab G is absent from the published profile **by ruling**, not by omission |
| R7 | **The CTA stays *"reply to this email and I'll send you the link + access code"*** — chosen deliberately, because it demonstrates that access control is handled rather than hiding the Access gate | 2026-08-18 | 🔴 **No demo URL may appear on screen anywhere in the clip.** A viewer who reads a URL off the video hits the Access wall before ever talking to us — which inverts the CTA |
| R8 | **Drop the ฿15,000 contrast from beat 4** — option (a) of three, ruled after the remap was measured | 2026-08-18 | The ladder is now **declared** rather than demonstrated. See §4.1 for what was lost, what carries it instead, and why (b) was rejected as dishonest |

---

## 3. Filming constraints

These are not stylistic preferences. Each one exists because the alternative states
something the product does not do, or reads a number the ruling above keeps off camera.

Each rule is stated once in **plain, unformatted text** so that `git grep` finds it. That
is not a stylistic choice: this file exists because a grep returned zero, and a rule
broken up by emphasis markers is a rule the next grep will miss.

| Constraint | Why |
|---|---|
| Never read the numeral for "เกินสามหมื่น" | The screen shows ฿30,001 — the DoA band boundary. Reading it aloud turns a band into a headline figure |
| Say tamper-evident, never immutable | The audit chain detects retroactive edits; it does not prevent them. ✅ Confirmed at session 237: the live UI says `tamper-evident` itself, so where the two disagree, the **marketing artifact is the one that is wrong**, not the product |
| Say "เส้นทางที่ถูกกำกับ", never "vero-lite ไม่ให้โมเดลตัดสินอะไรเลย" | Overclaims. The legacy reactive path **does** execute a model-suggested handler — behind a human gate. The honest claim is that the model never holds the authority, not that it never acts |
| No benchmark numbers anywhere | The 12/12 anti-hallucination result is real, but it is 12 questions over an 11-row synthetic set. On camera it would read as a product benchmark. This is R1's enforcement, generalised |

---

## 4. The beat-4 remap — measured; do NOT re-derive

Session 237 measured this against the live published system. It is recorded here because
re-deriving it costs a full render-and-measure cycle, and because the naive reading
("just film Tab G") is wrong.

**Why Tab G is out.** `deploy/published/oct-fleet-maintenance/published.env` publishes
`A,C,F,H,I,J`. Tab G is excluded **by ruling** (SD-3 session 218; ADR-0032 D1.2 — the
governed hero is bespoke per design partner and belongs to the procurement system: *one
system, one story*), and the fleet governance surface **refuses `live=true`** rather than
faking it. The storyboard's shots 4a–4c were verified on a local **dev**-profile run
where all ten tabs render — a different system.

**Tab H replaces all three shots with ONE frame, and gains:**

- The whole beat fits in **one viewport with zero scrolling** (`docH == 737`), where Tab
  G's two halves were **797 px apart** against a 720 px viewport — provably unable to
  share a frame.
- The persona cards render the **authority ladder as identity**, not as configuration.
- The gate panel states the case **in the product's own words** — the spend, the tier it
  lands in, the band, and *"separation of duties binds this gate: the requester cannot
  approve their own requisition"*.
- **`Advisory · shown, never routes · deterministic`** — beat 2.5's argument, written by
  the product instead of narrated by the founder.
- The **Verify chain** button sits in the **same frame** (y = 302), so R4's shot needs no
  separate setup.

**Two supersessions, both measured — record them as evolution, not as errors:**

1. **R4's "4 shots, not 3" no longer describes the shoot.** One Tab H frame carries what
   three Tab G shots carried, and the Verify-chain button is already in it. R4's intent
   is satisfied more cheaply than R4's mechanics assumed.
2. **Session 220's §D warning — "Postgres must be up, a run must already sit in
   `waiting_human`, and there is no UI control that fires one, so fire it via API
   off-camera" — no longer applies on the published profile.** The `waiting_human` run is
   seeded at boot, so no off-camera API call is needed. Since PLAN-0110 the demo also
   self-reports whether it is still shootable — see §6.

**Tab F is a bonus frame.** Its vertical chips prove multi-vertical on one line without a
portal, and it carries *"the LLM drafts the summary (advisory); it decides nothing"* — R3
and beat 2.5, stated by the product.

### 4.1 What the remap cost — the ฿15,000 contrast (R8)

Measured at session 239, and **not** recorded by the sessions that designed the remap: the
old beat had a shot that *demonstrated* the authority ladder routing a second, cheaper
repair to the fleet manager instead of the owner. **No published tab renders that.** Tab A
lists the anomaly but shows no tier; Tab F names both rungs in prose; Tab H's gate panel
states only the ฿48,000 case.

So the remap trades a **demonstration** for a **declaration**. Three options went to Cray,
who ruled **(a) — drop it**:

| | Option | Outcome |
|---|---|---|
| ✅ **(a)** | Drop the contrast; let the persona role lists carry the ladder | **RULED.** Buys back runtime R2 is short of |
| **(b)** | Assert it in the VO over Tab A's anomaly rings | **Rejected — dishonest.** The frame shows no tier, so the VO would claim what the screen does not. Additionally false in the picture: Tab A shows **three** anomalies, and two of the three exceed the band floor |
| **(c)** | Build it — surface the routed tier per anomaly | **Rejected for the shoot**, not forever. A code change, not a filming decision |

**The consequence, and where it lands.** The persona role lists are now the only reliable
carrier of *"this is a ladder, not always-escalate"* — so the shot that shows them has to
**say** it, not leave it to be inferred from three cards. That is a real narrowing of the
beat, accepted knowingly.

⚠️ **Do not reopen this as "the beat feels thin".** The thinness is the ruled trade, not a
defect. If it is ever worth paying for, the fix is (c) — a build, not a retake.

---

## 5. Open — not ruled

Nothing below is decided. They are recorded so they are not rediscovered.

1. 🔴 **The VO has never been stopwatched, and every runtime in the storyboard is an
   estimate.** Thai has no word spaces, word count is not a usable proxy, and no Thai
   narration-rate benchmark exists. R2's 140 s leaves **less** slack than the 110 s that
   was drafted, so this is the largest unknown in the plan — it may force the 7-beat
   structure back to 6.
2. **`Advisory proposal (stubbed)` renders three times** on Tab H's gate panel, and
   *(stubbed)* reads as unfinished on camera. ⚠️ **Corrected at session 239 — this is not
   a duplicate render.** The gate states *"3 candidates reached this gate; the reasons
   above describe the first"*: they are three genuine proposals that all carry the same
   placeholder title. The choice is therefore **not** "crop the duplicate" but **name each
   candidate**, which turns an unfinished-looking panel into a real one. **Undecided.**
3. **The fonts are too small to film**: persona name 13.5 px, id 11 px, gate reasons
   12 px on a 927 px viewport. Shooting needs roughly 150 % zoom or a narrower window —
   ⚠️ **and every geometry number in §4 must then be re-measured**, including `docH` and
   the Verify-chain button's y.
4. **The run list carries an orange `11 WAITING ON YOU` badge**, which reads as *"this
   operator is behind"*. ⚠️ The number measured at session 239 is **dev-box specific** —
   that database has accumulated runs from every vertical since bring-up, while each
   published system has its own. **Crop the left column, or re-measure on the published
   host before rolling. Do not film the number as measured locally.**

---

## 6. Before shooting — check the demo is still shootable

The beat-4 frame depends on a demo run sitting in `waiting_human`. A visitor who plays
the approval beat consumes it, and it stays consumed until someone deploys. The state is
observable without changing anything:

```bash
ssh -o BatchMode=yes ms-s1 docker exec oct-fleet-maintenance-app python -m services.db.demo_run_reset
```

Expect `DEMO-STATE: PRISTINE`. 🔴 **No token at all is a FAILED check, never a pass** —
that is the module's own contract. If it reads `CONSUMED`, the restore procedure is
`deploy/published/oct-fleet-maintenance/DEMO-RESET.md`.

⚠️ Reading the state is free. **Restoring it is a host-state change and needs explicit
Cray go per occasion** (`CLAUDE.md` §8).

---

## 7. Provenance

| Ruling / constraint | Originating session | Surviving source at time of rehoming |
|---|---|---|
| R1 | 220 (typed 2026-08-10) | storyboard v2, inline at beat 2.5 — **outside** the ruling table, which is why later summaries dropped it |
| R2–R5 | 220 (typed 2026-08-12) | storyboard v2 ruling table |
| R6, R7 | 237 (typed 2026-08-18) | session-237 handoff §5.3 |
| R8 | 239 (typed 2026-08-18) | **this file** — ruled in-session once §4.1's loss was measured; recorded here first, not rehomed |
| §3 filming constraints | 220, re-confirmed 237 | storyboard v2 (beats 2.5 and 4) + session-237 handoff §6.1 |
| §4 remap | 237, **geometry re-measured 239** | session-237 handoff §6.1; re-taken on `oct-demo-published-fleet` at 1280×720 |
| §4.1 the lost contrast | **239** | measured this session — no prior artifact records it |
| §5 open items | 220 (item 1), 237 (items 2–3), **239 (item 4 + item 2's correction)** | session-220 handoff §6, session-237 handoff §5.4, session-239 measurement |

All sources except this file are gitignored. Rulings were transcribed from the
originating artifact rather than from the most recent summary of it — the summaries were
each accurate about what they cited and each carried a smaller inventory than the one
before.

## References

- [`docs/conventions/local-first-published-parity.md`](../../conventions/local-first-published-parity.md)
  — the convention the beat-4 failure produced; the **why** behind §4
- [`CLAUDE.md`](../../../CLAUDE.md) §8 — the host-state gate governing §6
- `ADR-0032` D1.2 — one system, one story (why Tab G is not published)
- `ADR-006` D2 — the public/private strategy split this file is written under
- `deploy/published/oct-fleet-maintenance/published.env` — the published tab set
- `deploy/published/oct-fleet-maintenance/DEMO-RESET.md` — the restore procedure
