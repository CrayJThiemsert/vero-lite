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

import pathlib
from typing import Any

import pytest
from ruamel.yaml import YAML

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


# --------------------------------------------------------------------------- #
# PLAN-0117 — the two supplier-evaluation bands on `Vendor`
#
# Band 1 (SD-3, "synonym-carrying"): Thai synonyms + seed values + AUTHORED stamps.
# Band 2 (SD-3a, "dormant"): declared, prompt-visible, synonym-free, UNPOPULATED,
# and carrying a written `description` that is its whole contract.
# --------------------------------------------------------------------------- #

#: Band 1, and the ONE designated Thai synonym each must put in the prompt.
#: Designated rather than "any synonym" so a silent narrowing of a synonym list
#: still reddens.
_SYNONYM_BAND = {
    "standing": "สถานะอู่",
    "is_contracted": "อู่คู่สัญญา",
    "repairs_completed_count": "ประวัติงานซ่อม",
    "comeback_count": "งานซ่อมซ้ำ",
    "avg_turnaround_days": "รอบเวลาซ่อมเฉลี่ย",
}

#: Band 2 — declared but deliberately unpopulated.
_DORMANT_BAND = ("tax_id", "cert_status", "sanctions_flag", "single_source_flag")

#: The three facts a garage nobody has kept records for cannot have.
_HISTORY_FACTS = ("repairs_completed_count", "comeback_count", "avg_turnaround_days")

_YAML_PATH = (
    pathlib.Path(__file__).resolve().parents[3]
    / "verticals"
    / "fleet_maintenance"
    / "ontology"
    / "fleet_maintenance_v0.yaml"
)


def _vendor_property_block(name: str) -> dict[str, Any]:
    """One Vendor property as written in the RAW YAML.

    Read from the file, not from loaded meta: `description` is dropped at load
    (that is what makes it cost zero prompt bytes), so loaded meta cannot check
    the dormant band's description contract at all.
    """
    with _YAML_PATH.open(encoding="utf-8") as handle:
        data = YAML(typ="safe").load(handle)
    return dict(data["object_types"]["Vendor"]["properties"][name])


def _vendor_property(meta, name: str):  # type: ignore[no-untyped-def]
    vendor = next(o for o in meta.object_types if o.name == "Vendor")
    return next(p for p in vendor.properties if p.name == name)


def test_the_translate_prompt_carries_a_thai_name_for_every_supplier_fact(meta) -> None:  # type: ignore[no-untyped-def]
    """AC-2 — a fact the operator cannot NAME in Thai is not answerable.

    Same line as `accounting_code`/รหัสรถ above: declaring the property buys
    nothing if the prompt hides the operator's actual word.
    """
    described = _describe_ontology(meta)
    missing = sorted(p for p, thai in _SYNONYM_BAND.items() if thai not in described)
    assert not missing, f"no Thai synonym reaches the prompt for: {missing}"
    # The rendering still excludes provenance prose — the descriptions carry
    # AUTHORED stamps for a human reading the YAML and would bloat every call.
    assert "AUTHORED / DEMO SEED" not in described
    assert "PROMOTION PATH" not in described


def test_every_supplier_fact_has_at_least_one_carrying_row() -> None:
    """AC-3 — a declared fact no row can supply is unanswerable in practice.

    The positive control for the honesty row below: "some vendor has no history"
    only means something if some other vendor does.
    """
    rows = synthetic.vendor_records()
    assert rows, "no vendor rows at all — every assertion below would be vacuous"
    unsupplied = sorted(
        prop for prop in _SYNONYM_BAND if not any(r.get(prop) is not None for r in rows)
    )
    assert not unsupplied, f"declared but no row carries a value: {unsupplied}"


def test_one_vendor_has_no_repair_history_at_all() -> None:
    """AC-3 — the F9 honesty pattern: absent is not zero.

    A garage can be used once before anyone has a record for it. Absent means
    "nobody has counted"; zero means "counted, and it was none". Without this row
    a completeness KPI over these facts would report 100% no matter what.
    """
    rows = synthetic.vendor_records()
    history = set(_HISTORY_FACTS)
    without = sorted(r["vendor_id"] for r in rows if not (history & set(r)))
    assert without, "every vendor carries history — a completeness KPI would be vacuous"
    # Positive control: the absence above is only meaningful if the facts exist.
    with_history = sorted(r["vendor_id"] for r in rows if history <= set(r))
    assert with_history, "no vendor carries the history facts — the absence proves nothing"


def test_the_dormant_band_is_declared_and_reaches_the_prompt(meta) -> None:  # type: ignore[no-untyped-def]
    """AC-3a(a) — declaring now means a value is usable the day it exists.

    The point of the dormant band: no code change on the day the narrative
    brings the fact, because the translate prompt already names the property.
    """
    described = _describe_ontology(meta)
    absent = sorted(p for p in _DORMANT_BAND if p not in described)
    assert not absent, f"dormant properties missing from the translate prompt: {absent}"


