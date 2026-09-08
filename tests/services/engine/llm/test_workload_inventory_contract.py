"""Every ``.chat(`` call site under ``services/`` is declared in the workload taxonomy.

PLAN-0119 AC-1. The motivating gap: before this module there was **no inventory at all**
of which LLM call site asks for which kind of work, so every question about budgets,
truncation, or residency had to be re-derived by grepping. PLAN-0119 §3 built the
inventory by hand; this guard is what stops it rotting the day someone adds a call site.

Why it enumerates from the TREE and not from a constant: a committed-file guard that
compares a list to itself agrees with itself by construction. It would redden on an edit
to the inventory and stay green forever on a new file — which is precisely the direction
the rot actually runs. So the tree is the subject and
``docs/conventions/llm-workload-taxonomy.md`` is the claim being checked.

Scope + limits, stated honestly:

* This is a **declaration-existence** guard, not a correctness one. It proves every site
  is classified; it cannot prove the class is the RIGHT one. That judgment is the
  checklist's (§3 of the artifact) and a reviewer's.
* It sees only ``services/``. The **G Gate** workload lives in
  ``.claude/hooks/_sonnet_classifier.py`` — outside this scope by construction, listed in
  the inventory as ``services_scope: no``, and therefore **unguarded**. A real hole, named
  rather than hidden.
* It matches on the AST, not on text, so a ``.chat(`` inside a comment or a docstring is
  invisible to it and a multi-line call is found at its opening line. It matches **any**
  attribute call named ``chat`` — a non-Ollama ``.chat(`` would be reported as an
  undeclared site, which is the safe direction to be wrong in.
"""

from __future__ import annotations

import ast
import re
from functools import lru_cache
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_SERVICES = _REPO_ROOT / "services"
_ARTIFACT = _REPO_ROOT / "docs" / "conventions" / "llm-workload-taxonomy.md"

#: The five classes the artifact is allowed to assign. A sixth would mean the taxonomy
#: changed, which is a PLAN-level event, not an implementer's choice.
_CLASSES = frozenset({"G", "S", "J", "N", "A"})


class CallSite:
    """One ``.chat(`` call found in the tree.

    ``shape`` is what the client's chokepoint can already tell apart without any new
    argument (PLAN-0119 Step 3): a ``response_format`` present means the constrained
    STRUCTURING pass, a ``think`` with no ``response_format`` means the free-form
    REASONING pass. It is ``None`` for a bare call that passes neither.
    """

    __slots__ = ("path", "line", "function", "shape")

    def __init__(self, path: str, line: int, function: str | None, shape: str | None) -> None:
        self.path = path
        self.line = line
        self.function = function
        self.shape = shape

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return f"{self.path}:{self.line} (fn={self.function}, shape={self.shape})"


def _repo_relative(path: Path) -> str:
    """Repo-relative POSIX path, or the bare name for a module outside the repo.

    The fallback is not cosmetic: the positive control below parses a synthetic module
    under ``tmp_path``, and ``Path.relative_to`` RAISES rather than returning ``None`` for
    a path outside the root. Without this the control could not run — and a control that
    cannot run is exactly the vacuous green this module exists to prevent.
    """
    if path.is_relative_to(_REPO_ROOT):
        return path.relative_to(_REPO_ROOT).as_posix()
    return path.name


def _shape_of(call: ast.Call) -> str | None:
    """Which of the two Pattern B passes this call is, read off its keywords."""
    keywords = {kw.arg for kw in call.keywords}
    if "response_format" in keywords:
        return "structuring"
    if "think" in keywords:
        return "reasoning"
    return None


def _sites_in(source: str, path: Path) -> list[CallSite]:
    """Every ``.chat(`` call in one module, with its enclosing function."""
    found: list[CallSite] = []
    stack: list[tuple[ast.AST, str | None]] = [(ast.parse(source, filename=str(path)), None)]
    while stack:
        node, enclosing = stack.pop()
        for child in ast.iter_child_nodes(node):
            function = enclosing
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                function = child.name
            if (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and child.func.attr == "chat"
            ):
                found.append(
                    CallSite(
                        path=_repo_relative(path),
                        line=child.lineno,
                        function=function,
                        shape=_shape_of(child),
                    )
                )
            stack.append((child, function))
    return found


