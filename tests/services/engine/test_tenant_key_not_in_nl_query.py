"""AC-11 — an LLM cannot express a cross-tenant query (PLAN-0101, Cray's call 2).

**The worry this answers, in Cray's framing:** that with ``tenant_id`` absent from
the ontology, a future LLM processing ontology data might sweep across tenants and
mix them, producing an answer that is confidently wrong.

**Why the answer runs the opposite way to the intuition.** The NL-query path never
writes SQL — measured, zero raw-SQL execution sites across ``services/``. A question
becomes a ``StructuredQuery`` through constrained generation, and
``nl_query._validate_query`` checks every ``filters[].property`` against the object
type's property list *drawn from the ontology*. So the ontology is not merely a
description; it is the **allowlist of what a model is permitted to name**.

Putting ``tenant_id`` in the ontology would therefore make cross-tenant selection
*expressible* — the model could emit ``filters: [{property: "tenant_id", ...}]`` and
the validator would wave it through. Leaving it out makes that query
**inexpressible**, which is a structural guarantee rather than a behavioural hope,
and it does not depend on the model being careful. SD-2's ruling (b) is what keeps
the key out; this file is what keeps it *asserted* instead of incidental.

**Non-vacuity.** These tests fail the day someone adds ``tenant_id`` to an ontology
YAML: the property would validate, the rejection assertion would find no error, and
the guard reddens loudly rather than quietly permitting the thing it exists to
forbid.

**No D7(vii) breach.** This asserts an ABSENCE. It builds no per-request tenant
resolution, no row-level security, and no tenant-scoped authn.
"""

from __future__ import annotations

import pytest

from services.engine.nl_query import QueryFilter, StructuredQuery, _validate_query
from services.engine.ontology_meta import load_ontology_meta

_VERTICALS = ("energy", "supply_chain")


def _type_index(vertical: str) -> dict[str, object]:
    meta = load_ontology_meta(vertical)
    return {obj.name: obj for obj in meta.object_types}


def _first_type(vertical: str) -> str:
    return load_ontology_meta(vertical).object_types[0].name


@pytest.mark.parametrize("vertical", _VERTICALS)
def test_a_filter_naming_the_tenant_key_is_rejected(vertical: str) -> None:
    """The validator refuses ``tenant_id`` as a filter property, in every vertical.

    Parameterised over more than one vertical on purpose: a single-vertical check
    would pass if some *other* ontology quietly declared the key.
    """
    object_type = _first_type(vertical)
    query = StructuredQuery(
        object_type=object_type,
        filters=[QueryFilter(property="tenant_id", op="eq", value="acme")],
    )
    errors = _validate_query(query, _type_index(vertical))  # type: ignore[arg-type]
    assert errors, (
        f"{vertical}: a filter on 'tenant_id' was ACCEPTED — the key has entered the "
        "ontology, and an LLM can now select across tenants"
    )
    assert any("tenant_id" in message for message in errors), errors


@pytest.mark.parametrize("vertical", _VERTICALS)
def test_the_tenant_key_is_not_a_property_of_any_object_type(vertical: str) -> None:
    """The same fact one layer down — no object type declares it at all.

    The validator test above could in principle pass for the wrong reason (a
    validator bug rejecting everything). This one reads the ontology projection
    directly, so the two fail independently.
    """
    offenders = [
        f"{obj.name}.{prop.name}"
        for obj in load_ontology_meta(vertical).object_types
        for prop in obj.properties
        if prop.name == "tenant_id"
    ]
    assert offenders == [], (
        f"{vertical}: tenant_id is declared on {offenders} — SD-2 ruled (b), the key "
        "stays out of the semantic layer so it never becomes domain vocabulary a "
        "model can reason or filter on"
    )


@pytest.mark.parametrize("vertical", _VERTICALS)
def test_a_legitimate_filter_is_still_accepted(vertical: str) -> None:
    """The positive control. Without it, a validator that rejected EVERY filter
    would satisfy the two tests above while having broken NL query entirely — the
    rejection assertion would be true for the wrong reason."""
    meta = load_ontology_meta(vertical)
    obj = next(o for o in meta.object_types if o.properties)
    prop = obj.properties[0]
    query = StructuredQuery(
        object_type=obj.name,
        filters=[QueryFilter(property=prop.name, op="eq", value="anything")],
    )
    errors = _validate_query(query, _type_index(vertical))  # type: ignore[arg-type]
    assert errors == [], f"{vertical}: a real property was rejected: {errors}"
