"""PLAN-0068 PR1 substrate pin — every Pond carries a per-species ``do_floor``.

The FK-parent band column (ADR-016 FKP, 2026-07-12 amendment) is seeded by
construction so PR2's per-species judge migration never hits the FKP-3 fail-loud
on a null band (the supply_chain per-cargo_type precedent). This is the additive
SUBSTRATE half only; the ``read_do`` join + the ``judge`` migration to
``threshold_field: do_floor`` + the demo-visible per-species flip land in PR2
(SD-4 = two PRs, the ratified Cray divergence).

Synthetic, deterministic, offline — no LLM, no DB.
"""

from __future__ import annotations

from verticals.aquaculture.data_adapter.synthetic import ponds

# SD-2 per-species DO floor (mg/L) — synthetic but plausible: penaeid shrimp
# (whiteleg/tiger) need higher dissolved oxygen; tilapia is hypoxia-tolerant.
_SPECIES_FLOOR = {"whiteleg_shrimp": 4.0, "tiger_prawn": 4.5, "tilapia": 3.0}


def test_every_pond_carries_its_species_do_floor() -> None:
    pond_list = ponds()
    assert pond_list, "no synthetic ponds seeded"
    for pond in pond_list:
        assert "do_floor" in pond, f"{pond['pond_id']} is missing do_floor (FKP-3 would fail-loud)"
        expected = _SPECIES_FLOOR[pond["species"]]
        assert pond["do_floor"] == expected, (
            f"{pond['pond_id']} ({pond['species']}) do_floor "
            f"{pond['do_floor']} != expected {expected}"
        )


def test_all_declared_species_have_a_seeded_floor() -> None:
    # Guards a new species landing without a floor → an unbanded pond at run.
    seeded = {p["species"] for p in ponds()}
    assert seeded == set(_SPECIES_FLOOR), f"species/floor drift: seeded={seeded}"
