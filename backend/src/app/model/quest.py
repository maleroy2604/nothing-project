from sqlalchemy import CheckConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.app.model.base import Base


class Quest(Base):
    __tablename__ = "quests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('not_started', 'in_progress', 'completed')",
            name="ck_quests_status_valid",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="not_started"
    )
