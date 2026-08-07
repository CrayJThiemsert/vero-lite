# Runbook — operating the published OCT demo

> **Scope.** The publicly reachable demo deployment defined by ADR-0035 and built by
> PLAN-0100: bring-up, teardown, the prompt-log deletion paths D6 obliges, and the
> protocol for the one Cray-gated live run.
>
> ⚠️ **Not yet running anywhere.** Phase 5 (the live run, PLAN-0100 Step 11) is still
> owed, and nothing has been deployed. This runbook was written **before** exposure
> because two of its sections — the deletion paths and the Phase-5 pass/fail reads — are
> worth nothing if written afterwards: the first is a compliance obligation that must be
> executable on day 1, and the second stops a live result from being graded into whatever
> it happened to produce.
>
> _[Corrected s213, `superseded by new info`: this note also listed **Phase 3
> (`deploy/published/`)** as owed. It shipped in **#1063** (Step 8) — the compose project,
> `published.env` and the ingress allowlist are all committed, which is why the commands
> below now name the project the compose file actually declares. The same edit fixed
> **seven** invocations that passed `-p vero-oct`: that project name matches nothing —
> `docker-compose.yml` declares `name: vero-published`, and `vero_oct` is the **network**.
> Every deletion path below was therefore unexecutable as written, which is the one
> failure this file exists to prevent.]_
>
> **Standing it up the first time is a different job** and lives in
> [`published-demo-bring-up.md`](published-demo-bring-up.md) — tunnel, subdomain, Access
> policy, rate cap, getting the source onto the host. This file starts once it is running.
>
> Companion record: [`docs/compliance/ropa-published-demo.md`](../compliance/ropa-published-demo.md).

---

## 0. The standing gate

**Every command in this runbook that touches MS-S1 — deploying onto it, warming a model,
any SSH — is a host-state action and needs Cray's explicit go, every time**
(CLAUDE.md §8). The gate covers the whole host, not just inference. Nothing here is
pre-authorised by being written down.

---

## 1. Prompt-log deletion — the three paths

ADR-0035 D6 obliges three, and they are not interchangeable.

### 1.1 Automatic rotation (90 days)

Runs on the **write path**, not on a schedule: there is no cron on the serving host, and a
retention policy enforced by a scheduler nobody installed is a promise rather than a
control. Each write deletes day-files older than **90 days**.

Implementation `services/engine/llm/prompt_log.py` · behaviour asserted in
`tests/api/test_prompt_log.py`, including the 89/91-day boundary and the rule that the
cutoff reads the file **name**, never its mtime (a restore or a volume remount rewrites
mtimes and would silently resurrect expired rows).

**Nothing to run.** Verify it is working by listing the volume — the oldest file should
never be more than 90 days old:

```bash
docker compose -p vero-published exec app ls -1 /var/log/vero/prompt-log
```

### 1.2 Manual purge (full)

⚠️ **Filename correction, recorded rather than silently applied.** PLAN-0100's runbook
section drafts this command against `prompts-*.jsonl` (plural). The writer shipped in
Step 7 names its files **`prompt-YYYY-MM-DD.jsonl`** (singular). ADR-0035 D6 pins no
filename — it says only "an append-only JSONL file per day" — so the implementation is
authoritative and the PLAN's draft was a pre-implementation guess. **The command below
uses the name the code actually writes.** A purge command that matches nothing is the
exact silent failure this dataset's controls exist to prevent, so verify the count before
and after rather than trusting the exit code:

```bash
docker compose -p vero-published exec app sh -c 'ls -1 /var/log/vero/prompt-log/prompt-*.jsonl | wc -l'
```

```bash
docker compose -p vero-published exec app find /var/log/vero/prompt-log -name 'prompt-*.jsonl' -delete
```

Re-run the count: it must be `0`. `find -delete` exits 0 when it matches nothing, so the
count is the evidence and the exit code is not.

### 1.3 Manual purge (date-scoped, for partial purges)

One day:

```bash
docker compose -p vero-published exec app rm -f /var/log/vero/prompt-log/prompt-2026-08-04.jsonl
```

A month:

```bash
docker compose -p vero-published exec app find /var/log/vero/prompt-log -name 'prompt-2026-08-*.jsonl' -delete
```

These purge **files**. To remove individual lines, see the DSR path below.

---

## 2. DSR path — honored within 30 days

A data-subject request has **two surfaces**, and serving only one leaves a copy behind.

**Before starting, read the constraint honestly:** this dataset stores no subject
identifier at all (ADR-0035 D6, ratified OQ-2 — no IP, no headers, no gate identity). A
request therefore cannot be served by looking a person up. It is served by the email at
the vendor plus a content search over what they typed.

**Step 1 — locate.** Search the log for what the requester tells you they typed. Case
-insensitive, and check the count before deleting anything:

