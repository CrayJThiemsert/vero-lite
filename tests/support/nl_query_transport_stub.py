"""A ChatClient stub that replaces the MODEL TRANSPORT and nothing else.

Shared by the tests that must drive the *real* NL-query engine offline: the
grouped-count scenario (PLAN-0104 AC-2) and the gold-set-versus-engine check.
Both make the same claim — that execute, relabel and phrase are the shipped code
running on real data — so the claim is worth having in exactly one place where a
reviewer can check it.

What is faked: the HTTP call to the model. A call carrying ``response_format`` is
the translate stage and returns canned JSON; a call without one is the phrase
stage and raises, which routes phrasing to the engine's real deterministic
template. Both are transport behaviours the engine already handles.

What is NOT faked: every engine seam. Nothing here stubs validation, execution,
relabelling, phrasing or the data adapter — a test that stubbed either side of
the seam under test would agree with itself by construction.
"""

from __future__ import annotations

import json
from typing import Any

from services.engine.llm.client import ChatResult, OllamaError


class TranslateOnlyStub:
    """Return a canned translate response; fail the phrase call.

    ``phrase`` may be supplied to exercise the LLM phrasing arm instead of the
    deterministic fallback; by default the phrase transport raises, because most
    callers want to assert on text the engine itself authored.
    """

    def __init__(self, query: dict[str, Any], *, phrase: str | None = None) -> None:
        self._query_json = json.dumps(query)
        self._phrase = phrase
        self.translate_calls = 0
        self.phrase_calls = 0

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        if response_format is not None:  # translate stage
            self.translate_calls += 1
            return ChatResult(content=self._query_json, thinking=None, model="stub", raw={})
        if self._phrase is None:  # phrase stage — degrade to the real template
            raise OllamaError("forced phrase transport failure — use the deterministic answer")
        self.phrase_calls += 1
        return ChatResult(content=self._phrase, thinking=None, model="stub", raw={})
