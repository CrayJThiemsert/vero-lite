#!/usr/bin/env python
"""Dev/demo helper — seed ONE fresh ``waiting_human`` procurement run for the Control-leg
operate demo (PLAN-0054 Step 6; rotation + subject stamp: PLAN-0084 Steps 1 + 5).

Run it before a rehearsal, or after you have resolved / cancelled the previous run: the
``audit_log`` is append-only (a tamper-evidence trigger, PLAN-0047), so a run cannot be reset
in place — you seed a NEW run instead.

    python scripts/seed_operate_demo.py                    # a fresh unique run_id, the hero asset
    python scripts/seed_operate_demo.py my-run-id          # a chosen run_id (back-compat)
    python scripts/seed_operate_demo.py --asset AST-CNC-009  # rotate: seed ANOTHER asset's scenario
    python scripts/seed_operate_demo.py --rotate           # pick a non-hero asset by day index

Rotation is DATA-DRIVEN: any asset with exactly one PurchaseOrder row is rotatable (the
fixture ships one per asset); an unknown id fails with the rotatable list. Different assets
land DIFFERENT DOA tiers — stdout names the approver the operator must log in as.

Then open the OCT Monitor (View H) at the demo port, log in as the NAMED approver, and
operate it. The run also lights its asset's node on the Operational Map (View A) via the
``trigger_context.subject`` stamp (PLAN-0084).

NOT PRODUCTION CODE: this is a manual dev/demo script — it is never imported or invoked by
the app. Production is already seed-free (the lifespan seed is gated on OCT_DEMO_SEED_OPERATE,
off by default); this script just makes the demo loop convenient. It writes to whatever
``DATABASE_URL`` points at, so only run it against a demo database.
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib
import secrets
import sys
from datetime import date

# Make ``services`` / ``verticals`` importable when run as `python scripts/seed_operate_demo.py`.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))


async def _rotatable_assets() -> tuple[str, list[str]]:
    """(hero asset, sorted non-hero rotatable assets) — data-driven from the adapter's
    PurchaseOrder rows (rotatable = the asset of exactly one PO; never a hardcoded list)."""
    from collections import Counter

    from verticals.procurement.data_adapter.fastenal_csv import FastenalCsvAdapter
    from verticals.procurement.hero_demo.run import _HERO_PO

    pos = await FastenalCsvAdapter().fetch_objects("PurchaseOrder")
    counts = Counter(p["equipment_id"] for p in pos)
    hero_asset = next(p["equipment_id"] for p in pos if p["po_id"] == _HERO_PO)
    rotatable = sorted(a for a, n in counts.items() if n == 1)
    return hero_asset, [a for a in rotatable if a != hero_asset]


async def _seed(run_id: str, asset_id: str | None) -> None:
    from services.db.session import async_session
    from verticals.procurement.hero_demo.run import seed_operate_waiting_human_run

    async with async_session() as session:
        result = await seed_operate_waiting_human_run(session, run_id=run_id, asset_id=asset_id)

    print(f"seeded {result.run.run_id!r} -> status {result.run.status}")
    subject = (result.run.trigger_context or {}).get("subject") or {}
    if subject:
        print(
            f"subject: {subject.get('object_type')} {subject.get('primary_key')} "
            "(lights the Operational Map node — View A)"
        )
    # PLAN-0084 Step 5 (AC-7): name the DOA tier + the approver this run's gate needs —
    # rotated assets land different tiers, so the operator must know who to log in as.
    approve = next((s for s in result.step_results if s.step_id == "approve"), None)
    doa_entries = ((approve.audit or {}).get("doa_tier") or [{}]) if approve else [{}]
    doa = doa_entries[0]
    tier = doa.get("resolved_tier_id")
    approver = doa.get("resolved_approver_id")
    if approver:
        print(f"DOA tier: {tier} -> log in as {approver!r} to approve (View H · Monitor)")
    else:
        print("DOA tier: not annotated on the parked run — open Monitor and check the gate")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed one fresh waiting_human procurement run for the operate demo."
    )
    parser.add_argument(
        "run_id",
        nargs="?",
        default=None,
        help="run id (default: a fresh unique run-operate-<hex>)",
    )
    parser.add_argument(
        "--asset",
        default=None,
        metavar="EQUIPMENT_ID",
        help="seed the scenario for this asset (rotatable = any asset with exactly one "
        "PurchaseOrder row; unknown ids fail with the rotatable list)",
    )
    parser.add_argument(
        "--rotate",
        action="store_true",
        help="pick a NON-HERO rotatable asset by day-of-month index (stateless: the same "
        "day picks the same asset; combine with an explicit run_id for repeat seeds)",
    )
    args = parser.parse_args()
    if args.asset and args.rotate:
        parser.error("--asset and --rotate are mutually exclusive")

    asset_id = args.asset
    if args.rotate:
        hero, others = asyncio.run(_rotatable_assets())
        if not others:
            parser.error(f"no non-hero rotatable assets found (hero: {hero})")
        asset_id = others[date.today().day % len(others)]
        print(f"--rotate picked {asset_id!r} (day index over {others})")

    run_id = args.run_id or f"run-operate-{secrets.token_hex(3)}"
    asyncio.run(_seed(run_id, asset_id))


if __name__ == "__main__":
    main()
