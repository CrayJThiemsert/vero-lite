"""Offline oracle for the runtime-image contract (PLAN-0095, O-1..O-6).

The failure mode that matters is not "someone edits the ``Dockerfile``" -- it is
"someone adds a new runtime-resolved root and the image silently stops booting".
A test that hardcodes the expected ``COPY`` list re-encodes the Dockerfile and
passes tautologically forever. So this module **derives** the image's required
content set from the code and asserts the Dockerfile covers it.

Runs with **no Docker daemon**: stdlib (``ast``, ``configparser``, ``json``,
``posixpath``, ``shlex``, ``tomllib``) + pytest + ``ruamel.yaml`` (already a main
dependency, ``pyproject.toml``). No subprocess, no Docker SDK, no network.

Every repo path is anchored at ``Path(__file__)``, never CWD.

Derivation-status labels are **binding** (PLAN-0095 Design table) -- a presence
check is never dressed up as derived:

======  ==============================================================
O-1     derived (the roots AND the scan set itself, by transitive
        closure seeded from the app package -- code that never enters
        the image cannot fail inside it, so it must not constrain it)
O-2     derived from ``pyproject.toml`` (hatchling build inputs)
O-3     semantic invariant, two satisfying configurations
O-4     mixed: anchored presence (``alembic.ini``, ``prepend_sys_path``)
        + derived (the ``script_location`` directory)
O-5     ``USER``        -- presence check, honestly labeled
        ``HEALTHCHECK`` -- semi-derived (route cross-check vs the entry
                           module's own decorators)
        ``.dockerignore`` -- presence + content floor, honestly labeled
O-6     structural (compose-consumes-image shape)
======  ==============================================================

Honest limitation, stated up front: the AST scan is **one hop**. A path root
built dynamically, or a constant imported from *another* module, is not derived.
The born-RED run (PLAN-0095 AC-2) proves the one-hop scan catches the real,
current defect class.
"""

from __future__ import annotations

import ast
import configparser
import json
import posixpath
import re
import shlex
import tomllib
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

import pytest
from ruamel.yaml import YAML

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = REPO_ROOT / "Dockerfile"
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"
#: PLAN-0103 Step 4 moved this into a per-system profile directory. The path is
#: still a single literal because the O5 guard only needs ONE compose file that
#: declares a named-volume mount to be non-vacuous, and oct-energy is the system
#: that has one (the ADR-0035 D6 prompt log).
#:
#: ⚠️ If a second profile grows a named volume, add it here — the `exists()` skip
#: in the O5 loop means a wrong or missing path contributes nothing rather than
#: erroring. That is survivable only because the loop's non-vacuity assertion
#: fires when the total comes to zero: this exact rename left `expected` empty
#: and the assertion is what caught it, from `tests/docker/`, after every
#: `tests/deploy/` test had gone green.
PUBLISHED_COMPOSE = REPO_ROOT / "deploy" / "published" / "oct-energy" / "docker-compose.yml"
DOCKERIGNORE = REPO_ROOT / ".dockerignore"
ALEMBIC_INI = REPO_ROOT / "alembic.ini"
PYPROJECT = REPO_ROOT / "pyproject.toml"

# The app package is the ONE seed the oracle names: it is what the image exists
# to run, and it is unconditionally COPY'd. Everything else the image must ship
# is discovered FROM it by transitive closure -- never enumerated here.
APP_ROOT = "services"
ENTRY_MODULE = REPO_ROOT / APP_ROOT / "api" / "main.py"

# Secrets floor for the build context (source of truth = CLAUDE.md section 8,
# constitutional rather than code -- hence a content floor, not a derivation).
DOCKERIGNORE_FLOOR = (".env", ".git")

_PATH_CALLS = frozenset({"Path"})
_IMPORT_CALLS = frozenset({"import_module"})

# The probe URL sits INSIDE a python expression, so it is extracted by pattern
# rather than by tokenizing: the surrounding call syntax is not separable by
# whitespace (`urlopen('http://.../health', timeout=2)`).
_URL_PATTERN = re.compile(r"https?://[^\s'\"(),]+")


# --------------------------------------------------------------------------
# Dockerfile parsing
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Copy:
    """One ``COPY`` directive, split into sources / destination / stage flag."""

    sources: tuple[str, ...]
    dest: str
    from_stage: str | None


