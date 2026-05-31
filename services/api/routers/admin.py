"""Admin / ops routes for the OCT demo (PLAN-0014).

``GET /warm``  — load the recommender model into MS-S1 VRAM (browser/phone
tappable; Ollama's GET endpoints only *list*, so this is the GET→POST bridge).
``GET /sleep`` — unload it (free VRAM).

Both are best-effort and report status; on an unreachable host they return
**HTTP 503** with ``reachable: false`` and never raise. Phase-2 demo endpoints:
**no auth** (LAN/localhost demo box), consistent with the other unauthenticated
demo routes. ``GET`` is intentional so the address bar / a Telegram tap-link can
trigger them; warming is effectively idempotent (a re-load just resets the
``keep_alive`` window).
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from services.api.config import settings
from services.engine.llm.client import OllamaClient, OllamaError, OllamaUnreachableError

router = APIRouter(tags=["admin"])


def _client() -> OllamaClient:
    """Build an OllamaClient for the configured model + host (monkeypatched in tests)."""
    return OllamaClient(
        base_url=settings.ollama_host,
        model=settings.recommender_model,
        timeout=settings.llm_request_timeout_s,
    )


async def _ps_safe(client: OllamaClient) -> list[dict[str, Any]]:
    """Best-effort ``/api/ps`` — never raises (status reporting is non-critical)."""
    try:
        return await client.ps()
    except OllamaError:
        return []


async def _warm_bg(client: OllamaClient) -> None:
    """Background warm for the ``?wait=false`` path — swallow all errors."""
    try:
        await client.warm(keep_alive=settings.ollama_keep_alive)
    except OllamaError:
        pass


@router.get("/warm")
async def warm(
    background_tasks: BackgroundTasks, wait: bool = Query(default=True)
) -> dict[str, Any]:
    """Load the configured model into MS-S1 VRAM. Browser/phone-hittable (GET).

    Default **blocks** until loaded (~11s cold, instant if already resident) and
    reports ``load_seconds``. ``?wait=false`` schedules the load and returns
    immediately with ``warming: true``.
    """
    client = _client()
    if not wait:
        background_tasks.add_task(_warm_bg, client)
        return {
            "model": settings.recommender_model,
            "ollama_host": settings.ollama_host,
            "warming": True,
        }
    started = time.monotonic()
    try:
        result = await client.warm(keep_alive=settings.ollama_keep_alive)
    except OllamaUnreachableError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "reachable": False,
                "model": settings.recommender_model,
                "ollama_host": settings.ollama_host,
                "error": str(exc),
            },
        ) from exc
    except OllamaError as exc:
        raise HTTPException(
            status_code=502, detail={"reachable": True, "loaded": False, "error": str(exc)}
        ) from exc
    return {
        "model": settings.recommender_model,
        "ollama_host": settings.ollama_host,
        "reachable": True,
        "loaded": True,
        "done_reason": result.get("done_reason"),
        "load_seconds": round(time.monotonic() - started, 2),
        "ps": await _ps_safe(client),
    }


@router.get("/sleep")
async def sleep() -> dict[str, Any]:
    """Unload the configured model from MS-S1 VRAM (free it). Browser-hittable (GET)."""
    client = _client()
    try:
        result = await client.unload()
    except OllamaUnreachableError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "reachable": False,
                "model": settings.recommender_model,
                "ollama_host": settings.ollama_host,
                "error": str(exc),
            },
        ) from exc
    except OllamaError as exc:
        raise HTTPException(
            status_code=502, detail={"reachable": True, "unloaded": False, "error": str(exc)}
        ) from exc
    return {
        "model": settings.recommender_model,
        "ollama_host": settings.ollama_host,
        "reachable": True,
        "unloaded": True,
        "done_reason": result.get("done_reason"),
        "ps": await _ps_safe(client),
    }
