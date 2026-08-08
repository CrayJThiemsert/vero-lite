"""PLAN-0100 AC-8 — the prompt-log writer, its closed field set, and rotation.

D6's bargain has two halves and this module tests both: the operator can read
what visitors asked, and the record cannot identify who asked. The second half is
the one a test has to defend, because it fails by ADDITION — nobody removes the
privacy, someone adds a field. So the key assertion is **set-equality**, not
presence: a row that gained a ``client_ip`` reddens here even though every field
D6 requires is still there.

Driven through the real routes against the real writer; the only stand-in is the
upstream Ollama server (``tests/support/ollama_stub``), per the AC preamble.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from httpx import AsyncClient

from services.api.config import settings
from services.engine.llm import prompt_log
from services.engine.ontology_meta import load_ontology_meta
from tests.support.ollama_stub import ollama_stub

REPO_ROOT = Path(__file__).resolve().parents[2]

_TYPED = "which sites breached the threshold last night?"

#: D6's field set, written out HERE rather than imported from the module.
#: Asserting against ``prompt_log.FIELDS`` would compare the code to itself:
#: widening that constant would widen the test with it, and the row could grow a
#: ``session_id`` with every test still green. This literal is the independent
#: copy, and ``test_the_module_field_set_matches_d6`` is what keeps the two honest.
_D6_FIELDS = frozenset({"ts_utc", "route", "vertical", "text", "model", "outcome", "arm"})


def test_the_module_field_set_matches_d6() -> None:
    """The writer's own constant still equals the ratified set.

    Changing D6's field set is a governance act (ADR-0035 D6, ratified OQ-2), so
    it must fail a test and be argued, not pass because both sides moved together.
    """
    assert prompt_log.FIELDS == _D6_FIELDS


def _translatable() -> str:
    object_type = load_ontology_meta(settings.oct_vertical).object_types[0].name
    return json.dumps({"object_type": object_type, "operation": "count"})


@pytest.fixture
def log_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Enable the log into a temp dir. Never the configured production path."""
    target = tmp_path / "prompt-log"
    monkeypatch.setattr(settings, "prompt_log_enabled", True)
    monkeypatch.setattr(settings, "prompt_log_dir", str(target))
    monkeypatch.setattr(settings, "llm_backend", "local")
    return target


