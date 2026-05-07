# Code Style

> Style rules enforced by tooling. Violations block commits via pre-commit.

---

## Python

### Formatting

- **Line length:** 100
- **Formatter:** `ruff format` (Black-compatible)
- **Imports:** Sorted via ruff (isort-compatible)

### Type Hints

- **Mandatory** on all functions, methods, class attributes
- Use `from __future__ import annotations` for forward references when needed
- Prefer `list[X]` / `dict[K, V]` over `List[X]` / `Dict[K, V]` (Python 3.12+)

### Docstrings

- **Required** on public modules, classes, and functions
- Style: Google-style (compatible with `mkdocstrings` if/when docs site is added)

### Async

- **Default** for I/O-bound code (DB, HTTP, LLM calls)
- Sync code only for CPU-bound work or simple utility scripts

### Pydantic Models

- All API request/response models extend `BaseModel`
- Use `Field(...)` with `description` for all fields:
  ```python
  class PatientCreate(BaseModel):
      name: str = Field(..., description="Patient legal name")
      species: Literal["dog", "cat", "other"] = Field(..., description="Patient species")
  ```
- Use `model_config = ConfigDict(...)` for v2 settings (not class `Config`)
- Prefer `Annotated[T, Field(...)]` over default-value Field for type clarity

## Tooling

All must pass before push:

```bash
ruff check .          # Lint
ruff format .         # Format
mypy services/        # Type check (strict mode in pyproject.toml)
pytest                # Tests; coverage threshold 70%
pre-commit run --all-files
```

## File Organization

- `services/<domain>/` — One package per bounded context (api, ontology, etc.)
- `services/<domain>/main.py` — Entry point if standalone service
- `services/<domain>/models/` — Pydantic + SQLAlchemy models
- `services/<domain>/routers/` — FastAPI routers
- `tests/` — Mirror `services/` structure: `tests/<domain>/test_<module>.py`

## Naming

- **Modules:** `snake_case` (lowercase with underscores)
- **Classes:** `PascalCase`
- **Functions/variables:** `snake_case`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private:** Leading underscore `_helper_func`

## Comments

- Prefer self-documenting code via good naming + type hints
- Comments explain **why**, not **what**
- TODO comments include owner and ADR/issue reference:
  ```python
  # TODO(jirachai): replace with pgvector lookup once ADR-005 lands
  ```

## Anti-Patterns

❌ **Don't:** Mix sync and async carelessly (e.g., `requests` in async handler)
✅ **Do:** Use `httpx.AsyncClient` for HTTP in async paths

❌ **Don't:** Catch broad `Exception` without re-raising or logging
✅ **Do:** Catch specific exceptions; let unexpected errors propagate

❌ **Don't:** Silent type-ignore (`# type: ignore` without explanation)
✅ **Do:** `# type: ignore[error-code]  # reason: ...`

## References

- `pyproject.toml` — Tool configurations (ruff, mypy, pytest)
- `.pre-commit-config.yaml` — Enforced hooks
- `CLAUDE.md` §8 — Code quality constraints
