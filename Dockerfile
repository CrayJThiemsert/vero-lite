FROM python:3.12-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.11.9 /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
# --no-install-project: the image never needs this project installed as a
# distribution. Dropping the local build removes hatchling's build inputs
# (the package tree and the readme) from the image entirely, and keeps this
# layer cacheable because no source is COPY'd before it. See PLAN-0095 E-3
# before re-adding the install -- the migration command below does NOT need it.
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.12-slim AS runtime
WORKDIR /app
RUN useradd --system --no-create-home vero
COPY --from=builder /app/.venv /app/.venv
COPY services/ ./services/
COPY verticals/ ./verticals/
# One image, different commands: the default CMD serves the DB-less demo and
# never reads these, while `docker run <image> alembic upgrade head` is the
# pilot/production migration step (PLAN-0095 SD-2).
COPY alembic/ ./alembic/
COPY alembic.ini ./

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000

# Pre-create every path a named volume gets mounted on, owned by the runtime
# user. MEASURED 2026-08-08 (PLAN-0100 Step 11, case 5): without this the
# published demo wrote ZERO prompt-log rows across 90+ POST /query requests.
#
# The mechanism is Docker's, not ours. When a named volume is mounted on a path
# the image does NOT contain, Docker creates that path fresh as root:root 0755;
# only when the path already exists in the image does the volume inherit its
# content AND its ownership. The runtime drops to `vero` (uid 999) two lines
# below, so it landed on a root-owned directory it could not write to.
#
# It failed SILENTLY, which is what made it expensive: prompt_log.record swallows
# OSError by design (services/engine/llm/prompt_log.py:120) so a request never
# fails because of it — and PermissionError is an OSError. ADR-0035 D6's whole
# regime (the RoPA instance, 90-day retention, the runbook purge command, the DSR
# path) therefore described a file that did not exist. No offline test could see
# it: AC-8 exercises the writer function, never the deployed volume's ownership.
RUN mkdir -p /var/log/vero/prompt-log && chown -R vero:vero /var/log/vero

USER vero
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s \
  CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"]
# `python -m` puts the WORKDIR on sys.path by interpreter contract, which is what
# makes the copied trees importable with the project uninstalled. The bare console
# script would instead rely on an implementation detail of uvicorn's own sys.path
# handling.
CMD ["python", "-m", "uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
