export type QuestStatus = "not_started" | "in_progress" | "completed";

export interface Step {
  id: number;
  quest_id: number;
  position: number;
  title: string;
  description: string;
}

export interface Quest {
  id: number;
  guide_id: number;
  position: number;
  title: string;
  completion_criteria: string;
  description: string;
  status: QuestStatus;
  steps: Step[];
}

export interface Guide {
  id: number;
  quests: Quest[];
}

export type QuestUpdate = Partial<
  Pick<Quest, "status" | "title" | "description" | "completion_criteria">
>;