@dataclass
class Stage:
    """One build stage: its directives in order, plus the derived conveniences."""

    base: str
    alias: str | None
    directives: list[tuple[str, str]] = field(default_factory=list)

    @property
    def workdir(self) -> str | None:
        """The last ``WORKDIR`` declared in this stage, if any."""
        found = None
        for instruction, argument in self.directives:
            if instruction == "WORKDIR":
                found = argument.strip()
        return found

    @property
    def copies(self) -> list[Copy]:
        """Every ``COPY`` in this stage, in order."""
        return [_parse_copy(a) for i, a in self.directives if i == "COPY"]

    @property
    def context_copies(self) -> list[Copy]:
        """``COPY`` directives reading the build context (not ``--from=``)."""
        return [c for c in self.copies if c.from_stage is None]

    @property
    def runs(self) -> list[str]:
        """Every ``RUN`` argument in this stage, in order."""
        return [a for i, a in self.directives if i == "RUN"]

    def first(self, instruction: str) -> str | None:
        """The first argument for ``instruction``, or ``None`` if absent."""
        for i, a in self.directives:
            if i == instruction:
                return a
        return None


def _self_and_ancestors(path: str) -> list[str]:
    """``/var/log/vero/prompt-log`` -> that path plus each parent above ``/``.

    A ``chown -R`` on an ancestor covers the mount point, so an ancestor counts.
    """
    pure = PurePosixPath(path)
    return [str(pure), *(str(parent) for parent in pure.parents if str(parent) != "/")]


def _named_volume_mounts(compose_path: Path) -> dict[str, list[str]]:
    """Writable NAMED-volume mount points, per service that builds this image.

    Bind mounts are excluded: their ownership comes from the host, not from the
    image. Read-only mounts are excluded: the process never writes there, so a
    root-owned mount point is harmless.
    """
    yaml = YAML(typ="safe")
    document = yaml.load(compose_path.read_text(encoding="utf-8")) or {}
    services = document.get("services") or {}
    declared_volumes = set(document.get("volumes") or {})

    mounts: dict[str, list[str]] = {}
    for name, spec in services.items():
        if not isinstance(spec, dict) or spec.get("build") is None:
            continue
        destinations: list[str] = []
        for entry in spec.get("volumes") or []:
            if not isinstance(entry, str):
                continue
            parts = entry.split(":")
            if len(parts) < 2 or parts[0] not in declared_volumes:
                continue
            if len(parts) > 2 and "ro" in parts[2].split(","):
                continue
            destinations.append(parts[1])
        if destinations:
            mounts[name] = destinations
    return mounts


def _logical_lines(text: str) -> list[str]:
    """Join backslash-continued Dockerfile lines; drop blanks and comments."""
    lines: list[str] = []
    buffer = ""
    for raw in text.splitlines():
        stripped = raw.strip()
        if not buffer and (not stripped or stripped.startswith("#")):
            continue
        if stripped.endswith("\\"):
            buffer += stripped[:-1].rstrip() + " "
            continue
        buffer += stripped
        lines.append(buffer.strip())
        buffer = ""
    if buffer.strip():
        lines.append(buffer.strip())
    return lines


def _parse_copy(argument: str) -> Copy:
    """Split a ``COPY`` argument into sources, destination and ``--from=``."""
    from_stage: str | None = None
    positional: list[str] = []
    for token in shlex.split(argument):
        if token.startswith("--from="):
            from_stage = token.split("=", 1)[1]
        elif token.startswith("--"):
            continue
        else:
            positional.append(token)
    if not positional:
        return Copy((), "", from_stage)
    return Copy(tuple(positional[:-1]), positional[-1], from_stage)


def _parse_stages(text: str) -> list[Stage]:
    """Parse the Dockerfile into ordered stages, split on ``FROM``."""
    stages: list[Stage] = []
    for line in _logical_lines(text):
        parts = line.split(None, 1)
        instruction = parts[0].upper()
        argument = parts[1].strip() if len(parts) > 1 else ""
        if instruction == "FROM":
            tokens = argument.split()
            alias = None
            if len(tokens) >= 3 and tokens[-2].upper() == "AS":
                alias = tokens[-1]
            stages.append(Stage(base=tokens[0] if tokens else "", alias=alias))
            continue
        if stages:
            stages[-1].directives.append((instruction, argument))
    return stages


def _exec_form(argument: str) -> list[str] | None:
    """Return the JSON exec-form token list, or ``None`` for shell form."""
    text = argument.strip()
    if not text.startswith("["):
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
        return [str(item) for item in parsed]
    return None


