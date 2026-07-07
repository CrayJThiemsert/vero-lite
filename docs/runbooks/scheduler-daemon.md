# Runbook — the `schedule`-trigger scheduler daemon (PLAN-0055 / ADR-0028)

The long-lived worker that fires `schedule`-triggered procedures on a clock. It is a **pure
clock** — no MS-S1 / LLM dependency (the scheduler decides *when* to run; the run's executors,
behind the injected resolver, decide *what*). All scheduling policy (due/skip/missed/no-double-fire)
lives in the pure `fire_due_schedules` function (PLAN-0055 Step 4); the daemon is a thin loop
(Step 5) and this ops surface is the deploy wiring (Step 7).

## What it does

`uv run vero-lite scheduler --vertical <v>` performs, in order:

1. **Load** the vertical spec (`verticals/<v>/procedures.yaml`).
2. **Register** the vertical's procedure-executor factory (OQ-6: explicit, not auto-discovered —
   only **procurement** ships one today; energy has none, so an energy schedule would 409 at fire).
3. **Sync** `schedule_states` from the spec (the registration step): one row per
   `schedule`-trigger procedure, keyed `"<vertical>:<procedure_id>"`, carrying its `cron` + IANA
   `timezone`. Idempotent — the spec owns `cron`/`timezone`; the daemon owns the live clock
   (`last_fired`/`next_fire`), preserved across a re-sync. A cron change drops the stale
   `next_fire` so it recomputes.
4. **Run** the tick loop: every `--interval-seconds` (default 60) it reads the wall clock, loads
   the schedule set, and fires the due ones. Graceful shutdown on **SIGTERM / SIGINT** — it
   finishes the current tick (no torn writes; each fire commits atomically) then exits.

> **No vertical ships a `schedule`-trigger procedure yet.** Until the procurement demo (PLAN-0055
> Step 8) authors one (+ its `ServicePrincipal`), the daemon runs and ticks but syncs **0**
> schedules. This is expected — the machinery is in place ahead of the first real schedule.

## Prerequisites

- The `schedule_states` table exists — run migrations: `uv run alembic upgrade head` (0011).
- `DATABASE_URL` points at the target Postgres (see `docker-compose.yml` / `.env`).
- For a vertical whose runs reach a `gated` step, an authored `Person` approver must exist for a
  human to resolve the park (RF-1); a scheduled run's service actor can never self-approve (AC-5).

## Invocation

```bash
# foreground (Ctrl-C to stop)
uv run vero-lite scheduler --vertical procurement
# custom tick interval
uv run vero-lite scheduler --vertical procurement --interval-seconds 30
```

## Missed-round alerting (optional — PLAN-0055 Step 7a / AC-8)

When the daemon was down across one or more fire slots, the next tick fires the due slot once
(skip-no-backfill, SD-P2), logs a WARN `scheduler.missed_round`, and — if armed — sends a
best-effort Telegram ping so the **absence** of runs is detectable. Arm it with the existing
notifier env vars (no new bot; the ping carries no PII — schedule id + slot only):

```bash
TELEGRAM_NOTIFY_ENABLED=true
TELEGRAM_BOT_TOKEN=<bot token>
TELEGRAM_CHAT_ID=<chat id>
# TELEGRAM_NOTIFY_COOLDOWN_S=600   # optional; debounces repeat alerts (default 600s)
```

Unlike the MS-S1-unreachable ping, the missed-round alert has **no `llm_backend` gate** — it fires
regardless of which LLM backend (or none) is configured, and holds its own cooldown anchor.

## Observability (structured logs, `structlog`)

| event | level | meaning |
|-------|-------|---------|
| `scheduler.start` / `scheduler.stop` | info | loop lifecycle (graceful) |
| `scheduler.tick` | info | one pass — `evaluated` / `fired` / `skipped` / `recovered` counts |
| `scheduler.fired` | info | a run started (`schedule_id`, `run_id`, `run_status`, `missed`) |
| `scheduler.missed_round` | **warn** | downtime skipped ≥1 slot (also pings Telegram if armed) |
| `scheduler.already_fired` | warn | restart recovery — a slot's run already existed, not re-fired (AC-7) |
| `scheduler.skipped_in_flight` | warn | SD-P3 — a prior run of the same procedure is still parked |
| `scheduler.tick_failed` | error | a tick raised; logged + swallowed, the loop survives |

## Deploy: systemd

```ini
# /etc/systemd/system/vero-scheduler.service
[Unit]
Description=vero-lite schedule-trigger scheduler
After=network-online.target postgresql.service

[Service]
Type=simple
WorkingDirectory=/opt/vero-lite
EnvironmentFile=/opt/vero-lite/.env
ExecStart=/usr/local/bin/uv run vero-lite scheduler --vertical procurement
Restart=on-failure
RestartSec=5
KillSignal=SIGTERM
TimeoutStopSec=90

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload && sudo systemctl enable --now vero-scheduler
journalctl -u vero-scheduler -f          # watch the structured logs
```

`Restart=on-failure` + the per-slot idempotency guard (AC-7) make a crash safe: on restart the
daemon recovers the schedule set from `schedule_states` and does not re-fire a slot whose run
already committed.

## Deploy: docker / compose

Run the same console script as a separate service alongside the API (its own container, one
process = one daemon):

```yaml
# docker-compose.yml (excerpt)
services:
  scheduler:
    image: vero-lite:latest
    command: ["uv", "run", "vero-lite", "scheduler", "--vertical", "procurement"]
    env_file: .env
    depends_on: [db]
    restart: unless-stopped
    stop_signal: SIGTERM
    stop_grace_period: 90s
```

## Notes

- **Single instance.** Run exactly one scheduler process per (vertical, DB). Two would race on the
  same slots — the per-slot `run_id` PK makes a double-fire *fail loudly* (IntegrityError on the
  second), not silently duplicate, but it is still a misconfiguration.
- **MS-S1 stays cold.** Nothing here calls a model. Procurement's executor factory is a
  deterministic advisory stub (host-state-free).
