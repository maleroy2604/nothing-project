import type { Quest } from "../types/quest";

interface QuestListProps {
  quests: Quest[];
}

export default function QuestList({ quests }: QuestListProps) {
  if (quests.length === 0) {
    return <p>No quests yet.</p>;
  }

  return (
    <ul>
      {quests.map((quest) => (
        <li key={quest.id}>
          <h2>{quest.title}</h2>
          <p>{quest.description}</p>
          <span>{quest.status.replace("_", " ")}</span>
        </li>
      ))}
    </ul>
  );
}
