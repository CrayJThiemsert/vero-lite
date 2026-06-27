"""Tests for the procedure-draft intake routes (classify / build / instantiate) —
PLAN-0040 Phase B, Step B3 / AC-B5 (the PLAN-0017 face reused for the generator).

The route → generator path runs OFFLINE: ``procedure_draft._chat_client`` is monkeypatched
to a recorded-fixture chat client (the D12 offline seam), so the two LLM calls are
deterministic and zero host-state (no MS-S1). Proves:

- **classify** proposes an archetype (no skeleton yet, LOCKED-5); an off-catalog narrative
  abstains; a non-local backend / unreachable MS-S1 degrades to a clear non-silent state
  with the manual-pick catalog (D9).
- **build** runs ONLY on an explicit ``confirmed=true`` archetype (no-bypass, LOCKED-5),
  refuses an unknown archetype, and emits the gate-render envelope whose every governance
  value is an unfilled stub (D3/D6) with the ``governance_todo`` worklist + the
  ``governance_options`` allowlist (D4).
- **instantiate** is the deterministic, zero-LLM fallback: a manually-picked archetype →
  the same envelope from the template alone (no client built at all, D9).
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from services.api.config import settings
from services.api.main import app
from services.api.routers import procedure_draft
from services.engine.llm.client import ChatResult, OllamaUnreachableError

# --------------------------------------------------------------------------- #
# fixtures + the recorded-fixture chat client (the offline seam)
# --------------------------------------------------------------------------- #


@pytest.fixture
async def http() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class _FakeChatClient:
    """Replays recorded JSON contents in call order (call 1 = classify, 2.. = prose);
    an :class:`Exception` entry is raised when reached (a transport failure)."""

    def __init__(self, results: list[Any]) -> None:
        self._results = list(results)
        self.calls = 0

    async def chat(self, messages: Any, **kw: Any) -> ChatResult:
        self.calls += 1
        item = self._results.pop(0)
        if isinstance(item, Exception):
            raise item
        return ChatResult(content=item, thinking=None, model="gpt-oss:20b", raw={})


def _use_client(monkeypatch: pytest.MonkeyPatch, results: list[Any]) -> _FakeChatClient:
    """Point the route's client factory at a recorded fake + force a local backend."""
    monkeypatch.setattr(settings, "llm_backend", "local")
    fake = _FakeChatClient(results)
    monkeypatch.setattr(procedure_draft, "_chat_client", lambda: fake)
    return fake


def _classify(archetype_id: str, *, confidence: float = 0.9) -> str:
    return json.dumps(
        {
            "archetype_id": archetype_id,
            "step_gates": [
                {"step_id": "read", "gate_kind": "none"},
                {"step_id": "judge", "gate_kind": "in_file_band"},
                {"step_id": "act", "gate_kind": "none"},
            ],
            "rationale": "an anomaly then a gated action",
            "confidence": confidence,
        }
    )


_CLEAN_PROSE = json.dumps(
    {
        "title": "Detect and remediate sensor anomalies",
        "steps": [
            {"step_id": "read", "description": "Read the incoming signal for the assets."},
            {"step_id": "judge", "description": "Compare each reading against the operating band."},
            {"step_id": "act", "description": "Propose a remediation for each flagged asset."},
        ],
    }
)


# --------------------------------------------------------------------------- #
# /procedures/draft/classify
# --------------------------------------------------------------------------- #


