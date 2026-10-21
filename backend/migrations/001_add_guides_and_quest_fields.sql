BEGIN;

CREATE TABLE IF NOT EXISTS guides (
    id SERIAL PRIMARY KEY
);

ALTER TABLE quests ADD COLUMN guide_id INTEGER;
ALTER TABLE quests ADD COLUMN position INTEGER;
ALTER TABLE quests ADD COLUMN completion_criteria TEXT;

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

ALTER TABLE quests ALTER COLUMN guide_id SET NOT NULL;
ALTER TABLE quests ALTER COLUMN position SET NOT NULL;
ALTER TABLE quests ALTER COLUMN completion_criteria SET NOT NULL;
ALTER TABLE quests
    ADD CONSTRAINT fk_quests_guide_id_guides
    FOREIGN KEY (guide_id) REFERENCES guides(id) ON DELETE CASCADE;
ALTER TABLE quests
    ADD CONSTRAINT ck_quests_position_positive
    CHECK (position >= 1);
ALTER TABLE quests
    ADD CONSTRAINT uq_quests_guide_position
    UNIQUE (guide_id, position);

COMMIT;
