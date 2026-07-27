# PLAN-0095: Docker image boot — build + serve the DB-less OCT demo

**Status:** Complete
**Owner:** Claude Code (draft authored by the `plan-drafter` subagent — see disclosure at foot; revised after the Cray SD rulings, session 176)
**Created:** 2026-07-26
**Completed:** 2026-07-27 (session 177) — Steps 1–5 in [#927](https://github.com/CrayJThiemsert/vero-lite/pull/927), Step 7 in [#928](https://github.com/CrayJThiemsert/vero-lite/pull/928). Step 6 (optional live evidence) ran on Cray's explicit go: the image built for the first time, `/health` answered 200 about two seconds after `docker run` with no database reachable, all six verticals appeared in the boot log, the container ran as `uid=999(vero)` with its `HEALTHCHECK` reporting `healthy`, and `alembic current` printed `0012 (head)` from inside the image against the live Postgres. **OQ-2's residual and OQ-3 are both resolved by that run**; OQ-1 (the hosting model) remains open by design.
**Related ADRs:** ADR-0032 (D1 demo→pilot wedge — the strategic frame), ADR-006 (vertical plugin layout — why `verticals/` lives outside `services/`), ADR-002 (LAN trust model — *touched* by the hosting question; surfaced in OQ-1, **not decided here**). **No new ADR is proposed** — see OQ-1.

## Goal

Make the scaffold-era `Dockerfile` actually build and boot, serving the synthetic
OCT demo **with no database**, gated by an **offline oracle** — a pytest module
that needs no Docker daemon and that **derives** the image's required content set
from the code instead of re-encoding the Dockerfile's text in a second file.
Per the session-176 rulings the deliverable is **both** (SD-1 = (c)): the
**standalone image is THE artifact** — `docker run -p 8000:8000 <image>` →
`/health` answers and the OCT demo UI serves on a machine with nothing but
Docker — and a **thin compose service that consumes that same image** proves the
pilot→production path (the image composes with a real Postgres). The artifact is
**shaped to grow into production without a rewrite** under two hosting models
(customer uses an instance we host; we stand up a server at the customer's
site) — *shaped to grow*, *not built-as-production*: TLS, secrets, orchestration
and release flow stay Out of Scope.

## Context (grounded against `main` = `1c19654`)

### Why now

ADR-0032 D1 makes the demo→pilot wedge the standing direction, and the session-175
ruling settled the demo target as the **live-API shape**. Today the engine boots
only on the dev machine. Prior art already names the problem verbatim — the
PLAN-0047 deferral note: *"Dockerfile cannot boot the app — copies only
`services/`, no `verticals/` or `alembic/`"*
(`docs/plans/done/0047-pre-pilot-hardening-authn-gate-audit.md:142-143`). The
`Dockerfile` is untouched since the initial scaffold commit (`56d9c3d`,
2026-05-07), and **nothing in the repo referenced it at the start of this
PLAN**: no `build:` key in `docker-compose.yml` (postgres + redis only), zero
hits in `.github/workflows/ci.yml`, `scripts/`, or `tests/`, no root `Makefile`.
That absence is why "boots" has never had an acceptance criterion — this PLAN
gives it one.

### The production frame (Cray ruling, session 176)

Cray's reframe, recorded because it overturned two of this draft's
recommendations: *"วันนี้อาจจะเป็นแค่ demo+pilot ก็จริง แต่ถ้ามันต้องกลายเป็น
pilot→production ควรเป็นรูปแบบไหน เราอยากให้มีเป็นรูปแบบที่พร้อมสำหรับการพัฒนาสู่
production ที่อาจเป็นได้ทั้งลูกค้าใช้งานผ่าน server ของเรา หรือ เราไปสร้าง server
ให้ลูกค้า"* — the artifact must be shaped so it grows into production without a
rewrite, under two hosting models: (i) the customer uses an instance we host,
(ii) we stand up a server at the customer's site. The boundary is explicit:
**"ready for development toward production," not "build production now."**
Three consequences drive the revisions below:

1. In **both** hosting models the unit of deployment is the **same standalone
   image** — compose does not replace it, compose *consumes* it (SD-1 ruling).
2. The production pattern is **one image, different commands**: the unchanged
   default CMD serves the DB-less demo; `docker run <image> alembic upgrade
   head` is the pilot/production migration step (SD-2 ruling).
3. The over-promise concern that motivated eliminating `alembic/` is answered
   **by documentation, not by omission** (SD-2 ruling; E-2 withdrawn).

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
  runs `uv run alembic upgrade head` as normal practice). **SD-2 ruling: the
  image INCLUDES both, documented** — one image, different commands (see
  Surfaced Decisions).