def _resolve_dest(workdir: str | None, dest: str) -> str:
    """Normalize a ``COPY`` destination against the stage's ``WORKDIR``."""
    base = workdir or "/"
    joined = dest if dest.startswith("/") else posixpath.join(base, dest)
    return posixpath.normpath(joined)


def _covers_root(stage: Stage, root: str) -> bool:
    """True iff a build-context ``COPY`` lands ``root`` at ``<WORKDIR>/<root>``.

    Both halves are required: a source naming the root, and a destination that
    resolves to the root's place under the stage's ``WORKDIR``. That pairing is
    what makes the CWD-relative reads inside the image resolve.
    """
    workdir = stage.workdir
    for copy in stage.context_copies:
        sources = {s.rstrip("/") for s in copy.sources}
        if root not in sources:
            continue
        if _resolve_dest(workdir, copy.dest) == posixpath.join(workdir or "/", root):
            return True
    return False


def _copies_file(stage: Stage, filename: str) -> bool:
    """True iff a build-context ``COPY`` in this stage names ``filename``."""
    return any(filename in {s.rstrip("/") for s in copy.sources} for copy in stage.context_copies)


# --------------------------------------------------------------------------
# AST derivation -- what the image must ship
# --------------------------------------------------------------------------


def _module_constants(tree: ast.Module) -> dict[str, str]:
    """Module-level ``NAME = "literal"`` bindings, for one-hop constant resolution.

    Mandatory, not a nicety: the real boot defect this oracle exists to catch
    passes a module-level constant to ``import_module``, so a literal-only scan
    would miss the very bug that motivates the oracle.
    """
    constants: dict[str, str] = {}
    for node in tree.body:
        target: ast.expr | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
        elif isinstance(node, ast.AnnAssign):
            target = node.target
        else:
            continue
        value = node.value
        if (
            isinstance(target, ast.Name)
            and isinstance(value, ast.Constant)
            and isinstance(value.value, str)
        ):
            constants[target.id] = value.value
    return constants


def _call_name(func: ast.expr) -> str | None:
    """The bare callee name for ``f(...)`` or ``mod.f(...)``."""
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _resolve_string(node: ast.expr, constants: dict[str, str]) -> str | None:
    """Resolve a string literal, or a same-module module-level string constant."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return constants.get(node.id)
    return None


def _roots_in_module(path: Path) -> set[str]:
    """First path components of relative ``Path(...)`` roots + imported packages."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    constants = _module_constants(tree)
    roots: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        name = _call_name(node.func)
        if name is None:
            continue
        value = _resolve_string(node.args[0], constants)
        if value is None:
            continue
        if name in _PATH_CALLS:
            if value.startswith(("/", "~")):
                continue
            parts = PurePosixPath(value).parts
            if parts and parts[0] not in {".", ".."}:
                roots.add(parts[0])
        elif name in _IMPORT_CALLS:
            head = value.split(".")[0]
            if head:
                roots.add(head)
    return roots


def _required_roots() -> set[str]:
    """Top-level repo directories the runtime image must ship.

    Transitive closure seeded from the app package: derive that package's roots,
    then scan each derived root that is itself a repo package, to fixpoint. The
    scan set is therefore itself derived -- the oracle never names the roots it
    must discover. Code that never enters the image cannot fail inside it, so it
    must not constrain the image; seeding from the app root is exactly that rule.

    Names are filtered to those that exist as top-level repo directories, which
    drops installed-package imports and output-file paths with no allowlist.
    """
    required = {APP_ROOT}
    queue = [APP_ROOT]
    scanned: set[str] = set()
    while queue:
        root = queue.pop()
        if root in scanned:
            continue
        scanned.add(root)
        package = REPO_ROOT / root
        if not (package / "__init__.py").is_file():
            continue
        for module in sorted(package.rglob("*.py")):
            for name in _roots_in_module(module):
                if name in required or not (REPO_ROOT / name).is_dir():
                    continue
                required.add(name)
                queue.append(name)
    return required


def _hatchling_build_inputs() -> set[str]:
    """Build inputs hatchling reads, derived from ``pyproject.toml``."""
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    inputs = {"pyproject.toml", "uv.lock"}
    readme = data.get("project", {}).get("readme")
    if isinstance(readme, str):
        inputs.add(readme)
    wheel = (
        data.get("tool", {}).get("hatch", {}).get("build", {}).get("targets", {}).get("wheel", {})
    )
    for package in wheel.get("packages", []):
        if isinstance(package, str):
            inputs.add(package.rstrip("/"))
    return inputs