```bash
docker compose -p vero-published exec app grep -ric 'SEARCH-TERM' /var/log/vero/prompt-log/
```

**Step 2 — delete the matching lines** (keeping every other line in that day's file):

```bash
docker compose -p vero-published exec app sh -c "for f in /var/log/vero/prompt-log/prompt-*.jsonl; do grep -iv 'SEARCH-TERM' \"\$f\" > \"\$f.tmp\" && mv \"\$f.tmp\" \"\$f\"; done"
```

Re-run Step 1: the count must be `0`. If the request is broad enough that per-line
deletion is unreliable, delete the whole day file (§1.3) — over-deleting is the safe
direction here, since nothing downstream reads this log.

**Step 3 — remove the requester's email from the vendor allowlist.** Cloudflare Access
policy, portal-side.

**Step 4 — file the vendor-side deletion request** with Cloudflare, for the gate email and
their edge access-log metadata. Our deletion does not reach the vendor's own records; this
step is what makes the erasure complete (RoPA §4 — Cloudflare is an erasure-propagation
target).

**Step 5 — note the action** in the RoPA instance's §9 action log: date, scope, requester,
whether the vendor request was filed, and by whom. **The record is the evidence** — an
unrecorded DSR action is indistinguishable from one that never happened.

---

## 3. Operate / teardown

**Bring-up order.** Portal-side connector last, so the demo is never reachable before the
app behind it is healthy:

1. Bring up the published compose project (`deploy/published/`) — *owed, PLAN-0100 Step 8*.
2. Confirm the app answers on the internal network, and that the proxy 404s an excluded
   route (the AC-6(c) smoke).
3. Confirm the D6 notice renders and `UI_PROFILE=published` is in effect — the served
   `index.html` must carry `<meta name="ui-profile" content="published">`.
4. Only then start the portal-side connector / publish the tunnel route.

**The one-command kill.** Teardown is portal-side and does not require touching the app:
**delete the tunnel route / stop the connector.** That removes reachability in one action
without a redeploy, which is why the app publishes no `ports:` — there is no second way in
to forget about.

**Key provisioning for the demo operator.** `API_AUTH_ENABLED=true`, so the operator needs
a raw key whose sha256 digest is in `API_KEYS`. Generate the pair with the one-liner in
`.env.example`; the **raw key is what the operator types to log in** and is never
committed (CLAUDE.md §8). Note that login probes `GET /whoami` — that route must be on the
published allowlist or no key can be stored at all (PLAN-0100 census finding C-1).

**MS-S1.** Every command against it — deploy, warm, SSH, or a model check — is host-state.
See §0. Live runs are minimized by policy: evidence, not a CI gate.

---

## 4. Phase 5 protocol — the single Cray-gated live run

**Pass/fail reads are fixed HERE, before any go is requested.** That is the whole point of
this section: a live result graded after the fact is not evidence, it is a story told
about whatever happened.

**Preconditions, all required:**
- every offline AC of PLAN-0100 green;
- the portal repo stood up and Cray has named the domain (the OQ-4 trigger);
- **explicit Cray go recorded** before any command touches MS-S1.

**One visit, minimized**, under the D1(5) do-no-harm duty.

### 4.1 P4 — edge timeout vs the LLM route

- **Measure:** wall-clock time from request to first byte for a `POST /query` that takes
  the LLM arm, through the vendor edge, repeated 3×.
- **PASS:** every trial returns a complete answer, and the observed latency leaves margin
  under `LLM_REQUEST_TIMEOUT_S=25`.
- **FAIL:** the edge terminates the request before the app answers, at any trial.
- **INSUFFICIENT-EVIDENCE:** MS-S1 unreachable, the model absent, or the tunnel not
  established — a **skip, never a pass**.

### 4.2 P5 — eviction coexistence

- **Measure:** whether serving the demo's LLM route evicts a model another workload had
  resident on MS-S1 (`/api/ps` before and after).
- **PASS:** no neighbour model is evicted.
- **FAIL:** the demo call evicts a resident neighbour.
- **Consequence of FAIL, pre-committed:** **every `assisted` row in the route allowlist
  drops to `deterministic` until Cray re-rules** (the P12 bounded iteration). This is
  recorded now so the outcome is not renegotiated once it is inconvenient.

### 4.3 After the run

Commit the artifacts. Then the PROVISIONAL allowlist is either **revised** (a follow-up PR
citing the artifact) or **explicitly confirmed "no revision"** in the closeout — silence
is not confirmation.

---

*PLAN-0100 Step 10 (AC-10). Deletion paths and the 90/30-day figures are ADR-0035 D6's,
restated verbatim. The §1.2 filename correction is recorded above rather than applied
silently.*
