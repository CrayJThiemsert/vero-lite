"""API-key authentication for state-changing routes (PLAN-0047 Step 1, SD-1 = (a)).

Pilot-grade static per-person API keys: ``settings.api_keys`` maps the
SHA-256 hex digest of a raw bearer key to the ``person_id`` it
authenticates. The raw key travels only in the ``Authorization: Bearer``
header; the server holds digests, never raw keys (CLAUDE.md §8 — keys
live in env / ``.env``, outside git).

Fail-closed semantics (AC-1):

- missing / malformed / unknown credential → **401**;
- authenticated ``person_id`` with no ``Person`` mapping in the active
  vertical's authored principal set → **403** — membership is enforceable
  only when that vertical *ships* principals (procurement is the only
  N=1 today, ADR-0026); a vertical with no authored principal set gets
  identity recorded with ``person=None`` and membership enforcement arms
  itself the moment principals are authored (the OQ-6 N≥2 marker tracks
  that boundary);
- ``api_auth_enabled=false`` → the dependency is inert
  (``AuthContext(None, None)``) — an explicit per-deployment dev/demo
  escape, default **on**.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Annotated

from fastapi import Header, HTTPException

from services.api.config import settings
from services.engine.procedures.spec import Person, load_procedures


@dataclass(frozen=True)
class AuthContext:
    """The authenticated caller of a state-changing request.

    ``person_id`` is ``None`` only when authn is disabled; ``person`` is
    ``None`` when disabled OR when the active vertical ships no authored
    principal set to resolve against.
    """

    person_id: str | None
    person: Person | None


def _principal_index(vertical: str) -> dict[str, Person]:
    """The active vertical's authored principals keyed by ``person_id``.

    Empty when the vertical has no procedures file or ships no
    ``principals`` block — parsed per request (approve/execute are rare
    human actions; no cache means no staleness after a YAML edit).
    """
    try:
        procedures = load_procedures(vertical)
    except FileNotFoundError:
        return {}
    return {p.person_id: p for p in procedures.principals}


async def get_current_principal(
    authorization: Annotated[str | None, Header()] = None,
) -> AuthContext:
    """FastAPI dependency: authenticate a state-changing request, fail-closed.

    The principal is resolved SERVER-side from the bearer key — request
    bodies never carry (and are never trusted for) an identity (AC-2).
    """
    if not settings.api_auth_enabled:
        return AuthContext(person_id=None, person=None)
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="missing or malformed Authorization bearer API key"
        )
    raw_key = authorization.removeprefix("Bearer ").strip()
    digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    person_id = settings.api_keys.get(digest)
    if person_id is None:
        raise HTTPException(status_code=401, detail="unknown API key")
    index = _principal_index(settings.oct_vertical)
    if index:
        person = index.get(person_id)
        if person is None:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"authenticated subject '{person_id}' has no Person mapping in "
                    f"vertical '{settings.oct_vertical}'"
                ),
            )
        return AuthContext(person_id=person_id, person=person)
    return AuthContext(person_id=person_id, person=None)