def _entry_get_routes() -> set[str]:
    """GET route paths declared by the entry module's own route decorators.

    One-hop by design: routes contributed by included routers are not derived --
    a liveness target should be entry-module-local anyway.
    """
    tree = ast.parse(ENTRY_MODULE.read_text(encoding="utf-8"))
    routes: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not decorator.args:
                continue
            if _call_name(decorator.func) != "get":
                continue
            value = _resolve_string(decorator.args[0], {})
            if value:
                routes.add(value)
    return routes


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def stages() -> list[Stage]:
    """Parsed Dockerfile stages (the last one is the runtime stage)."""
    parsed = _parse_stages(DOCKERFILE.read_text(encoding="utf-8"))
    assert parsed, f"{DOCKERFILE} declares no FROM stage"
    return parsed


@pytest.fixture(scope="module")
def runtime(stages: list[Stage]) -> Stage:
    """The final stage -- what actually ships."""
    return stages[-1]


@pytest.fixture(scope="module")
def install_stage(stages: list[Stage]) -> tuple[Stage, str]:
    """The stage (and RUN line) that installs dependencies, located by content."""
    matches = [(stage, run) for stage in stages for run in stage.runs if "uv sync" in run]
    assert len(matches) == 1, (
        "expected exactly one dependency-install RUN (`uv sync`) across all stages; "
        f"found {len(matches)}"
    )
    return matches[0]


# --------------------------------------------------------------------------
# O-1 -- runtime-root coverage (the load-bearing check; DERIVED)
# --------------------------------------------------------------------------


def test_o1_runtime_stage_ships_every_derived_root(runtime: Stage) -> None:
    """Every root the code resolves at runtime must land under the WORKDIR."""
    required = _required_roots()
    missing = sorted(root for root in required if not _covers_root(runtime, root))
    assert not missing, (
        "runtime stage does not ship these derived root(s): "
        + ", ".join(missing)
        + f" -- derived set: {sorted(required)}; "
        + f"runtime COPY sources: {[c.sources for c in runtime.context_copies]}. "
        "These roots are read at runtime (relative Path(...) or import_module) and "
        "are NOT enumerated in this module -- they are derived from the app package "
        "by transitive closure, so a new one is picked up automatically."
    )


# --------------------------------------------------------------------------
# O-2 -- builder project-install invariant (DERIVED from pyproject.toml)
# --------------------------------------------------------------------------


def test_o2_builder_install_is_either_skipped_or_fed(
    install_stage: tuple[Stage, str],
) -> None:
    """Either skip the local-project build, or COPY every input it needs first."""
    stage, run = install_stage
    if "--no-install-project" in run:
        return

    inputs = _hatchling_build_inputs()
    copied: set[str] = set()
    for instruction, argument in stage.directives:
        if instruction == "RUN" and argument == run:
            break
        if instruction != "COPY":
            continue
        copy = _parse_copy(argument)
        if copy.from_stage is None:
            copied |= {s.rstrip("/") for s in copy.sources}

    missing = sorted(inputs - copied)
    assert not missing, (
        "the dependency-install RUN builds the local project (no "
        "`--no-install-project`), but these build inputs derived from "
        f"pyproject.toml are never COPY'd before it: {missing} "
        f"(required: {sorted(inputs)}; copied before the RUN: {sorted(copied)}). "
        "Either COPY them, or drop the local-project build with "
        "`--no-install-project`."
    )


# --------------------------------------------------------------------------
# O-3 -- import strategy + WORKDIR consistency (SEMANTIC INVARIANT)
# --------------------------------------------------------------------------


def test_o3_imports_have_a_guaranteed_resolution_path(
    runtime: Stage, install_stage: tuple[Stage, str]
) -> None:
    """The app must be importable: installed in the venv, or CWD on ``sys.path``."""
    assert runtime.workdir, "the runtime stage declares no WORKDIR"

    _, run = install_stage
    project_installed = "--no-install-project" not in run

    cmd = runtime.first("CMD")
    tokens = _exec_form(cmd) if cmd is not None else None
    cwd_on_path = bool(tokens) and tokens is not None and tokens[:2] == ["python", "-m"]

    assert project_installed or cwd_on_path, (
        "no guaranteed import resolution path: the local project is NOT installed "
        "(`--no-install-project`), and the CMD is not the exec-form `python -m ...` "
        f"that puts the WORKDIR on sys.path by interpreter contract (CMD = {cmd!r}). "
        "Relying on the bare console script means relying on an implementation "
        "detail of the server's own sys.path handling."
    )


