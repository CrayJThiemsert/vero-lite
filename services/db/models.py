"""Hand-authored SQLAlchemy ORM models for the energy ontology entities.

OQ-4: Phase 2 hand-authors the ORM (an "ORM emitter" is a later
Rule-of-Three candidate, PLAN-0005 §8.1). Column types track the
*emitted* DDL (``verticals/energy/generated/schema.sql``), not the
ADR-008 D3 narrative — see PLAN-0005 C-1. The DDL/ORM parity test
(``tests/services/db/test_schema_parity.py``) guards against drift.

These ORM classes are the persisted ontology entities. ``RecommendedAction``
here is the persisted projection of the ADR-007 D2 runtime envelope
(``services/engine/actions.py``) — OQ-1's two layers, deliberately not
unified.

CHECK constraints from the emitted DDL are intentionally omitted for
Phase 2: enum validity is enforced at the pydantic layer, and the
parity test covers column types, not constraints.
"""

from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, Double, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from services.db.base import Base


class Site(Base):
    """Energy ontology entity: a physical location hosting Assets."""

    __tablename__ = "site"

    site_id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    site_type: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float | None] = mapped_column(Double)
    lng: Mapped[float | None] = mapped_column(Double)


class Asset(Base):
    """Energy ontology entity: a physical operational unit."""

    __tablename__ = "asset"
    __table_args__ = (Index("idx_asset_site_id", "site_id"),)

    asset_id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    asset_type: Mapped[str | None] = mapped_column(Text)
    capacity_kw: Mapped[float | None] = mapped_column(Double)
    status: Mapped[str | None] = mapped_column(Text)
    install_date: Mapped[date | None] = mapped_column(Date)
    site_id: Mapped[str] = mapped_column(Text, ForeignKey("site.site_id"), nullable=False)


class OperationalEvent(Base):
    """Energy ontology entity: a time-stamped operational signal."""

    __tablename__ = "operational_event"
    __table_args__ = (
        Index("idx_operational_event_asset_id", "asset_id"),
        Index("idx_operational_event_site_id", "site_id"),
    )

    event_id: Mapped[str] = mapped_column(Text, primary_key=True)
    event_type: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str | None] = mapped_column(Text)
    measured_value: Mapped[float | None] = mapped_column(Double)
    unit: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    asset_id: Mapped[str | None] = mapped_column(Text, ForeignKey("asset.asset_id"))
    site_id: Mapped[str | None] = mapped_column(Text, ForeignKey("site.site_id"))


class Alert(Base):
    """Energy ontology entity: an actionable notification from events."""

    __tablename__ = "alert"

    alert_id: Mapped[str] = mapped_column(Text, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    urgency: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(Text)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reasoning: Mapped[str | None] = mapped_column(Text)


class RecommendedAction(Base):
    """Energy ontology entity: the persisted projection of a RecommendedAction envelope (OQ-1)."""

    __tablename__ = "recommended_action"
    __table_args__ = (
        Index("idx_recommended_action_alert_id", "alert_id"),
        Index("idx_recommended_action_target_asset_id", "target_asset_id"),
    )

    action_id: Mapped[str] = mapped_column(Text, primary_key=True)
    action_type: Mapped[str | None] = mapped_column(Text)
    confidence_score: Mapped[float | None] = mapped_column(Double)
    status: Mapped[str | None] = mapped_column(Text)
    parameters: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    alert_id: Mapped[str] = mapped_column(Text, ForeignKey("alert.alert_id"), nullable=False)
    target_asset_id: Mapped[str | None] = mapped_column(Text, ForeignKey("asset.asset_id"))


class AlertEventLink(Base):
    """Energy ontology entity: a join row linking an Alert to an OperationalEvent."""

    __tablename__ = "alert_event_link"
    __table_args__ = (
        Index("idx_alert_event_link_alert_id", "alert_id"),
        Index("idx_alert_event_link_event_id", "event_id"),
    )

    link_id: Mapped[str] = mapped_column(Text, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    alert_id: Mapped[str] = mapped_column(Text, ForeignKey("alert.alert_id"), nullable=False)
    event_id: Mapped[str] = mapped_column(
        Text, ForeignKey("operational_event.event_id"), nullable=False
    )
