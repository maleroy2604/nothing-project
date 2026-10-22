"""Add guides and guide-specific quest fields.

Revision ID: 001_add_guides_and_quest_fields
Revises: 000_create_quests
"""
from alembic import op
import sqlalchemy as sa

revision = "001_add_guides_and_quest_fields"
down_revision = "000_create_quests"
branch_labels = None
depends_on = None


def _constraint_names(table: str, kind: str) -> set[str | None]:
    inspector = sa.inspect(op.get_bind())
    if kind == "foreign_key":
        return {item["name"] for item in inspector.get_foreign_keys(table)}
    if kind == "check":
        return {item["name"] for item in inspector.get_check_constraints(table)}
    return {item["name"] for item in inspector.get_unique_constraints(table)}


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("guides"):
        op.create_table(
            "guides",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    quest_columns = {
        column["name"] for column in sa.inspect(op.get_bind()).get_columns("quests")
    }
    if "guide_id" not in quest_columns:
        op.add_column("quests", sa.Column("guide_id", sa.Integer(), nullable=True))
    if "position" not in quest_columns:
        op.add_column("quests", sa.Column("position", sa.Integer(), nullable=True))
    if "completion_criteria" not in quest_columns:
        op.add_column(
            "quests", sa.Column("completion_criteria", sa.Text(), nullable=True)
        )

    op.execute(
        """
        DO $$
        DECLARE
            fallback_guide_id INTEGER;
        BEGIN
            IF EXISTS (SELECT 1 FROM quests WHERE guide_id IS NULL) THEN
                INSERT INTO guides DEFAULT VALUES
                RETURNING id INTO fallback_guide_id;

                UPDATE quests AS quest
                SET guide_id = fallback_guide_id,
                    position = ordered_quests.position,
                    completion_criteria = COALESCE(
                        NULLIF(quest.description, ''),
                        quest.title
                    )
                FROM (
                    SELECT id, ROW_NUMBER() OVER (ORDER BY id)::INTEGER AS position
                    FROM quests
                    WHERE guide_id IS NULL
                ) AS ordered_quests
                WHERE quest.id = ordered_quests.id;
            END IF;
        END
        $$;
        """
    )
    op.execute(
        """
        UPDATE quests
        SET completion_criteria = COALESCE(NULLIF(description, ''), title)
        WHERE completion_criteria IS NULL
        """
    )
    op.execute(
        """
        WITH missing_positions AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY id)::INTEGER AS position
            FROM quests
            WHERE position IS NULL
        )
        UPDATE quests
        SET position = missing_positions.position
        FROM missing_positions
        WHERE quests.id = missing_positions.id
        """
    )

    op.alter_column("quests", "guide_id", nullable=False)
    op.alter_column("quests", "position", nullable=False)
    op.alter_column("quests", "completion_criteria", nullable=False)

    quest_foreign_keys = sa.inspect(op.get_bind()).get_foreign_keys("quests")
    has_guide_foreign_key = any(
        foreign_key["constrained_columns"] == ["guide_id"]
        and foreign_key["referred_table"] == "guides"
        for foreign_key in quest_foreign_keys
    )
    if not has_guide_foreign_key:
        op.create_foreign_key(
            "fk_quests_guide_id_guides",
            "quests",
            "guides",
            ["guide_id"],
            ["id"],
            ondelete="CASCADE",
        )
    if "ck_quests_position_positive" not in _constraint_names("quests", "check"):
        op.create_check_constraint(
            "ck_quests_position_positive", "quests", "position >= 1"
        )
    if "uq_quests_guide_position" not in _constraint_names("quests", "unique"):
        op.create_unique_constraint(
            "uq_quests_guide_position", "quests", ["guide_id", "position"]
        )


def downgrade() -> None:
    if "uq_quests_guide_position" in _constraint_names("quests", "unique"):
        op.drop_constraint("uq_quests_guide_position", "quests", type_="unique")
    if "ck_quests_position_positive" in _constraint_names("quests", "check"):
        op.drop_constraint("ck_quests_position_positive", "quests", type_="check")
    for foreign_key in sa.inspect(op.get_bind()).get_foreign_keys("quests"):
        if (
            foreign_key["constrained_columns"] == ["guide_id"]
            and foreign_key["referred_table"] == "guides"
            and foreign_key["name"]
        ):
            op.drop_constraint(
                foreign_key["name"], "quests", type_="foreignkey"
            )
    quest_columns = {
        column["name"] for column in sa.inspect(op.get_bind()).get_columns("quests")
    }
    for column in ("completion_criteria", "position", "guide_id"):
        if column in quest_columns:
            op.drop_column("quests", column)
    if sa.inspect(op.get_bind()).has_table("guides"):
        op.drop_table("guides")
