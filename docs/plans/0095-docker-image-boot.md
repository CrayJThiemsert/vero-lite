# PLAN-0095: Docker image boot — build + serve the DB-less OCT demo

**Status:** Draft
**Owner:** Claude Code (draft authored by the `plan-drafter` subagent — see disclosure at foot)
**Created:** 2026-07-26
**Related ADRs:** ADR-0032 (D1 demo→pilot wedge — the strategic frame), ADR-006 (vertical plugin layout — why `verticals/` lives outside `services/`). **No new ADR is proposed** — see OQ-1.

## Goal

Make the scaffold-era `Dockerfile` actually build and boot, serving the synthetic
OCT demo **with no database**, gated by an **offline oracle** — a pytest module
that needs no Docker daemon and that **derives** the image's required content set
from the code instead of re-encoding the Dockerfile's text in a second file. The
deliverable is a hand-someone-the-demo image (exact shape = SD-1): `docker run -p
8000:8000 <image>` → `/health` answers and the OCT demo UI serves, on a machine
with nothing but Docker installed.

## Context (grounded against `main` = `1c19654`)

### Why now

ADR-0032 D1 makes the demo→pilot wedge the standing direction, and the session-175
ruling settled the demo target as the **live-API shape**. Today the engine boots
only on the dev machine. Prior art already names the problem verbatim — the
PLAN-0047 deferral note: *"Dockerfile cannot boot the app — copies only
`services/`, no `verticals/` or `alembic/`"*
(`docs/plans/done/0047-pre-pilot-hardening-authn-gate-audit.md:142-143`). The
`Dockerfile` is untouched since the initial scaffold commit (`56d9c3d`,
2026-05-07), and **nothing in the repo references it**: no `build:` key in
`docker-compose.yml` (postgres + redis only), zero hits in
`.github/workflows/ci.yml`, `scripts/`, or `tests/`, no root `Makefile`. That
absence is why "boots" has never had an acceptance criterion — this PLAN gives it
one.

### The defect set — two broken COPY statements, each with two symptoms, plus hygiene gaps

(Deliberately **not** "8 independent defects" — an earlier characterization
overstated independence.)

**Builder stage — `uv sync` at `Dockerfile:8` fails:**

- **D1** — `Dockerfile:7` copies only `pyproject.toml uv.lock`, but `uv sync`
  installs the local project, and hatchling (`pyproject.toml:51-52`,
  `packages = ["services"]`) finds no package tree → build fails.
- **D2** — `pyproject.toml:7` declares `readme = "README.md"`, which hatchling
  also reads at build time; `README.md` is never copied either, so even with D1
  fixed, `uv sync` fails a second time.

**Runtime stage — boot fails:**

- **D3 (first-order)** — `Dockerfile:13` copies only `services/`; `verticals/`
  is never copied. The first failure is a plain Python import, not a file-path
  miss: `services/engine/discovery.py:45` calls
  `importlib.import_module(_VERTICALS_PACKAGE)` (the constant
  `_VERTICALS_PACKAGE = "verticals"` at `discovery.py:33`), invoked uncaught as
  the first line of `lifespan()` (`services/api/main.py:166`) →
  `ModuleNotFoundError` at boot.
- **D4** — `alembic/` + `alembic.ini` are never copied. Alembic is live (12 real
  revisions under `alembic/versions/`; `docs/runbooks/run-oct-demo.md:72,258,468`
  runs `uv run alembic upgrade head` as normal practice) — but whether the
  **image** needs it at all is a design question. This PLAN proposes to
  **ELIMINATE** it from the image (SD-2).
- **D5 (second-order — reachable only once D3 is fixed)** — CWD-relative path
  resolution: `services/engine/ontology_meta.py:152-154` returns
  `Path("verticals") / vertical / "ontology" / f"{vertical}_v0.yaml"` and
  `services/engine/procedures/spec.py:1820-1822` returns
  `Path("verticals") / vertical / "procedures.yaml"`. Both resolve against CWD,
  so the fix must copy `verticals/` **and** keep `WORKDIR /app` consistent with
  the copy destinations. This is a recognized codebase idiom
  (`services/engine/procedures/at2_signature.py:15-20` documents it); a targeted
  search found no other CWD-relative roots under `services/`.

