"""PLAN-0051 Step 5 — classify reason-then-structure A/B: the Cray-gated LIVE twin metric
(AC-6; HOST-STATE).

**SKIPPED by default.** Runs only with ``OCT_LIVE_MS_S1=1`` AND a reachable MS-S1
(``http://192.168.1.133:11434``, model ``gpt-oss:20b``). A live run is **host-state**
(CLAUDE.md §8 — get Cray's go, minimise live runs). The OFFLINE gate is binding (AC-1 arm
plumbing + AC-2 corpus driver in ``test_reason_then_structure_classify``); THIS is confirming
evidence of the reasoning-order lift, not the gate — a red live result blocks the *value
claim*, not the merge (LOCKED-5 / OQ-D).

PRE-COMMITTED READS (recorded in this committed harness BEFORE any live run — the §8 "offline
oracle is the gate" / Lesson #0026 discipline; NOT adjusted after the run)::

    3 arms {baseline, field_order_flip, two_pass}; N >= 3 reps; report the WORST rep per arm.

    (1) SAFETY (HARD assert): every arm, every rep, all 11 AT-2-class narratives ABSTAIN
        (Arm-B = 11/11). The reasoning-order lever must NOT weaken the moat brake — a single
        Arm-B false-accept in ANY arm FAILS this test (a real regression, not a null result).

    (2) LIFT (measured + printed VERDICT, NOT assert-failed): a variant arm WINS iff its worst-rep
        gated AT-1+AT-3 match (denominator 11) both (a) reaches the absolute floor >= 9/11 AND
        (b) strictly exceeds the baseline arm's worst-rep gated match. A null result (no lift) is a
        VALID experimental finding for Step 6 — this experiment MEASURES whether reasoning-order
        helps; it does not assume it does (unlike PLAN-0041, which regression-tested a known fix).

Both the safety brake and the lift route through the BYTE-IDENTICAL production guard: the A/B
goes through ``classify_ab_route`` -> ``classify_narrative(arm=...)``, so the arm changes only
the classify prompt/schema, never the deterministic abstain-guard (LOCKED-3).

Run for evidence (Step 5b), with Cray's host-state go + MS-S1 warm::

    OCT_LIVE_MS_S1=1 python -m pytest \\
        tests/services/engine/procedures/test_reason_then_structure_classify_live.py -s -v
"""

from __future__ import annotations

import os

import httpx
import pytest

from services.engine.llm.client import OllamaClient
from services.engine.procedures.generator.pipeline import ClassifyArm
from tests.services.engine.procedures.classify_enrichment_fixtures import FIXTURES, ClassifyFixture
from tests.services.engine.procedures.reason_then_structure_ab import classify_ab_route

_BASE_URL = os.environ.get("OLLAMA_HOST", "http://192.168.1.133:11434")
_MODEL = os.environ.get("RECOMMENDER_MODEL", "gpt-oss:20b")
_VERTICAL = "draft"
_REPS = max(3, int(os.environ.get("OCT_LIVE_REPS", "3")))  # N >= 3 (AC-6)
_ARMS: list[ClassifyArm] = ["baseline", "field_order_flip", "two_pass"]
_VARIANTS: list[ClassifyArm] = ["field_order_flip", "two_pass"]  # measured against baseline

# the pre-committed reads (the oracle — see this module's docstring; fixed before any run)
_ARM_B_HARD = 11  # all 11 AT-2-class narratives abstain, EVERY arm, EVERY rep (safety)
_ARM_A_ABSOLUTE_FLOOR = 9  # a winning variant's worst-rep gated AT-1+AT-3 must reach >= 9/11


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


def _is_gated_arm_a(fx: ClassifyFixture) -> bool:
    """Arm A's GATED denominator = the AT-1 + AT-3 textbooks (AT-1b is measured-only, OQ-E)."""
    return fx.arm == "A_lift" and fx.expected in {"AT-1", "AT-3"}


@live
async def test_classify_reason_then_structure_ab_live() -> None:
    """AC-6: the 3-arm classify A/B on the live model. HARD-asserts the Arm-B safety brake in
    every arm/rep; measures + prints the per-variant Arm-A lift VERDICT vs baseline (worst rep)."""
    client = OllamaClient(base_url=_BASE_URL, model=_MODEL)
    per_arm_a: dict[str, list[int]] = {arm: [] for arm in _ARMS}
    per_arm_b: dict[str, list[int]] = {arm: [] for arm in _ARMS}

    print(
        f"\n[LIVE classify A/B] model={_MODEL} reps={_REPS} arms={_ARMS} fixtures={len(FIXTURES)}"
    )
    for rep in range(_REPS):
        for arm in _ARMS:
            a_match = b_abstain = 0
            for fx in FIXTURES:
                route, _path = await classify_ab_route(
                    client, fx.narrative, vertical=_VERTICAL, arm=arm
                )
                if _is_gated_arm_a(fx):
                    a_match += int(route == fx.expected)
                elif fx.arm == "B_abstain":
                    b_abstain += int(route == "abstain")
                    if route != "abstain":
                        print(f"[rep {rep}][{arm}] ⚠ Arm-B FALSE-ACCEPT {fx.fixture_id} -> {route}")
            per_arm_a[arm].append(a_match)
            per_arm_b[arm].append(b_abstain)
            print(f"[rep {rep}][{arm}] ArmA gated={a_match}/11  ArmB abstain={b_abstain}/11")

    worst_a = {arm: min(per_arm_a[arm]) for arm in _ARMS}
    worst_b = {arm: min(per_arm_b[arm]) for arm in _ARMS}
    base_a = worst_a["baseline"]

    print("\n=== VERDICT (pre-committed reads; worst rep per arm) ===")
    for arm in _ARMS:
        print(f"  {arm:16s} ArmA gated={worst_a[arm]}/11  ArmB abstain={worst_b[arm]}/11")
    for variant in _VARIANTS:
        lift = worst_a[variant] - base_a
        win = (
            lift >= 1
            and worst_a[variant] >= _ARM_A_ABSOLUTE_FLOOR
            and worst_b[variant] == _ARM_B_HARD
        )
        print(
            f"  VERDICT {variant}: ArmA lift vs baseline = {lift:+d} "
            f"(worst {worst_a[variant]}/11 vs {base_a}/11) -> {'WIN' if win else 'no-lift'}"
        )

    # (1) SAFETY (HARD): Arm-B 11/11 in EVERY arm, EVERY rep — the moat brake holds under the lever
    for arm in _ARMS:
        assert worst_b[arm] == _ARM_B_HARD, (
            f"Arm-B regression in arm '{arm}': worst rep abstained {worst_b[arm]}/11 "
            f"(need {_ARM_B_HARD}/11) — the lever let an AT-2-class narrative through"
        )
    # (2) LIFT is a measured VERDICT (printed above), NOT an assertion: a no-lift is a valid Step-6
    # finding. This experiment measures whether reasoning-order helps; it does not assume it.
