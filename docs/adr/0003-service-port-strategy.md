# ADR-003: Service Port Strategy

**Status:** Accepted
**Date:** 2026-05-06
**Deciders:** Jirachai Thiemsert (founder)
**Related:** ADR-002 (network topology), PLAN-001 (starter pack scaffold)

## Context

vero-lite is being developed on **Cray-Legion5Pro**, a shared developer machine that already runs multiple long-lived Docker stacks for the founder's other projects (notably **smb-flow**). During Phase E of PLAN-001 execution, attempting `docker compose up -d` failed because vero-lite's default service ports collided with already-running containers:

```
Active containers on Cray-Legion5Pro (smb-flow stack):
- smb-dev-postgres    → 0.0.0.0:5432   (Postgres 16-alpine)
- aaas-postgres       → 0.0.0.0:5433   (Postgres 16)
- aaas-legacy-procurement-db → 0.0.0.0:5434
- aaas-legacy-healthcare-db  → 0.0.0.0:5435
- smb-dev-redis       → internal-only on 6379 (no host bind, OK)
- smb-dev-whisper     → 0.0.0.0:8000   (FastAPI/Whisper)
- ...and others (n8n, pgadmin, dashboards, tunnels)
```

vero-lite's intended ports clashed at three levels:
- **Postgres 5432** — taken by `smb-dev-postgres`
- **Redis 6379** — free (smb-dev-redis is internal only)
- **FastAPI 8000** — taken by `smb-dev-whisper`

PLAN-001 anticipated this risk ("can change in `.env` if conflict") but the scaffold templates hard-coded the host ports in `docker-compose.yml`, so the conflict could not be resolved without code changes.

Three forces are at play:

1. **Founder co-tenancy** — the same dev box hosts multiple long-running projects. Stopping smb-flow containers to free ports is destructive (loses in-progress state) and only works if the dev knows their machine inside-out.
2. **Design partner deployments** — vero-lite will eventually run on vet-clinic dev/staging machines whose port allocations are unknown. The scaffold has to handle "your environment, your ports" cleanly.
3. **PDPA-aligned isolation** — each vet clinic deployment should be independently configurable so that one tenant's port choice can't accidentally collide with another.

## Decision

All host-side service ports in `docker-compose.yml` use the `${VAR:-default}` fallback pattern, parameterised through the `.env` file:

```yaml
# docker-compose.yml
services:
  postgres:
    ports:
      - "${POSTGRES_HOST_PORT:-5432}:5432"
  redis:
    ports:
      - "${REDIS_HOST_PORT:-6379}:6379"
```

The FastAPI app is started with an explicit `--port` flag (no automatic Docker mapping in dev), defaulting to 8000 but overridable per-machine.

### Port allocation table

| Service           | Container port | Default host port | Env variable          | vero-lite on Cray-Legion5Pro |
|-------------------|----------------|-------------------|-----------------------|------------------------------|
| Postgres          | 5432           | 5432              | `POSTGRES_HOST_PORT`  | **5436** (5432–5435 taken)   |
| Redis             | 6379           | 6379              | `REDIS_HOST_PORT`     | 6379 (free)                  |
| FastAPI (dev)     | n/a            | 8000              | `--port` flag         | **8001** (8000 taken)        |

### File responsibilities

- `.env.example` — committed to git, documents the variables and **uses vendor defaults** (5432, 6379, 8000). This is the canonical reference for new contributors.
- `.env` — git-ignored, **per-machine overrides**. Created by the developer when their environment requires non-default ports.
- `docker-compose.yml` — uses `${VAR:-default}` fallback so the file is consistent across machines.
- `DATABASE_URL` / `REDIS_URL` — must always match the chosen `*_HOST_PORT` (these are what host-side processes connect to).

### Rule for future services

Any new service added to vero-lite that binds a host port (e.g., MCP server, Celery flower, MinIO) **must** follow the same pattern:

```yaml
service-name:
  ports:
    - "${SERVICE_NAME_HOST_PORT:-DEFAULT}:CONTAINER_PORT"
```

with a corresponding entry in `.env.example` and (where applicable) the port allocation table above.

## Consequences

### Positive

- **Coexistence with other projects** — vero-lite never demands exclusive ownership of vendor-default ports. Developers running smb-flow, other side projects, or even other vet-clinic deployments on the same box are unaffected.
- **Design-partner-ready** — when we deploy at the first vet clinic, their dev box may already have Postgres or Redis running. They edit `.env`, not `docker-compose.yml`. No fork, no manual merge later.
- **CI/CD reproducibility** — CI runners (eventually self-hosted on MS-S1 MAX) start with a known-clean port space. They use `.env.example` defaults; conflicts there indicate a real problem worth surfacing.
- **No destructive operations** — Phase E recovery used `docker compose down` (vero-lite stack only) and a `.env` edit. The smb-flow stack was never touched.
- **Documents an actual lived experience** — this ADR was written while the conflict was fresh, capturing reasoning that would have been lost or rationalised retroactively.

