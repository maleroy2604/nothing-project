"""Add editable guide titles.

Revision ID: d7b42a1c9e61
Revises: c4f7f814e73a
"""
from alembic import op
import sqlalchemy as sa

revision = "d7b42a1c9e61"
down_revision = "c4f7f814e73a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "guides",
        sa.Column("title", sa.String(length=200), nullable=False, server_default=""),
    )
    op.execute("UPDATE guides SET title = 'Guide ' || id WHERE title = ''")
    op.alter_column("guides", "title", server_default=None)


def downgrade() -> None:
    op.drop_column("guides", "title")
