"""PLAN-0048 Step 1 — the compile seam: ``plan_read`` + ``ReadRefusal`` +
``readable_object_types`` (AC-1..AC-3).

ORACLE-FIRST DISCIPLINE (AC-2 / Lesson #0026, mirroring PLAN-0046 AC-5 and the
house block above the read-gate tests in ``test_orchestrator.py``): the pass/fail
matrix below is COMMITTED BEFORE any test or implementation code exists, so the
refusal contract cannot be quietly bent to whatever the implementation happens
to do. The tests in this module must implement EXACTLY this matrix; deviations
are surfaced, never silently absorbed.
"""

# ---------------------------------------------------------------------------
# PRE-COMMITTED PASS/FAIL MATRIX (PLAN-0048 AC-1/AC-2/AC-3; SD-1..SD-5 ratified
# as-recommended 2026-07-04 — single-read only, scope fixed).
# Fixture registry: object_type_names = {Pond, Reading}; step_id = "read".
#
# COMPILE (returns ReadPlan; AC-1):
#   COMPILE-1  reads=["Pond"], allowlist=["Pond"]          -> ReadPlan(step_id="read",
#              object_type="Pond", where={})   (in ontology ∩ allowlist)
#   COMPILE-2  reads=["Pond"], where={"verdict": "breach"} -> ReadPlan.where ==
#              {"verdict": "breach"}            (the where mapping is carried)
#   COMPILE-3  reads=["Pond"], allowlist=[]                -> compiles (LOCKED-5 /
#              OQ-6: empty object_types = UNCONSTRAINED, mirrors the load gate)
#
# REFUSE (raises ReadRefusal with STRUCTURED fields — refusal_kind + step_id
# (+ object_type where applicable); AC-2, the five ratified shapes):
#   REFUSE-1   reads=["Ghost"] (∉ ontology)                -> unknown_object_type,
#              object_type="Ghost", step_id="read"
#   REFUSE-2   reads=["Pond"], allowlist=["Reading"]       -> outside_allowlist,
#              object_type="Pond", step_id="read"
#   REFUSE-3   reads=["Pond", "Reading"] (len > 1)         -> unsupported_read_shape
#              (SD-1 ratified: single-read only; joins await a join grammar)
#   REFUSE-4   reads=["Pond"] + from="prior"               -> unsupported_read_shape
#              (two competing input sources = ambiguous; where would double-apply)
#   REFUSE-5   reads absent + from absent (entry-point)    -> unbound_query
#              (a silent [] here is exactly the must-1-banned empty masquerade)
#
# GUARDS beyond the ratified minimum (AC-1 totality — plan_read never returns
# garbage for ANY Step shape; labeled as guards, not matrix rows):
#   GUARD-1    reads absent + from="prior"                 -> unsupported_read_shape
#              (no DECLARED read to compile; SD-1 locates identity pass-through
#              in the Step-2 executor, which does not consult plan_read for it)
#   GUARD-2    step.kind != QUERY                          -> unsupported_read_shape
#              (the compile seam is a query-step contract; library callers get a
#              typed refusal, not a nonsense plan)
#
# INSPECT (readable_object_types; D-N3):
#   INSPECT-1  allowlist=[]                 -> the whole ontology set (LOCKED-5)
#   INSPECT-2  allowlist=["Pond"]           -> {"Pond"}   (ontology ∩ allowlist)
#   INSPECT-3  allowlist=["Pond", "Ghost"]  -> {"Pond"}   (unknown types drop out)
#
# TRIPWIRE (AC-3 — one bound, zero drift): the same fixture matrix driven
# through BOTH the load gate (validate_read_bindings) and plan_read must yield
# IDENTICAL accept/refuse decisions for the bound shapes:
#   in-ontology + in-allowlist -> both accept
#   unknown object_type        -> both refuse (gate: ProcedureError "does not
#                                 exist in the vertical's ontology"; seam:
#                                 unknown_object_type)
#   outside non-empty allowlist-> both refuse (gate: "is outside agent";
#                                 seam: outside_allowlist)
#   empty allowlist            -> both accept (unconstrained)
# The gate's ProcedureError messages stay BYTE-IDENTICAL to the pre-refactor
# wording (the PLAN-0046 tests in test_orchestrator.py are untouched and green).
# ---------------------------------------------------------------------------
