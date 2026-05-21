"""SQLAlchemy declarative base for the persistence layer."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base shared by every vero-lite ORM model."""
