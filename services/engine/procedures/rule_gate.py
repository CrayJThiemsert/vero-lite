"""The deterministic ``rule_gate`` compliance enforcement (ADR-0025 D2/D3; PLAN-0044 A1b Step 4).

The RUN-side enforcement of the author-time :class:`~services.engine.procedures.spec.ComplianceGate`
(the typed AT-2 ``rule_gate`` content): given the per-criterion compliance signal a candidate
carries (data-access = (a) — intake enriches the requisition with the supplier's compliance status,
mirroring the ``scored_rule`` candidate-quote enrichment, Cray-confirmed session 91), evaluate every
authored :class:`~services.engine.procedures.spec.ComplianceRule` and **block the PO on ANY failed
criterion** — the candidate is tagged non-``compliant`` so the downstream ``approve`` fan-out
(``where: {compliant: true}``) drops it. Compliance is **non-waivable by type**: ``blocks_po`` is
``Literal[True]`` (a non-blocking compliance rule is unrepresentable, ADR-0025 D3) and this executor
has **no pass-a-failed-rule path** — there is no ``waive`` argument, no override flag.

Pure + deterministic: no LLM, no DB, no network — the offline tests are the gate (CLAUDE.md §8).
The LLM does NOT evaluate the rule (governed ≠ generated, ADR-0019 IN-3); the gate is this pure
function.

**What is enforced vs deferred (the A1b/A2 boundary).** A :class:`ComplianceRule` carries a
human-authored ``spec`` predicate (e.g. ``"supplier.tax_id present and valid"``) that is *rendered
read-only in v1; evaluated on the deferred A2 run path* (ADR-0025 D2, the ``spec`` field doc). So v1
does **not** parse / evaluate the prose predicate — it reads a structured per-criterion PASS/FAIL
signal off the candidate (the ``compliance`` map an upstream classify step produces) and enforces
the **gate**: block on any fail. The gate (block-the-PO-on-any-fail, non-waivable) is what A1b run
enforcement adds; evaluating an arbitrary predicate from raw supplier fields stays A2.

**Fail CLOSED.** A candidate that is not a mapping, or carries no ``compliance`` signal map at all,
raises :class:`RuleGateError` (the intake enrichment contract was not met — a data/config error, not
a candidate outcome). A criterion whose signal is **absent OR false within a present map** FAILS
(soft-blocks that candidate): an unverifiable blocking-compliance criterion cannot be waved through.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from services.engine.procedures.orchestrator import ProcedureError
from services.engine.procedures.spec import ComplianceGate

COMPLIANCE_FIELD = "compliance"
"""The candidate entity field carrying the per-criterion compliance signal map
(``{criterion: bool}``) — the intake enrichment convention (data-access = (a)), mirroring the
``scored_rule`` ``candidate_quotes`` field."""


class RuleGateError(ProcedureError):
    """A ``rule_gate`` step failed CLOSED (PLAN-0044 A1b Step 4).

    Raised when a candidate is not a mapping or carries no :data:`COMPLIANCE_FIELD` signal map —
    the intake enrichment contract was not met, so the gate cannot be evaluated (a data/config
    error, distinct from a candidate simply failing a criterion). Failing closed blocks the
    candidate BEFORE any downstream approval — compliance is never silently assumed."""


def _signal_true(value: Any) -> bool:
    """Coerce a per-criterion compliance signal to ``bool`` — robust to the CSV/JSON string form
    (``"false"`` / ``"true"``): ``bool("false")`` is ``True`` in Python, which would silently pass a
    non-compliant criterion. A string is truthy only for an explicit truthy token; an ABSENT signal
    (``None``) is falsy (fail closed — an unverifiable blocking criterion cannot pass)."""
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "on", "pass", "passed"}
    return bool(value)


@dataclass(frozen=True)
class RuleResult:
    """One evaluated compliance rule — the stable-keyed per-criterion outcome (render / audit).

    ``spec`` is the human-authored predicate carried through for the read-only render / audit;
    it is NON-AUTHORITATIVE display text, never re-evaluated here (the prose predicate's evaluation
    is the deferred A2 run path, ADR-0025 D2). The authoritative outcome is ``passed``."""

    criterion: str
    passed: bool
    spec: str

    def to_audit(self) -> dict[str, Any]:
        """JSON-safe projection for the step audit / output_set (JSONB)."""
        return {"criterion": self.criterion, "passed": self.passed, "spec": self.spec}


@dataclass(frozen=True)
class ComplianceVerdict:
    """The structured, stable-keyed ``rule_gate`` outcome (PLAN-0044 A1b Step 4).

    ``compliant`` is the gate verdict (``True`` only if EVERY rule passed — the PO is blocked on
    ANY fail, ADR-0025 D3). ``failed_criteria`` names the criteria that blocked (so a read-only
    render can show WHY the candidate was blocked); ``results`` is every rule's per-criterion
    outcome (in authored order)."""

    compliant: bool
    results: list[RuleResult]
    failed_criteria: list[str]

    def to_audit(self) -> dict[str, Any]:
        """JSON-safe projection for the step audit / output_set (JSONB)."""
        return {
            "compliant": self.compliant,
            "failed_criteria": list(self.failed_criteria),
            "results": [r.to_audit() for r in self.results],
        }


def evaluate_compliance(gate: ComplianceGate, candidate: Mapping[str, Any]) -> ComplianceVerdict:
    """Evaluate ``candidate`` against every rule in ``gate``, blocking on ANY fail (PLAN-0044 A1b
    Step 4). See the module docstring for the enforced-vs-deferred boundary.

    Reads the candidate's :data:`COMPLIANCE_FIELD` signal map and, per authored
    :class:`ComplianceRule`, marks the criterion ``passed`` iff its signal is an explicit truthy
    token — an absent or false signal FAILS. The verdict is ``compliant`` only if every rule
    passed; there is no waive path (compliance is non-waivable by type, ``blocks_po`` is
    ``Literal[True]``). Fails CLOSED (:class:`RuleGateError`) if ``candidate`` carries no signal
    map. Deterministic: same inputs → same verdict; the LLM is not consulted.
    """
    if not isinstance(candidate, Mapping):
        raise RuleGateError(
            f"rule_gate: candidate {candidate!r} is not a mapping — cannot read its "
            f"'{COMPLIANCE_FIELD}' signal map (fail closed)"
        )
    if COMPLIANCE_FIELD not in candidate:
        raise RuleGateError(
            f"rule_gate: candidate {candidate.get('primary_key', '?')!r} carries no "
            f"'{COMPLIANCE_FIELD}' signal map — the compliance gate cannot be evaluated (intake "
            "enriches the candidate with per-criterion compliance status, PLAN-0044 A1b Step 4 "
            "data-access = (a)); fail closed"
        )
    signals = candidate[COMPLIANCE_FIELD]
    if not isinstance(signals, Mapping):
        raise RuleGateError(
            f"rule_gate: '{COMPLIANCE_FIELD}' must be a criterion->signal map, got "
            f"{type(signals).__name__} — fail closed"
        )
    results = [
        RuleResult(
            criterion=rule.criterion.value,
            passed=_signal_true(signals.get(rule.criterion.value)),
            spec=rule.spec,
        )
        for rule in gate.rules
    ]
    failed = [r.criterion for r in results if not r.passed]
    return ComplianceVerdict(compliant=not failed, results=results, failed_criteria=failed)
