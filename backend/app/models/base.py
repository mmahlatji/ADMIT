from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared base every model inherits from, so they all register on one metadata."""
