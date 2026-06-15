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
    body = """\
version: 1
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
