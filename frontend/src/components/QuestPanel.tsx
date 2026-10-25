import type { FormEventHandler } from "react";
import type { Quest } from "../types/quest";

interface QuestPanelProps {
  quests: Quest[];
  selectedQuestId: number | null;
  showQuestForm: boolean;
  questTitle: string;
  questDescription: string;
  completionCriteria: string;
  savingContent: boolean;
  updatingQuestId: number | null;
  onToggleQuestForm: () => void;
  onQuestTitleChange: (value: string) => void;
  onQuestDescriptionChange: (value: string) => void;
  onCompletionCriteriaChange: (value: string) => void;
  onCreateQuest: FormEventHandler<HTMLFormElement>;
  onUpdateQuestStatus: (quest: Quest, checked: boolean) => void;
  onSelectQuest: (questId: number) => void;
}

export default function QuestPanel({
  quests,
  selectedQuestId,
  showQuestForm,
  questTitle,
  questDescription,
  completionCriteria,
  savingContent,
  updatingQuestId,
  onToggleQuestForm,
  onQuestTitleChange,
  onQuestDescriptionChange,
  onCompletionCriteriaChange,
  onCreateQuest,
  onUpdateQuestStatus,
  onSelectQuest,
}: QuestPanelProps) {
  return (
    <section className="quest-panel" aria-labelledby="quest-list-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">THE JOURNEY</p>
          <h3 id="quest-list-heading">Quests</h3>
        </div>
        <div className="section-actions">
          <span className="subtle-count">{quests.length} total</span>
          <button className="small-action" type="button" onClick={onToggleQuestForm}>
            {showQuestForm ? "Cancel" : "+ Quest"}
          </button>
        </div>
      </div>

      {showQuestForm && (
        <form className="content-form" onSubmit={onCreateQuest}>
          <label>
            Quest title
            <input
              required
              maxLength={200}
              value={questTitle}
              onChange={(event) => onQuestTitleChange(event.target.value)}
            />
          </label>
          <label>
            Description
            <textarea
              value={questDescription}
              onChange={(event) => onQuestDescriptionChange(event.target.value)}
            />
          </label>
          <label>
            Completion criteria
            <input
              placeholder="Defaults to the quest title"
              value={completionCriteria}
              onChange={(event) => onCompletionCriteriaChange(event.target.value)}
            />
          </label>
          <button className="primary-button" type="submit" disabled={savingContent}>
            {savingContent ? "Saving…" : "Create quest"}
          </button>
        </form>
      )}

      {quests.length === 0 ? (
        <p className="empty-quests">This guide doesn’t have any quests yet.</p>
      ) : (
        <ol className="quest-list">
          {quests.map((quest, index) => {
            const isSelected = selectedQuestId === quest.id;
            const isCompleted = quest.status === "completed";
            return (
              <li
                className={`quest-item${isSelected ? " is-selected" : ""}${isCompleted ? " is-completed" : ""}`}
                key={quest.id}
              >
                <label className="quest-checkbox">
                  <input
                    type="checkbox"
                    checked={isCompleted}
                    disabled={updatingQuestId === quest.id}
                    onChange={(event) => onUpdateQuestStatus(quest, event.target.checked)}
                    aria-label={`${isCompleted ? "Mark" : "Complete"} ${quest.title}`}
                  />
                  <span className="custom-checkbox" aria-hidden="true">
                    {isCompleted && "✓"}
                  </span>
                </label>
                <button
                  type="button"
                  className="quest-open"
                  onClick={() => onSelectQuest(quest.id)}
                >
                  <span className="quest-number">{String(index + 1).padStart(2, "0")}</span>
                  <span className="quest-copy">
                    <span className="quest-title">{quest.title}</span>
                    <span className="quest-step-count">
                      {quest.steps.length} {quest.steps.length === 1 ? "step" : "steps"}
                    </span>
                  </span>
                  <span className="quest-chevron" aria-hidden="true">›</span>
                </button>
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}
