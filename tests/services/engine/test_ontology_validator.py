"""Tests for ``services.engine.ontology_validator`` (L1 + L2).

All assertions use Lesson #7 §3.2 in-process ``main()`` invocations
plus pytest's ``capsys`` capture — never ``subprocess.run`` + ``echo
$?``. Each invalid-input case asserts the stderr summary line shape
and the per-error ``<file>:<line>:<col>`` reference.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from services.engine.ontology_validator import main

_LINE_COL_RE = re.compile(r":\d+:\d+:")

_VALID_YAML = """\
version: 0
namespace: energy
object_types:
  Asset:
    primary_key: asset_id
    properties:
      asset_id:
        type: string
        required: true
      name:
        type: string
      status:
        type: enum
        values: [active, retired]
  Site:
    primary_key: site_id
    properties:
      site_id:
        type: string
        required: true
link_types:
  asset_hosted_at_site:
    from: Asset
    to: Site
    cardinality: many_to_one
    foreign_key: Asset.asset_id -> Site.site_id
"""


def _write(tmp_path: Path, name: str, body: str) -> Path:
    path = tmp_path / name
    path.write_text(body)
    return path


def test_happy_path_returns_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    yaml_path = _write(tmp_path, "ok.yaml", _VALID_YAML)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 0
    assert "OK: 1 file(s) valid" in captured.err


# ---------- L1 cases ----------


def test_l1_missing_required_field(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    body = """\
version: 0
namespace: energy
object_types:
  Asset:
    properties:
      asset_id:
        type: string
"""
    yaml_path = _write(tmp_path, "bad.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "error(s) across" in captured.err
    assert _LINE_COL_RE.search(captured.err)
    assert "primary_key" in captured.err


def test_l1_wrong_type_for_version(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # PLAN-0049 SD-2: `version` is now an integer >= 0 (content revision), so a
    # non-integer (or negative) value is the invalid case — a positive int like
    # 1 is VALID (see test_l1_version_revision_is_valid).
    body = """\
version: "one"
namespace: energy
object_types:
  Asset:
    primary_key: asset_id
    properties:
      asset_id:
        type: string
"""
    yaml_path = _write(tmp_path, "bad.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "error(s) across" in captured.err
    assert _LINE_COL_RE.search(captured.err)


def test_l1_version_revision_is_valid(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """PLAN-0049 SD-2: a positive content-revision version (>= 0) validates."""
    body = """\
version: 1
namespace: energy
object_types:
  Asset:
    primary_key: asset_id
    properties:
      asset_id:
        type: string
        required: true
"""
    yaml_path = _write(tmp_path, "ok.yaml", body)
    ret = main([str(yaml_path)])
    assert ret == 0


def test_l1_unknown_property_type(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    body = """\
version: 0
namespace: energy
object_types:
  Asset:
    primary_key: asset_id
    properties:
      asset_id:
        type: blob
"""
    yaml_path = _write(tmp_path, "bad.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "error(s) across" in captured.err
    assert _LINE_COL_RE.search(captured.err)
    assert "blob" in captured.err


def test_l1_rejects_plan_section_8_6_list_of_dicts_form(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """R-K1 schema fidelity guarantee: list-of-dicts grammar from
    PLAN-003 §8.6 illustration must be REJECTED."""
    body = """\
version: 0
namespace: energy
object_types:
  - name: Asset
    primary_key: asset_id
    properties:
      - name: asset_id
        type: string
"""
    yaml_path = _write(tmp_path, "bad.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "error(s) across" in captured.err


# ---------- L2 cases ----------


def test_l2_dangling_ref_target(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    body = """\
version: 0
namespace: energy
object_types:
  Asset:
    primary_key: asset_id
    properties:
      asset_id:
        type: string
      site_ref:
        type: ref
        target: NonexistentSite
"""
    yaml_path = _write(tmp_path, "bad.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "error(s) across" in captured.err
    assert _LINE_COL_RE.search(captured.err)
    assert "NonexistentSite" in captured.err


def test_l2_link_to_undefined_object_type(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    body = """\
version: 0
namespace: energy
object_types:
  Alert:
    primary_key: alert_id
    properties:
      alert_id:
        type: string
link_types:
  alert_to_event:
    from: Alert
    to: NonexistentEvent
    cardinality: many_to_one
    foreign_key: Alert.alert_id -> NonexistentEvent.event_id