### Negative

- **One more file to remember** — new contributors must `cp .env.example .env` before `docker compose up`. The bootstrap script handles this, but manual setup needs the step.
- **`DATABASE_URL` duplication** — the connection string and `POSTGRES_HOST_PORT` must agree. A malformed `.env` (e.g., port mismatch between the two) will fail at runtime, not at parse time. Mitigated by `pydantic-settings` validation in `services/api/config.py` (TODO: add cross-field validator).
- **Slightly more shell substitution** — `docker-compose` parses `${VAR:-default}` correctly, but tools that read the YAML statically (e.g., some IDE plugins) may not. Acceptable trade-off.

### Neutral

- The `${VAR:-default}` syntax is standard POSIX shell parameter expansion and is supported by `docker compose` v2 (which the project requires anyway).
- This ADR does not specify which ports to use *in production*. Production port selection (Kubernetes services, cloud load balancers, etc.) is a separate concern, deferred to a future ADR when production deployment is on the roadmap.

## Alternatives Considered

### Alternative 1: Hardcode different ports in `docker-compose.yml`

Just change `5432:5432` to `5436:5432` directly in `docker-compose.yml`.

- **Pros:** Zero new files, simplest diff.
- **Cons:** vero-lite repo permanently encodes "Cray-Legion5Pro's specific port allocation," which is arbitrary and machine-specific. Every other developer would have to either accept the wrong defaults or fork the file.
- **Why rejected:** Burns founder's machine quirks into the public repo's defaults. Breaks the moment a second person clones it.

### Alternative 2: Stop smb-flow containers before `docker compose up`

Use `docker stop smb-dev-postgres smb-dev-whisper` whenever working on vero-lite.

- **Pros:** No code change.
- **Cons:** Destructive (interrupts smb-flow work), error-prone (must remember to restart afterward), and doesn't generalise — vero-lite cannot demand its host's other services step aside.
- **Why rejected:** Treats co-tenancy as a problem to bulldoze rather than a constraint to design around. Won't survive contact with design partners.

### Alternative 3: Use a per-developer `docker-compose.override.yml`

Docker Compose's official mechanism for local overrides.

- **Pros:** Native Docker Compose feature, well-documented.
- **Cons:** Requires the developer to know about the override file convention. Less discoverable than `.env`. Two files to keep in sync (override file + Python's `Settings` reading `.env`).
- **Why rejected:** `.env` already exists for the Python app's configuration (Pydantic Settings). Reusing it for ports avoids a second source of truth. We can revisit `compose.override.yml` if container-specific overrides (volumes, healthchecks) become needed beyond just ports.

### Alternative 4: Random / dynamic port allocation

Have Docker Compose pick any free port (`- "5432"` instead of `"5432:5432"`).

- **Pros:** Never conflicts.
- **Cons:** The actual port is unknown until containers start, which breaks `DATABASE_URL` in `.env`, hardcoded test fixtures, and developer muscle memory ("connect with `psql -p 5432`").
- **Why rejected:** Solves a problem that isn't really there (dev needs *predictable* ports, not *automatic* ones) and creates a worse one (configuration sprawl).

## References

- Phase E execution log (Session 3): `docker compose up` first attempt failed with port 5432 conflict; second attempt with `.env` overrides succeeded.
- Docker Compose environment variables: https://docs.docker.com/compose/environment-variables/
- POSIX parameter expansion (`${VAR:-default}`): https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html#tag_18_06_02
- smb-flow port allocations observed during Phase E: `5432, 5433, 5434, 5435, 5050, 5678, 5679, 8000, 8501, 3000` (informational, may change).

## Implementation Notes

### Pattern reference (for future ADRs and PRs)

```yaml
# docker-compose.yml — every host port is overridable
services:
  <service>:
    ports:
      - "${<SERVICE>_HOST_PORT:-<vendor-default>}:<container-port>"
```

```bash
# .env.example — vendor defaults, committed
<SERVICE>_HOST_PORT=<vendor-default>

# .env — per-machine overrides, gitignored
<SERVICE>_HOST_PORT=<actual-free-port>
```

### Connection string consistency

`DATABASE_URL` and `REDIS_URL` are read by Python (Pydantic Settings) and must agree with the `*_HOST_PORT` chosen for Docker. Future improvement: add a Pydantic `model_validator` that asserts the URL's port equals `POSTGRES_HOST_PORT` / `REDIS_HOST_PORT` and fails fast at app startup with a helpful error message.
