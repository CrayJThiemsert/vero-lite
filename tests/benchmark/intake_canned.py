"""The canned ``ChatClient`` the intake benchmark's offline tests drive.

Not a test module — a shared helper, in the shape of ``tests/api/js_source.py``.
It lives here because two test modules now need the same transport double and a
second copy would drift: ``test_intake_extraction_scenario.py`` (the AC-3 plumbing
scenario) and ``test_intake_instrument_residual_terms.py`` (PLAN-0119 Step 2).

It attaches at ``intake.py``'s own ``ChatClient`` Protocol seam (``intake.py:39-50``),
which exists precisely so extraction can be driven offline. That is the transport
**beyond** the plumbing under test, not one side of it — nothing between a gold case
and a scored outcome is replaced by using it.
"""

from __future__ import annotations

from typing import Any

from services.engine.llm.client import ChatResult


class CannedTransport:
    """A ``ChatClient`` that replays pre-set message bodies instead of calling a box.

    When the scripted contents run out it repeats the last one, so a single valid
    body can serve a whole-gold-set run without the script having to enumerate every
    case.
    """

    def __init__(
        self,
        contents: list[str],
        *,
        model: str = "canned-model",
        raises: Exception | None = None,
        envelopes: list[dict[str, Any]] | None = None,
        thinkings: list[str | None] | None = None,
    ) -> None:
        self._contents = contents
        self._model = model
        self._raises = raises
        # `envelopes` is the Ollama response envelope `ChatResult.raw` carries — the
        # generation accounting (`done_reason`, `eval_count`, the ns durations) the
        # recorder reads via `call_metrics`. Default `{}` keeps every pre-existing
        # test on the optional-tolerant path, which is itself the behaviour a live
        # server with an older envelope would produce.
        self._envelopes = envelopes
        self._thinkings = thinkings
        self.calls = 0
        #: What ``think`` actually arrived on each call. Recorded because PLAN-0119
        #: Step 2's ``--think`` claim is about what reaches the WIRE — asserting on
        #: the flag the runner parsed would only prove that argparse works.
        self.thinks: list[bool | str | None] = []

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | str | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        self.calls += 1
        self.thinks.append(think)
        if self._raises is not None:
            raise self._raises
        index = min(self.calls - 1, len(self._contents) - 1)

        def _pick(seq: list[Any] | None, default: Any) -> Any:
            if seq is None:
                return default
            return seq[min(self.calls - 1, len(seq) - 1)]

        return ChatResult(
            content=self._contents[index],
            thinking=_pick(self._thinkings, None),
            model=self._model,
            raw=_pick(self._envelopes, {}),
        )
