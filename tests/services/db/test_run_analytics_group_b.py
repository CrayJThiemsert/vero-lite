"""AC-10 — the Group-B carrier proof (PLAN-0088 Step 6).

Poses each of the four Group-B questions **as a query** over the seeded corpus,
through the substrate's public surface only, asserting the exact values the
factory computed independently in plain Python:

* **B1** band recalibration fuel — the distribution of a measured value against
  its band verdict (``verdict_reading_stats``).
* **B2** DoA/approval-chain calibration fuel — approval outcome + gate dwell
  grouped by resolved DoA tier (``gate_tier_outcomes``).
* **B3** refusal-mining fuel — refusal counts by kind x procedure
  (``refusal_counts_by_procedure``).
* **B4** procedure-generation fuel — run frequency by procedure x trigger x
  terminal status (``trigger_outcome_counts``).

What this suite proves, paired with AC-11's static converse, is that the
*questions* are expressible while the improvement *loop* stays unbuilt: nothing
here derives a proposal, and AC-11 proves no proposal machinery exists to derive
one with.

**Half of this file is non-degeneracy tests, and they are the load-bearing half.**
An exact-value assertion over a corpus whose dimensions are collinear passes
whether or not the query carries those dimensions — the s170 mutation probe found
exactly that failure (deleting the approver FILTER left both value oracles green,
because every resolved gate happened to carry an approver). B3's kind was a
BIJECTION of the procedure when this step opened. So each Group-B dimension is
pinned here as a property of the corpus itself: if a future edit re-collapses one,
these fail loudly rather than letting the value oracle go quietly vacuous.
"""

from __future__ import annotations

import statistics
from collections.abc import AsyncIterator
from dataclasses import dataclass
from itertools import pairwise

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.db import run_analytics as ra
from services.db.base import Base
from tests.db_support import create_test_engine
from tests.support.run_corpus_factory import Corpus, build_corpus

_SEED = 1234
_N_RUNS = 250


@dataclass
class _Seeded:
    session: AsyncSession
    corpus: Corpus


@pytest.fixture
async def seeded() -> AsyncIterator[_Seeded]:
    corpus = build_corpus(seed=_SEED, n_runs=_N_RUNS)
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(eng, expire_on_commit=False)
    async with maker() as seed_session:
        seed_session.add_all(corpus.rows)
        await seed_session.commit()
    async with maker() as session:
        yield _Seeded(session=session, corpus=corpus)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


# --------------------------------------------------------------------------
# B1 — band recalibration fuel
# --------------------------------------------------------------------------


async def test_b1_verdict_reading_distribution_exact(seeded: _Seeded) -> None:
    """Every verdict's entity count, reading stats and missing-reading count are exact."""
    rows = await ra.verdict_reading_stats(seeded.session)
    expected = seeded.corpus.verdict_readings
    assert {row.verdict for row in rows} == set(expected)
    for row in rows:
        want = expected[str(row.verdict)]
        readings: list[int] = want["readings"]
        assert row.entity_count == want["entity_count"]
        assert row.reading_count == len(readings)
        assert row.readings_missing == want["readings_missing"]
        assert float(row.avg_reading) == pytest.approx(statistics.mean(readings))
        assert int(row.max_reading) == max(readings)


async def test_b1_readings_carry_a_missing_subset_on_every_verdict(seeded: _Seeded) -> None:
    """The never-raise path is exercised, and not pooled on one verdict.

    Without this, ``readings_missing`` could be zero everywhere and the
    absent-reading branch of the extraction would never run — the assertion above
    would still pass while proving nothing about it.
    """
    expected = seeded.corpus.verdict_readings
    missing_by_verdict = {label: v["readings_missing"] for label, v in expected.items()}
    assert sum(missing_by_verdict.values()) > 0
    assert all(n > 0 for n in missing_by_verdict.values()), missing_by_verdict


async def test_b1_reading_bands_separate_the_verdicts(seeded: _Seeded) -> None:
    """Per-verdict means are DISTINCT, so mis-grouped readings would move them.

    If every verdict drew readings from one pool the means would coincide and a
    query that attributed readings to the wrong verdict would still match.
    """
    rows = await ra.verdict_reading_stats(seeded.session)
    means = sorted(float(row.avg_reading) for row in rows)
    assert len(means) == len(set(means))
    assert min(m2 - m1 for m1, m2 in pairwise(means)) > 1.0


# --------------------------------------------------------------------------
# B2 — DoA / approval-chain calibration fuel
# --------------------------------------------------------------------------


async def test_b2_approval_outcome_by_doa_tier_exact(seeded: _Seeded) -> None:
    """Gate counts + dwell stats per (tier, outcome) are exact."""
    rows = await ra.gate_tier_outcomes(seeded.session)
    expected = seeded.corpus.gate_tier_outcomes
    assert {(str(row.doa_tier), row.outcome) for row in rows} == set(expected)
    for row in rows:
        want = expected[(str(row.doa_tier), row.outcome)]
        durations: list[int] = want["durations"]
        assert row.gate_count == want["gate_count"]
        assert row.avg_duration_ms == pytest.approx(statistics.mean(durations))
        assert row.max_duration_ms == max(durations)


async def test_b2_every_tier_carries_both_outcomes(seeded: _Seeded) -> None:
    """Rejects exist, and land on EVERY tier.

    A corpus that never rejected would let ``gate_tier_outcomes`` collapse to a
    plain per-tier count with the outcome column constant — the query would be
    indistinguishable from one that never computed the outcome at all.
    """
    expected = seeded.corpus.gate_tier_outcomes
    tiers = {tier for tier, _ in expected}
    for tier in tiers:
        assert (tier, "approved") in expected, tier
        assert (tier, "rejected") in expected, tier
    rejected = sum(v["gate_count"] for (_, outcome), v in expected.items() if outcome == "rejected")
    approved = sum(v["gate_count"] for (_, outcome), v in expected.items() if outcome == "approved")
    assert rejected > 0 and approved > rejected


