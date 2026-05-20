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
