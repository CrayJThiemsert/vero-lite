# Runbook — fleet PM data onboarding (Wialon export + the paper PM folder)

**Owner:** น้องเมย์ (operator №1), with the owner for the one-off baseline
**Applies to:** the `fleet_maintenance` vertical's AT-3 calm path (`pm_service_round`)
**Built by:** PLAN-0096 Step 9 / AC-10

---

## Why this is a runbook and not a feature

Two numbers decide when a truck is flagged for its interval service:

| Number | Where it lives today | How it gets in |
|---|---|---|
| current odometer | Wialon (GPS already fitted — *"รถผมติด GPS ไว้แล้วนะ"*) | monthly CSV export → import → confirm |
| **last-service** odometer | a paper folder in the office | **one-off manual load** → import → confirm |

The second one is the reason this document exists. There is no system anywhere that
holds it, so it cannot be integrated — it has to be typed once, by someone who can
read the folder. That is an onboarding **task**, and building code to pretend
otherwise would mean inventing the numbers. Until it is done, every
`next_service_due_km` in the fleet is a fixture value and the calm path is a
demonstration rather than a tool.

**Nothing here writes to a truck on its own.** Every import proposes; a human
confirms; only confirmed values are visible to the ontology. That is Q4's answer made
structural — the partner said his telematics figures are approximate, so a machine
reading is a claim, not a fact.

---

## A. One-off: load the last-service baseline

Do this once per truck, at onboarding. Budget an hour with the folder.

1. Make a spreadsheet with exactly two columns:

   ```csv
   plate,last_service_odometer_km
   80-1234 กรุงเทพมหานคร,450000
   70-5678 กรุงเทพมหานคร,585000
   ```

   * `plate` — exactly as written on the truck. Case and extra spaces are tolerated;
     a plate the fleet does not have is rejected on its own row with a reason, and the
     rest of the file still imports.
   * `last_service_odometer_km` — the odometer **at the last interval service**, not
     the interval and not today's reading. Thousands separators are fine.

2. Save as CSV (UTF-8) and upload:

   ```bash
   curl -F "file=@last-service.csv" http://localhost:8103/api/pm/imports
   ```

3. The response lists every row with `status: "proposed"` and a computed
   `next_service_due_km` = last service + 100,000 km (the interval the partner gave:
   *"เข้าศูนย์ทุกแสนกิโลฯ"*). **Read the computed due points before confirming** —
   this is the step that catches a mistyped digit, and it is much cheaper here than
   after a truck has been flagged or missed.

4. Confirm the rows you agree with:

   ```bash
   curl -X POST http://localhost:8103/api/pm/imports/<batch_id>/decisions \
     -H 'content-type: application/json' \
     -d '{"decisions":[{"import_row_id":"<row_id>","confirm":true}]}'
   ```

   Rows you leave out stay `proposed` and stay invisible. That is a safe state, not an
   unfinished one — come back to them.

5. Check what was accepted:

   ```bash
   curl http://localhost:8103/api/pm/overrides
   ```

## B. Recurring: the Wialon odometer export

Monthly, or whenever the fleet feels out of date.

1. Export the odometer/mileage report from Wialon per unit.
2. Reshape to the same contract — `plate` + `odometer_km`:

   ```csv
   plate,odometer_km
   80-1234 กรุงเทพมหานคร,412580
   ```

   > **Open intake question.** The partner's real Wialon export header has not been
   > seen yet; when it arrives, the accepted column names live in one place —
   > `KNOWN_COLUMNS` in `verticals/fleet_maintenance/pm_import.py` — so matching his
   > file is a one-constant edit, not a parser rewrite.

3. Upload, review, confirm — steps 2–5 above, unchanged.

A file may carry both columns at once; nothing forbids it.

---

## What a refusal means

| Response | Meaning | What to do |
|---|---|---|
| `422` naming a row | the file is malformed — **nothing was imported** | fix that row and re-upload the whole file |
| row `rejected`, reason `unknown_plate` | the plate matches no truck | check the plate, or the truck is retired |
| `409` on a decision | that row was already decided | decisions are final; re-import to propose again |
| `413` | the file is over the upload ceiling | split it |

A malformed file is refused **whole**, on purpose: a half-imported fleet is a state
nobody can reason about. A single unmatched plate is *not* malformed — it is an
ordinary onboarding event — so it never takes the other rows down with it.

---

## After a restart

The confirmed view is loaded at API startup. If the database was unreachable at boot,
the trucks serve their fixture values and the API says so — check the `view` block:

```bash
curl http://localhost:8103/api/pm/overrides
```

`view.loaded: false` with a `view.last_error` means *"could not read"*, which is a
different thing from an empty `overrides` list meaning *"nobody has confirmed
anything"*. Restart once the database is up; no re-confirmation is needed, because the
confirmations themselves are durable — only the in-process view was missing.

---

## Related

* `verticals/fleet_maintenance/pm_import.py` — the parser + the 100,000 km interval
* `services/db/pm_import.py` — the `pm_import_row` staging table
* `verticals/fleet_maintenance/pm_projection.py` — where a confirmed value becomes
  something the calm path can see
* `docs/plans/0096-fleet-flow-completion-phase1.md` §Step 9 / AC-10
