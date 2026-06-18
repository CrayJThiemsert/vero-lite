"""Tests for the SQLAlchemy ORM emitter in ``services.engine.code_generator``.

PLAN-0031 (Group B / B1). Behavioral, in-process text assertions on the generated
ORM source (no DB; no subprocess — Lesson #7 §3.3). The energy DDL<->ORM
schema-equivalence is guarded end-to-end by ``tests/services/db/test_schema_parity.py``
against the **generated** ORM; this file covers the emitter's structure + determinism.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.engine.code_generator import emit_orm


def _doc() -> dict[str, Any]:
    return {
        "version": 0,
        "namespace": "test",
        "object_types": {
            "Asset": {
                "primary_key": "asset_id",
                "properties": {
                    "asset_id": {"type": "string", "required": True},
                    "name": {"type": "string"},
                    "capacity_kw": {"type": "float"},
                    "install_date": {"type": "date"},
                    "status": {"type": "enum", "values": ["active", "retired"]},
                    "meta": {"type": "json"},
                    "site_ref": {"type": "ref", "target": "Site"},
                },
            },
            "Site": {
                "primary_key": "site_id",
                "properties": {
                    "site_id": {"type": "string", "required": True},
                    "opened_at": {"type": "timestamp"},
                    "open": {"type": "bool"},
                    "count_hint": {"type": "int"},
                },
            },
        },
        "link_types": {},
    }


def _emit(tmp_path: Path) -> str:
    out = tmp_path / "orm.py"
    emit_orm(_doc(), out)
    return out.read_text(encoding="utf-8")


def test_orm_emitter_classes_bound_to_base(tmp_path: Path) -> None:
    text = _emit(tmp_path)
    assert "class Asset(Base):" in text
    assert "class Site(Base):" in text
    assert '__tablename__ = "asset"' in text
    assert '__tablename__ = "site"' in text
    assert "from services.db.base import Base" in text
    assert "do not edit by hand" in text


def test_orm_emitter_type_mapping(tmp_path: Path) -> None:
    text = _emit(tmp_path)
    # PK (not null) + required (nullable=False) handled below; here the scalar map:
    assert "asset_id: Mapped[str] = mapped_column(Text, primary_key=True)" in text
    assert "name: Mapped[str | None] = mapped_column(Text)" in text
    assert "capacity_kw: Mapped[float | None] = mapped_column(Double)" in text
    assert "install_date: Mapped[date | None] = mapped_column(Date)" in text
    assert "opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))" in text
    assert "open: Mapped[bool | None] = mapped_column(Boolean)" in text
    assert "count_hint: Mapped[int | None] = mapped_column(BigInteger)" in text
    # enum -> Text, CHECK omitted (enum validity at the Pydantic layer)
    assert "status: Mapped[str | None] = mapped_column(Text)" in text
    assert "CHECK" not in text
    # json -> JSONB (postgresql dialect)
    assert "meta: Mapped[dict[str, Any] | None] = mapped_column(JSONB)" in text
    assert "from sqlalchemy.dialects.postgresql import JSONB" in text


def test_orm_emitter_ref_becomes_foreignkey_plus_index(tmp_path: Path) -> None:
    text = _emit(tmp_path)
    assert 'site_ref: Mapped[str | None] = mapped_column(Text, ForeignKey("site.site_id"))' in text
    assert '__table_args__ = (Index("idx_asset_site_ref", "site_ref"),)' in text


def test_orm_emitter_is_deterministic(tmp_path: Path) -> None:
    out_a = tmp_path / "a.py"
    out_b = tmp_path / "b.py"
    emit_orm(_doc(), out_a)
    emit_orm(_doc(), out_b)
    assert out_a.read_text(encoding="utf-8") == out_b.read_text(encoding="utf-8")
