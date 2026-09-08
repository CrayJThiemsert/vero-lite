"""PLAN-0119 Step 4 / AC-7 — a truncated A Author draft says so on disk (D-2).

Its own module (battery denominators — see ``test_capacity.py``'s header). The
happy path and the other fallback shapes are covered by
``test_scaffold_llm.py``; nothing here duplicates them.

**The defect this closes.** ``llm_synthetic_or_none`` logs *"LLM synthetic draft
unusable; using the deterministic draft"* for every failure it swallows. That
sentence is equally true of a transport fault and of a draft the server CUT at
``num_predict``, and the A Author call — the largest output in the system — is
the likeliest in the repo to hit its cap. So the two most different diagnoses
available ("raise the cap" vs "the model is broken") produced a byte-identical
record, and nothing on disk could separate them.

⚠️ These tests read a LOG LINE, which is an unusual oracle. It is the right one
here: the log line IS the artifact D-2 is about. A test asserting on an exception
object would pass on a system whose operator still cannot tell the two failures
apart, which is the whole complaint.
"""

from __future__ import annotations

import logging
from typing import Any

import pytest

from services.engine import scaffold
from services.engine.llm.client import ChatResult
from services.engine.scaffold import RecommendConfig

_SRC_ROOT = __import__("pathlib").Path(__file__).resolve().parents[3]


def _doc() -> dict[str, Any]:
    from services.engine import code_generator

    return code_generator.load_doc(
        _SRC_ROOT / "verticals" / "energy" / "ontology" / "energy_v0.yaml"
    )


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


class _TruncatedClient:
    """A double returning exactly what a cap-truncated call returns.

    Empty content and ``done_reason="length"`` with ``eval_count`` equal to the
    configured cap is the envelope PLAN-0118 measured on all 45 empty attempts,
    and the shape Ollama issue #17978 reports. Not invented for this test.
    """

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> ChatResult:
        return ChatResult(
            content="",
            thinking=None,
            model="gpt-oss:20b",
            raw={
                "done_reason": "length",
                "eval_count": 1024,
                "prompt_eval_count": 741,
                "message": {"role": "assistant", "content": ""},
            },
        )


class _StoppedButUnparseableClient:
    """A draft the model FINISHED and that still will not parse.

    The contrast case: same unusable outcome, entirely different diagnosis. This
    is what makes the truncation disclosure a measurement rather than a constant.
    """

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> ChatResult:
        return ChatResult(
            content="{not json at all",
            thinking=None,
            model="gpt-oss:20b",
            raw={
                "done_reason": "stop",
                "eval_count": 37,
                "prompt_eval_count": 741,
                "message": {"role": "assistant", "content": "{not json at all"},
            },
        )


def _run(monkeypatch: pytest.MonkeyPatch, client: Any) -> None:
    monkeypatch.setattr(scaffold, "_build_chat_client", lambda: client)
    roles = scaffold.detect_roles(_doc())
    result = scaffold.llm_synthetic_or_none(roles, _config(), _doc())
    assert result is None, "an unusable draft must still fall back, not raise"


def test_a_truncated_draft_records_done_reason_length(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """AC-7. The witness the criterion names: a double returning
    ``done_reason="length"`` with empty content.
    """
    with caplog.at_level(logging.WARNING, logger="services.engine.scaffold"):
        _run(monkeypatch, _TruncatedClient())

    text = caplog.text
    assert "done_reason='length'" in text, f"a cut draft must say so; the warning was: {text!r}"


def test_the_disclosure_carries_the_count_that_makes_a_cut_legible(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """``eval_count`` equal to the configured cap is the signature of a cut.

    ``done_reason`` alone says generation stopped at a limit; the count is what
    lets a reader check it against the budget that was actually sent.
    """
    with caplog.at_level(logging.WARNING, logger="services.engine.scaffold"):
        _run(monkeypatch, _TruncatedClient())

    text = caplog.text
    missing = [token for token in ("eval_count=1024", "content_chars=0") if token not in text]
    assert not missing, f"the disclosure omitted {missing}; warning was: {text!r}"


def test_a_finished_but_unparseable_draft_is_not_reported_as_truncated(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """🔴 The POSITIVE CONTROL, and the reason the test above proves anything.

    A disclosure hard-coded to say ``'length'`` would satisfy AC-7's witness
    perfectly while telling an operator the same thing about every failure —
    which is the defect D-2 describes, wearing a new sentence. This asserts the
    reported reason TRACKS the server's, by driving the other case through the
    same path and requiring a different answer.
    """
    with caplog.at_level(logging.WARNING, logger="services.engine.scaffold"):
        _run(monkeypatch, _StoppedButUnparseableClient())

    text = caplog.text
    assert (
        "done_reason='stop'" in text
    ), f"the reported reason must track the server's; warning was: {text!r}"
    assert (
        "done_reason='length'" not in text
    ), f"a finished draft must not be reported as truncated; warning was: {text!r}"


def test_a_double_without_a_full_envelope_still_falls_back(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The never-raise contract survives a client that returns something odd.

    Enrichment is best-effort; a disclosure helper that broke the fallback it is
    describing would be strictly worse than the bare sentence it replaced.
    """

    class _BareClient:
        async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> Any:
            return object()

    with caplog.at_level(logging.WARNING, logger="services.engine.scaffold"):
        _run(monkeypatch, _BareClient())

    assert "unusable" in caplog.text, f"the fallback must still be logged: {caplog.text!r}"
