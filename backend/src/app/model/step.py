from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.model.base import Base

if TYPE_CHECKING:
    from src.app.model.quest import Quest


class Step(Base):
    __tablename__ = "quest_steps"
    __table_args__ = (
        CheckConstraint("position >= 1", name="ck_quest_steps_position_positive"),
        UniqueConstraint("quest_id", "position", name="uq_quest_steps_quest_position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quest_id: Mapped[int] = mapped_column(
        ForeignKey("quests.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    quest: Mapped["Quest"] = relationship(back_populates="steps")
