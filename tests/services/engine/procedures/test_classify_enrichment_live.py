"""PLAN-0041 Step 5 — the Cray-gated LIVE before/after twin metric (AC-7; HOST-STATE).

**SKIPPED by default.** Runs only with ``OCT_LIVE_MS_S1=1`` AND a reachable MS-S1
(``http://192.168.1.133:11434``, model ``gpt-oss:20b``). A live run is **host-state**
(CLAUDE.md §8 — get Cray's go, minimise live runs). The OFFLINE gate is binding
(``test_generator_pipeline`` for the guard byte-identity + the enriched prompt, and
``test_classify_enrichment_fixtures`` for the labelled set); THIS is confirming evidence of
the lift, not the gate (OQ-D). A red live result blocks the *value claim*, not the merge.

PRE-COMMITTED PASS/FAIL READ (recorded in this committed harness BEFORE any live run — the §8
"offline oracle is the gate" / Lesson #0026 discipline; do NOT adjust after the run)::

    N ≥ 3 reps; report the WORST run, never the best.
    PASS iff (Arm B — HARD)   every rep: all 11 AT-2-class narratives ABSTAIN on the
                              enriched ("after") prompt            (worst-rep Arm-B = 11/11)
         AND (Arm A — lift)   worst-rep gated AT-1+AT-3 (after) ≥ 9/11
         AND (Arm A — strict) worst-rep gated AT-1+AT-3 (after) > (before) on the same rep
    A single Arm-B false-accept (any rep) FAILS the PLAN regardless of the Arm-A lift.
    AT-1b is recorded (after-match / total) but NOT part of the pass/fail.

The twin metric (OQ-C), measured on the 26-narrative ``FIXTURES`` set:

* **Arm B (zero-regression, HARD):** the enriched ("after") prompt must STILL abstain on all
  11 AT-2-class narratives in EVERY rep. One false-accept fails the whole PLAN.
* **Arm A (lift):** the gated AT-1 + AT-3 match-rate (denominator 11) must STRICTLY improve
  ``after > before`` and reach ``≥ 9/11`` in the worst rep. AT-1b is reported, not gated (OQ-E).

Reference baseline: PLAN-0040's AC-B5 live finding observed the un-enriched prompt at ~7/11 on
the gated AT-1/AT-3 textbooks. The "before" arm RE-MEASURES that in the same session (same
model / seed / temperature) for a paired read — ~7/11 is the reference, not the asserted number.
The set is small (26) + hand-authored and classify is non-deterministic live, so a single 11/11
is weak evidence of a *rate*: hence N ≥ 3, worst reported, Arm A read as "X/11 → Y/11 on this
set", never a population rate.

Both arms route through the **byte-identical** deterministic guard
(``pipeline._archetype_disagreement`` + the closed-label check) imported from production — the
A/B isolates the *prompt* lever; the guard is the same on both sides. The "before" arm
reconstructs the pre-#475 (un-enriched) classify prompt; the "after" arm uses the shipped
``prompts.build_classify_messages``.

Run for evidence (Step 5), with Cray's host-state go + MS-S1 warm:

    OCT_LIVE_MS_S1=1 python -m pytest \\
        tests/services/engine/procedures/test_classify_enrichment_live.py -s -v
"""

from __future__ import annotations

import json
import os
from collections import Counter

import httpx
import pytest
from pydantic import ValidationError

from services.engine.llm.client import OllamaClient
from services.engine.llm.prompt import Message, render_untrusted_block
from services.engine.llm.structured import ChatClient
from services.engine.procedures.archetypes.template import REGISTRY
from services.engine.procedures.generator import pipeline, prompts
from services.engine.procedures.generator.schemas import (
    ABSTAIN,
    Classification,
    classification_schema,
)
from tests.services.engine.procedures.classify_enrichment_fixtures import FIXTURES, ClassifyFixture

_BASE_URL = os.environ.get("OLLAMA_HOST", "http://192.168.1.133:11434")
_MODEL = os.environ.get("RECOMMENDER_MODEL", "gpt-oss:20b")
_VERTICAL = "draft"
_REPS = max(3, int(os.environ.get("OCT_LIVE_REPS", "3")))  # N ≥ 3 (AC-7)