@lru_cache(maxsize=1)
def _tree_sites() -> tuple[CallSite, ...]:
    """Every ``.chat(`` call site under ``services/``, discovered by walking the tree."""
    found: list[CallSite] = []
    for path in sorted(_SERVICES.rglob("*.py")):
        found.extend(_sites_in(path.read_text(encoding="utf-8"), path))
    return tuple(sorted(found, key=lambda s: (s.path, s.line)))


# --------------------------------------------------------------------------- #
# The site key — PLAN-0119 Step 1's one design choice, ruled at s286.
# --------------------------------------------------------------------------- #
def _site_key(site: CallSite) -> str:
    """Reduce a call site to the string the inventory table addresses it by.

    This is the guard's whole maintenance profile in one function, and the three
    candidates trade off differently:

    (a) ``f"{site.path}:{site.line}"`` — matches PLAN-0119 §3's table verbatim and is
        maximally precise. Cost: it reddens on ANY edit that shifts a line in one of the
        eight inventory files. Measured over the last 200 commits on ``main``, 45 of them
        (~22%) touched at least one of those files; ``nl_query.py`` alone, which holds
        three sites, was touched 15 times.

    (b) ``site.path`` with a per-file COUNT — immune to line drift; reddens when a call is
        added to or removed from a listed file, and when a call appears in an unlisted
        file. Cost: it cannot address an individual site, so the table cannot carry a
        per-site class where one file holds two classes — and three files do
        (``pipeline.py`` J+S, ``nl_query.py`` J+S+N, ``run_query.py`` S+N).

    (c) ``f"{site.path}::{site.function}::{site.shape}"`` — immune to line drift AND able
        to address each site individually. Verified at authoring time: this key is unique
        across all 14 current sites, including both Pattern B pairs, which differ by shape.
        Cost: a second call of the SAME shape added to the same function would collide, so
        the enumerator must fail loudly on a duplicate key rather than silently merge two
        sites.

    RULED (Cray, typed, session 286): **(c)**. The collision cost is mitigated exactly as
    the ruling named — by :func:`test_the_site_key_addresses_each_call_site_uniquely`, which
    fails rather than letting one row quietly cover two sites. That check is a test assert
    and not a ``raise`` inside :func:`_tree_sites` on purpose: only an assertion has a
    ``stable_key`` the probe battery can address, and an unwitnessable guard is not evidence
    (battery probe ``1b``).
    """
    return f"{site.path}::{site.function}::{site.shape or 'bare'}"


@lru_cache(maxsize=1)
def _inventory() -> dict[str, str]:
    """The inventory table as ``{site key: class}``, parsed from the canonical artifact."""
    text = _ARTIFACT.read_text(encoding="utf-8")
    body = text.split("<!-- INVENTORY-TABLE-START -->")[1].split("<!-- INVENTORY-TABLE-END -->")[0]
    rows: dict[str, str] = {}
    for line in body.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0] in {"", "Site"} or set(cells[0]) <= {"-", ":"}:
            continue
        key = cells[0].strip("`")
        klass = cells[1].strip().strip("*").split()[0] if cells[1].strip() else ""
        rows[key] = klass
    return rows


def test_the_enumerator_is_not_returning_an_empty_tree() -> None:
    """The anti-vacuity control: every guard below passes trivially on an empty enumeration.

    Deliberately NOT an equality against a pinned count. A pinned number would have to be
    written from the same walk it is checking, so it would agree with itself by
    construction and could only ever redden on a legitimate new call site — the one event
    the real guard already reports, and reports better.

    Printing the count is what makes a surprise one step to diagnose: PLAN-0119 §3 says 14,
    this walk says 14, and the two are NOT the same 14 (§2's `was an error` note).
    """
    sites = _tree_sites()
    assert len(sites) >= 1, "the enumerator found NOTHING — it is broken, not the tree"
    print(f"enumerated={len(sites)} declared={len(_inventory())}")


