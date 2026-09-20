# ADMIT

Postgraduate admissions management for the UCT Computer Science honours intake.
Admissions data arrives in waves across the cycle, from several systems, in
spreadsheets that do not agree with each other. ADMIT ingests those sheets,
reconciles them against what is already on file, and keeps a record of what
changed and why.

- **Heterogeneous ingestion**, one adapter per source sheet (ASR, UCT marks, IT
  transcripts, motivations), each normalising its own column vocabulary.
- **Incremental updates**: re-importing a sheet updates records in place
  instead of duplicating them, and never silently overturns a decision a
  convenor has already made.
- **Configurable admissions rules**, a rule engine that previews the effect of
  a proposed rule on the current intake before it's saved.
- **Applicant lifecycle**, a state machine driving each application through
  applied, reviewed, offered, accepted, denied or cancelled.

## Stack

| | |
|---|---|
| Backend | FastAPI, SQLAlchemy 2.0, Alembic, pandas, uv |
| Frontend | React 18, TypeScript, Vite, React Router, Zod |
| Database | PostgreSQL 17 (Supabase) |
| Auth & storage | Supabase (JWT auth, object storage for uploaded sheets) |

## Prerequisites

- Docker, if you just want the app running (see below)
- Python 3.11+ and [uv](https://docs.astral.sh/uv/), if you're developing the backend
- Node 18+, if you're developing the frontend
- Access to the team's Supabase project either way. There's no offline mode,
  auth and the database both go through it

## Running it with Docker

This is the fastest way to get the whole app up, and it's what to use if you
just need it running rather than actively developing it.

**1. Get both `.env` files sorted first.** Docker doesn't create these for
you, and the containers will start and immediately fail without them:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Then fill both in following the [Environment variables](#environment-variables)
section below, same as the non-Docker setup. `docker-compose.yml` reads
`backend/.env` and `frontend/.env` directly, so once these two files are
correct, Docker is correct.

**2. Build and run the api and web services:**

```bash
docker compose up api web
```

This also starts the `ollama` container (see [Ollama](#ollama-and-the-ask-feature)
below); it comes up whether you ask for it or not.

First build takes a few minutes (pulling base images, `npm install`, `uv sync`
inside the containers). After that, `docker compose up api web` again reuses
the built images and starts in seconds.

**3. Wait for the api to say it's ready.** Watch the logs; you want to see:

```
api-1  | INFO:     Application startup complete.
api-1  | INFO:     Uvicorn running on http://0.0.0.0:8000
```

**4. Open the app.** Frontend at http://localhost:5173, API at
http://localhost:8000, interactive API docs at http://localhost:8000/docs.

**5. Run migrations once, from your host, against the same database the
containers are pointed at:**

```bash
cd backend && uv run alembic upgrade head
```

(This needs `uv sync` on your host too, just for this one command. The
containers run the app; they don't run one-off admin commands for you.)

To stop everything: `Ctrl+C`, or `docker compose down` from another terminal.
To rebuild after pulling changes that touch dependencies:
`docker compose build api web`.

`docker-compose.yml` also defines a `test_db` service, a throwaway local
Postgres used only for testing a migration before it touches Supabase.
Nothing in normal day-to-day use needs it; see [Migrations](#migrations).

### Ollama and the "Ask" feature

The natural-language "Ask" page runs its model in a separate `ollama`
container. Everything else — ingestion, the rules engine, the applicant
lifecycle, exports — works without it.

**With Ollama (the default).** `docker compose up api web` starts `ollama` as
well, because `api` declares `depends_on: ollama`.

- The first start pulls `qwen2.5-coder:7b-instruct-q6_K`, several GB, before
  the container reports healthy. A cold volume can take up to 15 minutes, so
  watch the logs rather than assuming it has hung.
- Inference is CPU-only and slow: the first question after startup can take a
  minute or more, and complex questions can take minutes. The model is kept
  resident in memory (`OLLAMA_KEEP_ALIVE` is `-1`), which trades RAM for a warm
  start on later questions.

**Without Ollama.** There is no `docker compose` command that starts `api`
without also starting Ollama: the dependency and the `OLLAMA_URL` /
`OLLAMA_MODEL` values are set in the compose file's `environment:` block, not
read from `backend/.env`. To run without it, comment out `depends_on: ollama`
and the two `OLLAMA_*` lines in `docker-compose.yml`, then:

```bash
docker compose up api web
```

Everything works except `/ask`, which fails and points at the missing model.
This skips the multi-GB download and frees the memory the model would
otherwise hold, at the cost of the Ask page.

## Running it without Docker

### 1. Backend environment

```bash
cd backend
cp .env.example .env
```

Then see [Environment variables](#environment-variables) below.

### 2. Frontend environment

```bash
cd frontend
cp .env.example .env
```

Same section below.

### 3. Install and migrate

```bash
cd backend && uv sync
uv run alembic upgrade head

cd ../frontend && npm install
```

### 4. Run

Two terminals:

```bash
cd backend && uv run uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend && npm run dev
```

The app is at http://localhost:5173, the API at http://localhost:8000, and
interactive API docs at http://localhost:8000/docs.

## Environment variables

### Backend (`backend/.env`)

| Variable | Where to find it |
|---|---|
| `DATABASE_URL` | Supabase dashboard, Connect, **Session pooler** (see note below) |
| `SUPABASE_URL` | Project Settings, Data API, Project URL |
| `SUPABASE_SECRET_KEY` | Project Settings, API Keys, **Secret keys**. Required, without it every file upload fails |
| `ENVIRONMENT` | `development` |

**Two things about `DATABASE_URL` that will bite you.**

Use the **Session pooler** string, not Direct connection. Direct connections
are IPv6-only, and most networks (including, apparently, most of ours) can't
reach them:

```
postgresql+psycopg://postgres.<project-ref>:<password>@aws-1-eu-west-1.pooler.supabase.com:5432/postgres
```

The scheme has to be `postgresql+psycopg` (psycopg 3). A plain `postgresql://`
resolves to psycopg2, which isn't installed, and fails with
`ModuleNotFoundError: No module named 'psycopg2'`.

If your database password contains any of ``$ % & + [ ] / @ : #`` it needs to
be percent-encoded, or the URL gets silently misparsed:

```bash
python -c "import urllib.parse,getpass; print(urllib.parse.quote(getpass.getpass('pw: '), safe=''))"
```

### Frontend (`frontend/.env`)

| Variable | Value |
|---|---|
| `VITE_SUPABASE_URL` | same as `SUPABASE_URL` |
| `VITE_SUPABASE_ANON_KEY` | Project Settings, API Keys, **Publishable key** (safe in a browser) |
| `VITE_API_BASE_URL` | `http://localhost:8000` |

## First account

Roles aren't self-assigned. Sign up at `/signup` (a UCT email and a 7-digit
employee number are both required), which creates the account with **no
role** and leaves it pending. A convenor then grants a role via
`POST /users/{user_id}/role`. Until then the account can sign in but reaches
nothing else.

For the very first convenor on a fresh database, set the role directly:

```sql
UPDATE users SET role = 'convenor' WHERE employee_id = '<your employee id>';
```

## Tests

```bash
cd backend
uv run pytest -q
uv run ruff check .
```

The integration tests under `backend/tests/data/` run real synthetic sheets
through the whole import pipeline. That data is committed deliberately; every
other spreadsheet is gitignored, so a real faculty export can't get committed
by habit.

Frontend:

```bash
cd frontend
npx tsc --noEmit
npm run build
```

## Importing sheets

Upload at `/file-upload`, or `POST /imports/{source_type}` with `source_type`
one of `asr`, `uct_marks`, `it_transcripts`, `motivations`. Convenor or admin
only.

**Order matters.** Only the ASR sheet creates applicants; marks, transcripts
and motivations all look one up by campus id and flag the row if it's
missing. Upload ASR first. The upload page enforces this, the API doesn't.

**Import older sheets first.** A sheet whose effective dates predate what's
on file is treated as stale and flagged, which is deliberate. Loading
December before October will flag almost every October row.

**Uploads are slow from a laptop.** The database is in `eu-west-1`, so from
South Africa each query costs about 160ms and a 345-row sheet takes several
minutes. That's network latency, not the import itself: the same work takes
seconds when the API runs in the same region. Use a trimmed sheet for demos.

## Migrations

```bash
cd backend
uv run alembic upgrade head                        # apply
uv run alembic revision --autogenerate -m "..."    # create
uv run alembic check                               # models vs schema
```

Autogenerate output always needs review. On Postgres it won't create enum
types before using them, it emits `NOT NULL` columns with no default (which
fails on a populated table), and it won't add the `USING` clause a type
change needs. Run every generated migration against a scratch database
before committing it, using the `test_db` service from `docker-compose.yml`:

```bash
docker compose up -d test_db
DATABASE_URL="postgresql+psycopg://admin:admin@localhost:5433/admit_db" uv run alembic upgrade head
```

## Layout

```
backend/
  app/
    adapters/     one module per source sheet, column vocab and validation
    models/       SQLAlchemy tables
    queries/      data access, no business logic
    routers/      HTTP endpoints, thin
    schemas/      Pydantic request and response shapes
    services/
      imports/    reconciling adapter output into the database
      state/      applicant lifecycle state machine
      storage/    Supabase object storage
    rule_engine.py
  alembic/versions/
  tests/
frontend/src/
  context/    auth context
  lib/        supabase client, api wrapper, auth helpers
  pages/      signin, signup, dashboard, uploads, and the convenor workspace
```

Layering is `router -> service -> queries -> database`. Never skip a layer.
`get_db` owns the transaction: query helpers `flush()`, and the request
commits once at the end.
