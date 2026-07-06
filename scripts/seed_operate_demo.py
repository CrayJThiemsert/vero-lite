#!/usr/bin/env python
"""Dev/demo helper — seed ONE fresh ``waiting_human`` procurement run for the Control-leg
operate demo (PLAN-0054 Step 6).

Run it before a rehearsal, or after you have resolved / cancelled the previous run: the
``audit_log`` is append-only (a tamper-evidence trigger, PLAN-0047), so a run cannot be reset
in place — you seed a NEW run instead.

    python scripts/seed_operate_demo.py               # a fresh unique run_id
    python scripts/seed_operate_demo.py my-run-id     # a chosen run_id

Then open the OCT Monitor (View H) at the demo port, log in as an approver, and operate it.

NOT PRODUCTION CODE: this is a manual dev/demo script — it is never imported or invoked by
the app. Production is already seed-free (the lifespan seed is gated on OCT_DEMO_SEED_OPERATE,
off by default); this script just makes the demo loop convenient. It writes to whatever
``DATABASE_URL`` points at, so only run it against a demo database.
"""

from __future__ import annotations

import asyncio
import pathlib
import secrets
import sys

# Make ``services`` / ``verticals`` importable when run as `python scripts/seed_operate_demo.py`.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))


async def _seed(run_id: str) -> None:
    from services.db.session import async_session
    from verticals.procurement.hero_demo.run import seed_operate_waiting_human_run

    async with async_session() as session:
        result = await seed_operate_waiting_human_run(session, run_id=run_id)
    print(f"seeded {result.run.run_id!r} -> status {result.run.status}")
    print("open the OCT Monitor (View H), log in as an approver (e.g. appr-pm), and operate it.")


def main() -> None:
    run_id = sys.argv[1] if len(sys.argv) > 1 else f"run-operate-{secrets.token_hex(3)}"
    asyncio.run(_seed(run_id))


if __name__ == "__main__":
    main()
