"""Tests for the LLM-drafted synthetic enrichment (PLAN-0016 Step 2).

The LLM path is exercised with a fake chat client (no live MS-S1, deterministic,
offline — the recommender-test pattern). The load-bearing checks: a valid draft
is parsed + semantically validated (refs resolve, enums valid, exactly one
breaching reading that is the latest event), and ANY failure — bad JSON, a
broken invariant, a transport error, or the local backend being off — falls back
to the deterministic draft so enrichment never breaks scaffolding.
"""

from __future__ import annotations

import json
import os
import shutil
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from services.api.config import settings
from services.engine import code_generator, scaffold
from services.engine.scaffold import LlmSyntheticError, RecommendConfig

_SRC_ROOT = Path(__file__).resolve().parents[3]


def _energy_doc() -> dict[str, Any]:
    return code_generator.load_doc(
        _SRC_ROOT / "verticals" / "energy" / "ontology" / "energy_v0.yaml"
    )


def _roles() -> scaffold.VerticalRoles:
    return scaffold.detect_roles(_energy_doc())


def _config() -> RecommendConfig:
    return RecommendConfig(
        threshold=4.0,
        direction="below",
        label="dissolved-oxygen crash",
        unit="mg/L",
        recovery_value=5.5,
        recovery_description="recovered",
        problem="ponds lose oxygen at night",
    )


def _events_ok() -> list[dict[str, Any]]:
    return [
        {
            "event_id": "e1",
            "event_type": "reading",
            "severity": "info",
            "measured_value": 6.5,
            "unit": "mg/L",
            "occurred_at": "2026-06-01T01:00:00Z",
            "asset_id": "a1",
            "site_id": "s1",
        },
        {
            "event_id": "e2",
            "event_type": "reading",
            "severity": "critical",
            "measured_value": 3.2,
            "unit": "mg/L",
            "occurred_at": "2026-06-01T02:00:00Z",
            "asset_id": "a1",
            "site_id": "s1",
        },
    ]


def _canned(events: list[dict[str, Any]] | None = None) -> str:
    return json.dumps(
        {
            "sites": [
                {
                    "site_id": "s1",
                    "name": "North",
                    "site_type": "substation",
                    "lat": 13.7,
                    "lng": 100.5,
                },
                {
                    "site_id": "s2",
                    "name": "South",
                    "site_type": "microgrid",
                    "lat": 13.8,
                    "lng": 100.6,
                },
            ],
            "assets": [
                {
                    "asset_id": "a1",
                    "name": "Unit A",
                    "asset_type": "battery",
                    "status": "active",
                    "site_id": "s1",
                },
                {
                    "asset_id": "a2",
                    "name": "Unit B",
                    "asset_type": "inverter",
                    "status": "active",
                    "site_id": "s2",
                },
            ],
            "events": _events_ok() if events is None else events,
        }
    )


# --- parse + semantic validation -----------------------------------------


def test_parse_synthetic_valid() -> None:
    sites, assets, events = scaffold._parse_synthetic(_canned(), _roles(), _config(), _energy_doc())
    assert len(sites) == 2
    assert len(assets) == 2
    # occurred_at is parsed to a tz-aware datetime; the breach (3.2) is last.
    assert events[-1]["measured_value"] == 3.2
    assert events[-1]["occurred_at"].tzinfo is not None


def test_parse_rejects_invalid_json() -> None:
    with pytest.raises(LlmSyntheticError):
        scaffold._parse_synthetic("not json", _roles(), _config(), _energy_doc())


def test_parse_rejects_breach_not_latest() -> None:
    events = [
        {**_events_ok()[1], "occurred_at": "2026-06-01T01:00:00Z"},  # breach early
        {**_events_ok()[0], "occurred_at": "2026-06-01T03:00:00Z"},  # safe later
    ]
    with pytest.raises(LlmSyntheticError, match="latest"):
        scaffold._parse_synthetic(_canned(events), _roles(), _config(), _energy_doc())