"""
    yaml_path = _write(tmp_path, "bad.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "error(s) across" in captured.err
    assert _LINE_COL_RE.search(captured.err)
    assert "NonexistentEvent" in captured.err


def test_l2_primary_key_not_in_properties(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    body = """\
version: 0
namespace: energy
object_types:
  Asset:
    primary_key: missing_field
    properties:
      asset_id:
        type: string
"""
    yaml_path = _write(tmp_path, "bad.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "error(s) across" in captured.err
    assert _LINE_COL_RE.search(captured.err)
    assert "missing_field" in captured.err


def test_l2_foreign_key_endpoint_field_undeclared(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    body = """\
version: 0
namespace: energy
object_types:
  Asset:
    primary_key: asset_id
    properties:
      asset_id:
        type: string
  Site:
    primary_key: site_id
    properties:
      site_id:
        type: string
link_types:
  asset_hosted_at_site:
    from: Asset
    to: Site
    cardinality: many_to_one
    foreign_key: Asset.site_id -> Site.site_id
"""
    yaml_path = _write(tmp_path, "bad.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "error(s) across" in captured.err
    assert "site_id" in captured.err


def test_l2_malformed_foreign_key_string(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """foreign_key that fails the ``<Obj>.<f> -> <Obj>.<f>`` grammar →
    SemanticValidationError with the canonical ``does not match`` message."""
    body = """\
version: 0
namespace: energy
object_types:
  Asset:
    primary_key: asset_id
    properties:
      asset_id:
        type: string
  Site:
    primary_key: site_id
    properties:
      site_id:
        type: string
link_types:
  asset_hosted_at_site:
    from: Asset
    to: Site
    cardinality: many_to_one
    foreign_key: Asset.asset_id Site.site_id
"""
    yaml_path = _write(tmp_path, "bad.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "error(s) across" in captured.err
    assert _LINE_COL_RE.search(captured.err)
    assert "does not match" in captured.err


def test_l2_enum_with_empty_values_list(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """enum property with an empty ``values`` list → SemanticValidationError
    ('requires non-empty values list')."""
    body = """\
version: 0
namespace: energy
object_types:
  Asset:
    primary_key: asset_id
    properties:
      asset_id:
        type: string
      status:
        type: enum
        values: []
"""
    yaml_path = _write(tmp_path, "bad.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "error(s) across" in captured.err
    assert "requires non-empty values list" in captured.err


def test_l2_quantity_binding_kind_not_in_enum(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """ADR-0021 (D6): a quantity_bindings kind absent from the measured_kind enum →
    SemanticValidationError ('is not a value of the measured_kind enum')."""
    body = """\
version: 0
namespace: energy
object_types:
  OperationalEvent:
    primary_key: event_id
    properties:
      event_id:
        type: string
      measured_kind:
        type: enum
        values: [temperature]
    quantity_bindings:
      - kind: pressure
        unit: bar
"""
    yaml_path = _write(tmp_path, "bad.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "is not a value of the measured_kind enum" in captured.err


def test_l2_quantity_binding_duplicate_kind(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """ADR-0021 (D6): a kind bound more than once → SemanticValidationError."""
    body = """\
version: 0
namespace: energy
object_types:
  OperationalEvent:
    primary_key: event_id
    properties:
      event_id:
        type: string
      measured_kind:
        type: enum
        values: [temperature, frequency]
    quantity_bindings:
      - kind: temperature
        unit: celsius
      - kind: temperature
        unit: fahrenheit
