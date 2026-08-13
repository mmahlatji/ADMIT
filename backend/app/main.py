"""ADMIT API entrypoint.

Thin FastAPI app: mounts routers, does no logic of its own.
Layering is router -> service -> queries -> database — never skip a layer.
"""

from fastapi import FastAPI

app = FastAPI(title="ADMIT API", version="0.1.0")

# Routers are registered here as they're built, e.g.:
# from app.routers import applicants, imports, users
# app.include_router(applicants.router)
# app.include_router(imports.router)
# app.include_router(users.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
