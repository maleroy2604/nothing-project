export interface Quest {
  id: number;
  title: string;
  description: string;
  status: "not_started" | "in_progress" | "completed";
}

export type QuestCreate = Pick<Quest, "title" | "description">;