"""
    yaml_path = _write(tmp_path, "bad.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "more than once" in captured.err


def test_malformed_yaml_reports_parse_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Unparseable YAML → graceful 'YAML parse failed' SchemaValidationError,
    not an uncaught exception."""
    body = "object_types: [unterminated\n"
    yaml_path = _write(tmp_path, "broken.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "error(s) across" in captured.err
    assert "YAML parse failed" in captured.err


def test_top_level_yaml_not_a_mapping(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A top-level YAML sequence (not a mapping) → 'top-level YAML must be a
    mapping' SchemaValidationError."""
    body = """\
- version: 0
- namespace: energy
"""
    yaml_path = _write(tmp_path, "list.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "error(s) across" in captured.err
    assert "top-level YAML must be a mapping" in captured.err


def test_l2_non_dict_link_def_skipped_gracefully(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A ``link_types`` entry whose value is not a mapping is skipped by L2
    (no crash); L1 still reports the schema mismatch."""
    body = """\
version: 0
namespace: energy
object_types:
  Asset:
    primary_key: asset_id
    properties:
      asset_id:
        type: string
link_types:
  asset_hosted_at_site: just_a_string
"""
    yaml_path = _write(tmp_path, "bad.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "error(s) across" in captured.err


def test_l2_non_dict_object_def_skipped_gracefully(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An ``object_types`` entry whose value is not a mapping is skipped by L2
    (no crash); L1 still reports the schema mismatch."""
    body = """\
version: 0
namespace: energy
object_types:
  Asset: just_a_string
"""
    yaml_path = _write(tmp_path, "bad.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "error(s) across" in captured.err


def test_l1_error_nested_in_link_types_derives_context(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An L1 schema error under ``link_types`` derives a
    ``<link>.<field>`` context via ``_ctx_from_path``."""
    body = """\
version: 0
namespace: energy
object_types:
  Asset:
    primary_key: asset_id
    properties:
      asset_id:
        type: string
  Site:
    primary_key: site_id
    properties:
      site_id:
        type: string
link_types:
  asset_hosted_at_site:
    from: Asset
    to: Site
    cardinality: many_to_many
    foreign_key: Asset.asset_id -> Site.site_id
"""
    yaml_path = _write(tmp_path, "bad.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "error(s) across" in captured.err
    assert _LINE_COL_RE.search(captured.err)
    assert "asset_hosted_at_site.cardinality" in captured.err


def test_cli_no_args_prints_usage_and_returns_1(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``main([])`` with no file arguments → usage line on stderr, return 1."""
    ret = main([])
    captured = capsys.readouterr()
    assert ret == 1
    assert "usage:" in captured.err


# ---------- ADR-0027 R2 / PLAN-0050 Step 1: L1 shape for the four enrichment constructs ----------

_ENRICHED_YAML = """\
version: 1
namespace: energy
object_types:
  Asset:
    primary_key: asset_id
    synonyms:
      th: [sinsap]
      en: [asset, equipment]
    verified_queries:
      - question: How many active assets are there?
        answer: Count Asset rows where status is active.
    properties:
      asset_id:
        type: string
        required: true
      status:
        type: enum
        values: [active, retired]
        synonyms:
          en: [state, condition]
        sample_values: [active, retired]
  OperationalEvent:
    primary_key: event_id
    properties:
      event_id:
        type: string
      asset_id:
        type: string
      measured_kind:
        type: enum
        values: [temperature]
    quantity_bindings:
      - kind: temperature
        unit: celsius
        grain: hourly
        join_path: OperationalEvent.asset_id -> Asset.asset_id
"""


def test_l1_enrichment_constructs_valid(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """ADR-0027 R2 (PLAN-0050 Step 1, AC-1): a YAML declaring all four
    enrichment constructs (object-type + property ``synonyms``, ``sample_values``,
    object-type ``verified_queries``, quantity-binding ``grain``/``join_path``)
    passes L1 (and L2 — Step 1 adds no L2 checks for them yet)."""
    yaml_path = _write(tmp_path, "enriched.yaml", _ENRICHED_YAML)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 0
    assert "OK: 1 file(s) valid" in captured.err


def test_l1_bare_yaml_still_valid_absent_enrichment(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-1 / D2 backward-compat: an ontology declaring NONE of the four
    constructs still validates unchanged (absent = pre-R2 grammar)."""
    yaml_path = _write(tmp_path, "bare.yaml", _VALID_YAML)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 0
    assert "OK: 1 file(s) valid" in captured.err


def test_l1_synonyms_flat_list_rejected(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """AC-1 malformed: ``synonyms`` as a flat list (not a ``{th, en}`` map) → L1 reject."""
    body = """\
version: 0
namespace: energy
object_types:
  Asset:
    primary_key: asset_id
    synonyms: [asset, equipment]
    properties:
      asset_id:
        type: string
"""
    yaml_path = _write(tmp_path, "bad.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "error(s) across" in captured.err
    assert _LINE_COL_RE.search(captured.err)


def test_l1_synonyms_extra_lang_key_rejected(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-1 malformed: an unknown lang key in ``synonyms`` → L1 reject
    (``additionalProperties: false`` on the ``{th, en}`` map)."""
    body = """\
version: 0
namespace: energy
object_types:
  Asset:
    primary_key: asset_id
    properties:
      asset_id:
        type: string
        synonyms:
          fr: [identifiant]
"""
    yaml_path = _write(tmp_path, "bad.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "error(s) across" in captured.err
    assert _LINE_COL_RE.search(captured.err)


def test_l1_verified_query_missing_question_rejected(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-1 malformed: a ``verified_queries`` entry missing ``question`` → L1 reject."""
    body = """\
version: 0
namespace: energy
object_types:
  Asset:
    primary_key: asset_id
    verified_queries:
      - answer: An answer with no question.
    properties:
      asset_id:
        type: string
"""
    yaml_path = _write(tmp_path, "bad.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "error(s) across" in captured.err
    assert "question" in captured.err


# ---------- ADR-0027 R2 / PLAN-0050 Step 3: L2 consistency for the enrichment constructs ----------

_L2_ENUM_HEAD = """\
version: 1
namespace: energy
object_types:
  Asset:
    primary_key: asset_id
    properties:
      asset_id:
        type: string
      status:
        type: enum
        values: [active, retired]
"""


def test_l2_sample_value_not_in_enum_rejected(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-3 (SD-C): a ``sample_values`` entry outside an enum property's ``values``
    → L2 reject (the closed-set reading; L1 accepts any string array)."""
    body = _L2_ENUM_HEAD + "        sample_values: [active, DECOMMISSIONED]\n"
    yaml_path = _write(tmp_path, "bad.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "error(s) across" in captured.err
    assert "not a declared enum value" in captured.err


def test_l2_synonyms_duplicate_within_lang_rejected(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-3: a synonym repeated within a language list → L2 reject."""
    body = """\
version: 1
namespace: energy
object_types:
  Asset:
    primary_key: asset_id
    synonyms:
      en: [asset, asset]
    properties:
      asset_id:
        type: string
"""
    yaml_path = _write(tmp_path, "bad.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "error(s) across" in captured.err
    assert "more than once" in captured.err


def test_l2_verified_queries_duplicate_question_rejected(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-3: two ``verified_queries`` with the same ``question`` → L2 reject."""
    body = """\
version: 1
namespace: energy
object_types:
  Asset:
    primary_key: asset_id
    verified_queries:
      - question: How many assets?
        answer: A count.
      - question: How many assets?
        answer: Another count.
    properties:
      asset_id:
        type: string
"""
    yaml_path = _write(tmp_path, "bad.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "error(s) across" in captured.err
    assert "repeats question" in captured.err


def test_l2_join_path_undefined_object_type_rejected(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-3 (SD-5): a quantity-binding ``join_path`` whose endpoint object_type is
    undefined → L2 reject (endpoint resolution, mirroring foreign_key)."""
    body = """\
version: 1
namespace: energy
object_types:
  OperationalEvent:
    primary_key: event_id
    properties:
      event_id:
        type: string
      asset_id:
        type: string
      measured_kind:
        type: enum
        values: [temperature]
    quantity_bindings:
      - kind: temperature
        unit: celsius
        join_path: OperationalEvent.asset_id -> Ghost.asset_id
"""
    yaml_path = _write(tmp_path, "bad.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 1
    assert "error(s) across" in captured.err
    assert "join_path" in captured.err
    assert "Ghost" in captured.err


# ---------- ADR-0027 R2 / PLAN-0050 Step 4: D2 backward-compat GATE (AC-4) ----------


def test_ac4_real_verticals_validate_clean_post_r2() -> None:
    """AC-4 (D2 backward-compat GATE): both real verticals — energy + supply_chain,
    which declare NONE of the R2 enrichment constructs — still validate clean after
    Steps 1-3. Byte-identity of generated artifacts is proven separately: running
    ``vero-lite generate`` on both verticals leaves the working tree git-clean."""
    repo_root = Path(__file__).resolve().parents[3]
    for vertical in ("energy", "supply_chain"):
        path = repo_root / "verticals" / vertical / "ontology" / f"{vertical}_v0.yaml"
        assert main([str(path)]) == 0, f"{vertical} failed to validate clean"


def test_ac4_quantity_bindings_without_r2_fields_validate_clean(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC-4 (D2 GATE): an object with ``quantity_bindings`` but NO R2 ``grain`` /
    ``join_path`` (and no ``synonyms`` / ``sample_values`` / ``verified_queries``)
    validates clean — the new ``_check_*`` all no-op on absent constructs."""
    body = """\
version: 0
namespace: energy
object_types:
  OperationalEvent:
    primary_key: event_id
    properties:
      event_id:
        type: string
      measured_kind:
        type: enum
        values: [temperature]
    quantity_bindings:
      - kind: temperature
        unit: celsius
"""
    yaml_path = _write(tmp_path, "bare_qb.yaml", body)
    ret = main([str(yaml_path)])
    captured = capsys.readouterr()
    assert ret == 0
    assert "OK: 1 file(s) valid" in captured.err