# --------------------------------------------------------------------------
# O-4 -- migration-capability chain (MIXED: anchored presence + derived)
# --------------------------------------------------------------------------


def test_o4_migration_capability_chain_is_intact(runtime: Stage) -> None:
    """One image, different commands: the migration command must actually work."""
    # (i) anchored presence -- the anchor is the minimal hardcode; the
    #     requirement originates in the PLAN-0095 SD-2 ruling, not in code.
    assert _copies_file(runtime, ALEMBIC_INI.name), (
        f"{ALEMBIC_INI.name} is never COPY'd into the runtime stage, so the "
        "documented in-image migration command cannot find its configuration."
    )

    parser = configparser.ConfigParser()
    parser.read_string(ALEMBIC_INI.read_text(encoding="utf-8"))

    # (ii) DERIVED -- rename the migrations directory and this follows.
    script_location = parser.get("alembic", "script_location", fallback="").strip()
    assert script_location, f"{ALEMBIC_INI.name} declares no script_location"
    assert _covers_root(runtime, script_location.rstrip("/")), (
        f"the migrations directory named by {ALEMBIC_INI.name} "
        f"(script_location = {script_location!r}) is never COPY'd into the runtime "
        "stage; the in-image migration command would find no revisions."
    )

    # (iii) anchored presence -- without this bridge the in-image migration
    #       silently loses the app import under the WORKDIR.
    prepend = parser.get("alembic", "prepend_sys_path", fallback="")
    entries = {part.strip() for part in prepend.replace(":", ",").split(",")}
    assert "." in entries, (
        f"{ALEMBIC_INI.name} does not prepend '.' to sys.path "
        f"(prepend_sys_path = {prepend!r}), so the migration environment cannot "
        "import the app package under the image's WORKDIR."
    )


# --------------------------------------------------------------------------
# O-5 -- hygiene, with honest derivation labels
# --------------------------------------------------------------------------


def test_o5_runtime_does_not_run_as_root(runtime: Stage) -> None:
    """PRESENCE CHECK, honestly labeled -- no code source of truth exists.

    The requirement originates in the PLAN-0095 SD-3a ruling. It is still a
    genuine check (deleting the directive fails it) and it constrains the
    value's *meaning* rather than its exact text.
    """
    user = runtime.first("USER")
    assert user is not None, "the runtime stage declares no USER -- it would run as root"
    assert user.strip().split(":")[0] not in {
        "root",
        "0",
    }, f"the runtime stage runs as root (USER {user!r})"


def test_o5_named_volume_mount_points_are_writable_by_the_runtime_user(
    runtime: Stage,
) -> None:
    """DERIVED -- the mount points come from the compose files, never from a constant.

    Docker creates a named volume's mount point as ``root:root`` when the image
    does not already contain that path; only a path present in the image passes
    its ownership to the volume. Since the runtime stage drops to a non-root
    USER, any writable named-volume mount point absent from the image is
    unwritable at runtime.

    That failure is SILENT for the prompt log -- ``prompt_log.record`` swallows
    OSError by design -- so it survived every offline test and was only found by
    PLAN-0100 Step 11's live run, after 90+ published POST /query requests had
    written nothing. This guard reads the real compose files and the real
    Dockerfile so a NEW named volume inherits the check automatically.
    """
    runtime_user = (runtime.first("USER") or "").strip().split(":")[0]
    assert runtime_user, "the runtime stage declares no USER"

    # Everything the runtime stage does BEFORE dropping privileges. A chown after
    # the USER switch cannot work -- the user it would need to run as is gone.
    before_user: list[str] = []
    for instruction, argument in runtime.directives:
        if instruction == "USER":
            break
        if instruction == "RUN":
            before_user.append(argument)
    expected: list[tuple[str, str, str]] = []
    for compose_path in (COMPOSE_FILE, PUBLISHED_COMPOSE):
        if not compose_path.exists():
            continue
        label = compose_path.relative_to(REPO_ROOT).as_posix()
        for service, dests in _named_volume_mounts(compose_path).items():
            for dest in dests:
                expected.append((label, service, dest))

    assert expected, (
        "no writable named-volume mount point was derived from any compose file -- "
        "the guard would pass vacuously. Check _named_volume_mounts against the "
        f"compose files ({COMPOSE_FILE.name}, {PUBLISHED_COMPOSE.name})."
    )

    unprepared = []
    for compose_name, service, dest in expected:
        candidates = _self_and_ancestors(dest)
        # Checked per RUN directive, not against the concatenation: `mkdir` in one
        # command and the path in an unrelated one must not read as coverage.
        made = any("mkdir" in run and any(c in run for c in candidates) for run in before_user)
        owned = any(
            "chown" in run and runtime_user in run and any(c in run for c in candidates)
            for run in before_user
        )
        if not (made and owned):
            unprepared.append(f"{compose_name}:{service} -> {dest} (mkdir={made} chown={owned})")

    assert not unprepared, (
        "named-volume mount point(s) the image never creates and chowns to "
        f"{runtime_user!r} before `USER {runtime_user}`: {unprepared}. Docker will "
        "create each as root:root, and the non-root runtime cannot write there. "
        f"RUN directives seen before the USER switch: {before_user!r}"
    )


