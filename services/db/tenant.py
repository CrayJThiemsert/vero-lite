"""The tenant key — one definition, shared by every mapped table (ADR-0035 D7).

PLAN-0101 SD-1 ruled **(b)**: the write stamp is a column-level Python default
(``default=lambda: settings.tenant_id``), deliberately with **no**
``server_default`` — an unstamped write must fail ``NOT NULL`` loudly rather than
land silently under a database-side default nobody chose. SD-1's Step-1.4
measurement is why that matters: neither ``alembic check`` nor
``--autogenerate`` can see a ``server_default`` that drifts back in, so the
absence is a claim the tooling cannot check for us.

PLAN-0101 SD-2 ruled **(b)**: the generator special-cases the key rather than the
ontology carrying it. SD-1(b) + SD-2(b) compose here — this mixin holds both the
column and its default, and ``code_generator.emit_orm`` emits it onto every
generated class exactly as the hand-written models inherit it. That is what keeps
**one** definition of the tenant column in the tree: a second, inline copy in the
emitter template would drift from this one silently.

A column-level Python default covers ORM *and* Core inserts, which is why SD-1
option (a)'s session-seam bypass does not exist. It is late-bound (evaluated at
INSERT), so a test can exercise a non-default tenant by monkeypatching the
settings object without restarting the process — the idiom the two-tenant fixture
relies on.

The key is **not** part of the semantic layer: it never enters the ontology, any
generated semantic surface, or the resolved-procedures governance hash. Keeping it
out of the ontology is load-bearing rather than tidy — the ontology is the
allowlist ``nl_query._validate_query`` checks a model-authored filter against, so
a key the ontology does not declare is one an LLM cannot name, and cross-tenant
selection stays inexpressible through the NL-query path.
"""

from __future__ import annotations

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from services.api.config import settings

TENANT_COLUMN_NAME = "tenant_id"
"""The column name, shared with ``code_generator`` so the emitted DDL and this
mixin cannot disagree about what the generated ORM inherits."""


class TenantKeyMixin:
    """Adds the ``tenant_id`` column, stamped from ``settings.tenant_id`` at INSERT.

    Mixed into every mapped class — the 14 hand-written tables by import, the 7
    generated ones because ``emit_orm`` writes the mixin into the class header.
    A new table that forgets it is caught by PLAN-0101 AC-5's set-equality guard,
    not by review.
    """

    tenant_id: Mapped[str] = mapped_column(Text, nullable=False, default=lambda: settings.tenant_id)
