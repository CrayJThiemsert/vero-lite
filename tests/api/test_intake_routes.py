"""Tests for the PLAN-0017 intake-face routes (extract / defaults / generate).

The route → engine path runs offline: ``intake._chat_client`` is monkeypatched to
a fake chat client, and ``intake._repo_root`` to a staged temp repo (so generate
writes the ontology + scaffold there, never the working tree). Proves:

- **AC-2 (the human gate is real):** ``/intake/generate`` refuses an unconfirmed
  package (no bypass), and an edit made to the package is provably reflected in
  the generated artifacts (the edit-propagation guarantee).
- **AC-3 (direction):** a below-breach package lands ``OCT_RECOMMEND_DIRECTION=below``
  with a below-threshold synthetic breach (the recommender's rule-path precondition;
  the live fire is verified end-to-end in Step 4).
- **AC-4 (MS-S1 local + graceful degradation):** extraction degrades to a clear,
  non-silent state on a non-local backend / unreachable MS-S1 / unparseable output.
- **AC-5 (engine untouched):** generate invokes ``scaffold_vertical`` unchanged and
  surfaces the refuse-to-clobber guard rather than overwriting by default.
"""

from __future__ import annotations

import shutil
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from services.api.config import settings
from services.api.main import app
from services.api.routers import intake
from services.engine.llm.client import ChatResult, OllamaUnreachableError