def test_o5_healthcheck_targets_a_route_the_entry_module_serves(runtime: Stage) -> None:
    """SEMI-DERIVED -- presence and shape asserted, target cross-checked vs the code."""
    healthcheck = runtime.first("HEALTHCHECK")
    assert healthcheck is not None, "the runtime stage declares no HEALTHCHECK"

    marker = healthcheck.upper().find("CMD")
    assert marker != -1, f"HEALTHCHECK declares no CMD: {healthcheck!r}"
    tokens = _exec_form(healthcheck[marker + 3 :])
    assert tokens, (
        f"HEALTHCHECK is not in exec form: {healthcheck!r} -- shell form depends on a "
        "shell being present and on shell quoting"
    )
    assert tokens[0].startswith("python"), (
        f"HEALTHCHECK does not probe with stdlib python (first token {tokens[0]!r}); "
        "the slim base image ships no curl"
    )

    probed = {urlsplit(match).path for token in tokens for match in _URL_PATTERN.findall(token)}
    assert probed, f"no probe URL found in the HEALTHCHECK command: {tokens!r}"

    served = _entry_get_routes()
    unserved = sorted(probed - served)
    assert not unserved, (
        f"HEALTHCHECK probes {unserved}, which the entry module does not serve as a "
        f"GET route (derived from its own decorators: {sorted(served)})"
    )


def test_o5_dockerignore_covers_the_secrets_floor() -> None:
    """PRESENCE + CONTENT FLOOR, honestly labeled.

    The source of truth is CLAUDE.md section 8's secrets constraint -- never ship
    a secrets file into a build context -- which is constitutional, not code, so
    this cannot be derived and is not dressed up as if it were.
    """
    assert DOCKERIGNORE.is_file(), (
        f"{DOCKERIGNORE.name} is absent -- the whole repo, including any local "
        "secrets file and the git history, enters the build context"
    )
    entries = {
        line.strip().lstrip("/")
        for line in DOCKERIGNORE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    missing = sorted(item for item in DOCKERIGNORE_FLOOR if item not in entries)
    assert not missing, f"{DOCKERIGNORE.name} does not exclude {missing} from the build context"


# --------------------------------------------------------------------------
# O-6 -- compose consumes the image (STRUCTURAL)
# --------------------------------------------------------------------------


def test_o6_compose_consumes_this_image_and_does_not_redefine_the_run() -> None:
    """Compose must build THIS Dockerfile and leave the run definition to it."""
    yaml = YAML(typ="safe")
    document = yaml.load(COMPOSE_FILE.read_text(encoding="utf-8"))
    services = (document or {}).get("services") or {}

    consumers: list[str] = []
    for name, spec in services.items():
        if not isinstance(spec, dict):
            continue
        build = spec.get("build")
        if build is None:
            continue
        context = build if isinstance(build, str) else str(build.get("context", "."))
        if posixpath.normpath(context) == ".":
            consumers.append(name)

    assert consumers, (
        "no compose service builds this repository's image (no service with a build "
        f"context resolving to the repo root); services present: {sorted(services)}. "
        "An `image:`-only reference would pin something that can silently diverge "
        "from this Dockerfile."
    )

    redefining = sorted(name for name in consumers if "command" in services[name])
    assert not redefining, (
        f"compose service(s) {redefining} override `command:`, so the image's CMD is "
        "no longer the single definition of how the app runs"
    )
