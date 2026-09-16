"""ADMIT API entrypoint.

Thin FastAPI app: mounts routers, does no logic of its own.
Layering is router -> service -> queries -> database, never skip a layer.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    applicants,
    applications,
    import_documents,
    import_runs,
    imports,
    matching_reviews,
    nl_query,
    notes,
    rules,
    student_documents,
    system_logs,
    users,
    votes,
)

app = FastAPI(title="ADMIT", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(imports.router)
app.include_router(import_documents.router)
app.include_router(notes.router)
app.include_router(applications.router)
app.include_router(applicants.router)
app.include_router(matching_reviews.router)
app.include_router(votes.router)
app.include_router(import_runs.router)
app.include_router(system_logs.router)
app.include_router(rules.router)
app.include_router(student_documents.router)
app.include_router(nl_query.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