- **D5 (second-order — reachable only once D3 is fixed)** — CWD-relative path
  resolution: `services/engine/ontology_meta.py:152-154` returns
  `Path("verticals") / vertical / "ontology" / f"{vertical}_v0.yaml"` and
  `services/engine/procedures/spec.py:1820-1822` returns
  `Path("verticals") / vertical / "procedures.yaml"`. Both resolve against CWD,
  so the fix must copy `verticals/` **and** keep `WORKDIR /app` consistent with
  the copy destinations. This is a recognized codebase idiom
  (`services/engine/procedures/at2_signature.py:15-20` documents it); a targeted
  search found no other CWD-relative roots under `services/`.

**Hygiene gaps (not boot blockers; SD-3 ruling: all four IN):** no `USER`
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
  demo target. Including `alembic/` (SD-2) changes none of this: nothing in the
  default CMD's boot path reads it.

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
image uses neither: `services/` and `verticals/` are copied to `/app`, and
running uvicorn as `python -m uvicorn` puts the CWD (`/app`) at the head of
`sys.path` by documented interpreter contract. So **D1 and D2 are ELIMINATED,
not repaired**: `--no-install-project` removes the hatchling build from the
image entirely, which also preserves the dependency-layer cache (no source COPY
before `uv sync`). The SD-2-ruled migration command needs no project install
either — see the alembic design point below.

Target `Dockerfile` (the Step 2 rewrite — hygiene and alembic lines are now
integral, per the SD-2/SD-3 rulings):