_SRC_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
async def http() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def staged_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Stage a temp repo (a copy of main.py) and point intake._repo_root at it, so
    generate writes the ontology + scaffold into the temp tree, not the real repo."""
    staged = tmp_path / "repo"
    api = staged / "services" / "api"
    api.mkdir(parents=True)
    shutil.copy2(_SRC_ROOT / "services" / "api" / "main.py", api / "main.py")
    monkeypatch.setattr(intake, "_repo_root", lambda: staged)
    yield staged


class _FakeChatClient:
    def __init__(self, results: list[ChatResult | Exception]) -> None:
        self._results = list(results)
        self.calls = 0

    async def chat(self, messages: Any, **kw: Any) -> ChatResult:
        self.calls += 1
        item = self._results.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _result(content: str) -> ChatResult:
    return ChatResult(content=content, thinking=None, model="gpt-oss:20b", raw={})


def _draft(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "namespace": "cold_room",
        "domain_label": "cold storage temperature monitoring",
        "asset_role": {
            "type_name": "ColdRoom",
            "properties": [{"name": "volume_m3", "type": "float"}],
        },
        "site_role": {"type_name": "Warehouse", "properties": []},
        "metric": {"label": "over-temp", "unit": "C", "threshold": 8.0, "direction": "above"},
        "action_types": ["dispatch_technician", "increase_cooling"],
        "problem": "Temperature excursions spoil the stored stock.",
        "decision": "Increase cooling.",
        "recovery_value": 4.0,
        "recovery_description": "Temperature back to safe range.",
        "confidence": 0.8,
    }
    base.update(overrides)
    return base


def _package_payload(**overrides: Any) -> dict[str, Any]:
    """A full, valid IntakePackage dict for generate request bodies."""
    base = _draft(**overrides)
    base.setdefault("source", "manual_entry")
    return base


# --------------------------------------------------------------------------- #
# /intake/extract — AC-4 local-only + graceful degradation
# --------------------------------------------------------------------------- #


async def test_extract_ok(monkeypatch: pytest.MonkeyPatch, http: AsyncClient) -> None:
    import json

    monkeypatch.setattr(settings, "llm_backend", "local")
    monkeypatch.setattr(
        intake, "_chat_client", lambda: _FakeChatClient([_result(json.dumps(_draft()))])
    )
    res = await http.post(
        "/intake/extract", json={"description": "we run cold rooms in warehouses"}
    )
    body = res.json()
    assert res.status_code == 200
    assert body["state"] == "ok"
    assert body["source"] == "ms_s1_live"  # the harness stamps provenance
    assert body["package"]["namespace"] == "cold_room"
    assert body["package"]["metric"]["direction"] == "above"


async def test_extract_degraded_when_backend_not_local(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    """AC-4 / §8: a non-local backend never falls through to the hosted API —
    extraction degrades to a clear non-silent state."""
    monkeypatch.setattr(settings, "llm_backend", "hosted")
    res = await http.post("/intake/extract", json={"description": "cold rooms"})
    body = res.json()
    assert body["state"] == "degraded"
    assert body["package"] is None
    assert "local backend" in body["detail"]


async def test_extract_degraded_when_unreachable(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    monkeypatch.setattr(settings, "llm_backend", "local")
    monkeypatch.setattr(
        intake, "_chat_client", lambda: _FakeChatClient([OllamaUnreachableError("MS-S1 down")])
    )
    body = (await http.post("/intake/extract", json={"description": "cold rooms"})).json()
    assert body["state"] == "degraded"
    assert "unreachable" in body["detail"].lower()


async def test_extract_degraded_on_unparseable_output(
    monkeypatch: pytest.MonkeyPatch, http: AsyncClient
) -> None:
    monkeypatch.setattr(settings, "llm_backend", "local")
    monkeypatch.setattr(
        intake,
        "_chat_client",
        lambda: _FakeChatClient([_result("x"), _result("y"), _result("z")]),
    )
    body = (await http.post("/intake/extract", json={"description": "cold rooms"})).json()
    assert body["state"] == "degraded"
    assert body["package"] is None


# --------------------------------------------------------------------------- #
# /intake/defaults — AC-4 prebaked fallback
# --------------------------------------------------------------------------- #


async def test_defaults_are_source_tagged(http: AsyncClient) -> None:
    body = (await http.get("/intake/defaults")).json()
    namespaces = {d["namespace"] for d in body["defaults"]}
    assert namespaces == {"solar_farm", "water_utility"}
    assert all(d["source"] == "prebaked_default" for d in body["defaults"])


# --------------------------------------------------------------------------- #
# /intake/generate — AC-2 (the gate is real), AC-3, AC-5
# --------------------------------------------------------------------------- #


async def test_generate_rejects_unconfirmed_no_bypass(staged_root: Path, http: AsyncClient) -> None:
    """AC-2: generation refuses an unconfirmed package and writes nothing — there
    is no path from a package to the engine that bypasses the explicit confirm."""
    res = await http.post(
        "/intake/generate", json={"package": _package_payload(), "confirmed": False}
    )
    assert res.status_code == 422
    assert not (staged_root / "verticals" / "cold_room").exists()  # nothing scaffolded


async def test_generate_requires_confirmed_field(staged_root: Path, http: AsyncClient) -> None:
    """Omitting `confirmed` entirely is a 422 too (the flag is required)."""
    res = await http.post("/intake/generate", json={"package": _package_payload()})
    assert res.status_code == 422
    assert not (staged_root / "verticals" / "cold_room").exists()


async def test_generate_edit_propagates_to_artifacts(staged_root: Path, http: AsyncClient) -> None:
    """AC-2 edit-propagation: a property rename + an enum value edited in the gate
    is provably present in the generated artifacts (not just the happy path)."""
    edited = _package_payload(
        asset_role={
            "type_name": "ColdRoom",
            "properties": [
                {"name": "operator_note_field", "type": "string"},  # a renamed/added prop
                {
                    "name": "room_class",
                    "type": "enum",
                    "values": ["edited_chiller", "edited_freezer"],
                },
            ],
        }
    )
    res = await http.post("/intake/generate", json={"package": edited, "confirmed": True})
    assert res.status_code == 200, res.text

    models = (staged_root / "verticals" / "cold_room" / "generated" / "models.py").read_text()
    types = (staged_root / "verticals" / "cold_room" / "generated" / "types.ts").read_text()
    assert "operator_note_field" in models  # the gate edit reached the generated model
    assert "edited_chiller" in models  # the edited enum member propagated
    assert "edited_chiller" in types


async def test_generate_below_direction_threads_through(
    staged_root: Path, http: AsyncClient
) -> None:
    """AC-3: a below-breach package lands DIRECTION=below + a below-threshold
    synthetic breach (the rule-path firing precondition)."""
    pkg = _package_payload(
        namespace="oxy_demo",
        metric={"label": "do-crash", "unit": "mg/L", "threshold": 4.0, "direction": "below"},
    )
    res = await http.post("/intake/generate", json={"package": pkg, "confirmed": True})
    body = res.json()
    assert res.status_code == 200, res.text
    assert body["direction"] == "below"
    assert "OCT_RECOMMEND_DIRECTION=below" in body["env_block"]
    synthetic = (
        staged_root / "verticals" / "oxy_demo" / "data_adapter" / "synthetic.py"
    ).read_text()
    assert "3.2" in synthetic  # 4.0 * 0.8 — a crash below the threshold


async def test_generate_invokes_engine_and_registers(staged_root: Path, http: AsyncClient) -> None:
    """AC-5 (PLAN-0032/B2): the engine is invoked unchanged — artifacts emitted + the
    vertical is discoverable WITHOUT a main.py code-mod (auto-registered at runtime via
    the registry import-scan)."""
    original_main = (staged_root / "services" / "api" / "main.py").read_text()
    res = await http.post(
        "/intake/generate", json={"package": _package_payload(), "confirmed": True}
    )
    body = res.json()
    assert res.status_code == 200, res.text
    assert body["asset_type"] == "ColdRoom"
    assert body["site_type"] == "Warehouse"
    assert body["registered"] is True
    for name in ("models.py", "schema.sql", "schema.json", "mcp_tools.json", "types.ts"):
        assert (staged_root / "verticals" / "cold_room" / "generated" / name).exists()
    # main.py is NOT code-modded; discovery rides the scaffolded register_<ns>_* entry fns.
    assert (staged_root / "services" / "api" / "main.py").read_text() == original_main
    handlers = (staged_root / "verticals" / "cold_room" / "handlers.py").read_text()
    assert "def register_cold_room_handlers(" in handlers


async def test_generate_refuses_to_clobber(staged_root: Path, http: AsyncClient) -> None:
    """AC-5: a second generate without force is refused (409); force overwrites."""
    first = await http.post(
        "/intake/generate", json={"package": _package_payload(), "confirmed": True}
    )
    assert first.status_code == 200, first.text
    again = await http.post(
        "/intake/generate", json={"package": _package_payload(), "confirmed": True}
    )
    assert again.status_code == 409
    assert "clobber" in again.json()["detail"]["error"]
    forced = await http.post(
        "/intake/generate", json={"package": _package_payload(), "confirmed": True, "force": True}
    )
    assert forced.status_code == 200, forced.text
