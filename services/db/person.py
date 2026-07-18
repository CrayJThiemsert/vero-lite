"""Generated SQLAlchemy ORM models from ontology YAML — do not edit by hand."""

from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from services.db.base import Base


class Person(Base):
    __tablename__ = "person"

    person_id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    roles: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