**Hygiene gaps (not boot blockers — scoped deliberately in SD-3):** no `USER`
(runtime runs as root), no `HEALTHCHECK`, no `.dockerignore` anywhere in the repo
(verified absent), stale `uv:0.4` pin at `Dockerfile:4`.

### Boot-without-a-database is viable — verified, not assumed

- Engine creation is lazy: *"importing this module does not open a connection"*
  (`services/db/session.py:3-5`, docstring).
- Every `Settings` field has a default — no required env var
  (`services/api/config.py`; `database_url` defaults at `:38-41`, `oct_vertical`
  defaults to `"energy"` at `:179-185`, `oct_demo_seed_operate` defaults `False`
  at `:243-253`; `settings = Settings()` at `:328` constructs cleanly from
  nothing).
- `lifespan()` (`services/api/main.py:159-219`) touches the DB **only** under
  `if vertical == "procurement" and settings.oct_demo_seed_operate:`
  (`:187-192`) — off by default, and fail-soft even then (`try/except` at
  `:197-210`).
- The one unconditional data call at boot —
  `await registry.get_adapter(vertical).fetch_objects("OperationalEvent")`
  (`main.py:178`) — resolves, for the default `energy` vertical, to the
  **synthetic** adapter: *"Return synthetic object dicts"*
  (`verticals/energy/data_adapter/__init__.py:52-63`). No DB.
- The demo UI is served from a `Path(__file__)`-anchored directory
  (`_STATIC_DIR = Path(__file__).parent / "static"`, `main.py:37`, mounted at
  `:256`), so `COPY services/` already carries it.
- Conclusion: with `verticals/` present, boot does not hard-require Postgres.
  DB-backed routes fail only when actually called — acceptable for the synthetic
  demo target.

One operational note, not a defect: `api_auth_enabled` defaults `True`
(`config.py:53-61`) and gates **state-changing** routes only, so the read-side
demo works out of the box; a demo of the approve/execute loop needs either
provisioned `API_KEYS` or `-e API_AUTH_ENABLED=false` at `docker run`. Step 7
documents this.

## Design

### The fix — eliminate the project install instead of feeding it

The image never needs the project installed as a distribution. The only two
consumers of `uv sync`'s local-project install are the importable `services`
wheel and the `vero-lite` console script (`pyproject.toml:44-45`) — and the
image's CMD uses neither: `services/` and `verticals/` are copied to `/app`, and
running uvicorn as `python -m uvicorn` puts the CWD (`/app`) at the head of
`sys.path` by documented interpreter contract. So **D1 and D2 are ELIMINATED,
not repaired**: `--no-install-project` removes the hatchling build from the
image entirely, which also preserves the dependency-layer cache (no source COPY
before `uv sync`).

Target `Dockerfile` (the Step 2 rewrite; hygiene lines land in Step 4 per SD-3):

