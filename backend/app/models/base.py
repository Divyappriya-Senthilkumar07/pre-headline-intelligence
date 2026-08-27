import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import DateTime, String, TypeDecorator
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VectorType(TypeDecorator):
    """
    Multilingual embedding vector type.
    Uses pgvector Vector on PostgreSQL, falls back to String/JSON representation on other dialects.
    """
    impl = Vector
    cache_ok = True

    def __init__(self, dim: int = 384):
        self.dim = dim
        super().__init__(dim)

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(self.dim))
        else:
            from sqlalchemy import JSON
            return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, (list, tuple)):
            return list(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value


class TimestampMixin:
    """Standard timestamp audit fields."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
