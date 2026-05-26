"""PLAN-0010 scheduled-task autonomy loop — code package.

Data lives at ``loop/inbox/`` + ``loop/processed/`` (repo top, per
PLAN-0010 Step 1 §1 — Code-picked SD-3 ratification). This package
holds the parser + (future) dispatcher.

Modules:

* :mod:`tools.loop._schema` — message parser + validator (stdlib-only;
  mirrors :mod:`tools.handoffs._schema` discipline)
* (Step 3b will add ``tools.loop.dispatcher`` — consumer poller with
  L1-L4 loop-detect integration)
"""
