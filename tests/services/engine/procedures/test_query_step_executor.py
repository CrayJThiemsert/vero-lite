"""PLAN-0048 Step 2 — the execute half: ``QueryStepExecutor`` + the structured
refusal divert (AC-4..AC-9).

ORACLE-FIRST DISCIPLINE (AC-7 / Lesson #0026, mirroring the Step-1 oracle in
``test_query_step.py``): the pass/fail matrix below is COMMITTED BEFORE any
executor or test code exists. The tests in this module must implement EXACTLY
this matrix; deviations are surfaced, never silently absorbed.
"""

# ---------------------------------------------------------------------------
# PRE-COMMITTED PASS/FAIL MATRIX (PLAN-0048 AC-4..AC-9; SD-1..SD-5 ratified
# as-recommended 2026-07-04). Counting fake adapter records every
# fetch_objects(object_type, filter_expr) call. Fixture ontology =
# {Pond, Reading}; step_id = "read".
#
# EXECUTE (AC-4 — declared==dispatched, positively):
#   EXEC-1   reads=["Pond"], adapter has 3 Pond rows          -> dispatches
#            fetch_objects("Pond") EXACTLY; output == the 3 rows; trace carries
#            ONE read-provenance entry {kind: "read_provenance",
#            object_type: "Pond", fetched_count: 3, post_where_count: 3}
#   EXEC-2   reads=["Pond"], where={"status": "active"}, rows 2-active/1-not
#            -> output == the 2 active rows (post-fetch narrowing via the
#            SHARED matches_where predicate — LOCKED-3); provenance
#            fetched_count: 3, post_where_count: 2
#   EXEC-3   filter_expr is None on EVERY dispatch (LOCKED-3 — the engine keeps
#            the narrowing; nothing is pushed down to the adapter)
#
# ADVERSARIAL declared==dispatched (AC-5 — property over a matrix):
#   PROP-1   matrix varying reads/where/allowlist/adapter contents (incl. an
#            adapter whose store also holds rows of OTHER object_types):
#            adapter.calls == [declared object_type] — never one more, never a
#            substitute, and never the other types present in the store
#
# BOUNDED DISPATCH (AC-6):
#   BOUND-1  exactly ONE fetch_objects call per execute() (len(calls) == 1)
#   BOUND-2  an adapter that RAISES propagates the exception with NO re-fetch
#            (len(calls) == 1 after the raise — no retry loop exists)
#
# REFUSAL vs NO-DATA (AC-7 — the pre-committed read):
#   REF-1    out-of-coverage read (reads=["Ghost"]) RAISES ReadRefusal
#            (unknown_object_type) BEFORE any dispatch (len(calls) == 0)
#   REF-2    in-coverage read whose fetch yields ZERO post-where rows COMPLETES
#            with output == [] + provenance trace (fetched_count/post_where_count
#            recorded) — refusal and no-data are distinguishable from the
#            recorded StepResult alone: a refusal has NO completed StepResult
#            with output (it diverts via D4); no-data has a COMPLETED StepResult
#            with artifact output_set == [] and a read_provenance trace entry
#
# PASS-THROUGH (SD-1 — the executor's case, NOT plan_read's):
#   PASS-1   reads absent + from present -> execute() returns the
#            orchestrator-resolved input_set IDENTITY (no dispatch,
#            len(calls) == 0) + a read_passthrough trace entry
#
# D4 STRUCTURED DIVERT (AC-8 — run_procedure level):
#   D4-1     an entry-point query step with NO reads under the generic executor
#            + on_failure: escalate_to_human -> the run lands waiting_human and
#            the step's reasoning_trace carries a STRUCTURED entry
#            {kind: "read_refused", refusal_kind: "unbound_query",
#            step_id: "read", object_type: None} (no ontology I/O needed —
#            the load gate skips reads-absent procedures, so this exercises the
#            runtime refusal path in isolation)
#   D4-2     a multi-read step (BOTH types in ontology + allowlist, so the LOAD
#            GATE ACCEPTS it) refuses AT RUN TIME (SD-1 shape refusal is
#            runtime-only in v1) -> waiting_human + read_refused trace entry
#            with refusal_kind: "unsupported_read_shape"
#   D4-3     every NON-refusal exception keeps the byte-identical legacy trace
#            entry {kind: "error", summary: f"{type}: {exc}"} — asserted by an
#            executor raising RuntimeError through the same run path
#
# NO-REGRESSION (AC-9):
#   REG-1    no existing test file is modified by this step; the full
#            procedures suite (orchestrator D4 cases included) stays green;
#            hero_demo/run.py is byte-unchanged (asserted by the suite itself —
#            no new test needed, recorded here for the record)
# ---------------------------------------------------------------------------
