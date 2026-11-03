from sqlalchemy import (  # type: ignore[reportMissingImports]
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship  # type: ignore[reportMissingImports]

from ..core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    owner = relationship("User", back_populates="tasks")