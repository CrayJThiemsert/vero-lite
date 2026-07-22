"""The cross-procedure ``step_id`` scope guard (session 160).

**What this pins.** The SoD display flag is resolved against a per-VERTICAL flat set,
not a per-procedure one. ``GovernanceStepExecutor.sod_steps`` is a bare
``frozenset[str]`` (``governance_step.py``) and both consumers test plain membership::

    sod_required = step.step_id in self.sod_steps

Each vertical's ``procedures_factory`` builds that set by unioning
``constraint.distinct_steps`` over EVERY procedure in the vertical, because the
registry contract (``services/engine/registry.py``) takes a zero-arg
``ExecutorFactory`` registered once per vertical — the factory has no procedure in
hand when it builds the set.

So the moment two procedures in one vertical share a ``step_id`` and disagree about
whether that step is SoD-constrained, the unconstrained one **silently renders as
``sod_required``**. Nothing raises: it is a display/advisory flag, not a fail-closed
gate — the contrast with ``scored_rule._KNOWN_CRITERIA``, whose violation announces
itself as a ``ScoredRuleError``.

**Why a guard and not a fix.** The procedure-aware ``ExecutorFactory`` (keying
``sod_steps``/``stamp_steps`` by ``(procedure_id, step_id)``) is the real fix, and it
is deliberately deferred — it is the open half of **PLAN-0076 Step T1 (F-FACTORY)**,
whose criterion-vocabulary half shipped as PLAN-0087. The deferral rests on the
premise that the flattening is currently INERT. Before this module, that premise was
only asserted in prose. A repo-wide search for a collision guard finds only
INTRA-procedure ``step_id`` uniqueness (``spec.py``'s duplicate-``step_id`` validator,
scoped to one ``Procedure.steps``) — nothing cross-procedure.

**The premise is thinner than the PLANs state, which is why the check is worth
having.** PLAN-0087 records "zero live ``step_id`` collisions today". Collisions
already exist: procurement ships five procedures under one file and reuses ``intake``
and ``approve`` across three of them. What is actually zero is the OVER-MARK — all
three of those procedures declare the identical ``distinct_steps: [intake, approve]``,
so the union equals each per-procedure set and the flattening cannot be observed. One
procedure that reuses ``approve`` without declaring it SoD-constrained is enough to
break it, and nothing would turn RED. Now something does.

Pure-offline (YAML reads + pydantic load; no DB, no LLM, no MS-S1 — CLAUDE.md §8).
A failure here is not a test bug: it means the deferred flattening became observable
and F-FACTORY is owed.
"""

from __future__ import annotations

from pathlib import Path

from services.engine.procedures.spec import Procedure, VerticalProcedures, load_procedures_file


def _load_all_verticals() -> list[tuple[str, VerticalProcedures]]:
    """Every shipped vertical spec, sorted. Globs only ``verticals/*`` so the
    ``.claude/worktrees`` copies can never be picked up (the sibling AT-2 census
    module takes the same precaution)."""
    loaded: list[tuple[str, VerticalProcedures]] = []
    for path in sorted(Path("verticals").glob("*/procedures.yaml")):
        vertical = path.parent.name
        loaded.append((vertical, load_procedures_file(path, vertical=vertical)))
    return loaded


def _own_sod_steps(procedure: Procedure) -> frozenset[str]:
    """The step_ids THIS procedure declares SoD-constrained — the per-procedure truth
    a procedure-aware factory would key on."""
    steps: set[str] = set()
    for constraint in procedure.separation_of_duties:
        steps |= set(constraint.distinct_steps)
    return frozenset(steps)


def _vertical_sod_union(spec: VerticalProcedures) -> frozenset[str]:
    """The flat per-vertical set the executor actually receives today — exactly what
    each ``procedures_factory`` unions together."""
    steps: set[str] = set()
    for procedure in spec.procedures:
        steps |= _own_sod_steps(procedure)
    return frozenset(steps)


def test_no_procedure_inherits_another_procedures_sod_step() -> None:
    """THE GUARD. For every step of every procedure: being in the vertical's flat
    ``sod_steps`` union must mean the step's OWN procedure declared it SoD-constrained.

    A violation is a silent over-mark — the step renders ``sod_required`` purely
    because a SIBLING procedure constrains a step of the same name.
    """
    over_marks: list[str] = []
    for vertical, spec in _load_all_verticals():
        union = _vertical_sod_union(spec)
        for procedure in spec.procedures:
            own = _own_sod_steps(procedure)
            for step in procedure.steps:
                if step.step_id in union and step.step_id not in own:
                    over_marks.append(
                        f"{vertical}/{procedure.procedure_id}: step '{step.step_id}' would "
                        f"render sod_required from the vertical-flat union, but this "
                        f"procedure declares SoD only over {sorted(own) or '[]'}"
                    )

    assert not over_marks, (
        "cross-procedure step_id collision is no longer inert — the per-vertical flat "
        "`sod_steps` set now over-marks a step its own procedure does not constrain:\n  "
        + "\n  ".join(over_marks)
        + "\n\nThis is the premise PLAN-0076 Step T1 (F-FACTORY) defers on. Do NOT paper "
        "over it by renaming the colliding step: build the procedure-aware ExecutorFactory "
        "(key sod_steps/stamp_steps by (procedure_id, step_id)) or re-adjudicate T1 with Cray."
    )


def test_collisions_already_exist_so_the_guard_is_not_vacuous() -> None:
    """Non-vacuity, pinned in code rather than argued in prose.

    The guard above passes today. It would ALSO pass if no vertical ever reused a
    step_id across procedures — which is what PLAN-0087's "zero live step_id
    collisions today" claims. That claim is wrong, and if it were right this module
    would be dead weight. Collisions do exist; only the over-mark is absent. This
    test fails if that stops being true, i.e. if the guard silently becomes vacuous.
    """
    collisions: dict[str, set[str]] = {}
    for vertical, spec in _load_all_verticals():
        seen: dict[str, int] = {}
        for procedure in spec.procedures:
            for step_id in {step.step_id for step in procedure.steps}:
                seen[step_id] = seen.get(step_id, 0) + 1
        shared = {step_id for step_id, n in seen.items() if n > 1}
        if shared:
            collisions[vertical] = shared

    assert collisions, (
        "no vertical reuses a step_id across procedures any more — the scope guard in "
        "this module is now vacuous. Either drop it deliberately, or keep it and delete "
        "this non-vacuity pin with a note saying why."
    )
    assert "intake" in collisions.get("procurement", set())
    assert "approve" in collisions.get("procurement", set())
