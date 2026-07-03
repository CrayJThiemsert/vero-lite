"""Admin / ops routes for the OCT demo (PLAN-0014).

``GET /warm``  — load the recommender model into MS-S1 VRAM (browser/phone
tappable; Ollama's GET endpoints only *list*, so this is the GET→POST bridge).
``GET /sleep`` — unload it (free VRAM).

Both are best-effort and report status; on an unreachable host they return
**HTTP 503** with ``reachable: false`` and never raise. Both are **host-state
changes on MS-S1**, so they carry the PLAN-0047 Step-1 authn dependency
(``GET /llm/status`` stays open — read-only UI poll). ``GET`` is intentional so
the address bar / a Telegram tap-link can trigger them (with authn enabled the
caller must supply the bearer key, or the deployment sets
``api_auth_enabled=false``); warming is effectively idempotent (a re-load just
resets the ``keep_alive`` window).
"""

from __future__ import annotations

import re
import time
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from services.api.auth import AuthContext, get_current_principal
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


def _status_client() -> OllamaClient:
    """Build an OllamaClient for the read-only ``GET /llm/status`` residency probe.

    Uses the **short, dedicated** ``llm_status_timeout_s`` (PLAN-0018 AC-5) — not
    the ~120 s generation timeout ``_client()`` carries — so a slow/half-down host
    degrades the poll fast instead of hanging for a generation-length window.
    Monkeypatched in tests.
    """
    return OllamaClient(
        base_url=settings.ollama_host,
        model=settings.recommender_model,
        timeout=settings.llm_status_timeout_s,
    )


def _split_tag(model: str) -> tuple[str, str]:
    """Split an Ollama model reference into ``(repo, tag)``; bare name ⇒ tag ``latest``."""
    ref = model.strip()
    if ":" in ref:
        repo, tag = ref.rsplit(":", 1)
        return repo, tag
    return ref, "latest"


def _model_matches(resident: str, configured: str) -> bool:
    """Tolerant tag matching for residency (PLAN-0018 AC-4 / R2).

    Ollama may report the resident model bare, with an implicit/explicit
    ``:latest``, or fully tagged. Match requires the **repo** to be equal; the
    tag matches when equal or when either side is the implicit ``latest`` — so a
    *foreign* model (different repo) is never counted resident, but a bare/latest
    report of the configured repo is.
    """
    r_repo, r_tag = _split_tag(resident)
    c_repo, c_tag = _split_tag(configured)
    if r_repo != c_repo:
        return False
    return r_tag == c_tag or r_tag == "latest" or c_tag == "latest"


def _coerce_dt(raw: str) -> datetime | None:
    """Parse an Ollama ISO timestamp, tolerating ``Z`` + 9-digit nanoseconds."""
    text = raw.strip().replace("Z", "+00:00")
    text = re.sub(r"(\.\d{6})\d+", r"\1", text)  # trim sub-microsecond precision
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _parse_expiry(raw: object) -> tuple[str | None, float | None, bool]:
    """Map an ``/api/ps`` ``expires_at`` to ``(iso, seconds_remaining, expired)``.

    No / unparseable expiry ⇒ ``(…, None, False)`` — we cannot prove eviction, so
    we conservatively do **not** mark the present model expired (avoids a false
    ``cold`` per AC-3). A timestamp in the past ⇒ ``expired=True`` (AC-6).
    """
    if not isinstance(raw, str) or not raw:
        return None, None, False
    parsed = _coerce_dt(raw)
    if parsed is None:
        return raw, None, False
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    remaining = (parsed - datetime.now(UTC)).total_seconds()
    return raw, round(remaining, 1), remaining <= 0


def _resident_entry(models: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the ``/api/ps`` entry for the configured recommender model, or None."""
    for entry in models:
        for key in ("name", "model"):
            name = entry.get(key)
            if isinstance(name, str) and _model_matches(name, settings.recommender_model):
                return entry
    return None


class LlmStatusResponse(BaseModel):
    """Read-only residency snapshot of the configured recommender model on MS-S1.

    Derived from ``GET /api/ps`` only — the poll never loads the model
    (PLAN-0018 INV-1) and changes no host state (INV-2). ``warming`` is **not** a
    backend state: a load in progress is not reliably observable from ``/api/ps``,
    so the demo-shell UI overlays a transient warming state between a warm click
    and the flip to ``resident`` (PLAN-0018 AC-8).
    """

    state: Literal["resident", "cold", "unreachable", "error"] = Field(
        description=(
            "resident = the configured model is loaded (non-expired); cold = host "
            "reachable but the model is not resident; unreachable = host down "
            "(connect refused/timeout); error = host reachable but errored "
            "(bad JSON / non-2xx) — never reported as cold (AC-3 / R1+R10)"
        )
    )
    reachable: bool = Field(description="Whether the MS-S1 Ollama host answered the probe at all")
    model: str = Field(
        description="The configured recommender model the probe judged residency for"
    )
    ollama_host: str = Field(description="The MS-S1 Ollama base URL probed")
    expires_at: str | None = Field(
        default=None,
        description="ISO timestamp when keep_alive evicts the resident model; null unless resident",
    )
    seconds_remaining: float | None = Field(
        default=None,
        description="Seconds until keep_alive eviction; null unless resident (AC-6 expiry honesty)",
    )
    detail: str | None = Field(
        default=None,
        description="Diagnostic message when state is unreachable or error; null otherwise",
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
    background_tasks: BackgroundTasks,
    _auth: Annotated[AuthContext, Depends(get_current_principal)],
    wait: bool = Query(default=True),
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
async def sleep(_auth: Annotated[AuthContext, Depends(get_current_principal)]) -> dict[str, Any]:
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


@router.get("/llm/status")
async def llm_status() -> LlmStatusResponse:
    """Read-only residency snapshot of the recommender model on MS-S1 (PLAN-0018).

    Built on ``GET /api/ps`` **only** — the poll never loads the model (INV-1)
    and is side-effect-free (INV-2). Browser/UI-pollable; poll at a documented
    interval (the demo shell polls ~every 5 s — D-1: a documented client interval,
    not a server-side cache, is sufficient at demo scale). Uses the short
    ``llm_status_timeout_s`` probe timeout (AC-5), decoupled from the generation
    timeout, so a slow/half-down host degrades fast instead of hanging the poll.
    """
    client = _status_client()
    host = settings.ollama_host
    model = settings.recommender_model
    try:
        models = await client.ps()
    except OllamaUnreachableError as exc:
        return LlmStatusResponse(
            state="unreachable", reachable=False, model=model, ollama_host=host, detail=str(exc)
        )
    except OllamaError as exc:
        # Reachable but errored (bad JSON / non-2xx / mid-gen timeout) — never cold (AC-3/R10).
        return LlmStatusResponse(
            state="error", reachable=True, model=model, ollama_host=host, detail=str(exc)
        )

    entry = _resident_entry(models)
    if entry is None:
        return LlmStatusResponse(state="cold", reachable=True, model=model, ollama_host=host)

    expires_at, seconds_remaining, expired = _parse_expiry(entry.get("expires_at"))
    if expired:
        # Listed but past its keep_alive window — honest cold, not resident (AC-6).
        return LlmStatusResponse(state="cold", reachable=True, model=model, ollama_host=host)

    return LlmStatusResponse(
        state="resident",
        reachable=True,
        model=model,
        ollama_host=host,
        expires_at=expires_at,
        seconds_remaining=seconds_remaining,
    )
