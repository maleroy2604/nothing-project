"""Add board column to guides.

Revision ID: 8e21c4a0f6b3
Revises: d7b42a1c9e61
"""
from alembic import op
import sqlalchemy as sa

revision = "8e21c4a0f6b3"
down_revision = "d7b42a1c9e61"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "guides",
        sa.Column(
            "board_column",
            sa.String(length=20),
            nullable=False,
            server_default="backlog",
        ),
    )
    op.create_check_constraint(
        "ck_guides_board_column",
        "guides",
        "board_column IN ('backlog', 'daily', 'weekly', 'in_progress')",
    )
    op.alter_column("guides", "board_column", server_default=None)


def downgrade() -> None:
    op.drop_constraint("ck_guides_board_column", "guides", type_="check")
    op.drop_column("guides", "board_column")
