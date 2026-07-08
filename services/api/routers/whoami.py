"""`GET /whoami` — echo the principal a bearer key resolves to (PLAN-0058).

A thin read over the SINGLE fail-closed auth seam (``get_current_principal``):
it neither forks nor extends the seam's validation — it *reads* the resolved
``AuthContext``. The frontend ``login()`` reuses it as the one auth-validating
probe so a bad key rejects at login (SD-2 fail-closed / SD-3 reject-at-login).
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from services.api.auth import AuthContext, get_current_principal
from services.api.config import settings
from services.api.models.whoami import WhoamiResponse

router = APIRouter(tags=["auth"])


@router.get("/whoami", response_model=WhoamiResponse)
async def whoami(
    auth: Annotated[AuthContext, Depends(get_current_principal)],
) -> WhoamiResponse:
    """Echo the principal the bearer key resolves to, fail-closed.

    The shared dependency fails closed BEFORE this handler runs: a
    missing/malformed or unknown key → 401, and an authenticated subject with
    no ``Person`` mapping in a principals-shipping vertical → 403. With auth
    disabled the dependency is inert, so this returns ``person_id=null`` +
    ``auth_enabled=false`` (dev/demo open mode). No mutation, no DB — a pure
    projection of the resolved ``AuthContext``.
    """
    return WhoamiResponse(
        person_id=auth.person_id,
        display_name=auth.person.name if auth.person is not None else None,
        auth_enabled=settings.api_auth_enabled,
    )
