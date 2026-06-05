"""Live co-creation intake-face routes (PLAN-0017).

``POST /intake/extract``  — MS-S1-**local** free-text -> draft ``IntakePackage``
                            (AC-4: local only, never the hosted API; degrades to
                            a clear non-silent state on failure).
``GET  /intake/defaults`` — the prebaked source-tagged starter packages (AC-4
                            fallback when MS-S1 is cold/unreachable).
``POST /intake/generate`` — the gate's **confirmed** package -> assemble the OCT
                            ontology YAML -> ``vero-lite new-vertical`` (the
                            PLAN-0016 engine, unchanged — AC-5).

**AC-2 (the human gate is real).** ``/intake/generate`` is the ONLY route to the
engine, and it refuses any package that is not explicitly ``confirmed`` — there
is no server path from ``/intake/extract`` to generation that bypasses the gate
(``extract`` and ``generate`` are separate; ``generate`` never calls ``extract``).
The confirmed package in the request body is what drives generation, so an edit
made in the gate is provably reflected in the generated artifacts.

**AC-4 / CLAUDE.md §8.** Extraction runs on the MS-S1 local model only; if the
backend is not local, or MS-S1 is unreachable / low-quality, the response is a
non-silent ``degraded`` state and the operator falls back to a prebaked default
or manual entry — a silently-wrong ontology is never pushed on.

**Host-state note.** ``/intake/generate`` WRITES to the working tree (the
ontology YAML + the scaffold) and code-mods ``services/api/main.py`` — that is the
PLAN-0016 engine's contract; the live vertical-#4 boot is a deliberate operator
action (the demo box), driven from this route.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.api.config import settings
from services.api.intake_defaults import load_default_packages
from services.engine import ontology_validator, scaffold
from services.engine.intake_assembler import IntakePackage, PackageSource, assemble_yaml
from services.engine.llm.client import OllamaClient, OllamaError
from services.engine.llm.intake import IntakeExtractionError, extract_package

logger = logging.getLogger(__name__)

router = APIRouter(tags=["intake"])


def _chat_client() -> OllamaClient:
    """Build the MS-S1 local Ollama client for extraction (monkeypatched in tests).

    Raises ``RuntimeError`` when the backend is not local — extraction NEVER uses
    the hosted API (CLAUDE.md §8 / AC-4). Mirrors ``scaffold._build_chat_client``.
    """
    if settings.llm_backend != "local":
        raise RuntimeError(f"llm_backend={settings.llm_backend!r} is not 'local'")
    return OllamaClient(
        base_url=settings.ollama_host,
        model=settings.recommender_model,
        timeout=settings.llm_request_timeout_s,
    )


def _repo_root() -> Path:
    """The repo root the generate path writes the ontology + scaffold into
    (monkeypatched to a temp dir in tests)."""
    return Path.cwd()


def _recommend_config(package: IntakePackage) -> scaffold.RecommendConfig:
    """Map the confirmed package's metric/recovery onto the engine's config."""
    return scaffold.RecommendConfig(
        threshold=package.metric.threshold,
        direction=package.metric.direction,
        label=package.metric.label,
        unit=package.metric.unit,
        recovery_value=package.recovery_value,
        recovery_description=package.recovery_description,
        problem=package.problem,
        decision=package.decision,
    )


# --------------------------------------------------------------------------- #
# Request / response models (AC-6: Pydantic with Field(description=...))
# --------------------------------------------------------------------------- #


class ExtractRequest(BaseModel):
    description: str = Field(min_length=1, description="operator's free-text domain description")
    namespace_hint: str | None = Field(
        default=None, description="optional namespace slug to prefer for the vertical"
    )


class ExtractResponse(BaseModel):
    state: Literal["ok", "degraded"] = Field(
        description="ok = draft package; degraded = MS-S1 unavailable (use a default/manual entry)"
    )
    package: IntakePackage | None = Field(
        default=None, description="the draft partner-input package (null when degraded)"
    )
    source: PackageSource | None = Field(
        default=None, description="provenance of the package when ok (ms_s1_live)"
    )
    confidence: float | None = Field(
        default=None, description="coarse extraction confidence when ok (advisory)"
    )
    attempts: int | None = Field(default=None, description="constrained-decode attempts consumed")
    model: str | None = Field(default=None, description="the MS-S1 model used when ok")
    detail: str | None = Field(default=None, description="why extraction degraded (null when ok)")


class DefaultsResponse(BaseModel):
    defaults: list[IntakePackage] = Field(
        description="prebaked source-tagged starter packages (the AC-4 fallback)"
    )


class GenerateRequest(BaseModel):
    package: IntakePackage = Field(
        description="the human-reviewed, confirmed partner-input package"
    )
    confirmed: bool = Field(
        description="explicit human confirmation — generation REFUSES unless true (AC-2 no-bypass)"
    )
    force: bool = Field(
        default=False, description="overwrite existing scaffold files (clobber-guard override)"
    )


class GenerateResponse(BaseModel):
    namespace: str = Field(description="the generated vertical's namespace")
    asset_type: str = Field(description="the detected Asset-role object type")
    site_type: str = Field(description="the detected Site-role object type")
    direction: str = Field(description="the breach direction baked into the env block")
    ontology_path: str = Field(description="repo-relative path of the authored ontology YAML")
    env_block: str = Field(description="the OCT_* env block to boot the vertical")
    written: list[str] = Field(description="repo-relative scaffold files written")
    generated: list[str] = Field(description="generated codegen artifacts (name: path)")
    registered: bool = Field(description="whether the vertical was registered in main.py")
    next_steps: str = Field(description="operator-facing run checklist")


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #


@router.post("/intake/extract", response_model=ExtractResponse)
async def intake_extract(req: ExtractRequest) -> ExtractResponse:
    """Extract a draft package from the operator's free text via MS-S1 (local).

    On any failure (backend not local, MS-S1 unreachable/errored, or extraction
    unparseable after the retry budget) returns ``state='degraded'`` with a
    diagnostic ``detail`` — never silently a bad package (AC-4).
    """
    try:
        client = _chat_client()
    except RuntimeError as exc:
        return ExtractResponse(state="degraded", detail=f"MS-S1 local backend unavailable: {exc}")

    try:
        result = await extract_package(
            client,
            req.description,
            namespace_hint=req.namespace_hint,
            retry_budget=settings.llm_retry_budget,
        )
    except OllamaError as exc:
        return ExtractResponse(state="degraded", detail=f"MS-S1 unreachable or errored: {exc}")
    except IntakeExtractionError as exc:
        return ExtractResponse(state="degraded", detail=f"extraction failed: {exc}")

    pkg = result.package
    return ExtractResponse(
        state="ok",
        package=pkg,
        source=pkg.source,
        confidence=pkg.confidence,
        attempts=result.attempts,
        model=result.model,
    )


@router.get("/intake/defaults", response_model=DefaultsResponse)
async def intake_defaults() -> DefaultsResponse:
    """Return the prebaked starter packages (the AC-4 cold-MS-S1 fallback)."""
    return DefaultsResponse(defaults=load_default_packages())


@router.post("/intake/generate", response_model=GenerateResponse)
async def intake_generate(req: GenerateRequest) -> GenerateResponse:
    """Assemble + invoke the engine for a CONFIRMED package (the human gate).

    AC-2: refuses an unconfirmed package (no bypass). AC-5: invokes
    ``scaffold.scaffold_vertical`` unchanged and surfaces the refuse-to-clobber
    guard as a 409 rather than overwriting by default.
    """
    if not req.confirmed:
        raise HTTPException(
            status_code=422,
            detail="generation requires explicit human confirmation (confirmed=true)",
        )

    package = req.package
    root = _repo_root()
    ns = package.namespace
    yaml_path = root / "verticals" / ns / "ontology" / f"{ns}_v0.yaml"
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    yaml_path.write_text(assemble_yaml(package), encoding="utf-8")

    # Pre-validate (defensive — the assembler guarantees validity by construction,
    # but a schema error must surface here, never mid-generation in the live moment).
    findings = ontology_validator.validate_file(yaml_path)
    if findings:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "the assembled ontology failed validation",
                "findings": [f.render() for f in findings],
            },
        )

    try:
        result = scaffold.scaffold_vertical(
            ns, _recommend_config(package), repo_root=root, force=req.force
        )
    except scaffold.ScaffoldError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "error": str(exc),
                "namespace": ns,
                "hint": "pick a new namespace or set force=true to overwrite",
            },
        ) from exc

    return GenerateResponse(
        namespace=ns,
        asset_type=result.roles.asset_type,
        site_type=result.roles.site_type,
        direction=package.metric.direction,
        ontology_path=str(yaml_path.relative_to(root)),
        env_block=result.env_block,
        written=[str(p.relative_to(root)) for p in result.written],
        generated=[f"{name}: {p.relative_to(root)}" for name, p in result.generated.items()],
        registered=result.registered,
        next_steps=(
            f"Boot vertical #4 with OCT_VERTICAL={ns} (a second uvicorn on a separate port "
            "keeps #3 showable side-by-side); the env block above carries the recommender policy."
        ),
    )