def test_the_site_key_addresses_each_call_site_uniquely() -> None:
    """The (path, function, shape) key ruled at s286 must stay one-to-one.

    A second call of the SAME shape in the SAME function collides, and a collision does not
    announce itself: the inventory is a dict, so the two sites would quietly share one row
    and that row would vouch for a site nobody classified. The fix is to widen the key —
    a PLAN-0119 decision, not an implementer's — so this fails rather than degrading.
    """
    keys = [_site_key(site) for site in _tree_sites()]
    duplicates = {key for key in keys if keys.count(key) > 1}
    assert not duplicates, (
        f"keys={len(keys)} unique={len(set(keys))} — the s286 key no longer addresses "
        f"each site uniquely: {sorted(duplicates)}"
    )


def test_every_call_site_is_declared_in_the_taxonomy() -> None:
    """AC-1: no ``.chat(`` site under ``services/`` is missing a class."""
    inventory = _inventory()
    undeclared = [site for site in _tree_sites() if _site_key(site) not in inventory]
    assert not undeclared, (
        f"undeclared={len(undeclared)} declared={len(inventory)} — "
        f"add these to docs/conventions/llm-workload-taxonomy.md §2 and answer the §3 "
        f"checklist in the same PR: {[repr(s) for s in undeclared]}"
    )


def test_every_declared_class_is_one_of_the_five() -> None:
    """A typo'd class is a silent hole — it declares a site without classifying it."""
    bad = {key: klass for key, klass in _inventory().items() if klass not in _CLASSES}
    assert not bad, f"unknown classes (allowed {sorted(_CLASSES)}): {bad}"


def test_the_inventory_does_not_list_sites_that_no_longer_exist() -> None:
    """The other rot direction: a removed call site leaves a stale row behind."""
    keys = {_site_key(site) for site in _tree_sites()}
    stale = [key for key in _inventory() if key not in keys and not key.startswith(".claude/")]
    assert not stale, f"stale={len(stale)} live={len(keys)} — rows for removed sites: {stale}"


def test_the_enumerator_actually_sees_a_new_call_site(tmp_path: Path) -> None:
    """The positive control AC-1 demands: a newly added site MUST be visible.

    Without this, a broken enumerator returning ``[]`` would make every guard above pass
    vacuously — an empty ``undeclared`` list satisfies "nothing is undeclared".

    Both Pattern B shapes are checked in ONE assertion on purpose. Two asserts would be two
    claims, and a probe run stops at the first failure — so the second could never be
    witnessed without a second probe that adds nothing.
    """
    snippets = {
        "structuring": "async def f(client):\n    return await client.chat(m, response_format=s)\n",
        "reasoning": "async def f(client):\n    return await client.chat(m, think=True)\n",
    }
    seen = {}
    for shape, snippet in snippets.items():
        module = tmp_path / f"new_site_{shape}.py"
        module.write_text(snippet, encoding="utf-8")
        found = _sites_in(snippet, module)
        seen[shape] = [(len(found), found[0].shape if found else None)]
    assert seen == {
        "structuring": [(1, "structuring")],
        "reasoning": [(1, "reasoning")],
    }, f"the enumerator did not see a freshly added call site: measured {seen}"


def test_the_artifact_still_has_the_markers_the_parser_reads() -> None:
    """If the table markers are renamed, ``_inventory`` would raise, not silently empty."""
    text = _ARTIFACT.read_text(encoding="utf-8")
    for marker in ("<!-- INVENTORY-TABLE-START -->", "<!-- INVENTORY-TABLE-END -->"):
        assert text.count(marker) == 1, f"marker {marker!r} appears {text.count(marker)} times"
    assert re.search(r"^## 2\. Call-site inventory", text, re.M), "§2 heading moved"
