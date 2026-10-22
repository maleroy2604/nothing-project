"""Add ordered quest steps.

Revision ID: 002_add_quest_steps
Revises: 001_add_guides_and_quest_fields
"""
from alembic import op
import sqlalchemy as sa

revision = "002_add_quest_steps"
down_revision = "001_add_guides_and_quest_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not sa.inspect(op.get_bind()).has_table("quest_steps"):
        op.create_table(
            "quest_steps",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("quest_id", sa.Integer(), nullable=False),
            sa.Column("position", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column(
                "description",
                sa.Text(),
                nullable=False,
                server_default="",
            ),
            sa.CheckConstraint(
                "position >= 1", name="ck_quest_steps_position_positive"
            ),
            sa.ForeignKeyConstraint(
                ["quest_id"], ["quests.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "quest_id",
                "position",
                name="uq_quest_steps_quest_position",
            ),
        )


def downgrade() -> None:
    op.drop_table("quest_steps")