def test_the_dormant_band_carries_no_seeded_value() -> None:
    """AC-3a(b) — unpopulated is the CONTRACTED state, not an oversight.

    `sanctions_flag` is a legal assertion about a real business; `tax_id` is a
    statutory identifier. Authoring either as demo data in a public repository is
    the thing this reddens on. It is also what keeps the advisory
    `single_source_flag` unable to disagree with the per-case record.
    """
    rows = synthetic.vendor_records()
    assert rows, "no vendor rows — an empty seed satisfies any absence claim"
    seeded = sorted(f"{r['vendor_id']}.{p}" for r in rows for p in _DORMANT_BAND if p in r)
    assert not seeded, f"dormant properties carry authored values: {seeded}"


def test_every_dormant_property_carries_a_written_description() -> None:
    """AC-3a(c1) — the description IS the dormant band's whole contract.

    These four carry no AUTHORED stamp because nothing is authored for them, so
    a blank description would leave a reader no way to tell a deliberate dormant
    declaration from an abandoned one.
    """
    blank = sorted(
        p
        for p in _DORMANT_BAND
        if not str(_vendor_property_block(p).get("description", "")).strip()
    )
    assert not blank, f"dormant properties with no written description: {blank}"


def test_single_source_flag_names_the_authoritative_record() -> None:
    """AC-3a(c2) — the residual-concern mitigation, in the artifact.

    ADR-0034 D4 makes the per-case `RepairCaseJustification` the authoritative
    sole-source record. A vendor-level flag that forgot to say so is a second,
    independently-authored statement of the same fact — and two of those can
    disagree.
    """
    description = str(_vendor_property_block("single_source_flag").get("description", ""))
    assert description.strip(), "positive control: the description must exist to be checked"
    assert "RepairCaseJustification" in description
    assert "ADVISORY" in description


def test_the_dormant_band_costs_no_synonym_bytes(meta) -> None:  # type: ignore[no-untyped-def]
    """AC-3a(d) — the cost guard.

    Every synonym list is prompt bytes on every call. The dormant four are
    declared for the day a value arrives, not to be asked for in Thai today;
    synonyms for them arrive only via a deliberate later YAML edit when the
    narrative brings the term.
    """
    # Positive control FIRST: the check can see a synonym list at all, so a redden
    # below is about the dormant band and not about the reader being broken.
    assert _vendor_property(meta, "standing").synonyms is not None
    carrying = sorted(p for p in _DORMANT_BAND if _vendor_property(meta, p).synonyms is not None)
    assert not carrying, f"dormant properties carrying synonyms: {carrying}"


#: AC-1(b)'s pass read, fixed BEFORE the edit that produced it: the three
#: baseline properties plus both ruled bands. Pinned as a literal so adding or
#: dropping a property is a deliberate act with a reddening test, not a silent
#: drift in a list nothing compares against.
_RULED_VENDOR_PROPERTIES = [
    "accounting_code",
    "avg_turnaround_days",
    "cert_status",
    "comeback_count",
    "is_contracted",
    "name",
    "repairs_completed_count",
    "sanctions_flag",
    "single_source_flag",
    "standing",
    "tax_id",
    "vendor_id",
]


def _raw_vendor_yaml_lines() -> list[str]:
    return _YAML_PATH.read_text(encoding="utf-8").splitlines()


def test_the_vendor_block_declares_exactly_the_ruled_property_set(meta) -> None:  # type: ignore[no-untyped-def]
    """AC-1(b) — the whole declared surface, not just "the new ones are there".

    Two-sided on purpose: a property that vanished and a property nobody ruled
    both redden here. A one-sided "the ruled names are present" check would pass
    on a Vendor block that had quietly grown a twelfth field.
    """
    vendor = next(o for o in meta.object_types if o.name == "Vendor")
    assert sorted(p.name for p in vendor.properties) == _RULED_VENDOR_PROPERTIES


def test_every_authored_value_carries_its_demo_seed_stamp() -> None:
    """AC-1(c1) — SD-1(c)'s comment contract: an authored figure says so.

    One stamp per synonym-carrying property. The dormant four carry NO stamp —
    nothing is authored for them — so this counts the band, not the block.

    The stamp must sit on ONE line: `grep` and this test both read raw lines, so
    a phrase folded across two lines by YAML wrapping would be invisible to the
    very check that is supposed to find it.
    """
    stamped = [line for line in _raw_vendor_yaml_lines() if "AUTHORED / DEMO SEED" in line]
    assert len(stamped) == len(_SYNONYM_BAND), (
        f"expected one AUTHORED / DEMO SEED stamp per authored property "
        f"({len(_SYNONYM_BAND)}), found {len(stamped)}"
    )


def test_the_promotion_path_is_recorded_exactly_once() -> None:
    """AC-1(c2) — the route that RETIRES the stamps, stated once.

    Exactly once, not "at least once": a second copy is a second place to drift.
    """
    marked = [line for line in _raw_vendor_yaml_lines() if "PROMOTION PATH" in line]
    assert len(marked) == 1, f"expected exactly one PROMOTION PATH block, found {len(marked)}"
