"""AC-8 + AC-12 — two tenants, one database, driven through the REAL seam.

**Why a synthetic second tenant rather than waiting for a real one (Cray, call 3).**
Under a single tenant, SD-3's twelve constraint re-scopes are a 100% behavioural
no-op: every test is exactly as green before the change as after, so Step 4 would
ship with no evidence that it did anything at all — or that it did it in the right
places. A two-tenant fixture is the ONLY thing that can tell those apart, which
makes it the positive control for Cray's own SD-3 ruling rather than a convenience.

Production having one tenant per database does not constrain the test database. The
disposable test DB will hold whatever we write to it, and SD-1(b)'s ruled column
default is late-bound — evaluated at INSERT — so ``monkeypatch.setattr(settings,
"tenant_id", ...)`` switches tenants between write batches with no process restart.

**Anti-mock clause (AC-8, binding under CLAUDE.md §8).** Every write below goes
through the real ``async_sessionmaker``, the real ``run_procedure_persisted`` driver,
and the real ORM models. Nothing patches the session factory, the stamping seam, or
the models under test. A test that stubbed either side of the seam would agree with
itself by construction and prove nothing about the contract the system produces.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from services.api.config import settings
from services.db.audit_log import AuditLog, append_audit, verify_chain
from services.db.base import Base
from services.engine.llm.client import ChatResult
from services.engine.procedures.action_step import ActionStepExecutor
from services.engine.procedures.orchestrator import RunContext, StepExecutor, StepOutcome
from services.engine.procedures.persistence import run_procedure_persisted
from services.engine.procedures.runs import PipelineRun, StepResult
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    Procedure,
    Step,
    StepKind,
)
from services.engine.registry import registry
from tests.db_support import create_test_engine, drop_all_bounded

_TENANT_A = "scenario-acme"
_TENANT_B = "scenario-globex"

#: A fixed timestamp for the hand-built rows. A literal rather than ``func.now()``
#: because these tests assert on tenant scoping, never on ordering — and the dev
#: box's wall clock is measured NON-monotonic (revision 0023's whole subject), so a
#: clock-derived value here would be one more thing that can move under the test.
_NOW = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)


class _FakeChat:
    """The LLM boundary only. Not the seam under test — the seam under test is
    procedure -> persistence -> tenant stamp, and that runs for real below."""

    def __init__(self, results: list[ChatResult]) -> None:
        self._results = list(results)

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        return self._results.pop(0)


def _judgment_json() -> str:
    return json.dumps(
        {
            "title": "Start emergency aerator on pond p7",
            "description": "DO fell below the 4 mg/L breach threshold.",
            "rationale": "DO 3.2 mg/L is a breach; aerate.",
            "confidence": 0.92,
            "affected_entities": [{"object_type": "Pond", "primary_key": "p7"}],
            "suggested_handler": "aerate",
            "handler_payload": {"pond_id": "p7"},
        }
    )


def _chat_results() -> list[ChatResult]:
    return [
        ChatResult(content="draft", thinking="t", model="gpt-oss:20b", raw={}),
        ChatResult(content=_judgment_json(), thinking=None, model="gpt-oss:20b", raw={}),
    ]


class _Reading:
    """Realistic simulated data — a dissolved-oxygen breach, the shape the
    aquaculture vertical's synthetic events actually carry."""

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(
            output=[{"pond": "p7", "event_id": "e7", "measured_value": 3.2, "unit": "mg/L"}],
            reasoning_trace=[{"kind": "query", "summary": "read DO readings"}],
        )


class _Judge:
    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(
            output=list(input_set),
            reasoning_trace=[{"kind": "evaluate", "summary": "breach confirmed"}],
        )


async def _aerate(action: Any) -> dict[str, Any]:
    return {"ok": True, "executed": action.id}


def _agent() -> Agent:
    return Agent(
        agent_id="pond_agent",
        name="Pond Agent",
        autonomy_ceiling=Autonomy.GATED,
        allowed=AgentAllowed(action_handlers=["aerate"]),
    )


def _procedure() -> Procedure:
    return Procedure(
        procedure_id="tenant-round",
        title="Tenant Round",
        goal="Act on DO breaches.",
        run_by="pond_agent",
        steps=[
            Step(step_id="read", name="Read", kind=StepKind.QUERY),
            Step(step_id="judge", name="Judge", kind=StepKind.EVALUATE),
            Step(step_id="aerate", name="Aerate", kind=StepKind.ACTION, handler="aerate"),
        ],
    )


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await drop_all_bounded(conn)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


