"""Guards against an endpoint shipping without a role check.

Two endpoints (notes delete, import document download) once used
get_current_user directly, which only proves the token is valid: a signed-up
user still awaiting approval has role None and passed straight through. This
test makes that class of mistake fail the suite rather than reach review.
"""

from fastapi.routing import APIRoute

from app.main import app

# Routes that are meant to be reachable without a role.
# /users/me especially: a newly signed-up user has role None and needs it to
# find out they are pending approval.
NO_ROLE_REQUIRED = {
    "/health",
    "/users/me",
    "/openapi.json",
    "/docs",
    "/docs/oauth2-redirect",
    "/redoc",
}


def _iter_api_routes(router):
    """Walk every APIRoute reachable from a router.

    Recent FastAPI wraps an included router in _IncludedRouter rather than
    flattening its routes onto app.routes, so a plain scan of app.routes only
    finds /health. Handle both layouts.
    """
    for route in getattr(router, "routes", []):
        if isinstance(route, APIRoute):
            yield route
        elif hasattr(route, "original_router"):
            yield from _iter_api_routes(route.original_router)


def _is_role_gated(route: APIRoute) -> bool:
    """True if any of the route's dependencies came from require_role()."""
    return any(
        getattr(dependency.call, "enforces_role", False)
        for dependency in route.dependant.dependencies
    )


def test_every_route_is_role_gated():
    ungated = [
        f"{sorted(route.methods)} {route.path}"
        for route in _iter_api_routes(app)
        if route.path not in NO_ROLE_REQUIRED and not _is_role_gated(route)
    ]

    assert not ungated, (
        "these routes have no require_role dependency; add one, or add the path "
        f"to NO_ROLE_REQUIRED if it is deliberately open: {ungated}"
    )


def test_marker_actually_detects_a_gated_route():
    """If require_role ever stopped setting the marker, the test above would
    pass vacuously. This makes sure the detection itself still works.
    """
    gated = [route for route in _iter_api_routes(app) if _is_role_gated(route)]

    assert gated, "no route detected as role gated, the enforces_role marker is broken"
