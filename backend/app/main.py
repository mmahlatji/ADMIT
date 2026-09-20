"""ADMIT API entrypoint.

Thin FastAPI app: mounts routers, does no logic of its own.
Layering is router -> service -> queries -> database, never skip a layer.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import (
    applicants,
    applications,
    exports,
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

logger = logging.getLogger(__name__)

app = FastAPI(title="ADMIT", version="1.0.0")


# Registered before CORSMiddleware so CORS wraps it and its headers reach this
# response. Starlette's own 500 handler sits outside CORS, so an unhandled
# error there arrives with no CORS headers at all and the browser blocks it:
# the frontend sees an opaque network failure rather than any message.
@app.middleware("http")
async def handle_unhandled_errors(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Something went wrong handling that request."},
        )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Browsers hide all but a safelist of response headers from JS. The
    # decisions export reads its filename off this one.
    expose_headers=["Content-Disposition"],
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
app.include_router(exports.router)
app.include_router(student_documents.router)
app.include_router(nl_query.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