```dockerfile
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.4 /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY services/ ./services/
COPY verticals/ ./verticals/
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Design points:

- `COPY verticals/ ./verticals/` + unchanged `WORKDIR /app` fixes D3 **and** D5
  together (the CWD-relative `Path("verticals")` reads resolve under `/app`).
- `CMD ["python", "-m", "uvicorn", ...]` replaces the bare `uvicorn` console
  script. With the project no longer installed, `import services` /
  `import verticals` must resolve via `sys.path`; `python -m` guarantees CWD on
  `sys.path` by interpreter contract, where the bare console script relies on
  uvicorn's internal `sys.path.insert(0, ".")` — an implementation detail we
  choose not to depend on. `uvicorn[standard]` is a main dependency
  (`pyproject.toml:11`), so it survives `--no-dev`.
- The venv relocation pattern (`COPY --from=builder /app/.venv` + same base
  image + `ENV PATH`) is unchanged from the scaffold — it was never the broken
  part.
- `alembic/` is **not** copied (SD-2 recommendation). The `alembic` *library*
  stays in the venv regardless (main dependency, `pyproject.toml:15`) — removing
  it from `dependencies` is out of scope.

### The oracle — derived coverage, not a text mirror

The failure mode that matters is not "someone edits the Dockerfile" — it is
"someone adds a new runtime-resolved root under `services/` and the image
silently stops booting." A test that hardcodes the expected COPY list re-encodes
the Dockerfile and passes tautologically forever. So the oracle **derives** the
required set from the code and asserts the Dockerfile covers it. One new module,
`tests/docker/test_dockerfile_oracle.py` (follow the existing `tests/handoffs/`
subpackage precedent), stdlib + pytest only — `ast`, `tomllib`, `pathlib` — no
Docker SDK, no subprocess, no daemon. All repo paths are anchored at
`Path(__file__)`, never CWD.

**O-1 — runtime-root coverage (the load-bearing check).**
1. Parse the `Dockerfile` (line-based; split stages on `FROM`; take the final
   stage as runtime). Collect build-context `COPY` sources/destinations
   (ignore `--from=` copies here) and the `WORKDIR`; normalize destinations
   against it.
2. AST-scan every `services/**/*.py` **and every `verticals/**/*.py`**: collect
   the first path component of every relative single-string first argument to
   `Path(...)`, and the top-level package of every `import_module(...)`
   argument. **Arguments are resolved as either a string literal or a
   same-module module-level string constant** — constant resolution is
   mandatory, because the real defect's call site passes `_VERTICALS_PACKAGE`
   (`discovery.py:33` → `:45`); a literal-only scan misses the very bug that
   motivates the oracle.

   *[R2 correction, Code, at commit — the draft scanned `services/` only.
   Measured: `verticals/` has **zero** relative `Path("…")` roots and zero
   `import_module(` calls today, so widening the glob is **behavior-neutral
   now**. It is added because `verticals/` is the part of the tree that grows
   (one directory per new vertical), and "someone adds a new runtime-resolved
   root and the image silently stops booting" — the exact failure class this
   oracle exists to catch — is at least as likely to arrive there as under
   `services/`. Cost: one glob. The step-3 existence filter already prevents a
   bogus root from a seed/output path.]*
3. Filter the derived names to those that exist as top-level directories of the
   repo root (this drops installed-package imports like `yaml` and output-file
   paths, with zero hardcoded allowlist). Add `services` itself as the app root.
4. Assert: every derived root is covered by a runtime-stage COPY landing at
   `<WORKDIR>/<root>`.

Honest limitation, stated up front: a path root built dynamically or a constant
imported from *another* module is not derived — the scan is one-hop. The born-RED
run (AC-2) proves the one-hop scan catches the real, current defect class.

**O-2 — builder project-install invariant.** Locate the builder stage's
`RUN … uv sync …` line. Pass iff **either** `--no-install-project` is present,
**or** every hatchling build input — derived from `pyproject.toml` via `tomllib`
(`[project].readme`, each `[tool.hatch.build.targets.wheel].packages` entry) plus
`pyproject.toml` + `uv.lock` — is COPY'd into the stage **before** that RUN.
Two satisfying configurations, both semantically valid; nothing re-encodes the
current Dockerfile text.

**O-3 — import-strategy + WORKDIR consistency.** The runtime stage must declare
a `WORKDIR`; every O-1 derived root must land under it (the D5 guard); and
**either** the project is installed in the venv (O-2's second branch) **or** the
CMD is the exec-form `python -m uvicorn …` (CWD-on-`sys.path` guaranteed). This
is a two-configuration semantic invariant, not a CMD-text mirror: it fails
exactly when the import strategy has no guaranteed resolution path.

**Anti-tautology invariant (AC-3):** the oracle module must not contain the
string `verticals` anywhere — code, comments, or docstrings. Coverage of
`verticals/` must *fall out* of derivation. This is a one-line greppable check
any reviewer can run.

### Mutation table — the RED each oracle must show (non-vacuity, pre-committed)

| ID | Mutation | Expected RED |
|----|----------|--------------|
| M-A | The unmodified Dockerfile @ `1c19654` (no mutation needed — the oracle is born failing) | O-1 fails naming the missing verticals package root; O-2 fails (no flag, hatchling inputs absent) |
| M-B | Delete the `COPY verticals/ ./verticals/` line from the fixed Dockerfile | O-1 fails naming that root |
| M-C | Add `Path("webroot")` to any scanned `services/` module + create top-level `webroot/` dir; **no Dockerfile edit** | O-1 fails naming `webroot` — proves the derivation arm is live, not a frozen list |
| M-D | Strip `--no-install-project` from the `uv sync` line | O-2 fails (neither branch satisfied) |
| M-E | Revert CMD to `["uvicorn", ...]` | O-3 fails (no guaranteed import path with the project uninstalled) |

Mutation procedure (binding, per the false-PASS hazard in project memory): copy
each file-under-mutation to the session scratchpad **before** editing, observe
the RED, restore **from the scratchpad copy** — never `git checkout` (which can
wipe the edit under test and fake a PASS). Verify restoration via `git status`
clean + removal of the `webroot/` scratch dir.

## Acceptance Criteria

- [ ] **AC-1 — offline oracle exists and passes.** `tests/docker/test_dockerfile_oracle.py`
  implements O-1/O-2/O-3 and passes against the fixed Dockerfile.
  *Pass/fail read (pre-committed):* `pytest tests/docker -q` exits `0`, run per
  CLAUDE.md §8 evidence rules (streams merged `2>&1`, escaped `\$?`, no
  `head`/`tail` pipe). *No-daemon property:* the module imports stdlib + pytest
  only — a Grep for `subprocess|docker` over the module shows no tool
  invocation, and the CI PR run (whose workflow has zero Dockerfile references)
  executes it green.
- [ ] **AC-2 — born-RED recorded.** The identical oracle, run against the
  unmodified Dockerfile (M-A), fails with **two distinct assertion families**
  (runtime-root coverage; builder-install invariant). *Pass/fail read:*
  transcript in the PR body showing both failures and a non-zero exit.
- [ ] **AC-3 — anti-tautology.** The oracle module contains **zero** occurrences
  of the string `verticals`. *Pass/fail read:* Grep over the module = 0 matches.
  *Falsifying mutation:* M-C goes RED with no Dockerfile edit — the coverage set
  is derived, not enumerated.
- [ ] **AC-4 — mutations bite.** M-B, M-C, M-D, M-E each produce the RED named
  in the mutation table. *Pass/fail read:* mutation transcripts in the PR body,
  each with non-zero exit naming the right oracle; working tree restored clean
  afterward (scratchpad-restore procedure).
- [ ] **AC-5 — repo gates, full scope.** Full `ruff` clean, full
  `mypy services/` clean, **full** `pytest` green offline before push (the
  offline gate matches CI scope — never the changed subset alone). *Pass/fail
  read:* exit `0` on each, evidence rules as AC-1.
- [ ] **AC-6 — no AC needs a daemon.** Every AC above is evaluable with Docker
  absent; the live build appears only as Step 6, explicitly OPTIONAL +
  Cray-gated, labeled *evidence, not gate*. *Pass/fail read:* R2 reviewer
  inspection of this list + Steps.
- [ ] **AC-7 (contingent on SD-3).** Each hygiene item Cray rules IN ships with
  its own oracle assertion + named mutation: `USER` (mutation: delete the line →
  RED), `HEALTHCHECK` (mutation: delete → RED; the check command must be
  stdlib-python exec-form — slim has no curl), `.dockerignore` (mutation: delete
  the file or its `.env` line → RED). Items ruled OUT are recorded as waived
  here. (The uv pin refresh is deliberately oracle-less — "freshness" is not
  statically decidable; evidence = the diff itself. See SD-3d.)

## Out of Scope

- ❌ **CI image build.** Not proposed. Cost if wanted later: minutes per PR +
  registry pulls + a second gate surface, against a repo whose gate is the
  offline oracle (CLAUDE.md §8). Cray can raise it as a separate decision;
  nothing here precludes it.
- ❌ **Compose `app` service** — unless SD-1 is ruled (b)/(c); the default
  deliverable is the standalone image.
- ❌ **DB-full image mode / migrations-in-image** — SD-2 proposes eliminating
  `alembic/` from the image; the checkout-based
  `uv run alembic upgrade head` runbook flow is untouched and stays the
  migration path.
- ❌ **Dependency changes** — `alembic`/`celery`/`redis` stay in
  `pyproject.toml` `dependencies`; slimming the dep tree is a different task.
- ❌ **Runtime code changes** — the diff is `Dockerfile` + new tests + docs
  (+ `.dockerignore` if SD-3c is IN). M-C touches a `services/` module only
  transiently under the scratchpad-restore procedure and is never committed.
- ❌ **Registry publish / image tagging / release flow.**

## Surfaced Decisions (for Cray — not decided here)

- **SD-1 — What is the deliverable?** (a) a standalone `docker run` artifact
  **[recommended]**; (b) a compose service (`build:` key beside
  postgres/redis); (c) both. *Why (a):* it matches the ADR-0032 D1 wedge —
  hand-someone-the-demo — and the DB-less demo needs neither compose neighbor;
  a compose service would be a maintained surface with **no current consumer**
  (compose today is dev-infra only). *Why Cray:* there is no offline oracle for
  a distribution-shape judgment; it is a product/positioning call. The draft's
  Steps assume (a); ruling (b)/(c) adds a small compose + oracle-extension step.
- **SD-2 — `alembic/` in the image?** (a) **ELIMINATE** — do not copy
  `alembic/` or `alembic.ini` **[recommended]**; (b) include + document
  `docker run … alembic upgrade head` as a DB-full mode; (c) a separate
  migration image later, if a pilot needs it. *Why (a):* the demo target is
  deliberately DB-less; migrations are an operator action run from a checkout
  (`docs/runbooks/run-oct-demo.md:72,258,468`), and shipping migration
  machinery in a demo appliance widens what the artifact claims to be. *Why
  Cray:* this decides the artifact's identity (demo appliance vs deployable
  app) — a product-surface call with no oracle.
- **SD-3 — hygiene scope.** Rule each IN/OUT: (3a) `USER` nonroot (~2 lines +
  a `useradd` layer; container-escape hardening); (3b) `HEALTHCHECK` via
  stdlib-python exec-form against `/health` (`main.py:241-248` is a pure
  liveness probe, no DB — verified); (3c) `.dockerignore` (repo has none —
  keeps `.git`/`.venv`/`.env*` out of the build context sent to the daemon;
  `.env` hygiene is §8-adjacent); (3d) refresh the stale `uv:0.4` pin.
  *Recommendation: all four* — each is small and (3a–3c) oracle-checkable —
  but it is scope, and scope is Cray's. *Why Cray:* no oracle ranks "enough
  hygiene for a demo image"; it is a scope/posture judgment.

## Steps (cheapest + most reversible first; each with rollback)

### Step 1 — Write the oracle; watch it fail for the right reasons
Implement `tests/docker/test_dockerfile_oracle.py` (O-1/O-2/O-3 per Design) and
run it against the **unmodified** Dockerfile. *Pre-committed read:* non-zero
exit with the two M-A assertion families, the coverage failure naming the
verticals package root **in the failure message only** (the module source stays
clean per AC-3). Capture the transcript for the PR body (AC-2).
*Rollback:* delete `tests/docker/` — new files only, nothing else touched.

### Step 2 — Rewrite the Dockerfile
Apply the target Dockerfile from Design (single-file diff). *Pre-committed
read:* `pytest tests/docker -q` exits `0` (AC-1). *Rollback:* `git revert` of
the one-file commit.

### Step 3 — Mutation probes
Run M-B, M-C, M-D, M-E per the mutation table, scratchpad-copy → mutate →
observe RED → restore-from-copy (never `git checkout`). *Pre-committed read:*
four non-zero exits, each naming the expected oracle; `git status` clean after;
`webroot/` removed. Capture transcripts (AC-4). *Rollback:* the restore
procedure is the rollback; nothing is committed in this step.

### Step 4 — Hygiene per SD-3 ruling *(contingent)*
Add each ruled-IN item + its oracle assertion + run its named mutation (AC-7).
The `uv` pin refresh (3d) lands here oracle-less, with the chosen version noted
in the commit body. *Pre-committed read:* oracle suite green; per-item mutation
RED observed. *Rollback:* each item is an independent revertable line/file.

### Step 5 — Full offline gates + PR
Full `ruff` + `mypy services/` + full `pytest` (AC-5), then branch + PR per §7
(commit body via file, PR body via `--body-file`, transcripts embedded).
*Pre-committed read:* three zero exits, CI green on the PR. *Rollback:* n/a —
branch never touches `main` directly.

### Step 6 — OPTIONAL live-build evidence *(host-state — Cray-gated, runs only on explicit go)*
`docker build` writes an image into the local daemon's store — **outside the
worktree** — so this entire step requires an explicit Cray go **before** any
command runs (CLAUDE.md §8), and runs **once**. It is *evidence, not a gate*:
the PLAN completes without it. On go: `docker build -t vero-lite-demo .` →
`docker run --rm -p 8000:8000 -e API_AUTH_ENABLED=false vero-lite-demo` →
`curl /health` (expect `{"status":"ok",…}`) + one OCT read route returning
demo JSON. *Pre-committed read:* HTTP 200 on both, no Postgres running
anywhere. *Rollback/cleanup:* `docker rmi vero-lite-demo` (state it in the
evidence log). This step also settles OQ-2/OQ-3 empirically.

### Step 7 — Runbook section
Add "Run the demo from the image (DB-less)" to
`docs/runbooks/run-oct-demo.md` (or the SD-1-ruled home): the `docker run`
line, the `API_AUTH_ENABLED=false` / provisioned-`API_KEYS` note for the
approve/execute leg (`config.py:53-61`), and the explicit statement that
DB-backed routes are out of the image's demo scope. *Pre-committed read:* doc
builds no claims beyond what Steps 1–5 verified (each "the image does X" line
must trace to an AC or to Step 6 evidence). *Rollback:* revert the doc commit.

## Open Questions

- **OQ-1 — Is an ADR needed?** Author's read: **no** — this repairs
  already-committed broken scaffold code and adds a test; it creates no new
  architectural constraint (and no ADR currently mentions Docker — verified,
  zero matches across `docs/adr/`). *Tripwire:* if SD-1 lands on (b)/(c) **and**
  a CI image build is later added, the combination starts defining a deployment
  architecture — reconsider a small ADR at that point, per the dispatch's
  instruction to surface rather than draft.
- **OQ-2 — Does `uv:0.4` support `--no-install-project`?** Believed yes (the
  flag predates 0.4) — **still asserted-not-verified for 0.4**. Verify at
  execution, offline and in-worktree, before Step 2 lands. If not supported,
  SD-3d (pin refresh) becomes mandatory in Step 2 rather than hygiene in Step 4.

  *[R2 measurement, Code, at commit — NARROWED, not closed. The dev box runs
  `uv 0.11.9` and its `uv sync --help` does list `--no-install-project`
  (1 match). That confirms the flag on **0.11.9 only** and says nothing about
  the `ghcr.io/astral-sh/uv:0.4` image the `Dockerfile` pins — the two are
  ~7 minor versions apart, so this is evidence the design is sound on a modern
  uv, NOT evidence that the pinned builder accepts the flag. Practical read:
  it raises the odds that OQ-2's own fallback fires and SD-3d becomes
  mandatory. A cheaper resolution than a live `docker build`: pull the 0.4
  image's `--help` — but that is a daemon action, so it belongs in the
  Cray-gated Step 6, not the offline gate.]*
- **OQ-3 — Residual uv-behavior risk.** The offline oracle asserts the
  invariant *structure*; whether `uv sync --frozen --no-dev
  --no-install-project` behaves exactly as designed inside the builder is
  ultimately an empirical fact about uv. That residue is precisely what the
  optional Step 6 evidence covers — and why Step 6 exists at all.

## Eliminations proposed (per the dispatch's standing permission)

- **E-1 (decided by this design, oracle-covered):** the local-project install
  in the builder — D1 + D2 are removed, not repaired (`--no-install-project`).
- **E-2 (surfaced, SD-2):** `alembic/` + `alembic.ini` in the image.
- **E-3 (recorded so nobody re-adds it "for free"):** the `vero-lite` console
  script inside the image. It was never a stated requirement; re-adding it
  means re-adding the project install and both of its build-input problems.
  If an in-container CLI is ever wanted, that is a deliberate decision, not a
  side effect.

## Verification

How do we know it worked: the oracle was **born failing** against the broken
Dockerfile (AC-2), passes against the fixed one (AC-1), cannot be satisfied by
text-mirroring (AC-3 + M-C), and every load-bearing line of the fix has a named
mutation that turns the suite RED (AC-4) — all with **no Docker daemon**
anywhere in the gate path (AC-6). The optional live build (Step 6) is
corroborating evidence under CLAUDE.md §8, not the gate. Long-term regression
value: the derived oracle fails the build the day someone adds a new
runtime-resolved root under `services/` without teaching the image about it —
the failure mode that actually matters.

---

*Authorship disclosure (ADR-012 D4.3): drafted by the in-harness `plan-drafter`
subagent from a Code-originated dispatch (session 176 era, `main`@`1c19654`);
independent review = Code R2 + Cray ratification at PR merge. Separation:
INTACT — the drafter neither commits nor reviews.*