async def _run_as_tenant(engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch, tenant: str) -> None:
    """Drive one full procedure run under ``tenant``, through the real driver.

    The handler is registered by the CALLER, once per test: the registry refuses a
    duplicate name, and registering per tenant would make the second run die on
    bookkeeping rather than on anything this test is about.
    """
    monkeypatch.setattr(settings, "tenant_id", tenant)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    executors: dict[StepKind, StepExecutor] = {
        StepKind.QUERY: _Reading(),
        StepKind.EVALUATE: _Judge(),
        StepKind.ACTION: ActionStepExecutor(client_factory=lambda _m: _FakeChat(_chat_results())),
    }
    async with maker() as session:
        await run_procedure_persisted(
            session,
            _procedure(),
            _agent(),
            executors,
            vertical="aquaculture",
            run_id=f"run-{tenant}",
        )
        await append_audit(session, action="run_opened", run_id=f"run-{tenant}")
        await session.commit()


# --------------------------------------------------------------------------- #
# AC-12(ii) + AC-8 — the write path stamps each tenant's rows with its own key
# --------------------------------------------------------------------------- #


async def test_two_tenants_writing_through_the_real_seam_land_under_their_own_key(
    db_engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-8's end-to-end claim, doubled: two tenants, one database, no crossover.

    Drives ``run_procedure_persisted`` — the real write-ahead driver the HTTP run
    surface uses — twice, and asserts every ``pipeline_runs`` / ``step_results`` /
    ``audit_log`` row carries the tenant that was active when it was written. The
    single-tenant version of this assertion is satisfiable by a hardcoded constant;
    only the second tenant proves the stamp READS the setting.
    """
    registry.register_handler("aquaculture", "aerate", _aerate)
    await _run_as_tenant(db_engine, monkeypatch, _TENANT_A)
    await _run_as_tenant(db_engine, monkeypatch, _TENANT_B)

    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        runs = {
            r.run_id: r.tenant_id
            for r in (await session.execute(sa.select(PipelineRun))).scalars().all()
        }
        steps = [
            (s.run_id, s.tenant_id)
            for s in (await session.execute(sa.select(StepResult))).scalars().all()
        ]
        audits = [
            (a.run_id, a.tenant_id)
            for a in (await session.execute(sa.select(AuditLog))).scalars().all()
        ]

    assert runs == {f"run-{_TENANT_A}": _TENANT_A, f"run-{_TENANT_B}": _TENANT_B}
    assert steps, "no step results were written — the driver did not run"
    for run_id, tenant in steps:
        assert run_id == f"run-{tenant}", f"step result {run_id} stamped {tenant}"
    assert audits, "no audit rows were written — append_audit did not run"
    for run_id, tenant in audits:
        assert run_id is None or run_id == f"run-{tenant}", f"audit {run_id} stamped {tenant}"


# --------------------------------------------------------------------------- #
# AC-12(i) — the positive control for Cray's SD-3 ruling
# --------------------------------------------------------------------------- #


async def test_two_tenants_can_hold_the_same_seq_which_is_what_sd3_bought(
    db_engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The one observable consequence of re-scoping twelve constraints.

    ``uq_step_results_seq`` was ``(seq)`` and is now ``(tenant_id, seq)``. Under the
    OLD key, two tenants could not both hold ``seq = 1`` — the second insert would
    raise. Under the new key they can, and that is the entire behavioural difference
    SD-3 bought. Asserting it here is what turns Step 4 from twelve edits nobody can
    observe into a change with a consequence.

    ``seq`` is written explicitly, which the schema permits: ``step_results.seq`` is
    ``GENERATED BY DEFAULT``, not ``ALWAYS`` (revision 0023 needed explicit writes to
    backfill legacy rows in the old reader's order).
    """
    maker = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _insert(tenant: str, step_result_id: str) -> None:
        monkeypatch.setattr(settings, "tenant_id", tenant)
        async with maker() as session:
            session.add(
                PipelineRun(
                    run_id=f"seq-run-{tenant}",
                    procedure_id="p",
                    agent_id="a",
                    status="running",
                    started_at=_NOW,
                    updated_at=_NOW,
                )
            )
            await session.commit()
        async with maker() as session:
            session.add(
                StepResult(
                    step_result_id=step_result_id,
                    run_id=f"seq-run-{tenant}",
                    step_id="read",
                    status="complete",
                    seq=1,
                    created_at=_NOW,
                )
            )
            await session.commit()

    await _insert(_TENANT_A, "sr-a")
    # Under the pre-SD-3 key this second write is the one that raised.
    await _insert(_TENANT_B, "sr-b")

    async with maker() as session:
        rows = {
            (s.tenant_id, s.seq)
            for s in (await session.execute(sa.select(StepResult))).scalars().all()
        }
    assert rows == {(_TENANT_A, 1), (_TENANT_B, 1)}


async def test_one_tenant_still_cannot_hold_a_duplicate_seq(
    db_engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The other side of the same control — widening must not DISABLE the key.

    Without this, the test above would be satisfied by a migration that dropped
    ``uq_step_results_seq`` outright and never recreated it. A guarantee that is
    merely weaker is the intended outcome; a guarantee that is gone is not.
    """
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    monkeypatch.setattr(settings, "tenant_id", _TENANT_A)
    async with maker() as session:
        session.add(
            PipelineRun(
                run_id="dup-run",
                procedure_id="p",
                agent_id="a",
                status="running",
                started_at=_NOW,
                updated_at=_NOW,
            )
        )
        await session.commit()

    async def _add(step_result_id: str) -> None:
        async with maker() as session:
            session.add(
                StepResult(
                    step_result_id=step_result_id,
                    run_id="dup-run",
                    step_id="read",
                    status="complete",
                    seq=7,
                    created_at=_NOW,
                )
            )
            await session.commit()

    await _add("dup-1")
    with pytest.raises(IntegrityError) as rejected:
        await _add("dup-2")
    assert "uq_step_results_seq" in str(rejected.value)


# --------------------------------------------------------------------------- #
# AC-12(iii) — characterisation: what is scoped, and what is still global
# --------------------------------------------------------------------------- #


async def test_the_audit_chain_is_per_tenant_and_verifies_per_tenant(
    db_engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SD-3 rider 3, as behaviour rather than as a docstring.

    Two tenants append interleaved. Each chain must verify INTACT on its own, which
    is only true because ``append_audit``'s head lookup is tenant-scoped in lockstep
    with ``verify_chain``'s walk — an unscoped head would have tenant B linking onto
    tenant A's row_hash, and the scoped walk would then report a break.
    """
    maker = async_sessionmaker(db_engine, expire_on_commit=False)

    for tenant, action in (
        (_TENANT_A, "a1"),
        (_TENANT_B, "b1"),
        (_TENANT_A, "a2"),
        (_TENANT_B, "b2"),
        (_TENANT_A, "a3"),
    ):
        monkeypatch.setattr(settings, "tenant_id", tenant)
        async with maker() as session:
            await append_audit(session, action=action)
            await session.commit()

    for tenant, expected_actions in (
        (_TENANT_A, ["a1", "a2", "a3"]),
        (_TENANT_B, ["b1", "b2"]),
    ):
        monkeypatch.setattr(settings, "tenant_id", tenant)
        async with maker() as session:
            breaks = await verify_chain(session)
            rows = (
                (
                    await session.execute(
                        sa.select(AuditLog)
                        .where(AuditLog.tenant_id == tenant)
                        .order_by(AuditLog.audit_id)
                    )
                )
                .scalars()
                .all()
            )
        assert breaks == [], f"{tenant}'s chain reports breaks: {breaks}"
        assert [r.action for r in rows] == expected_actions


async def test_a_raw_write_that_forgets_the_stamp_fails_loudly(
    db_engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SD-1(b)'s enforcement mechanism, asserted rather than described.

    The ruling chose a Python-side default over a ``server_default`` precisely so an
    unstamped write DIES instead of landing under a value nobody chose. A raw insert
    is what a write path that bypassed the ORM would look like, and this is the
    positive control proving the ruling has teeth — Step 1.4 measured that no
    migration tooling would ever report it.
    """
    monkeypatch.setattr(settings, "tenant_id", _TENANT_A)
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    with pytest.raises(IntegrityError) as rejected:
        async with maker() as session:
            await session.execute(
                sa.text(
                    "INSERT INTO pipeline_runs (run_id, procedure_id, agent_id, status, "
                    "started_at, updated_at) VALUES ('raw-1', 'p', 'a', 'running', "
                    "now(), now())"
                )
            )
            await session.commit()
    assert "tenant_id" in str(rejected.value)
