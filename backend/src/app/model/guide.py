from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.model.base import Base

if TYPE_CHECKING:
    from src.app.model.quest import Quest


class Guide(Base):
    __tablename__ = "guides"
    __table_args__ = (
        CheckConstraint(
            "board_column IN ('backlog', 'daily', 'weekly', 'in_progress')",
            name="ck_guides_board_column",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    board_column: Mapped[str] = mapped_column(
        String(20), nullable=False, default="backlog"
    )
    quests: Mapped[list["Quest"]] = relationship(
        back_populates="guide",
        cascade="all, delete-orphan",
        order_by="Quest.position, Quest.id",
        lazy="selectin",
    )
