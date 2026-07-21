# `fleet_maintenance/` — FleetMaintenance vertical (PLAN-0086, the 6th vertical)

**Status:** Hand-written under the PLAN-0086 timed-scaffold measurement — deliberately NOT produced by `vero-lite new-vertical` (that scaffolds a Tier-1 recommend/breach mirror only, ADR-0015 D2, and using any generator for the parts a future scaffolder tool must replace would have contaminated the measurement).
**Asset-role:** `Truck` · **Site-role:** `Depot` · **Breach direction:** `above` the truck's own `minor_repair_ceiling_thb`
**Archetype:** AT-2 (`governed_repair_approval`) — the money `doa_tier` ladder REUSED unchanged; not a new AT-2 signature.
**First vertical shipping the PLAN-0085 gate advisory ON by default** (PLAN-0086 L-B — readable on day one).

> ⚠ The synthetic dataset in `data_adapter/synthetic.py` is a demo fixture. Every ฿ figure traces to the simulated customer's own words or to a logged intake answer — see the provenance header in `procedures.yaml`.

## Problem

A Thai trucking operator runs a mixed fleet (tractor heads + six-wheelers) on long-haul routes. When a truck breaks down mid-route the money decision happens on the phone, at speed, with a load and a delivery window at risk — and the operator's own approval rules collapse exactly when they matter most. Afterwards nobody can reconstruct who authorised what: the record lives in LINE groups and a paper notebook, so month-end accounting cannot answer "who ordered this, and was it price-compared?"

The owner already has rules. He states them plainly: the head mechanic settles small repairs, the fleet manager the middling ones, anything heavy comes to him; whoever files a claim may never approve it (a rule he adopted after being defrauded on parts); and large purchases must be price-compared across vendors. What he lacks is anything that *applies* those rules when the truck is already on the hard shoulder.

## Decision / action

`governed_repair_approval` turns the breakdown into a governed run:

1. **intake** — latest quoted repair per truck, joined to that truck's own repair ceiling.
2. **judge** — quote vs the truck's own `minor_repair_ceiling_thb`. Under the ceiling the head mechanic just fixes it and no governed run is needed; at or above, it breaches.
3. **reshape** — the breaching quote becomes a flat governed spend (`amount` / `currency`) plus the sourcing-hygiene signal map.
4. **quote_gate** — the hard sourcing rule (a large repair needs three competing quotes). Blocks on failure; non-waivable by type.
5. **approve** — the money `doa_tier` ladder routes the spend to the human authority its size demands, with separation of duties binding requester ≠ approver. The run **suspends** here: nothing is written until a human decides. The gate advisory explains *why* it stopped, in the run's own numbers — it decides nothing.
6. **fulfill** — the approved authorisation write (a no-op receipt stub until the design partner's garage/ERP integration lands).

The roadside bypass the owner described is modelled rather than ignored: the ladder's `emergency_waiver` relaxes the three-quote requirement, escalates the approver, and demands a written justification. It never skips the gate.

## Run this vertical

```dotenv
OCT_VERTICAL=fleet_maintenance
OCT_RECOMMEND_THRESHOLD=5000
OCT_RECOMMEND_DIRECTION=above
OCT_RECOMMEND_ENTITY_TYPE=Truck
OCT_RECOMMEND_ENTITY_ID_FIELD=truck_id
OCT_RECOMMEND_LABEL="repair quote over ceiling"
OCT_RECOVERY_VALUE=3200
OCT_RECOVERY_DESCRIPTION="quote back under the mechanic's ceiling"
```

Regenerate the ontology artifacts (all seven land gitignored under `generated/`):

```bash
uv run vero-lite validate fleet_maintenance && uv run vero-lite generate fleet_maintenance
```

## Known expressiveness gaps (stated by the customer, NOT enforced by the engine)

Recorded here deliberately — a governed system that silently drops half a customer's rule is worse than one that admits the gap:

| Customer rule | Enforced | Not enforced |
|---|---|---|
| Price-compare large repairs across three vendors | the three-quote requirement | the ฿ threshold that triggers it — a `rule_gate` criterion is pass/fail on a supplied signal and carries no threshold field |
| Roadside emergencies may proceed before approval | the waiver's escalation + mandatory justification | the ฿ cap on such spend, and the after-the-fact ratification window — `EmergencyWaiver` has no fields for either |
