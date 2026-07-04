"""PLAN-0051 Step 5 — nl_query reason-then-structure A/B: the Cray-gated LIVE metric
(AC-7; HOST-STATE).

**SKIPPED by default.** Runs only with ``OCT_LIVE_MS_S1=1`` AND a reachable MS-S1
(``http://192.168.1.133:11434``, model ``gpt-oss:20b``). A live run is **host-state**
(CLAUDE.md §8 — get Cray's go, minimise live runs). The OFFLINE gate is binding (AC-3 corpus
validators + AC-4 arm plumbing); THIS is confirming evidence, not the gate (LOCKED-5).

PRE-COMMITTED READS (recorded here + in ``nl_query_ab_fixtures`` BEFORE any live run — §8 /
Lesson #0026; NOT adjusted after the run)::

    3 arms {baseline, field_order_flip, two_pass}; N >= 3 reps; report the WORST rep per arm.
    Each fixture is scored by ``score_query`` on the RAW ``_translate`` output (SD-1); a query
    that never validates scores 0.0 (the model failed — honest, not skipped).

    A variant arm WINS iff (both):
      (a) REGRESSION FLOOR — its worst-rep mean score over the whole corpus is
          >= baseline's worst-rep mean minus ``REGRESSION_FLOOR_TOLERANCE`` (no material
          overall regression); AND
      (b) HARD-CLASS WIN — its worst-rep mean on the ``hard_class`` aggregate-superlative subset
          exceeds baseline's by at least ``HARD_CLASS_WIN_MIN_DELTA`` (the lever's whole purpose is
          retaining group_by + measured_kind on 'which X is most Y').

    The WIN/no-lift verdict is measured + PRINTED (NOT assert-failed) — a null result is a VALID
    Step-6 finding. The only HARD assertion is that the run produced valid measurements ([0,1]).
    Read as "X -> Y on this 27-question corpus", never a population rate (small hand-authored set,
    non-deterministic live model).

Run for evidence (Step 5b), with Cray's host-state go + MS-S1 warm::

    OCT_LIVE_MS_S1=1 python -m pytest \\
        tests/services/engine/test_reason_then_structure_nl_query_live.py -s -v

LIVE RESULT (2026-07-05, gpt-oss:20b, N=3, worst rep): mean baseline 0.978, field_order_flip
0.965, two_pass 0.978; hard-class 0.844 all arms (delta +0.000) — NO LIFT. Recommendation:
REJECT both variants, keep baseline. Full record: docs/logs/2026-07-05-plan0051-live-ab-results.md.
"""

from __future__ import annotations

import os
from statistics import mean

import httpx
import pytest

from services.engine.llm.client import OllamaClient
from services.engine.nl_query import QueryTranslationError, StructuredQuery, TranslateArm
from tests.services.engine.nl_query_ab_fixtures import (
    FIXTURES,
    HARD_CLASS_WIN_MIN_DELTA,
    LIVE_MIN_REPS,
    REGRESSION_FLOOR_TOLERANCE,
    score_query,
)
from tests.services.engine.reason_then_structure_nl_query_ab import translate_ab_query

_BASE_URL = os.environ.get("OLLAMA_HOST", "http://192.168.1.133:11434")
_MODEL = os.environ.get("RECOMMENDER_MODEL", "gpt-oss:20b")
_VERTICAL = "energy"
_REPS = max(LIVE_MIN_REPS, int(os.environ.get("OCT_LIVE_REPS", str(LIVE_MIN_REPS))))
_ARMS: list[TranslateArm] = ["baseline", "field_order_flip", "two_pass"]
_VARIANTS: list[TranslateArm] = ["field_order_flip", "two_pass"]  # measured against baseline


def _ms_s1_reachable() -> bool:
    try:
        return httpx.get(f"{_BASE_URL}/api/tags", timeout=5.0).status_code == 200
    except httpx.HTTPError:
        return False


live = pytest.mark.skipif(
    os.environ.get("OCT_LIVE_MS_S1") != "1" or not _ms_s1_reachable(),
    reason="live MS-S1 smoke — set OCT_LIVE_MS_S1=1 with a reachable gpt-oss:20b (host-state §8)",
)


async def _score_one(
    client: OllamaClient, question: str, gold: StructuredQuery, arm: TranslateArm
) -> float:
    """Translate one question for ``arm`` and score the RAW output; a never-valid query scores 0."""
    try:
        query = await translate_ab_query(client, question, vertical=_VERTICAL, arm=arm)
    except QueryTranslationError:
        return 0.0
    return score_query(gold, query)


@live
async def test_nl_query_reason_then_structure_ab_live() -> None:
    """AC-7: the 3-arm nl_query A/B on the live model. Measures + prints the per-variant SD-4
    verdict (regression floor + hard-class win) vs baseline; HARD-asserts only valid measurement."""
    client = OllamaClient(base_url=_BASE_URL, model=_MODEL)
    hard = [f for f in FIXTURES if f.hard_class]
    per_arm_all: dict[str, list[float]] = {arm: [] for arm in _ARMS}
    per_arm_hard: dict[str, list[float]] = {arm: [] for arm in _ARMS}

    print(
        f"\n[LIVE nl_query A/B] model={_MODEL} reps={_REPS} arms={_ARMS} fixtures={len(FIXTURES)}"
    )
    for rep in range(_REPS):
        for arm in _ARMS:
            scores = {
                fx.fixture_id: await _score_one(client, fx.question, fx.gold, arm)
                for fx in FIXTURES
            }
            mean_all = mean(scores.values())
            mean_hard = mean(scores[fx.fixture_id] for fx in hard)
            per_arm_all[arm].append(mean_all)
            per_arm_hard[arm].append(mean_hard)
            print(f"[rep {rep}][{arm}] mean={mean_all:.3f}  hard-class mean={mean_hard:.3f}")

    worst_all = {arm: min(per_arm_all[arm]) for arm in _ARMS}
    worst_hard = {arm: min(per_arm_hard[arm]) for arm in _ARMS}
    base_all, base_hard = worst_all["baseline"], worst_hard["baseline"]

    print("\n=== VERDICT (pre-committed SD-4 reads; worst rep per arm) ===")
    for arm in _ARMS:
        print(f"  {arm:16s} mean={worst_all[arm]:.3f}  hard-class={worst_hard[arm]:.3f}")
    for variant in _VARIANTS:
        floor_ok = worst_all[variant] >= base_all - REGRESSION_FLOOR_TOLERANCE
        hard_delta = worst_hard[variant] - base_hard
        win = floor_ok and hard_delta >= HARD_CLASS_WIN_MIN_DELTA
        print(
            f"  VERDICT {variant}: mean {worst_all[variant]:.3f} vs {base_all:.3f} "
            f"(floor {'OK' if floor_ok else 'REGRESSION'}); hard-class delta {hard_delta:+.3f} "
            f"-> {'WIN' if win else 'no-lift'}"
        )

    # HARD assertion: the run produced valid measurements only (a null lift is a Step-6 finding,
    # not a failure — the experiment measures whether the lever helps, it does not assume it).
    for arm in _ARMS:
        assert 0.0 <= worst_all[arm] <= 1.0
        assert 0.0 <= worst_hard[arm] <= 1.0