```dockerfile
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.11.9 /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.12-slim AS runtime
WORKDIR /app
RUN useradd --system --no-create-home vero
COPY --from=builder /app/.venv /app/.venv
COPY services/ ./services/
COPY verticals/ ./verticals/
COPY alembic/ ./alembic/
COPY alembic.ini ./
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
USER vero
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s \
  CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"]
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
- **Alembic — one image, different commands (SD-2 ruling).** The default CMD is
  untouched (DB-less demo; nothing in its boot path reads `alembic/`).
  `docker run <image> alembic upgrade head` is the pilot/production migration
  step, and the full enabling chain is verified: the `alembic` console script
  ships with the **main** dependency (`pyproject.toml:15`, survives `--no-dev`
  even with `--no-install-project`); `alembic.ini:6` (`script_location =
  alembic`) points at the copied scripts dir; and `alembic.ini:7`
  (`prepend_sys_path = .`) puts `/app` on `sys.path` so `env.py`'s
  `services.api.config` import resolves under `WORKDIR /app`. No project
  install required — which is why E-3 below is now load-bearing.
- **`USER vero` (SD-3a).** A system user, declared after the COPYs; root-owned,
  world-readable files are fine for a read-only runtime, and port 8000 is
  unprivileged.
- **`HEALTHCHECK` (SD-3b).** Exec-form stdlib-python (slim has no curl),
  targeting `/health` — verified a pure liveness probe, no DB
  (`main.py:241-248`). O-5 cross-checks the target path against the code.
- **`uv:0.11.9` pin (SD-3d).** Refreshed from the stale `0.4`; `0.11.9` is the
  version whose `--no-install-project` support was **measured on the dev box**
  (see OQ-2). The executor may bump to a newer tag at Step 2 only with the same
  offline verification. The oracle deliberately does not assert the tag —
  freshness is not statically decidable.
- The venv relocation pattern (`COPY --from=builder /app/.venv` + same base
  image + `ENV PATH`) is unchanged from the scaffold — it was never the broken
  part.

### The compose service — a thin consumer of the image, never a second truth (SD-1 ruling)

The compose `app` service exists to prove **the same image** composes with a
real Postgres — the pilot→production path. Hierarchy is binding: the image is
the artifact; compose consumes it via `build: .` and adds **only** composition
concerns (a DB URL pointing at the `postgres` service, a host-port mapping in
the ADR-003 `${VAR:-default}` pattern, a health-gated `depends_on`). It must
**not** override `command:` — the image's CMD stays the single definition of
how the app runs. O-6 enforces exactly this shape offline.

### The oracle — derived coverage, not a text mirror

The failure mode that matters is not "someone edits the Dockerfile" — it is
"someone adds a new runtime-resolved root and the image silently stops
booting." A test that hardcodes the expected COPY list re-encodes the
Dockerfile and passes tautologically forever. So the oracle **derives** the
required set from the code and asserts the Dockerfile covers it. One new module,
`tests/docker/test_dockerfile_oracle.py` (follow the existing `tests/handoffs/`
subpackage precedent) — `ast`, `tomllib`, `configparser`, `pathlib` from the
stdlib, pytest, and `ruamel.yaml` for O-6 (already a **main** dependency,
`pyproject.toml:23` — no new dependency). No Docker SDK, no subprocess, no
daemon. All repo paths are anchored at `Path(__file__)`, never CWD.

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

   *Implementation note (reconciles the correction with AC-3):* the widened
   scan set is itself **derived**, not hardcoded — the oracle module never names
   the roots it must discover, so the AC-3 grep stays valid. **The drafter's
   catch here was correct and is kept: a literal `verticals` glob would have
   broken AC-3, so the R2 correction above could not be implemented naively.**

   *[R2 round 2, Code — the derivation RULE is corrected; the reconciliation
   stands.* The revision proposed "every top-level repo directory that is a
   Python package (`__init__.py`), excluding the test tree", asserting that set
   is "exactly the app package and the verticals package". **Measured: it is
   three, not two** — `benchmarks/`, `services/`, `tests/`, `verticals/` all
   carry `__init__.py`, so excluding the test tree still admits `benchmarks/`.
   Benign today (`benchmarks/` has zero relative `Path("…")` roots and zero
   `import_module(` calls — verified), so the claim of behavior-identity holds
   *by luck, not by construction*. The latent hazard is a **false RED**:
   `benchmarks/` is never COPY'd into the image, so a benchmark adding
   `Path("fixtures")` would demand the image ship it, blocking a PR for a
   requirement the image does not have.

   **Use instead — transitive closure from what the image actually ships:**
   seed the scan set with `services/` (the app root, always COPY'd), derive its
   roots, and scan each derived root that is itself a repo package, repeating to
   fixpoint. Code that never enters the image cannot fail inside it, so it must
   not constrain the image. This is behavior-identical today (the seed yields
   `verticals` via `discovery.py:45`'s constant, and nothing further), needs no
   test-tree carve-out, keeps M-B and M-C biting exactly as tabled — delete
   `COPY verticals/` and the root is still derived from `services/`, so the RED
   fires — and remains AC-3-clean, since the seed is the app root, not a named
   vertical.]*
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

**O-4 — migration-capability chain (new; SD-2 ruling).** Three links, each
offline-checkable: (i) `alembic.ini` is COPY'd into the runtime stage — an
**anchored presence check** (the anchor string is the minimal hardcode; the
requirement originates in the SD-2 ruling, not in code); (ii) the directory
named by the repo `alembic.ini`'s `script_location` (`alembic.ini:6`) is COPY'd
— **derived** (rename the migrations dir and the oracle follows); (iii) the
`sys.path` bridge exists — `prepend_sys_path` covers `.` (`alembic.ini:7`),
without which the in-image `alembic upgrade head` silently loses the
`services` import. Break any link and the "one image, different commands"
promise is dead code.

**O-5 — hygiene assertions (new; SD-3 ruling) — with honest derivation labels.**
- **`USER` — pure presence check, labeled as such.** Assert a `USER` directive
  exists in the runtime stage and its value is neither `root` nor `0`.
  Derivation is impossible here: no code source of truth for "run as nonroot"
  exists — the requirement is the SD-3a ruling itself. It is a genuine check
  (deleting the line fails it), not a mirror (it constrains the value's
  *meaning*, not its exact text).
- **`HEALTHCHECK` — semi-derived.** Assert presence, exec-form, and a
  stdlib-python command (first token `python`, no curl on slim); then
  **extract the URL path from the healthcheck command and assert it matches a
  GET route derived from the API entry module's own route decorators**
  (AST over `services/api/main.py`; `/health` is defined there, `:241`). The
  test hardcodes no route — repoint the healthcheck at a path the code does
  not serve and the oracle fails. One-hop honesty: routes defined in included
  routers are not derived; a liveness target should be entry-module-local.
- **`.dockerignore` — presence + content floor, labeled as such.** Assert the
  file exists and covers `.env` and `.git`. The source of truth is CLAUDE.md
  §8's secrets constraint (never ship `.env` into a build context), which is
  constitutional, not code — so this cannot be derived and is not dressed up
  as if it were.

**O-6 — compose consumes the image (new; SD-1 ruling).** Parse
`docker-compose.yml` (`ruamel.yaml`). Assert: an app service exists whose
`build` context resolves to the repo root (it builds **this** Dockerfile — not
an `image:`-only reference pinning something divergent), and that it declares
**no `command:`** (the image's CMD remains the single definition of how the app
runs). Thin by design; ADR-003 port-pattern conformance is reviewed at R2, not
oracle-encoded.

Derivation-status summary (binding labels — a presence check presented as
derived is an R2 reject):

| Oracle | Status |
|--------|--------|
| O-1 | derived (roots AND the scan set itself — the set by transitive closure from the app root, per the R2-round-2 note) |
| O-2 | derived (from `pyproject.toml`) |
| O-3 | semantic invariant, two satisfying configurations |
| O-4 | mixed: anchored presence (`alembic.ini`, `prepend_sys_path`) + derived (`script_location` dir) |
| O-5 `USER` | presence check — honestly labeled |
| O-5 `HEALTHCHECK` | semi-derived (route cross-check vs entry-module AST) |
| O-5 `.dockerignore` | presence + content floor — honestly labeled |
| O-6 | structural (compose-consumes-image shape) |

**Anti-tautology invariant (AC-3):** the oracle module must not contain the
string `verticals` anywhere — code, comments, or docstrings. Coverage of
`verticals/` must *fall out* of derivation (the derived scan set, O-1 step 2,
keeps this true even with the widened scan). This is a one-line greppable check
any reviewer can run.

### Mutation table — the RED each oracle must show (non-vacuity, pre-committed)

| ID | Mutation | Expected RED |
|----|----------|--------------|
| M-A | The unmodified Dockerfile + compose file @ `1c19654` (no mutation needed — the oracle is born failing) | O-1 (missing verticals package root); O-2 (no flag, hatchling inputs absent); O-4 (no alembic COPYs); O-5 (no USER / HEALTHCHECK / `.dockerignore`); O-6 (no app service in compose) |
| M-B | Delete the `COPY verticals/ ./verticals/` line from the fixed Dockerfile | O-1 fails naming that root |
| M-C | Add `Path("webroot")` to any scanned module (either top-level package) + create top-level `webroot/` dir; **no Dockerfile edit** | O-1 fails naming `webroot` — proves the derivation arm is live, not a frozen list |
| M-D | Strip `--no-install-project` from the `uv sync` line | O-2 fails (neither branch satisfied) |
| M-E | Revert CMD to `["uvicorn", ...]` | O-3 fails (no guaranteed import path with the project uninstalled) |
| M-F | Delete the two alembic COPY lines | O-4 fails (anchor absent + `script_location` dir uncovered) |
| M-G | Delete the `USER` line | O-5 fails (runtime is root again) |
| M-H | Delete `HEALTHCHECK`; *variant:* repoint its URL at a path the entry module does not serve | O-5 fails; the variant proves the route cross-check derives, not mirrors |
| M-I | Delete `.dockerignore`; *variant:* drop its `.env` line | O-5 fails |
| M-J | In compose, replace the app service's `build:` with a pinned `image:` reference; *variant:* add a `command:` override | O-6 fails (compose stops consuming the image / redefines the run) |

Mutation procedure (binding, per the false-PASS hazard in project memory): copy
each file-under-mutation to the session scratchpad **before** editing, observe
the RED, restore **from the scratchpad copy** — never `git checkout` (which can
wipe the edit under test and fake a PASS). Verify restoration via `git status`
clean + removal of the `webroot/` scratch dir.

## Acceptance Criteria

- [x] **AC-1 — offline oracle exists and passes.** `tests/docker/test_dockerfile_oracle.py`
  implements O-1 through O-6 and passes against the fixed Dockerfile + compose
  file. *Pass/fail read (pre-committed):* `pytest tests/docker -q` exits `0`,
  run per CLAUDE.md §8 evidence rules (streams merged `2>&1`, escaped `\$?`, no
  `head`/`tail` pipe). *No-daemon property:* the module imports stdlib + pytest
  + `ruamel.yaml` (a main dependency) only — a Grep for `subprocess|docker`
  over the module shows no tool invocation, and the CI PR run (whose workflow
  has zero Dockerfile references) executes it green.
- [x] **AC-2 — born-RED recorded.** The identical oracle, run against the
  unmodified Dockerfile + compose file (M-A), fails with **five distinct
  assertion families**: runtime-root coverage, builder-install invariant,
  migration-capability chain, hygiene (USER / HEALTHCHECK / `.dockerignore`),
  and compose-consumes-image. *Pass/fail read:* transcript in the PR body
  showing all five and a non-zero exit.
- [x] **AC-3 — anti-tautology.** The oracle module contains **zero** occurrences
  of the string `verticals`. *Pass/fail read:* Grep over the module = 0 matches.
  *Falsifying mutation:* M-C goes RED with no Dockerfile edit — the coverage set
  is derived, not enumerated. Additionally, every oracle carries its
  derivation-status label from the Design table; a presence check presented as
  derived is an R2 reject.
- [x] **AC-4 — mutations bite.** M-B through M-J (including the M-H/M-I/M-J
  variants) each produce the RED named in the mutation table. *Pass/fail read:*
  mutation transcripts in the PR body, each with non-zero exit naming the right
  oracle; working tree restored clean afterward (scratchpad-restore procedure).
- [x] **AC-5 — repo gates, full scope.** Full `ruff` clean, full
  `mypy services/` clean, **full** `pytest` green offline before push (the
  offline gate matches CI scope — never the changed subset alone). *Pass/fail
  read:* exit `0` on each, evidence rules as AC-1.
- [x] **AC-6 — no AC needs a daemon (invariant).** Every AC above is evaluable
  with Docker absent — including O-6, which parses YAML and never runs compose;
  daemon actions (image build, container run, compose up, in-container
  migration) appear only in Step 6, explicitly OPTIONAL + Cray-gated, labeled
  *evidence, not gate*. *Pass/fail read:* R2 reviewer inspection of this list +
  Steps.
- [x] **AC-7 — ruled-in extensions ship oracle-checked.** The migration chain
  (O-4), the hygiene trio (O-5), and the compose shape (O-6) each exist with
  their named mutations per the table. The uv pin refresh (SD-3d) remains
  deliberately oracle-less — "freshness" is not statically decidable; evidence
  = the diff itself + the OQ-2 measurement that selected the tag.

## Out of Scope

- ❌ **CI image build.** Not proposed. Cost if wanted later: minutes per PR +
  registry pulls + a second gate surface, against a repo whose gate is the
  offline oracle (CLAUDE.md §8). Cray can raise it as a separate decision;
  nothing here precludes it.
- ❌ **Production operations beyond "shaped to grow"** (the ruling's explicit
  boundary): TLS, reverse proxy, secrets management, orchestration,
  hosted-tenancy configuration, backup/restore.
- ❌ **A DB-full demo mode.** The default `docker run` demo stays
  synthetic/DB-less; the compose service is the pilot-path *proof* that the
  image composes with a real Postgres — not a second demo.
- ❌ **Deciding the hosting model** (our server vs customer-site) — that is
  ADR-002-successor territory, surfaced in OQ-1, not decided by any step here.
- ❌ **Dependency changes** — `alembic`/`celery`/`redis` stay in
  `pyproject.toml` `dependencies`; slimming the dep tree is a different task.
- ❌ **Runtime code changes** — the diff is `Dockerfile` + `.dockerignore` +
  `docker-compose.yml` + new tests + docs. M-C touches a scanned module only
  transiently under the scratchpad-restore procedure and is never committed.
- ❌ **Registry publish / image tagging / release flow.**

## Surfaced Decisions — ruled by Cray, session 176 (analysis preserved as the decision record)

- **SD-1 — What is the deliverable?** Options as drafted: (a) a standalone
  `docker run` artifact *[author recommended]*; (b) a compose service
  (`build:` key beside postgres/redis); (c) both. *Author's case for (a), as
  originally argued:* it matches the ADR-0032 D1 wedge — hand-someone-the-demo
  — and the DB-less demo needs neither compose neighbor; a compose service
  would be a maintained surface with **no current consumer** (compose today is
  dev-infra only). *Why Cray:* no offline oracle for a distribution-shape
  judgment; a product/positioning call.

  **Ruling: (c) BOTH — author's (a) recommendation overturned; classified
  `superseded by new info`, not `was an error`.** The (a) case was sound on the
  demo-only premise it had; the production frame killed the premise: in both
  hosting models the unit of deployment is the **same standalone image**, so
  the pilot→production path *is* the compose service's consumer. Hierarchy is
  binding: the image is the artifact and the thing the oracle guards; compose
  is the thin proof that it composes with a real Postgres — never a second,
  divergent definition of how the app runs (enforced by O-6).

- **SD-2 — `alembic/` in the image?** Options as drafted: (a) ELIMINATE — do
  not copy `alembic/` or `alembic.ini` *[author recommended]*; (b) include +
  document `docker run … alembic upgrade head`; (c) a separate migration image
  later. *Author's case for (a), as originally argued:* the demo target is
  deliberately DB-less; migrations are an operator action run from a checkout
  (`docs/runbooks/run-oct-demo.md:72,258,468`), and shipping migration
  machinery in a demo appliance widens what the artifact claims to be. *Why
  Cray:* it decides the artifact's identity — a product-surface call with no
  oracle.

  **Ruling: (b) INCLUDE + document — author's (a) recommendation overturned;
  classified `superseded by new info`.** The one good argument for (a) —
  over-promising damages demo credibility — is answered **by documentation,
  not by omission**: one image, different commands (`docker run <image>` stays
  the DB-less demo; `docker run <image> alembic upgrade head` is the
  pilot/production migration step). The separate migration image (c) is the
  *riskier* option, not the safer one — it invites version skew between the
  migration scripts and the app they migrate. Cost: two COPY lines; the
  `alembic` library is in the venv either way (`pyproject.toml:15`). The
  enabling chain is verified at `alembic.ini:6-7` (see Design).

- **SD-3 — hygiene scope.** Options as drafted: rule each IN/OUT — (3a) `USER`
  nonroot; (3b) `HEALTHCHECK` (stdlib-python exec-form against `/health`,
  `main.py:241-248`, verified DB-free); (3c) `.dockerignore` (repo has none —
  keeps `.git`/`.venv`/`.env*` out of the build context; `.env` hygiene is
  §8-adjacent); (3d) refresh the stale `uv:0.4` pin. *Author recommended all
  four.*

  **Ruling: all four IN — recommendation confirmed (`confirmed — prior
  intact`).** Oracle coverage per O-5; the pin refresh stays oracle-less by
  design (AC-7).

## Steps (cheapest + most reversible first; each with rollback)

### Step 1 — Write the oracle; watch it fail for the right reasons
Implement `tests/docker/test_dockerfile_oracle.py` (O-1 through O-6 per Design)
and run it against the **unmodified** Dockerfile + compose file.
*Pre-committed read:* non-zero exit with the five M-A assertion families, the
coverage failure naming the verticals package root **in the failure message
only** (the module source stays clean per AC-3). Capture the transcript for the
PR body (AC-2). *Rollback:* delete `tests/docker/` — new files only, nothing
else touched.

### Step 2 — Rewrite the Dockerfile + add `.dockerignore`
Apply the target Dockerfile from Design and add a minimal `.dockerignore`
(floor: `.git`, `.venv`, `__pycache__/`, `*.py[cod]`, `.env`, `.env.*`,
`!.env.example`; the executor may extend — O-5 asserts only the floor). Before
committing the pin, re-verify `--no-install-project` support for the chosen uv
tag offline (OQ-2). *Pre-committed read:* O-1 through O-5 green; O-6 still RED
(compose untouched — expected, stated here so the partial green is not
misread). *Rollback:* revert the two-file diff.

### Step 3 — Add the compose `app` service (SD-1 (c))
One-file edit to `docker-compose.yml`, in the shape O-6 enforces — sketch:

```yaml
  app:
    build: .
    container_name: vero-app
    environment:
      DATABASE_URL: postgresql+asyncpg://vero:vero@postgres:5432/vero_lite  # pragma: allowlist secret
    ports:
      - "${API_HOST_PORT:-8000}:8000"
    depends_on:
      postgres:
        condition: service_healthy
```

`build: .` (consumes this Dockerfile), **no `command:`** (the image's CMD is
the single run definition), host port in the ADR-003 `${VAR:-default}` pattern
(matches `POSTGRES_HOST_PORT`, `docker-compose.yml:10`), in-network DB URL
(container-to-container; the CLAUDE.md §6 `*_HOST_PORT`-match rule governs
host-side URLs and is unaffected). Editing the file is offline; **bringing the
stack up is a daemon action and lives only in Step 6.**

⚠️ *Execution trap, measured while committing this PLAN:* the `vero:vero`
in-network URL trips the `detect-secrets` pre-commit hook as **Basic Auth
Credentials**, so the line needs the inline `# pragma: allowlist secret` shown
above — **in the real `docker-compose.yml` at Step 3, not only in this sketch.**
It is a pattern match, not a leak: `vero:vero` is the already-tracked dev
placeholder (`docker-compose.yml:6-7`, `services/api/config.py:39`). Use the
pragma, **never `--no-verify`** (CLAUDE.md §8). *Pre-committed read:*
full `pytest tests/docker -q` exits `0` (AC-1). *Rollback:* revert the
one-file diff.

### Step 4 — Mutation probes
Run M-B through M-J (with the M-H/M-I/M-J variants) per the mutation table,
scratchpad-copy → mutate → observe RED → restore-from-copy (never
`git checkout`). *Pre-committed read:* each run exits non-zero naming the
expected oracle; `git status` clean after; `webroot/` removed. Capture
transcripts (AC-4). *Rollback:* the restore procedure is the rollback; nothing
is committed in this step.

### Step 5 — Full offline gates + PR
Full `ruff` + `mypy services/` + full `pytest` (AC-5), then branch + PR per §7
(commit body via file, PR body via `--body-file`, transcripts embedded).
*Pre-committed read:* three zero exits, CI green on the PR. *Rollback:* n/a —
branch never touches `main` directly.

### Step 6 — OPTIONAL live evidence *(host-state — Cray-gated, runs only on explicit go)*
`docker build` writes an image into the local daemon's store — **outside the
worktree** — so this entire step requires an explicit Cray go **before** any
command runs (CLAUDE.md §8), and runs **once**. It is *evidence, not a gate*:
the PLAN completes without it. Two legs, each individually gated:

- **Image leg:** `docker build -t vero-lite-demo .` →
  `docker run --rm -p 8000:8000 -e API_AUTH_ENABLED=false vero-lite-demo` →
  `curl /health` (expect `{"status":"ok",…}`) + one OCT read route returning
  demo JSON, **no Postgres running anywhere**.
- **Compose leg (the SD-1/SD-2 proof):** `docker compose up -d postgres app` →
  `docker compose run --rm app alembic upgrade head` (expect revisions applied,
  exit 0) → `curl` `/health` via `${API_HOST_PORT:-8000}`.

*Pre-committed read:* HTTP 200s + zero exits as listed. *Rollback/cleanup:*
`docker compose down` **without `-v`** (the `postgres_data` volume may hold dev
data — never destroy it as a side effect) + `docker rmi vero-lite-demo`; state
both in the evidence log. This step also settles OQ-3 empirically.

### Step 7 — Runbook section
Add "Run the demo from the image (DB-less)" to
`docs/runbooks/run-oct-demo.md`: the `docker run` line; the
`API_AUTH_ENABLED=false` / provisioned-`API_KEYS` note for the approve/execute
leg (`config.py:53-61`); the explicit statement that the default CMD's demo
never touches Postgres; **the migration command**
(`docker run --rm -e DATABASE_URL=… <image> alembic upgrade head`) documented
as the pilot/production step — this documentation IS the SD-2 ruling's answer
to the over-promise concern; and the compose path. *Pre-committed read:* every
"the image does X" line traces to an AC or to Step 6 evidence. *Rollback:*
revert the doc commit.

## Open Questions

- **OQ-1 — Is an ADR needed?** Author's read: **no, this PLAN can land as-is**
  — it repairs already-committed broken scaffold code and adds tests; it
  creates no new architectural constraint (no ADR mentions Docker — verified,
  zero matches across `docs/adr/`). The original tripwire (SD-1 = (b)/(c)
  **and** a CI image build) is **not tripped**: SD-1 = (c) is ruled, but no CI
  build is in scope. **New tripwire — the hosting question (surfaced, NOT
  drafted here):** Cray's *"customer uses our server"* model touches ADR-002's
  LAN trust model directly — `docs/adr/0002-network-topology.md:76` (*"All LLM
  traffic stays on-prem LAN; never traverses public internet"*) and `:86` (the
  LAN trust model *"assumes … no untrusted devices"* and explicitly defers its
  own re-evaluation to an unnumbered future ADR-NN). Author's judgment, stated
  plainly: **this PLAN can land with that question open** — every step is
  worktree + offline (the live evidence is optional and dev-box-LAN), and
  nothing in the image or the compose service selects *where* the image runs;
  packaging is hosting-agnostic by construction (all config via env). The
  tripwire fires when someone starts writing **deployment configuration for a
  specific hosting model** — exposing the API beyond the LAN, tenancy for
  hosted customers, TLS/authn posture, or pointing a deployed image at an
  off-LAN LLM endpoint. That is the ADR-002-successor decision and must be its
  own ADR, drafted through the governance route — not a step smuggled in here.
- **OQ-2 — uv pin / flag support — RESOLVED by the SD-3d ruling + the R2
  measurement.** The original contingency ("if `uv:0.4` lacks the flag, the
  pin refresh becomes mandatory") can no longer fire: the pin refresh is ruled
  IN unconditionally, so the 0.4 question is moot — the image no longer pins
  0.4. The measurement below is preserved because it is what **selects** the
  new pin (`0.11.9`, dev-box-verified):

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

  Residual: whether the *containerized* 0.11.9 behaves identically — folded
  into OQ-3. If the executor bumps past 0.11.9, the same offline `--help`
  verification is required for the chosen tag (Step 2).
- **OQ-3 — Residual live-behavior risk.** The offline oracle asserts the
  invariant *structure*; whether `uv sync --frozen --no-dev
  --no-install-project` behaves exactly as designed inside the builder, and
  whether the in-container `alembic upgrade head` + compose composition behave
  as documented, are ultimately empirical facts. That residue is precisely
  what the optional Step 6 evidence covers — and why Step 6 exists at all.

## Eliminations (per the dispatch's standing permission — status after rulings)

- **E-1 — STANDS (decided by this design, oracle-covered):** the local-project
  install in the builder — D1 + D2 are removed, not repaired
  (`--no-install-project`). Unaffected by the rulings.
- **E-2 — WITHDRAWN (Cray SD-2 ruling, session 176).** The draft proposed
  eliminating `alembic/` + `alembic.ini` from the image. Withdrawn because the
  production frame supersedes the premise: the over-promise concern is
  answered by documentation, not omission; "one image, different commands" is
  the production pattern; and a separate migration image is the riskier shape
  (version skew between migration scripts and the app they migrate).
- **E-3 — STANDS, and is now load-bearing:** the `vero-lite` console script
  inside the image. With alembic riding in the image, the tempting move is to
  re-add the project install "so the `vero-lite` CLI works too" — do not. The
  migration path needs **no** project install: the `alembic` executable comes
  from the venv's main dependency (`pyproject.toml:15`) and `alembic.ini:7`'s
  `prepend_sys_path = .` bridges the `services` import under `WORKDIR /app`.
  Re-adding the project install re-imports **both** builder build-input
  defects (D1: package tree; D2: readme). If an in-container CLI is ever
  wanted, that is a deliberate decision with its own oracle update — not a
  side effect.

## Verification

How do we know it worked: the oracle was **born failing** against the broken
Dockerfile and the app-service-less compose file (AC-2, five families), passes
against the fixed pair (AC-1), cannot be satisfied by text-mirroring (AC-3 +
M-C, with every assertion carrying an honest derivation label), and every
load-bearing line of the fix has a named mutation that turns the suite RED
(AC-4, M-B–M-J) — all with **no Docker daemon** anywhere in the gate path
(AC-6). The optional live evidence (Step 6) corroborates under CLAUDE.md §8; it
is never the gate. Long-term regression value: the derived oracle fails the
build the day someone adds a new runtime-resolved root under either top-level
package without teaching the image about it; the compose service cannot
silently diverge from the image (O-6); and a renamed migrations dir or a
dropped `sys.path` bridge breaks the migration-capability chain loudly (O-4)
instead of at a customer site.

---

*Authorship disclosure (ADR-012 D4.3): drafted by the in-harness `plan-drafter`
subagent from a Code-originated dispatch (session 176 era, `main`@`1c19654`);
revised by the same subagent to incorporate Cray's SD-1/SD-2/SD-3 rulings and
the production frame (relayed via Code), preserving Code's two in-file R2
corrections verbatim. Independent review = Code R2 + Cray ratification at PR
merge. Separation: INTACT — the drafter neither commits nor reviews.*
