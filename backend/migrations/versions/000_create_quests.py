"""Create the original quests table when it is not already present.

Revision ID: 000_create_quests
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "000_create_quests"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not sa.inspect(op.get_bind()).has_table("quests"):
        op.create_table(
            "quests",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.CheckConstraint(
                "status IN ('not_started', 'in_progress', 'completed')",
                name="ck_quests_status_valid",
            ),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    pass