async def test_classify_proposes_an_archetype(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    """A clean narrative classifies to a PROPOSED archetype (no skeleton yet) + the
    manual-pick catalog; confidence is carried but advisory."""
    _use_client(monkeypatch, [_classify("AT-1", confidence=0.42)])
    res = await http.post(
        "/procedures/draft/classify",
        json={"narrative": "watch the sensors and act on anomalies", "vertical": "draft"},
    )
    body = res.json()
    assert res.status_code == 200, res.text
    assert body["state"] == "match"
    assert body["match"]["archetype_id"] == "AT-1"
    assert body["match"]["confidence"] == 0.42  # advisory, recorded — never routes
    assert {c["archetype_id"] for c in body["catalog"]} == {"AT-1", "AT-1b", "AT-3"}


async def test_classify_abstains_off_catalog(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    """An off-catalog (e.g. AT-2-class) narrative abstains — route to hand-author (LOCKED-7),
    with the catalog still offered for a manual pick."""
    _use_client(monkeypatch, [_classify("abstain")])
    body = (
        await http.post(
            "/procedures/draft/classify",
            json={"narrative": "score each supplier and approve by DOA tier", "vertical": "draft"},
        )
    ).json()
    assert body["state"] == "abstain"
    assert body["reason"] == "no_archetype_match"
    assert body["match"] is None
    assert len(body["catalog"]) == 3


async def test_classify_degraded_when_backend_not_local(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    """A non-local backend never falls through to the hosted API — classify degrades to a
    clear non-silent state (CLAUDE.md §8 / D9). No live client is ever built."""
    monkeypatch.setattr(settings, "llm_backend", "hosted")
    res = await http.post(
        "/procedures/draft/classify", json={"narrative": "watch and act", "vertical": "draft"}
    )
    body = res.json()
    assert body["state"] == "degraded"
    assert body["reason"] == "backend_not_local"
    assert len(body["catalog"]) == 3  # the manual-pick fallback is still offered


async def test_classify_degraded_when_unreachable(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    """An unreachable MS-S1 degrades (recoverable by manual pick), distinct from abstain."""
    _use_client(monkeypatch, [OllamaUnreachableError("MS-S1 down")])
    body = (
        await http.post(
            "/procedures/draft/classify", json={"narrative": "watch and act", "vertical": "draft"}
        )
    ).json()
    assert body["state"] == "degraded"
    assert body["reason"] == "llm_unreachable"


async def test_classify_rejects_empty_narrative(http: AsyncClient) -> None:
    """An empty narrative is a 422 (the request model requires min_length=1)."""
    res = await http.post("/procedures/draft/classify", json={"narrative": "", "vertical": "draft"})
    assert res.status_code == 422


# --------------------------------------------------------------------------- #
# /procedures/draft/build — the confirm boundary + the gate envelope
# --------------------------------------------------------------------------- #


async def test_build_emits_a_gate_skeleton_with_stubs(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    """A confirmed archetype builds the gate envelope: the governance values are absent
    stubs, the worklist is populated, the allowlist is present, and the input alias serialises
    as ``from`` (so the read-mode renderer reuses its path verbatim)."""
    _use_client(monkeypatch, [_CLEAN_PROSE])  # build only makes prose calls (no classify)
    res = await http.post(
        "/procedures/draft/build",
        json={
            "narrative": "watch the sensors and act on anomalies",
            "vertical": "draft",
            "archetype_id": "AT-1",
            "confirmed": True,
        },
    )
    body = res.json()
    assert res.status_code == 200, res.text
    assert body["state"] == "ok"
    assert body["prose_attempts"] == 1

    env = body["draft"]
    assert set(env["governance_options"]) == {"direction", "autonomy", "handler"}
    vert = env["verticals"][0]
    assert vert["vertical"] == "draft"
    # the placeholder agent's H bindings are emitted ABSENT (agent-side stubs)
    assert vert["agents"][0]["llm_model"] is None
    assert vert["agents"][0]["autonomy_ceiling"] is None

    proc = vert["procedures"][0]
    assert proc["archetype"] == "AT-1"
    steps = {s["step_id"]: s for s in proc["steps"]}
    # every governance VALUE is an absent stub (D3/D6)
    assert steps["judge"]["threshold"] is None and steps["judge"]["direction"] is None
    assert steps["act"]["handler"] is None
    # the judge carries its band KIND (G) with no value; act keeps its archetype posture
    assert steps["judge"]["facet"]["decision_condition"]["gate_kind"] == "in_file_band"
    assert steps["act"]["autonomy"] == "gated"
    # the input fan-out serialises with the `from` alias (read-mode render contract):
    # in the AT-1 template only `act` consumes an earlier step (the breach set from judge)
    assert steps["act"]["input"]["from"] == "judge"
    # the "YOU must author" worklist (OQ-C / AC-A7)
    assert set(proc["governance_todo"]) == {"judge", "act"}
    assert {s["field"] for s in proc["governance_todo"]["judge"]} == {"threshold", "direction"}
    assert {s["field"] for s in proc["governance_todo"]["act"]} == {"handler", "autonomy"}


async def test_build_refuses_unconfirmed(http: AsyncClient) -> None:
    """build refuses an unconfirmed request (no bypass, LOCKED-5) — a 422, no client built."""
    res = await http.post(
        "/procedures/draft/build",
        json={
            "narrative": "watch and act",
            "vertical": "draft",
            "archetype_id": "AT-1",
            "confirmed": False,
        },
    )
    assert res.status_code == 422


async def test_build_rejects_unknown_archetype(http: AsyncClient) -> None:
    """An AT-2 (deferred / not in the v1 registry) confirmed build is a 422 — never a
    down-classified skeleton (LOCKED-7)."""
    res = await http.post(
        "/procedures/draft/build",
        json={
            "narrative": "score and approve by DOA tier",
            "vertical": "draft",
            "archetype_id": "AT-2",
            "confirmed": True,
        },
    )
    assert res.status_code == 422


async def test_build_degraded_when_backend_not_local(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    """A confirmed build on a non-local backend degrades (never the hosted API)."""
    monkeypatch.setattr(settings, "llm_backend", "hosted")
    body = (
        await http.post(
            "/procedures/draft/build",
            json={
                "narrative": "watch and act",
                "vertical": "draft",
                "archetype_id": "AT-1",
                "confirmed": True,
            },
        )
    ).json()
    assert body["state"] == "degraded"
    assert body["reason"] == "backend_not_local"


async def test_build_abstains_when_prose_never_clean(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    """If the model never produces parseable prose, build abstains (``unclean_draft``) —
    it never ships a half-formed draft (D3/D5 terminal safety)."""
    _use_client(monkeypatch, ["not json", "still not json", "nope"])  # 3 = default retry budget
    body = (
        await http.post(
            "/procedures/draft/build",
            json={
                "narrative": "watch and act",
                "vertical": "draft",
                "archetype_id": "AT-1",
                "confirmed": True,
            },
        )
    ).json()
    assert body["state"] == "abstain"
    assert body["reason"] == "unclean_draft"
    assert body["draft"] is None


# --------------------------------------------------------------------------- #
# /procedures/draft/instantiate — the deterministic zero-LLM fallback (D9)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("archetype_id", "n_steps"),
    [("AT-1", 3), ("AT-1b", 5), ("AT-3", 3)],
)
async def test_instantiate_is_deterministic_and_offline(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient, archetype_id: str, n_steps: int
) -> None:
    """A manually-picked archetype instantiates the gate envelope from the template alone —
    NO chat client is ever built (the route works on a cold MS-S1)."""

    def _boom() -> Any:  # building a client would mean a host-state dependency — it must not
        raise AssertionError("instantiate must not build an LLM client")

    monkeypatch.setattr(procedure_draft, "_chat_client", _boom)
    res = await http.post(
        "/procedures/draft/instantiate",
        json={"archetype_id": archetype_id, "vertical": "draft"},
    )
    body = res.json()
    assert res.status_code == 200, res.text
    assert body["state"] == "ok"
    proc = body["draft"]["verticals"][0]["procedures"][0]
    assert proc["archetype"] == archetype_id
    assert len(proc["steps"]) == n_steps
    # the judge owes threshold + direction; every governance value is an absent stub
    assert "judge" in proc["governance_todo"]
    judge = next(s for s in proc["steps"] if s["kind"] == "evaluate")
    assert judge["threshold"] is None
    assert judge["facet"]["decision_condition"]["gate_kind"] == "in_file_band"


async def test_instantiate_env_band_owes_env_var(http: AsyncClient) -> None:
    """An env-band judge owes the env var binding (not threshold/direction) — the other
    band-authoring mode."""
    res = await http.post(
        "/procedures/draft/instantiate",
        json={"archetype_id": "AT-1", "vertical": "draft", "band_source": "env"},
    )
    body = res.json()
    assert res.status_code == 200, res.text
    proc = body["draft"]["verticals"][0]["procedures"][0]
    assert {s["field"] for s in proc["governance_todo"]["judge"]} == {"env_var"}
    judge = next(s for s in proc["steps"] if s["kind"] == "evaluate")
    assert judge["facet"]["decision_condition"]["gate_kind"] == "env_band"


async def test_instantiate_rejects_unknown_archetype(http: AsyncClient) -> None:
    res = await http.post(
        "/procedures/draft/instantiate", json={"archetype_id": "AT-2", "vertical": "draft"}
    )
    assert res.status_code == 422
