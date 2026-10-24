from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.model.base import Base

if TYPE_CHECKING:
    from src.app.model.guide import Guide
    from src.app.model.step import Step


class Quest(Base):
    __tablename__ = "quests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('not_started', 'in_progress', 'completed')",
            name="ck_quests_status_valid",
        ),
        CheckConstraint("position >= 1", name="ck_quests_position_positive"),
        UniqueConstraint("guide_id", "position", name="uq_quests_guide_position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guide_id: Mapped[int] = mapped_column(
        ForeignKey("guides.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    completion_criteria: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    test_null_col: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="not_started"
    )
    guide: Mapped["Guide"] = relationship(back_populates="quests")
    steps: Mapped[list["Step"]] = relationship(
        back_populates="quest",
        cascade="all, delete-orphan",
        order_by="Step.position, Step.id",
        lazy="selectin",
    )
