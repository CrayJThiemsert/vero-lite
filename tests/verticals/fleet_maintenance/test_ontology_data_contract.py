"""The fleet ontology and the rows it describes must agree (PLAN-0096 Step 8).

**Why this file exists.** Fleet was the only vertical with no adapter test. Energy and
supply_chain both emit Pydantic from their YAML and validate every synthetic row against
it; fleet's adapter returns raw dicts unvalidated. That gap has a specific, silent failure
mode, and it is the one this file closes:

    declare a property in the ontology, forget the value in ``synthetic.py``, and NOTHING
    goes red — while ``load_ontology_meta`` cheerfully advertises the property to the
    NL-query translate prompt, so the LLM is told the field exists and every question
    about it comes back confidently empty.

That is worse than a missing feature, because the answer looks authoritative. The tests
below are generic over the ontology rather than pinned to today's property list, so they
keep working for the next property somebody adds.

The two properties that prompted it — ``Truck.accounting_code`` (รหัสรถ) and
``Vendor.accounting_code`` (รหัสผู้ขาย) — are AC-9 export columns 8 and 6, deliberately
placed in the ontology rather than in an export-side lookup so the LLM can reason over
them (Cray, typed s190).
"""

from __future__ import annotations

import pytest

from services.engine.nl_query import _describe_ontology
from services.engine.ontology_meta import load_ontology_meta
from verticals.fleet_maintenance.data_adapter import synthetic

_VERTICAL = "fleet_maintenance"


@pytest.fixture(scope="module")
def meta():  # type: ignore[no-untyped-def]
    return load_ontology_meta(_VERTICAL)


# --------------------------------------------------------------------------- #
# The contract: what the ontology declares, the rows carry
# --------------------------------------------------------------------------- #


def test_every_required_property_is_present_in_every_row(meta) -> None:  # type: ignore[no-untyped-def]
    """A `required: true` property missing from the data is a broken promise.

    Generic over the ontology on purpose — this is the guard for the NEXT property
    somebody adds, not a restatement of today's list."""
    for object_type, source in synthetic.OBJECT_SOURCES.items():
        declared = next((o for o in meta.object_types if o.name == object_type), None)
        assert declared is not None, f"{object_type} is served but not declared"
        required = {p.name for p in declared.properties if p.required}
        for row in source():
            missing = required - set(row)
            assert not missing, f"{object_type} row {row} is missing required {sorted(missing)}"


def test_no_row_carries_a_property_the_ontology_never_declared(meta) -> None:  # type: ignore[no-untyped-def]
    """The other direction. A field only the data knows about is invisible to the LLM
    and to `GET /meta` — it exists for whoever reads the fixture and nobody else."""
    for object_type, source in synthetic.OBJECT_SOURCES.items():
        declared = next((o for o in meta.object_types if o.name == object_type), None)
        assert declared is not None
        known = {p.name for p in declared.properties}
        for row in source():
            undeclared = set(row) - known
            assert not undeclared, f"{object_type} row carries undeclared {sorted(undeclared)}"


# --------------------------------------------------------------------------- #
# AC-9's two accounting codes, and their non-vacuity pair
# --------------------------------------------------------------------------- #


def test_both_accounting_codes_are_declared_in_the_ontology(meta) -> None:  # type: ignore[no-untyped-def]
    """AC-9 columns 8 and 6 live in the ontology, which is the whole point — a code held
    in an export-side lookup is invisible to every LLM surface."""
    for object_type in ("Truck", "Vendor"):
        declared = next(o for o in meta.object_types if o.name == object_type)
        names = {p.name for p in declared.properties}
        assert "accounting_code" in names, object_type


@pytest.mark.parametrize(
    ("object_type", "source_name"),
    [("Truck", "truck_records"), ("Vendor", "vendor_records")],
)
def test_the_seed_carries_both_a_coded_and_an_uncoded_row(
    object_type: str, source_name: str
) -> None:
    """AC-9's KPI is only meaningful if something can fail it.

    An export drawn entirely from coded trucks and coded vendors reports 100% traceable
    no matter what the pipeline does. One uncoded row of each keeps the metric honest —
    and it is not a contrived fixture: a truck or a garage genuinely can be in use before
    accounting opens it in Express."""
    rows = getattr(synthetic, source_name)()
    coded = [r for r in rows if r.get("accounting_code")]
    uncoded = [r for r in rows if not r.get("accounting_code")]

    assert coded, f"no {object_type} carries an accounting_code — the export has nothing"
    assert uncoded, (
        f"every {object_type} carries an accounting_code — AC-9's KPI cannot drop below "
        "100% and is therefore vacuous"
    )


def test_the_vendor_registry_is_served_by_the_adapter() -> None:
    """A declared object nothing serves is a schema entry the LLM will ask about and
    never get an answer for."""
    assert "Vendor" in synthetic.OBJECT_SOURCES
    assert synthetic.OBJECT_SOURCES["Vendor"]()


# --------------------------------------------------------------------------- #
# The half that makes ontology placement actually pay off
# --------------------------------------------------------------------------- #


def test_the_translate_prompt_carries_the_thai_names(meta) -> None:  # type: ignore[no-untyped-def]
    """Putting the code in the ontology buys nothing if the prompt hides its name.

    ``_describe_ontology`` rendered only types, enums and ref targets, so a property whose
    only machine-readable name is ``accounting_code`` was unreachable from the operator's
    actual word — รหัสรถ. Operators here ask in Thai; this is the line between "in the
    ontology in principle" and "answerable"."""
    described = _describe_ontology(meta)

    assert "รหัสรถ" in described
    assert "รหัสผู้ขาย" in described
    # The rendering stays compact — synonyms only, never the multi-line descriptions,
    # which carry provenance for a human reading the YAML and would bloat every call.
    assert "guess-and-react" not in described
    assert "CONFIRMED by the design partner" not in described