def _rows(directory: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(directory.glob("prompt-*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


async def test_query_writes_one_row_with_the_closed_field_set(
    client: AsyncClient, log_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One question in, one row out, carrying exactly the D6 keys and nothing else."""
    async with ollama_stub(content=_translatable()) as stub:
        monkeypatch.setattr(settings, "ollama_host", stub.base_url)
        response = await client.post("/query", json={"question": _TYPED})
    assert response.status_code == 200, response.text

    rows = _rows(log_dir)
    assert len(rows) == 1, f"expected exactly one logged row, got {len(rows)}"
    row = rows[0]

    # The load-bearing assertion. Presence-checking would stay green the day a
    # field is ADDED, and addition is how this privacy promise actually breaks.
    assert (
        set(row) == _D6_FIELDS
    ), f"prompt-log row keys drifted from the D6 closed set: {sorted(set(row))}"
    # Named explicitly as well as by set-equality, so a future widening of FIELDS
    # cannot quietly re-admit them (the set assertion alone would follow it).
    assert not {"ip", "client_ip", "headers", "person_id", "identity"} & set(row)

    assert row["text"] == _TYPED, "the visitor's input must be recorded verbatim"
    assert row["route"] == "/query"
    assert row["vertical"] == settings.oct_vertical
    assert row["arm"] in ("llm", "deterministic")
    datetime.fromisoformat(str(row["ts_utc"]))  # parses, or this raises

    # This case drives the real route into the real writer, yet it said nothing
    # about `model` — so it stayed green while the row named a model that never
    # ran (PLAN-0100 Step 11, D-2). The set-equality above only checks that the
    # KEY is present; a wrong VALUE is exactly what it cannot see.
    # ⚠️ Honest limitation, stated rather than papered over: this assertion is
    # VACUOUS on a box whose .env sets OLLAMA_DEFAULT_MODEL to the same value as
    # recommender_model — which the dev box does (.env: OLLAMA_DEFAULT_MODEL=
    # gpt-oss:20b). That is a second reason D-2 survived locally, on top of the
    # routers being source-correct-looking. The non-vacuous check is
    # `test_logged_model_is_the_one_the_llm_path_actually_uses`, which compares
    # the setting NAMES in the two real modules and so cannot be fooled by two
    # settings that happen to agree. This one earns its place by covering the
    # other half: that the value actually reaches the row through the live path.
    assert row["model"] == settings.recommender_model, (
        f"the row records {row['model']!r}, but this route runs on "
        f"{settings.recommender_model!r}"
    )


async def test_nothing_is_written_when_disabled(
    client: AsyncClient, log_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Default-off means default-off: not an empty file, no file at all.

    The positive control is the test above — same harness, same route, one row.
    Without it this would pass against a writer that never worked.
    """
    monkeypatch.setattr(settings, "prompt_log_enabled", False)
    async with ollama_stub(content=_translatable()) as stub:
        monkeypatch.setattr(settings, "ollama_host", stub.base_url)
        response = await client.post("/query", json={"question": _TYPED})
    assert response.status_code == 200
    assert not log_dir.exists() or _rows(log_dir) == []


async def test_insights_query_is_logged_too(
    client_with_db: AsyncClient, log_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The second published LLM route writes its own row, tagged with its route.

    Its handler has five return points, three of them honest refusals — this
    drives a refusal deliberately (no corpus is seeded), because an unrecorded
    refusal is exactly the question an operator most wants to have seen.
    """
    async with ollama_stub(content=_translatable()) as stub:
        monkeypatch.setattr(settings, "ollama_host", stub.base_url)
        response = await client_with_db.post("/insights/query", json={"question": _TYPED})
    assert response.status_code == 200, response.text

    rows = [r for r in _rows(log_dir) if r["route"] == "/insights/query"]
    assert len(rows) == 1, f"expected one /insights/query row, got {len(rows)}"
    assert set(rows[0]) == _D6_FIELDS
    assert rows[0]["text"] == _TYPED


def test_rotation_deletes_beyond_retention_and_keeps_the_rest(tmp_path: Path) -> None:
    """Retention is enforced on the write path — there is no cron on that box."""
    now = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
    directory = tmp_path / "prompt-log"
    directory.mkdir()

    def plant(days_old: int) -> Path:
        day = (now - timedelta(days=days_old)).date().isoformat()
        path = directory / f"prompt-{day}.jsonl"
        path.write_text('{"text": "x"}\n', encoding="utf-8")
        return path

    ancient, just_over, just_under, today = plant(365), plant(91), plant(89), plant(0)
    unrelated = directory / "notes.txt"
    unrelated.write_text("not a log file", encoding="utf-8")

    deleted = prompt_log.rotate(directory, now=now)

    assert set(deleted) == {ancient, just_over}
    assert just_under.exists() and today.exists()
    # The 89/91 pair straddles the boundary on purpose: a rotation off by a day —
    # or one comparing the wrong direction — moves exactly one of them and would
    # otherwise look identical to a correct run.
    assert unrelated.exists(), "rotation must not touch files it did not write"


def test_rotation_reads_the_date_from_the_name_not_the_mtime(tmp_path: Path) -> None:
    """A restore or a volume remount rewrites mtimes; the name is written once.

    Keyed on mtime, a restored 2-year-old log would look brand new and outlive its
    retention silently — the failure mode of a promise nobody can see break.
    """
    now = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
    directory = tmp_path / "prompt-log"
    directory.mkdir()
    old_by_name = directory / "prompt-2020-01-01.jsonl"
    old_by_name.write_text("{}\n", encoding="utf-8")
    # Freshly written: its mtime is NOW, so an mtime-keyed rotation keeps it.
    assert old_by_name.stat().st_mtime > 0

    assert prompt_log.rotate(directory, now=now) == [old_by_name]
    assert not old_by_name.exists()


def test_logged_model_is_the_one_the_llm_path_actually_uses() -> None:
    """The row's `model` must name the model that ran, not a stale config default.

    PLAN-0100 Step 11 (D-2) caught the two disagreeing on the deployed demo: a
    single row recorded ``"model": "gemma4:26b"`` while the very same response
    reported ``phrased_by: "gpt-oss:20b"``. The routers were passing
    ``settings.ollama_default_model`` — the ADR-001 baseline, which nothing on this
    path reads — while ``nl_query`` builds its client from
    ``settings.recommender_model``.

    A wrong name is worse than a missing one for a D6 audit trail: ``gemma4:26b``
    is genuinely present on MS-S1, so nothing about the row looks suspect.

    Derived from both real modules rather than asserted against a literal — the
    invariant is "these two agree", so it survives either value being retuned.
    """
    sources = {
        "services/engine/nl_query.py": None,
        "services/api/routers/query.py": None,
        "services/api/routers/insights.py": None,
    }
    for relative in sources:
        sources[relative] = (REPO_ROOT / relative).read_text(encoding="utf-8")

    engine = re.search(
        r"OllamaClient\(\s*[^)]*?model=settings\.(\w+)",
        sources["services/engine/nl_query.py"],
        re.S,
    )
    assert engine, "could not find the OllamaClient construction in nl_query.py"
    engine_setting = engine.group(1)

    for router in ("services/api/routers/query.py", "services/api/routers/insights.py"):
        logged = re.search(
            r"prompt_log\.record\((?:[^()]|\([^()]*\))*?model=settings\.(\w+)",
            sources[router],
            re.S,
        )
        assert logged, f"could not find the prompt_log.record model argument in {router}"
        assert logged.group(1) == engine_setting, (
            f"{router} logs settings.{logged.group(1)} while the LLM path runs on "
            f"settings.{engine_setting}. The prompt log would name a model that never "
            f"served the request."
        )
