"""Procurement hero-demo composition layer (PLAN-0045).

Read-only demo glue that binds the C1 CSV dataset + the shipped A1b governance engine into the
hero-demo's two computed beats:

* ``governance_audit`` — the deterministic GOVERNANCE MOMENT capture (Step 1b): the real
  ``resolve_doa_tier`` + ``check_principal_sod`` + ``GovernedDecision`` run over the Fastenal
  ladder + principals (SD-1 Layered = the offline-fixture arm / CI gate / demo fallback).
* ``ledger`` — the ฿-impact ledger (Step 3): baseline (on-AVL wait) vs governed (off-AVL
  emergency) exposure, computed from the dataset columns.

Nothing here edits ``services/`` engine core (ADR-0023 / CQ-1); it only CALLS the shipped engine
APIs. All figures are DEMO-GRADE / PROVISIONAL (dossier §10).
"""
