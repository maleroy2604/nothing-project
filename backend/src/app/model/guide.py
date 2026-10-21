from typing import TYPE_CHECKING

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.model.base import Base

if TYPE_CHECKING:
    from src.app.model.quest import Quest


class Guide(Base):
    __tablename__ = "guides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quests: Mapped[list["Quest"]] = relationship(
        back_populates="guide",
        cascade="all, delete-orphan",
        order_by="Quest.position, Quest.id",
        lazy="selectin",
    )
