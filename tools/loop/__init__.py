"""PLAN-0010 scheduled-task autonomy loop — code package.

Data lives at ``loop/inbox/`` + ``loop/processed/`` (repo top, per
PLAN-0010 Step 1 §1 — Code-picked SD-3 ratification). This package
holds the parser, the dispatcher, and the status-digest workload.

Modules:

* :mod:`tools.loop._schema` — message parser + validator (stdlib-only;
  mirrors :mod:`tools.handoffs._schema` discipline)
* :mod:`tools.loop.dispatcher` — consumer poller with L1-L4
  loop-detect integration (Step 3b; shipped, currently disabled —
  PLAN-0010 closed "shipped + intentionally disabled", s118)
* :mod:`tools.loop._status_digest` — the ratified first workload
"""