def test_parse_rejects_no_breach() -> None:
    safe = {**_events_ok()[1], "measured_value": 9.9}  # 9.9 > 4 -> never crosses below
    with pytest.raises(LlmSyntheticError, match="one breaching reading"):
        scaffold._parse_synthetic(
            _canned([_events_ok()[0], safe]), _roles(), _config(), _energy_doc()
        )


def test_parse_rejects_unresolved_ref() -> None:
    bad = [{**_events_ok()[0], "site_id": "nope"}, _events_ok()[1]]
    with pytest.raises(LlmSyntheticError, match="does not resolve"):
        scaffold._parse_synthetic(_canned(bad), _roles(), _config(), _energy_doc())


def test_parse_rejects_bad_enum() -> None:
    data = json.loads(_canned())
    data["assets"][0]["status"] = "bogus"
    with pytest.raises(LlmSyntheticError, match="enum"):
        scaffold._parse_synthetic(json.dumps(data), _roles(), _config(), _energy_doc())


# --- integration: scaffold_vertical(llm=True) ----------------------------


class _FakeClient:
    def __init__(self, *, content: str | None = None, error: Exception | None = None) -> None:
        self._content = content
        self._error = error

    async def chat(self, messages: Any, *, response_format: Any = None, **kw: Any) -> Any:
        if self._error is not None:
            raise self._error
        return SimpleNamespace(content=self._content)


@pytest.fixture
def llm_repo(tmp_path: Path) -> Iterator[Path]:
    """Stage the energy ontology under a fresh namespace + a main.py copy."""
    staged = tmp_path / "repo"
    onto = staged / "verticals" / "ll_demo" / "ontology"
    onto.mkdir(parents=True)
    src = (_SRC_ROOT / "verticals" / "energy" / "ontology" / "energy_v0.yaml").read_text(
        encoding="utf-8"
    )
    (onto / "ll_demo_v0.yaml").write_text(
        src.replace("namespace: energy", "namespace: ll_demo"), encoding="utf-8"
    )
    api = staged / "services" / "api"
    api.mkdir(parents=True)
    shutil.copy2(_SRC_ROOT / "services" / "api" / "main.py", api / "main.py")
    old = Path.cwd()
    os.chdir(staged)
    try:
        yield staged
    finally:
        os.chdir(old)


def test_scaffold_llm_uses_llm_records(llm_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scaffold, "_build_chat_client", lambda: _FakeClient(content=_canned()))
    scaffold.scaffold_vertical("ll_demo", _config(), llm=True)
    src = (llm_repo / "verticals" / "ll_demo" / "data_adapter" / "synthetic.py").read_text(
        encoding="utf-8"
    )
    assert "--llm" in src  # the LLM source note
    assert "'s1'" in src or '"s1"' in src  # an LLM-supplied PK, not the deterministic site-01
    assert "3.2" in src


def test_scaffold_llm_falls_back_on_error(llm_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        scaffold, "_build_chat_client", lambda: _FakeClient(error=RuntimeError("boom"))
    )
    scaffold.scaffold_vertical("ll_demo", _config(), llm=True)
    src = (llm_repo / "verticals" / "ll_demo" / "data_adapter" / "synthetic.py").read_text(
        encoding="utf-8"
    )
    assert "deterministic" in src  # fell back to the deterministic draft
    assert "site-01" in src


def test_scaffold_llm_falls_back_when_backend_off(
    llm_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Real _build_chat_client refuses a non-local backend -> deterministic fallback.
    monkeypatch.setattr(settings, "llm_backend", "hosted")
    scaffold.scaffold_vertical("ll_demo", _config(), llm=True)
    src = (llm_repo / "verticals" / "ll_demo" / "data_adapter" / "synthetic.py").read_text(
        encoding="utf-8"
    )
    assert "deterministic" in src
