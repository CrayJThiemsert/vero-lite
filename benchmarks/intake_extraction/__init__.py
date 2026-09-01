"""PLAN-0118 — the intake-extraction benchmark lane.

Measures the model at the **shipped** ``extract_package`` seam
(``services/engine/llm/intake.py:155``) — the same entry the router consumes at
``services/api/routers/intake.py:45``. Nothing here re-implements the seam.

**What is scored (SD-2, ruled by Cray 2026-09-01).** ``metric.direction`` is the
headline: binary, derivable from breach physics, and ``_SYSTEM_INSTRUCTION`` states
that getting it wrong *"silently disables the recommender"*
(``intake.py:88-91``) — a named system consequence. Then ``metric.threshold`` and
``recovery_value`` (exact numeric), and band-compliance (the 2-5 / 1-3 / 2-4 counts,
which live in the prompt only and are NOT schema-enforced, so they are genuine
instruction-following signal).

**What is never scored, and why the scorer refuses it structurally rather than by
convention.** ``source`` is overwritten in code at ``intake.py:186``, so scoring it
would measure ``model_copy``. ``confidence`` carries ``default=1.0``
(``intake_assembler.py:183``), so a model that omits the field is indistinguishable
from a confident one. Both are refused by ``harness.py``'s guards, not by a note
someone can overlook.

**Reporting.** Raw fractions (``7/10``), never percentages-as-headlines — the gold
set is deliberately small (SD-1). Accuracy is reported **per direction** so a model
that always answers one way shows as ``4/4`` and ``0/5``, never as a blended figure.
The ``direction_stated`` bands (SD-1a) are likewise reported separately: neither
band's figure may be cited as evidence of the other's capability.

**The gold set is not an oracle of the system until the system's own output has been
scored against it** (CLAUDE.md §8). Everything offline here checks the file against
itself; model claims close only under the live baseline run (AC-6, separately
§8-gated).
"""