# the pre-committed targets (the oracle — see this module's docstring; fixed before any run)
_ARM_A_GATED_TARGET = 9  # AT-1 + AT-3 ≥ 9/11 after, in the worst rep
_ARM_B_HARD = 11  # all 11 AT-2-class narratives abstain, EVERY rep


def _ms_s1_reachable() -> bool:
    try:
        return httpx.get(f"{_BASE_URL}/api/tags", timeout=5.0).status_code == 200
    except httpx.HTTPError:
        return False


# Gate: the env flag is checked FIRST so the offline default never touches the network.
live = pytest.mark.skipif(
    os.environ.get("OCT_LIVE_MS_S1") != "1" or not _ms_s1_reachable(),
    reason="live MS-S1 smoke — set OCT_LIVE_MS_S1=1 with a reachable gpt-oss:20b (host-state §8)",
)


def _build_legacy_classify_messages(
    narrative: str, *, vertical: str, catalog: list[tuple[str, str, str]]
) -> list[Message]:
    """The PRE-#475 ("before") classify prompt — bare ``id: title`` catalog, NO per-archetype
    description and NO band explainer. Reconstructed here ONLY for the A/B baseline so the
    measured lift is attributable to the lever, not incidental prompt drift. Kept byte-faithful
    to the legacy assembly (the trusted ``_GOVERNANCE_BAR`` / ``_SECURITY`` are reused from the
    shipped module, so only the enrichment differs between the two arms)."""
    catalog_lines = "\n".join(f"- {aid}: {title}" for aid, title, _desc in catalog)
    system = (
        f"You classify an operational PROCEDURE NARRATIVE for the '{vertical}' vertical into "
        "exactly one catalogued archetype, or abstain. You SELECT from a CLOSED list — you "
        "never invent an archetype.\n\n"
        f"CATALOG (the only allowed archetype_id values, plus 'abstain'):\n{catalog_lines}\n\n"
        "Choose 'abstain' when no catalogued archetype fits — including any scoring / rule / "
        "approval-tier (DOA) shape, which is OUT OF SCOPE for v1 (abstain, never force-fit). "
        "For each step you infer, emit its gate_kind: 'none' for a read or act step, a band "
        "kind only for the single judge step. NEVER emit 'scored_rule', 'rule_gate', or "
        "'doa_tier' — if the narrative needs one, abstain instead.\n\n"
        f"{prompts._GOVERNANCE_BAR}\n\n{prompts._SECURITY}"
    )
    user = (
        "Classify the following procedure narrative. Emit the closed-enum archetype_id, the "
        "per-step gate_kind list, a short rationale, and your confidence.\n\n"
        f"{render_untrusted_block('procedure narrative', narrative)}"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


async def _route(client: ChatClient, messages: list[Message]) -> tuple[str, str]:
    """Call the live model with classify ``messages`` and apply the BYTE-IDENTICAL deterministic
    guard (``pipeline._archetype_disagreement`` + the closed-label check). Mirrors
    ``classify_narrative``'s post-call decision exactly, using the imported guard — so the A/B
    differs only in the prompt. Returns ``(route, guard_path)`` where ``route`` is the
    archetype_id or ``'abstain'`` and ``guard_path`` records WHICH path produced an abstain
    (``label_abstain`` vs ``step_disagreement``) so a silent label→backstop shift is visible."""
    result = await client.chat(messages, response_format=classification_schema())
    try:
        classification = Classification.model_validate(json.loads(result.content))
    except (json.JSONDecodeError, ValidationError):
        return ("abstain", "unparseable")
    if classification.archetype_id == ABSTAIN or classification.archetype_id not in REGISTRY:
        return ("abstain", "label_abstain")
    template = REGISTRY[classification.archetype_id]
    if pipeline._archetype_disagreement(classification, template) is not None:
        return ("abstain", "step_disagreement")
    return (classification.archetype_id, "matched")


def _gated_arm_a(fx: ClassifyFixture) -> bool:
    """Arm A's GATED denominator = the AT-1 + AT-3 textbooks (AT-1b is measured-only)."""
    return fx.arm == "A_lift" and fx.expected in {"AT-1", "AT-3"}


@live
async def test_classify_enrichment_before_after_live() -> None:
    """AC-7 twin metric on the live model — Arm B 11/11 abstain (HARD, every rep) AND Arm A
    gated lift ``after > before`` reaching ``≥ 9/11`` in the worst rep; AT-1b reported."""
    client = OllamaClient(base_url=_BASE_URL, model=_MODEL)
    catalog3: list[tuple[str, str, str]] = [
        (t.archetype_id, t.title, t.description) for t in REGISTRY.values()
    ]

    # per-rep tallies
    arm_a_before: list[int] = []
    arm_a_after: list[int] = []
    arm_b_after_abstain: list[int] = []
    arm_b_after_paths: Counter[str] = Counter()
    at1b_after_match = 0
    at1b_total = sum(1 for f in FIXTURES if f.expected == "AT-1b") * _REPS

    print(f"\n[LIVE A/B] model={_MODEL} reps={_REPS} fixtures={len(FIXTURES)}")
    for rep in range(_REPS):
        a_before = a_after = b_abstain = 0
        for fx in FIXTURES:
            before_msgs = _build_legacy_classify_messages(
                fx.narrative, vertical=_VERTICAL, catalog=catalog3
            )
            after_msgs = prompts.build_classify_messages(
                fx.narrative, vertical=_VERTICAL, catalog=catalog3
            )
            before_route, _bp = await _route(client, before_msgs)
            after_route, after_path = await _route(client, after_msgs)

            if _gated_arm_a(fx):
                a_before += int(before_route == fx.expected)
                a_after += int(after_route == fx.expected)
            elif fx.expected == "AT-1b":
                at1b_after_match += int(after_route == fx.expected)
            elif fx.arm == "B_abstain":
                b_abstain += int(after_route == "abstain")
                arm_b_after_paths[after_path] += 1
                if after_route != "abstain":
                    print(
                        f"[LIVE A/B][rep {rep}] ⚠ Arm-B FALSE-ACCEPT {fx.fixture_id} "
                        f"-> {after_route} ({'borderline' if fx.borderline else 'plain'})"
                    )

        arm_a_before.append(a_before)
        arm_a_after.append(a_after)
        arm_b_after_abstain.append(b_abstain)
        print(
            f"[LIVE A/B][rep {rep}] ArmA gated before={a_before}/11 after={a_after}/11 | "
            f"ArmB after-abstain={b_abstain}/11"
        )

    worst_a_after = min(arm_a_after)
    worst_a_idx = arm_a_after.index(worst_a_after)
    # paired_before = the before-count of the SAME rep as the worst after (a paired read on one
    # model state) — NOT the worst before across reps. This is the honest, non-cherry-pickable
    # comparison: the lift is asserted against the before measured under identical conditions.
    paired_before = arm_a_before[worst_a_idx]
    worst_b = min(arm_b_after_abstain)
    print(
        f"[LIVE A/B] WORST Arm-A after={worst_a_after}/11 (paired before={paired_before}/11) | "
        f"WORST Arm-B after-abstain={worst_b}/11 | Arm-B guard paths={dict(arm_b_after_paths)} | "
        f"AT-1b after-match={at1b_after_match}/{at1b_total} (reported, not gated)"
    )

    # Arm B (HARD, zero-regression): every rep 11/11 abstain on the enriched prompt
    assert worst_b == _ARM_B_HARD, (
        f"Arm-B regression: worst rep abstained {worst_b}/11 (need {_ARM_B_HARD}/11) — "
        "the enrichment let an AT-2-class narrative through; PLAN fails regardless of lift"
    )
    # Arm A (lift): worst-rep gated match-rate clears the bar AND strictly beats before
    assert (
        worst_a_after >= _ARM_A_GATED_TARGET
    ), f"Arm-A lift short: worst rep {worst_a_after}/11 < target {_ARM_A_GATED_TARGET}/11"
    assert (
        worst_a_after > paired_before
    ), f"Arm-A no strict lift: worst-rep after={worst_a_after} not > before={paired_before}"
