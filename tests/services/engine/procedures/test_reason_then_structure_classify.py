"""PLAN-0051 Step 1 — classify reason-then-structure arm plumbing (AC-1, fully offline).

The structural gate (CLAUDE.md §8, zero host-state): the three A/B arms —
``baseline`` / ``field_order_flip`` / ``two_pass`` — are wired correctly and the
deterministic abstain-guard + the closed-enum route are **byte-identical across all
three**. The arm moves ONLY the classify prompt/schema, never the guard (LOCKED-3).

The A/B *accuracy* measurement is the separate live twin-metric (Step 5, behind a Cray
host-state go); THIS proves only the plumbing, through a recorded ``ChatClient`` — no
MS-S1 call. Mirrors the recorded-fixture seam in ``test_generator_pipeline.py`` (D12).
"""

from __future__ import annotations

import json

import pytest

from services.engine.llm.client import ChatResult
from services.engine.procedures.generator.pipeline import (
    Abstained,
    ClassifyArm,
    ProposedMatch,
    classify_narrative,
)
from services.engine.procedures.generator.schemas import (
    ARCHETYPE_CHOICES,
    classification_schema,
    classification_schema_reasoning_first,
)

VERTICAL = "draft"


class _RecordingClient:
    """Replays canned JSON responses in call order and records each call's
    ``{think, has_format, response_format}`` — implements the ``ChatClient`` Protocol.
    The CHECKPOINT-0 assertion (never ``think=False`` + ``format``) is baked in, mirroring
    ``test_generator_pipeline.RecordedChatClient``. Call order per arm: two_pass = [reasoning,
    structuring]; baseline / field_order_flip = [structuring]."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self._index = 0
        self.calls: list[dict[str, object]] = []

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, object] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        assert not (
            think is False and response_format is not None
        ), "think=False + format (Ollama #15260)"
        self.calls.append(
            {
                "think": think,
                "has_format": response_format is not None,
                "response_format": response_format,
            }
        )
        if self._index >= len(self._responses):
            raise AssertionError("_RecordingClient: no more recorded responses")
        content = self._responses[self._index]
        self._index += 1
        return ChatResult(content=content, thinking=None, model="gpt-oss:20b-recorded", raw={})


def _classification_json(
    archetype_id: str,
    *,
    gates: list[tuple[str, str]] | None = None,
    rationale: str = "an anomaly then a gated action",
    confidence: float = 0.9,
) -> str:
    gates = (
        gates
        if gates is not None
        else [("read", "none"), ("judge", "in_file_band"), ("act", "none")]
    )
    return json.dumps(
        {
            "archetype_id": archetype_id,
            "step_gates": [{"step_id": s, "gate_kind": g} for s, g in gates],
            "rationale": rationale,
            "confidence": confidence,
        }
    )


def _responses_for(arm: ClassifyArm, classification: str) -> list[str]:
    """two_pass consumes a free-form reasoning response first; the single-call arms don't."""
    return ["free-form reasoning prose", classification] if arm == "two_pass" else [classification]


_ARMS: list[ClassifyArm] = ["baseline", "field_order_flip", "two_pass"]


# --- AC-1(a): the field-order-flip schema emits reasoning BEFORE the decision --------


def test_field_order_flip_schema_puts_rationale_first() -> None:
    """AC-1(a): the field_order_flip schema emits ``rationale`` (reasoning) as its FIRST
    property, BEFORE ``archetype_id`` (decision), with both marked required — the within-schema
    reasoning-before-decision variant. The decision surface is otherwise byte-identical."""
    flipped = classification_schema_reasoning_first()
    keys = list(flipped["properties"].keys())
    assert keys[0] == "rationale"
    assert keys.index("rationale") < keys.index("archetype_id")
    assert flipped["required"][:2] == ["rationale", "archetype_id"]  # reason emitted before commit
    # the decision surface is UNCHANGED: archetype_id still pinned to the closed enum
    assert flipped["properties"]["archetype_id"]["enum"] == list(ARCHETYPE_CHOICES)
    assert "AT-2" not in flipped["properties"]["archetype_id"]["enum"]
    # every property definition is preserved (only the ORDER differs from baseline)
    assert set(flipped["properties"]) == set(classification_schema()["properties"])


def test_baseline_schema_unchanged_decision_first() -> None:
    """AC-1(a) contrast: the shipped baseline schema is untouched — ``archetype_id`` (the
    decision) is still its FIRST property (the documented anti-pattern the flip addresses)."""
    base = classification_schema()
    assert next(iter(base["properties"].keys())) == "archetype_id"
    assert base["properties"]["archetype_id"]["enum"] == list(ARCHETYPE_CHOICES)


# --- AC-1(b): two_pass reasons (formatless) THEN structures (omitting think) ---------


async def test_two_pass_reasons_then_structures() -> None:
    """AC-1(b): the two_pass arm issues a free-form reasoning call (no ``format``, ``think=True``)
    BEFORE the constrained call, and the constrained call OMITS ``think`` (CHECKPOINT-0)."""
    client = _RecordingClient(_responses_for("two_pass", _classification_json("AT-1")))
    outcome = await classify_narrative(
        client, narrative="watch and act", vertical=VERTICAL, arm="two_pass"
    )
    assert isinstance(outcome, ProposedMatch)
    assert len(client.calls) == 2
    # call 1 = reasoning: NO format, think on
    assert client.calls[0]["has_format"] is False
    assert client.calls[0]["think"] is True
    # call 2 = structuring: format on, think omitted (never think=False + format)
    assert client.calls[1]["has_format"] is True
    assert client.calls[1]["think"] is None


