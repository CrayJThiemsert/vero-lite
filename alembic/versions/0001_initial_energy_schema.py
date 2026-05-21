"""initial energy schema

Revision ID: 0001
Revises:
Create Date: 2026-05-21

Creates the six energy ontology tables matching the emitted DDL
(verticals/energy/generated/schema.sql) — PLAN-0005 §6.6, commit 6.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "site",
        sa.Column("site_id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("site_type", sa.Text()),
        sa.Column("lat", sa.Double()),
        sa.Column("lng", sa.Double()),
    )
    op.create_table(
        "alert",
        sa.Column("alert_id", sa.Text(), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("urgency", sa.Text()),
        sa.Column("status", sa.Text()),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("reasoning", sa.Text()),
    )
    op.create_table(
        "asset",
        sa.Column("asset_id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("asset_type", sa.Text()),
        sa.Column("capacity_kw", sa.Double()),
        sa.Column("status", sa.Text()),
        sa.Column("install_date", sa.Date()),
        sa.Column("site_id", sa.Text(), sa.ForeignKey("site.site_id"), nullable=False),
    )
    op.create_table(
        "operational_event",
        sa.Column("event_id", sa.Text(), primary_key=True),
        sa.Column("event_type", sa.Text()),
        sa.Column("severity", sa.Text()),
        sa.Column("measured_value", sa.Double()),
        sa.Column("unit", sa.Text()),
        sa.Column("description", sa.Text()),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("asset_id", sa.Text(), sa.ForeignKey("asset.asset_id")),
        sa.Column("site_id", sa.Text(), sa.ForeignKey("site.site_id")),
    )
    op.create_table(
        "recommended_action",
        sa.Column("action_id", sa.Text(), primary_key=True),
        sa.Column("action_type", sa.Text()),
        sa.Column("confidence_score", sa.Double()),
        sa.Column("status", sa.Text()),
        sa.Column("parameters", postgresql.JSONB()),
        sa.Column("alert_id", sa.Text(), sa.ForeignKey("alert.alert_id"), nullable=False),
        sa.Column("target_asset_id", sa.Text(), sa.ForeignKey("asset.asset_id")),
    )
    op.create_table(
        "alert_event_link",
        sa.Column("link_id", sa.Text(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("alert_id", sa.Text(), sa.ForeignKey("alert.alert_id"), nullable=False),
        sa.Column(
            "event_id",
            sa.Text(),
            sa.ForeignKey("operational_event.event_id"),
            nullable=False,
        ),
    )
    op.create_index("idx_asset_site_id", "asset", ["site_id"])
    op.create_index("idx_operational_event_asset_id", "operational_event", ["asset_id"])
    op.create_index("idx_operational_event_site_id", "operational_event", ["site_id"])
    op.create_index("idx_recommended_action_alert_id", "recommended_action", ["alert_id"])
    op.create_index(
        "idx_recommended_action_target_asset_id", "recommended_action", ["target_asset_id"]
    )
    op.create_index("idx_alert_event_link_alert_id", "alert_event_link", ["alert_id"])
    op.create_index("idx_alert_event_link_event_id", "alert_event_link", ["event_id"])


def downgrade() -> None:
    op.drop_table("alert_event_link")
    op.drop_table("recommended_action")
    op.drop_table("operational_event")
    op.drop_table("asset")
    op.drop_table("alert")
    op.drop_table("site")
