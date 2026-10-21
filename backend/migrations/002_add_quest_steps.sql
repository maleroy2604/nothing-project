BEGIN;

CREATE TABLE quest_steps (
    id SERIAL PRIMARY KEY,
    quest_id INTEGER NOT NULL REFERENCES quests(id) ON DELETE CASCADE,
    position INTEGER NOT NULL CHECK (position >= 1),
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    CONSTRAINT uq_quest_steps_quest_position UNIQUE (quest_id, position)
);

COMMIT;
