"""A real local HTTP server speaking the Ollama chat contract (PLAN-0100 AC-7/AC-8).

Stands in for the **upstream dependency** (Ollama on MS-S1) and for nothing else.
The cap under test, the routes, the degrade path and the prompt-log writer are
all the real ones — per the AC preamble, a local stand-in may replace the
upstream and never the thing being measured.

It is a real socket on loopback, not an ``httpx.MockTransport``, for two reasons.
The in-flight cap is about **concurrency**, and a mock transport that returns
without yielding to the event loop cannot produce two genuinely overlapping
requests. And the conftest ``_no_outbound_network`` guard permits loopback
precisely so a stand-in like this is possible without the ``host_state`` marker
that would make it a live-model run.

``delay`` is what makes the overlap addressable: with it, request A is provably
still inside the client when request B arrives.
"""

from __future__ import annotations

import asyncio
import socket
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route


@dataclass
class StubState:
    """What the stub saw, for assertions after the fact."""

    base_url: str = ""
    #: One entry per ``/api/chat`` call that ARRIVED, in arrival order.
    calls: list[dict[str, Any]] = field(default_factory=list)
    #: The high-water mark of concurrent in-flight calls the stub itself observed.
    #: This is the stub's independent witness that the cap did its job: if the cap
    #: works, no two requests are ever inside the upstream at once, and asserting
    #: on the app's own reporting alone would be asserting on the thing under test.
    max_concurrent: int = 0
    _active: int = 0


def _free_port() -> tuple[socket.socket, int]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    sock.listen(64)
    return sock, sock.getsockname()[1]


@asynccontextmanager
async def ollama_stub(
    *,
    delay: float = 0.0,
    content: str = '{"answer": "stubbed"}',
    model: str = "stub-model",
) -> AsyncIterator[StubState]:
    """Serve the Ollama ``/api/chat`` contract on loopback for the block's duration."""
    state = StubState()

    async def chat(request: Request) -> JSONResponse:
        body = await request.json()
        state.calls.append(body)
        state._active += 1
        state.max_concurrent = max(state.max_concurrent, state._active)
        try:
            if delay:
                await asyncio.sleep(delay)
            return JSONResponse(
                {
                    "model": body.get("model", model),
                    "message": {"role": "assistant", "content": content},
                    "done": True,
                }
            )
        finally:
            state._active -= 1

    app = Starlette(routes=[Route("/api/chat", chat, methods=["POST"])])
    sock, port = _free_port()
    state.base_url = f"http://127.0.0.1:{port}"
    # log_config=None is load-bearing, not tidiness. uvicorn.Config applies a
    # GLOBAL logging dictConfig by default, which sets propagate=False on
    # "uvicorn.error" — so merely constructing this stub silently broke
    # tests/test_startup_log.py's caplog assertion elsewhere in the suite, while
    # the line it looked for was still being written to stderr. A stand-in must
    # not reconfigure the process it is standing in for.
    server = uvicorn.Server(
        uvicorn.Config(app, log_level="warning", lifespan="off", log_config=None)
    )
    task = asyncio.create_task(server.serve(sockets=[sock]))
    try:
        while not server.started:
            await asyncio.sleep(0.01)
        yield state
    finally:
        server.should_exit = True
        await task
        sock.close()
