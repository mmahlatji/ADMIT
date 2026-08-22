"""ADMIT API entrypoint.

Thin FastAPI app: mounts routers, does no logic of its own.
Layering is router -> service -> queries -> database, never skip a layer.
"""

from fastapi import FastAPI

from app.routers import users

app = FastAPI(title="ADMIT", version="1.0.0")
app.include_router(users.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
