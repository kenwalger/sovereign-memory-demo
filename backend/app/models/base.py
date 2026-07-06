"""SQLAlchemy declarative base for institutional memory models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared metadata registry for all relational entities.

    Serves as the SQLAlchemy declarative base used by document, record,
    evidence, and receipt ORM models.
    """
