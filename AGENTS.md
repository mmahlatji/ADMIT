# AGENTS.md

## Core Principles

- Understand the existing codebase before changing it.
- Make the smallest reasonable change that completely solves the problem.
- Prefer simple, readable, maintainable solutions.
- Follow existing architecture, conventions, and patterns unless there is a
  concrete reason not to.
- Don't introduce abstractions, dependencies, or architectural changes without a
  demonstrated need.
- Don't modify unrelated code, and don't rewrite working code merely because you
  would implement it differently.

## Requirements & Assumptions

- Treat the user's explicit requirements as the primary source of truth.
- Before implementing, inspect the relevant code, config, tests, and usage
  patterns; don't assume behavior the codebase can determine.
- If a requirement is genuinely ambiguous and interpretations would materially
  change the implementation, ask for clarification. Otherwise choose the
  reasonable low-risk interpretation and state the assumption.
- Never invent requirements, APIs, files, config, test results, or external
  behavior.

## Implementation

- Write idiomatic code for the language and framework in use.
- Prefer explicit, readable code over clever or compressed code.
- Use the type system; avoid `Any`, unchecked casts, and type-system escapes
  unless justified.
- Reuse existing utilities and abstractions when they already solve the problem;
  don't create an abstraction solely to remove a small amount of duplication.
- Keep functions, classes, and modules focused on clear responsibilities.
- Preserve existing behaviour unless changing it is part of the task.
- Handle reasonable edge cases at system boundaries.
- Don't prematurely optimize; when performance matters, identify the bottleneck
  before optimizing.

## Documentation

- Update relevant docs when public behaviour, APIs, config, setup, or workflows
  change; don't add docs that merely restate obvious code.
- Comments explain why something exists, not what it does; update comments when
  their explanation becomes incorrect.

## Transparency

- Never claim to have performed an action you did not (run a command, inspect a
  file, run tests, verify behaviour, consult docs, reproduce a bug).
- Distinguish: Observed (from code/tool output/tests/evidence), Inferred (derived
  from observations), Unknown (cannot currently be established).
- Resolve Unknown information that materially affects implementation by asking
  the user.

## Completion

Before declaring a task complete:

- Confirm the implementation matches the requirements.
- Review all modified files for unintended changes.
- Run relevant tests, linters, formatters, and type checkers where available.
- Remove temporary debugging code; verify no unnecessary deps/config changes.
- Report what changed, why, what was verified, and what remains unknown.

## Decision Rule

Order: Inspect -> Understand -> Identify missing info -> Ask if necessary ->
Implement -> Verify -> Report.

- If the implementation depends on information you don't have, ask instead of
  guessing.
- If the task is unambiguous and the codebase has the needed info, proceed
  without unnecessary questions.
- The agent is an implementation assistant, not a requirements author: never
  silently invent requirements or make consequential decisions on the user's
  behalf.

Backend (`backend/`) — FastAPI + SQLAlchemy + Alembic, Python >=3.11.

## Tech stack

- FastAPI (uvicorn) — entrypoint `app/main.py`; only `/health` exists so far, no routers mounted.
- SQLAlchemy 2.0 + psycopg3 (Postgres/Supabase) — use the typed ORM style:
  `Mapped[...]` + `mapped_column(...)`, never legacy `Column(...)`.
- Alembic — migrations (none yet; see Gotchas).
- Pydantic v2 + pydantic-settings — `Settings` reads `.env`; wire schemas in
  `app/schemas`, never reuse a model class as a schema.
- python-jose — JWT validation for Supabase access tokens; installed, not wired yet.

## Model conventions (app/models)

- Python `enum.Enum` + `SQLEnum(Enum, name="<pg_enum_name>")` for enum columns.
- UUID PKs: `Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)`.
- Timestamps: `DateTime(timezone=True)` with `default=lambda: datetime.now(UTC)`.
- Relationships: `relationship(back_populates=...)`, `cascade="all, delete-orphan"`
  for owned children; string forward refs for the far side.
- Check constraints via `__table_args__` (e.g. `applicant_marks` mark range 0–100).

## Setup & commands (run from `backend/`)

Package manager is `uv`, NOT pip/poetry. CI uses Python 3.11; the local `.venv` is 3.14.

