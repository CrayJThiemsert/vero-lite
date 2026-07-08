"""`GET /whoami` response model (PLAN-0058, SD-1 minimal shape)."""

from pydantic import BaseModel, Field


class WhoamiResponse(BaseModel):
    """Echo of the principal a bearer key resolves to via the auth seam.

    The frontend ``login()`` probes ``GET /whoami`` as the ONE
    auth-validating read so a bad key is rejected AT login instead of on the
    first operate POST. Shape ratified as SD-1 (minimal echo).
    """

    person_id: str | None = Field(
        default=None,
        description=(
            "the server-resolved principal id the bearer key maps to; null when "
            "auth is disabled (dev/demo open mode)"
        ),
    )
    display_name: str | None = Field(
        default=None,
        description=(
            "the resolved Person's display name; null when auth is disabled OR the "
            "active vertical ships no authored principals to resolve against"
        ),
    )
    auth_enabled: bool = Field(
        description=(
            "whether API-key auth is enforced — false is the dev/demo open mode where "
            "every endpoint is ungated and person_id is null"
        ),
    )
