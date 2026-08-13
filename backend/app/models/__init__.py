"""SQLAlchemy models — what's actually in the DB.

Includes fields that never leave the backend (e.g. password hash).
Pair each model with a schema in app/schemas; never merge the two into
one class — API shape and table shape diverge here (computed scores,
per-field provenance, role-gated fields like audit reasons).
"""