- `uv sync` — install deps (dev group included)
- `uv run ruff check .` — lint (line-length 100, flake8-bugbear,
  `extend-immutable-calls = ["fastapi.Depends"]`)
- `uv run pytest` — tests (no test files exist yet)
- `uv run uvicorn app.main:app --reload` — dev server on :8000

## Layering (enforced by convention — see package docstrings)

Never skip a layer: router -> service -> queries -> database.

- `app/routers` — HTTP only: auth/role check, validate, call ONE service fn
- `app/services` — all business logic; plain Python, no HTTP
- `app/queries` — SQLAlchemy queries, no business logic; services call these
- `app/models` — DB tables (may hold backend-only fields like password hashes)
- `app/schemas` — Pydantic wire shapes; never the same class as a model

## Gotchas

- `Base` (DeclarativeBase) is defined in `app/deps.py`, NOT `app/models`.
  Models import it via `from app.deps import Base`.
- Alembic is not wired to models yet: `alembic/env.py` has `target_metadata = None`
  with `from app.models import Base` commented out, so `--autogenerate` will NOT
  detect models. `alembic.ini` `sqlalchemy.url` is empty; `env.py` sets it from
  `get_settings().database_url`.
- Config via pydantic-settings (`app/config.py`) reads `.env` in `backend/`
  (`DATABASE_URL`, `SUPABASE_URL`, `ENVIRONMENT`). `.env` is gitignored — copy
  `.env.example`.
- Auth is stubbed: `get_current_user()` in `app/deps.py` raises
  `NotImplementedError`; `require_role()` depends on it. JWT deps
  (`python-jose`) are installed but unused so far.

## Database

The user designs the database; the agent implements against the schema provided.
Treat the schema and its constraints as part of the application's public contract.

- Never create, alter, drop, or rename tables, columns, keys, constraints,
  indexes, enums, functions, triggers, views, RLS policies, procedures, or types.
- Never generate or modify migrations unless the user provides the exact schema
  change and explicitly asks for the migration.
- Never infer a missing relationship/field, or "fix" a schema that seems
  inefficient, inconsistent, incomplete, or unconventional.
- If the implementation needs schema that wasn't provided, STOP and ask the user.
- If the schema seems incompatible with the requested feature, explain the
  incompatibility and ask how to proceed.
- Report (don't implement) any required DB change.

When writing code against the schema:

- Preserve referential integrity; enforce invariants in DB constraints where
  they must hold regardless of which app accesses the DB.
- Make schema changes via migrations (where the project uses them) and review
  generated migrations before considering them complete.
- Never discard existing data unless the user explicitly requests a destructive
  migration. When changing a column/constraint/relationship/index, account for
  existing data and dependent queries.
- Use transactions when multiple related DB operations must succeed or fail as
  one unit.

Allowed: read/inspect the schema, and write app code against it — models, ORM
mappings, queries, repositories, services, validation, endpoints, schemas.

## Git

- Never commit or push unless explicitly requested.
- Never force-push.
- Never reset, rebase, checkout, or discard existing user changes without
  explicit permission.
- Preserve unrelated uncommitted changes; before editing a file that already has
  changes, account for them and avoid overwriting.
- Keep the working tree focused on the requested task.

## Configuration & Infrastructure

- Don't modify env, deployment, CI/CD, Docker, infrastructure, or system config
  unless relevant to the task.
- Don't assume dev and prod environments are equivalent.
- Never run destructive commands against databases, filesystems, containers, or
  infrastructure without explicit authorization.
- Prefer reversible changes when touching infrastructure or configuration.

## CI

`.gitlab-ci.yml` path-based rules: backend jobs (`ruff check`, `pytest`) only run
when `backend/**` changes. Order: lint stage -> test stage.

## Known issues (models)

Don't "fix" these without the user; they're in the provided schema:

- Placeholder enums with empty bodies: `ProgramAction`, `ProgramReason`,
  `ProgramStatus` (`application_lifecycles.py`), `VoteDecision` (`votes.py`).
- FK typos: `application_lifecycles.py` → `"applicantions.application_number"`;
  `academic_plans.py` → `"academic_program.academic_program_code"` (singular).
- `applications.py`: `admit_type` annotated `Mapped[Choice]` but mapped to a
  `String` column.
