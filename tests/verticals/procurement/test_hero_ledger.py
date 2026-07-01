"""PLAN-0045 Step 3 / AC-6 — the hero-demo ฿-impact ledger (exact-฿ oracle).

Offline + deterministic (CLAUDE.md §8). Asserts the ledger math over the dataset columns,
Decimal-exact (never float). Pre-committed pass/fail reads = the dataset §"฿-impact" section:
baseline ~฿9.76M → governed ~฿1.65M, expedite premium ฿52,500, avoided downtime ~฿8.1M.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from verticals.procurement.hero_demo.ledger import build_hero_impact_ledger


@pytest.fixture
async def ledger() -> dict[str, Any]:
    return await build_hero_impact_ledger()


async def test_provisional_and_currency(ledger: dict[str, Any]) -> None:
    assert ledger["provisional"] is True
    assert ledger["currency"] == "THB"
    assert ledger["asset_id"] == "AST-CNC-014"
    assert ledger["part_id"] == "PRT-SPN-700"
    assert ledger["qty"] == 3


async def test_baseline_is_on_avl_14_day_wait(ledger: dict[str, Any]) -> None:
    baseline = ledger["baseline"]
    assert baseline["supplier_id"] == "SUP-FASTENAL-TH"  # the on-AVL preferred supplier
    assert baseline["lead_time_days"] == 14
    # downtime = ฿85,000/hr x 14 days x 8 productive hrs = ฿9,520,000
    assert baseline["downtime_thb"] == Decimal("9520000")
    # part = ฿78,500 on-contract x 3 = ฿235,500
    assert baseline["part_cost_thb"] == Decimal("235500")
    assert baseline["exposure_thb"] == Decimal("9755500")  # ~฿9.76M


async def test_governed_is_off_avl_2_day_emergency(ledger: dict[str, Any]) -> None:
    governed = ledger["governed"]
    assert governed["supplier_id"] == "SUP-RAPIDMRO"  # the off-AVL emergency supplier
    assert governed["lead_time_days"] == 2
    # downtime = ฿85,000/hr x 2 days x 8 productive hrs = ฿1,360,000
    assert governed["downtime_thb"] == Decimal("1360000")
    # part = the hero PO total (฿96,000 x 3) = ฿288,000
    assert governed["part_cost_thb"] == Decimal("288000")
    assert governed["exposure_thb"] == Decimal("1648000")  # ~฿1.65M


async def test_premium_and_avoided_and_net(ledger: dict[str, Any]) -> None:
    assert ledger["expedite_premium_thb"] == Decimal("52500")  # 288,000 - 235,500
    assert ledger["avoided_downtime_thb"] == Decimal("8160000")  # 9,520,000 - 1,360,000
    assert ledger["net_benefit_thb"] == Decimal("8107500")  # 9,755,500 - 1,648,000


async def test_all_money_values_are_decimal(ledger: dict[str, Any]) -> None:
    """No float on money (exact ฿ — the demo figure must not drift under float rounding)."""
    for key in ("expedite_premium_thb", "avoided_downtime_thb", "net_benefit_thb"):
        assert isinstance(ledger[key], Decimal)
    for side in ("baseline", "governed"):
        for key in ("downtime_thb", "part_cost_thb", "exposure_thb"):
            assert isinstance(ledger[side][key], Decimal)