async def test_b2_reads_the_governed_decision_array_not_a_dict(seeded: _Seeded) -> None:
    """The tier is read out of the ARRAY shape the engine actually persists.

    ``_record_governed_decision`` concatenates two list-returning helpers, so the
    persisted value is a JSON array; ``test_procurement_sod_gate`` asserts that
    against engine-produced rows. This pins the corpus to that shape — a dict here
    would make the B2 query pass against a fixture production never writes.
    """
    gate_steps = [
        row
        for row in seeded.corpus.rows
        if getattr(row, "audit", None) and "governed_decision" in (row.audit or {})
    ]
    assert gate_steps
    for step in gate_steps:
        ties = (step.audit or {})["governed_decision"]
        assert isinstance(ties, list), type(ties)
        assert all(tie["control_ref"]["kind"] == "doa_tier" for tie in ties)


# --------------------------------------------------------------------------
# B3 — refusal-mining fuel
# --------------------------------------------------------------------------


async def test_b3_refusal_counts_by_kind_and_procedure_exact(seeded: _Seeded) -> None:
    """Refusal counts per (kind, procedure) are exact, and re-aggregate to the kind totals."""
    rows = await ra.refusal_counts_by_procedure(seeded.session)
    expected = seeded.corpus.refusals_by_procedure
    assert {(str(row.refusal_kind), row.procedure_id) for row in rows} == set(expected)
    for row in rows:
        assert row.count == expected[(str(row.refusal_kind), row.procedure_id)]
    # Folding the procedure dimension away must reproduce the kind-only primitive:
    # the two views of the same facts cannot disagree.
    folded: dict[str, int] = {}
    for row in rows:
        folded[str(row.refusal_kind)] = folded.get(str(row.refusal_kind), 0) + row.count
    kind_only = await ra.refusal_counts(seeded.session)
    assert folded == {str(row.refusal_kind): row.count for row in kind_only}


async def test_b3_kind_is_not_a_function_of_procedure(seeded: _Seeded) -> None:
    """The kind x procedure grouping is NOT collinear — the defect this step fixed.

    Refusals fall on ``i % 5 == 0``, so for ``i = 5k`` the procedure index is
    ``k % 4``. Indexing the kind by ``k % 2`` (the shipped shape until Step 6) made
    the procedure's PARITY determine the kind: every procedure carried exactly one
    kind, and a query that dropped the kind dimension entirely would have produced
    identical numbers. This asserts the corpus can tell the two apart.
    """
    expected = seeded.corpus.refusals_by_procedure
    kinds_per_procedure: dict[str, set[str]] = {}
    for kind, procedure in expected:
        kinds_per_procedure.setdefault(procedure, set()).add(kind)
    assert all(len(kinds) > 1 for kinds in kinds_per_procedure.values()), kinds_per_procedure
    procedures_per_kind: dict[str, set[str]] = {}
    for kind, procedure in expected:
        procedures_per_kind.setdefault(kind, set()).add(procedure)
    assert all(len(procs) > 1 for procs in procedures_per_kind.values()), procedures_per_kind


# --------------------------------------------------------------------------
# B4 — procedure-generation fuel
# --------------------------------------------------------------------------


async def test_b4_trigger_outcome_frequency_exact(seeded: _Seeded) -> None:
    """Run frequency per (procedure, trigger, status) is exact and totals to the corpus."""
    rows = await ra.trigger_outcome_counts(seeded.session)
    expected = seeded.corpus.trigger_outcomes
    assert {(row.procedure_id, str(row.trigger), row.status) for row in rows} == set(expected)
    for row in rows:
        assert row.run_count == expected[(row.procedure_id, str(row.trigger), row.status)]
    assert sum(row.run_count for row in rows) == seeded.corpus.run_count


async def test_b4_trigger_varies_independently_of_procedure_and_status(seeded: _Seeded) -> None:
    """Each trigger appears under every procedure AND every status.

    The trigger is indexed ``(i // 5) % 3``. Indexing it by ``i % 3`` would have made
    ``manual`` mean "has a resolved gate" (gates resolve on ``i % 3 == 0``), and
    ``i % 4`` / ``i % 5`` would have tied it to the procedure / status outright — in
    any of those cases the three-way grouping would carry no more information than a
    two-way one.
    """
    expected = seeded.corpus.trigger_outcomes
    triggers = {trigger for _, trigger, _ in expected}
    procedures = {procedure for procedure, _, _ in expected}
    statuses = {status for _, _, status in expected}
    assert len(triggers) > 1
    for trigger in triggers:
        seen_procedures = {p for p, t, _ in expected if t == trigger}
        seen_statuses = {s for _, t, s in expected if t == trigger}
        assert seen_procedures == procedures, (trigger, seen_procedures)
        assert seen_statuses == statuses, (trigger, seen_statuses)


async def test_b4_trigger_vocabulary_is_the_shipped_enum(seeded: _Seeded) -> None:
    """The trigger values are the shipped ``Trigger`` enum, not an invented vocabulary.

    B4's dimension is only real if it names what the engine stamps. Both writers
    (``scheduler._trigger_context`` and the event bridge) write ``trigger_context
    ["trigger"]`` with a ``Trigger`` value.
    """
    from services.engine.procedures.spec import Trigger

    rows = await ra.trigger_outcome_counts(seeded.session)
    assert {str(row.trigger) for row in rows} <= {t.value for t in Trigger}
    assert {str(row.trigger) for row in rows} == {t.value for t in Trigger}