async def test_single_call_arms_make_one_constrained_call() -> None:
    """AC-1(b) contrast: baseline + field_order_flip each make exactly ONE constrained call
    (``format`` on, ``think`` omitted) — no reasoning pass."""
    for arm in ("baseline", "field_order_flip"):
        client = _RecordingClient([_classification_json("AT-1")])
        outcome = await classify_narrative(
            client, narrative="watch and act", vertical=VERTICAL, arm=arm
        )
        assert isinstance(outcome, ProposedMatch), arm
        assert len(client.calls) == 1, arm
        assert client.calls[0]["has_format"] is True, arm
        assert client.calls[0]["think"] is None, arm


async def test_field_order_flip_arm_passes_the_reasoning_first_schema() -> None:
    """AC-1(a)/(d): the field_order_flip arm hands Ollama the reasoning-first schema (rationale
    first), while baseline hands the decision-first schema — the arm selects the variant."""
    flip_client = _RecordingClient([_classification_json("AT-1")])
    await classify_narrative(
        flip_client, narrative="watch and act", vertical=VERTICAL, arm="field_order_flip"
    )
    flip_schema = flip_client.calls[0]["response_format"]
    assert isinstance(flip_schema, dict)
    assert next(iter(flip_schema["properties"].keys())) == "rationale"

    base_client = _RecordingClient([_classification_json("AT-1")])
    await classify_narrative(
        base_client, narrative="watch and act", vertical=VERTICAL, arm="baseline"
    )
    base_schema = base_client.calls[0]["response_format"]
    assert isinstance(base_schema, dict)
    assert next(iter(base_schema["properties"].keys())) == "archetype_id"


# --- AC-1(c): the deterministic guard + route are byte-identical across arms ---------


@pytest.mark.parametrize("arm", _ARMS)
async def test_matching_classification_routes_identically(arm: ClassifyArm) -> None:
    """AC-1(c): a matching classification produces the SAME ProposedMatch (AT-1) in every arm —
    the arm moves only the prompt/schema, never the guard/route (LOCKED-3)."""
    client = _RecordingClient(_responses_for(arm, _classification_json("AT-1")))
    outcome = await classify_narrative(
        client, narrative="watch and act", vertical=VERTICAL, arm=arm
    )
    assert isinstance(outcome, ProposedMatch)
    assert outcome.template.archetype_id == "AT-1"


@pytest.mark.parametrize("arm", _ARMS)
@pytest.mark.parametrize("at2_kind", ["scored_rule", "rule_gate", "doa_tier"])
async def test_at2_only_disagreement_abstains_identically(arm: ClassifyArm, at2_kind: str) -> None:
    """AC-1(c): the AT-2-only abstain-gate fires identically in every arm — the moat brake
    (LOCKED-3) is not weakened by the reasoning-order lever. An AT-2-only kind on the judge
    step disagrees with the AT-1 oracle → abstain, never a down-classified skeleton."""
    gates = [("read", "none"), ("judge", at2_kind), ("act", "none")]
    client = _RecordingClient(_responses_for(arm, _classification_json("AT-1", gates=gates)))
    outcome = await classify_narrative(
        client, narrative="score and gate it", vertical=VERTICAL, arm=arm
    )
    assert isinstance(outcome, Abstained)
    assert outcome.reason == "archetype_disagreement"


@pytest.mark.parametrize("arm", _ARMS)
async def test_abstain_label_routes_identically(arm: ClassifyArm) -> None:
    """AC-1(c): an explicit 'abstain' label routes to hand-author (no_archetype_match) in
    every arm — the closed-enum route is arm-independent."""
    client = _RecordingClient(_responses_for(arm, _classification_json("abstain")))
    outcome = await classify_narrative(
        client, narrative="score suppliers by DOA tier", vertical=VERTICAL, arm=arm
    )
    assert isinstance(outcome, Abstained)
    assert outcome.reason == "no_archetype_match"


@pytest.mark.parametrize("arm", _ARMS)
async def test_route_is_independent_of_confidence_in_every_arm(arm: ClassifyArm) -> None:
    """AC-1(c) / ADR-010 IN-3: the determinism invariant holds in EVERY arm — two
    classifications identical except confidence take the same route. The reasoning-order lever
    does not smuggle confidence into a routing branch."""
    high = _RecordingClient(_responses_for(arm, _classification_json("AT-1", confidence=0.95)))
    low = _RecordingClient(_responses_for(arm, _classification_json("AT-1", confidence=0.05)))
    out_high = await classify_narrative(high, narrative="watch and act", vertical=VERTICAL, arm=arm)
    out_low = await classify_narrative(low, narrative="watch and act", vertical=VERTICAL, arm=arm)
    assert isinstance(out_high, ProposedMatch) and isinstance(out_low, ProposedMatch)
    assert out_high.template.archetype_id == out_low.template.archetype_id == "AT-1"


# --- AC-1 / LOCKED-4 (R1): the shipped default is baseline ---------------------------


async def test_default_arm_is_baseline_and_byte_identical() -> None:
    """AC-1 / LOCKED-4 (R1): calling classify_narrative WITHOUT an arm makes exactly one
    constrained call with the decision-first baseline schema — byte-identical to the shipped
    path, so no shipped call site changes behaviour."""
    client = _RecordingClient([_classification_json("AT-1")])
    outcome = await classify_narrative(client, narrative="watch and act", vertical=VERTICAL)
    assert isinstance(outcome, ProposedMatch)
    assert len(client.calls) == 1
    assert client.calls[0]["has_format"] is True
    assert client.calls[0]["think"] is None
    schema = client.calls[0]["response_format"]
    assert isinstance(schema, dict)
    assert next(iter(schema["properties"].keys())) == "archetype_id"  # baseline, not flipped
