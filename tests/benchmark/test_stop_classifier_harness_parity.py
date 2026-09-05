"""AC-2 — the eval harness sends production's request and honours its timeout.

PLAN-0122 D-2. Before this, ``run_eval`` drove ``services.engine.llm.client.
OllamaClient``, which sends ``num_predict=settings.llm_max_output_tokens``
(1024). Production's ``_call_ollama`` sends no cap at all. That single field
made the harness a different system from the one it claimed to measure: under
the cap the measured empty-body rate was 53% for ``gpt-oss:20b`` against 74-75%
for both qwen candidates, so the benchmark penalised the challengers before any
judgement was made — and the reasoning pass, not the answer, is what overran the
budget (PLAN-0122 L-4).

Parity is asserted three ways, because each catches a different divergence:

* **A1 body** — the harness's body must equal the one production actually puts
  on the wire, captured by monkeypatching ``urlopen`` under BOTH. Comparing
  against a hand-written expected dict would only re-assert what this test's
  author believed production sends.
* **A2 timeout resolution** — the harness must READ ``sc.OLLAMA_TIMEOUT_SEC``,
  not copy it. Asserted by moving the production constant and watching the
  harness follow.
* **A3 timeout behaviour** — a resolved number proves nothing if it never
  reaches ``urlopen``. A stub that answers slower than the timeout must make
  both production and the harness raise, in the same window.
"""

from __future__ import annotations

import json
import threading
import time
import urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import pytest

from benchmarks.stop_classifier.run_eval import (
    build_request_body,
    post_chat,
    resolve_timeout,
    sc,
)

MODEL = "gpt-oss:20b"
SYSTEM = "system prompt under test"
USER = "user message under test"


class _Capture:
    """Stand-in for ``urlopen`` that records the request and returns a valid reply."""

    def __init__(self) -> None:
        self.body: dict[str, Any] | None = None
        self.timeout: float | None = None

    def __call__(self, request: Any, timeout: float | None = None) -> Any:
        self.body = json.loads(request.data.decode("utf-8"))
        self.timeout = timeout
        reply = json.dumps(
            {
                "message": {
                    "role": "assistant",
                    "content": '{"decision":"pause",' '"matched_rows":[],"reason":"x"}',
                }
            }
        ).encode("utf-8")

        class _Response:
            def read(self) -> bytes:
                return reply

            def __enter__(self) -> Any:
                return self

            def __exit__(self, *exc: object) -> bool:
                return False

        return _Response()


def test_harness_body_equals_production_body(monkeypatch: pytest.MonkeyPatch) -> None:
    """A1 — same model, system and user produce byte-equal request bodies."""
    monkeypatch.setenv("CLAUDE_CLASSIFIER_OLLAMA_MODEL", MODEL)

    prod_capture = _Capture()
    monkeypatch.setattr(sc.urllib.request, "urlopen", prod_capture)
    sc._call_ollama(SYSTEM, USER)
    prod_body = prod_capture.body
    assert prod_body is not None

    harness_body = build_request_body(MODEL, SYSTEM, USER)

    print(
        f"prod_options={prod_body['options']} harness_options={harness_body['options']} "
        f"prod_keys={sorted(prod_body)} harness_keys={sorted(harness_body)}"
    )
    assert "num_predict" not in prod_body["options"], "production grew a cap; re-measure L-4"
    assert harness_body == prod_body


def test_harness_timeout_follows_the_production_constant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A2 — the timeout is read from production, not copied from it.

    The shipped value is not hard-coded here on purpose: this asserts that the
    harness TRACKS the constant, which stays true if the constant is retuned.
    """
    shipped = float(sc.OLLAMA_TIMEOUT_SEC)
    pre = resolve_timeout(None)
    monkeypatch.setattr(sc, "OLLAMA_TIMEOUT_SEC", 3)
    post = resolve_timeout(None)
    print(f"pre={pre:.0f} post={post:.0f}")
    assert pre == shipped, "the harness did not read the shipped constant"
    assert post == 3.0, "the harness kept a copy instead of reading production"
    assert pre != post, "the patch must be observable, or this test proves nothing"
    assert resolve_timeout(12.5) == 12.5, "an explicit flag still wins"


class _SlowHandler(BaseHTTPRequestHandler):
    """Answers later than any timeout under test, so the caller must give up first."""

    def do_POST(self) -> None:  # noqa: N802 — BaseHTTPRequestHandler's API
        time.sleep(4.0)
        # The caller has already given up by now, so the socket is gone. That is
        # the point of the fixture; swallow the resulting broken pipe rather than
        # letting socketserver print a traceback that looks like a test failure.
        try:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"{}")
        except (BrokenPipeError, ConnectionResetError):
            return

    def log_message(self, *args: Any) -> None:
        return


@pytest.fixture()
def slow_server() -> Any:
    server = HTTPServer(("127.0.0.1", 0), _SlowHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()


def test_both_transports_time_out_in_the_same_window(
    slow_server: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A3 — the resolved timeout actually reaches the socket, in both.

    Without this, A2 could pass on a number the transport never uses.
    """
    monkeypatch.setattr(sc, "OLLAMA_TIMEOUT_SEC", 1)
    monkeypatch.setenv("CLAUDE_CLASSIFIER_OLLAMA_URL", slow_server)

    # The families the hook's own _run_with_retry catches; narrower than
    # Exception so a genuine bug cannot pass as a timeout.
    gave_up = (TimeoutError, urllib.error.URLError)

    start = time.perf_counter()
    with pytest.raises(gave_up):
        sc._call_ollama(SYSTEM, USER)
    prod_t = time.perf_counter() - start

    start = time.perf_counter()
    with pytest.raises(gave_up):
        post_chat(slow_server, build_request_body(MODEL, SYSTEM, USER), resolve_timeout(None))
    harness_t = time.perf_counter() - start

    print(f"prod_t={prod_t:.2f} harness_t={harness_t:.2f}")
    assert 1.0 <= prod_t <= 2.5, prod_t
    assert 1.0 <= harness_t <= 2.5, harness_t
