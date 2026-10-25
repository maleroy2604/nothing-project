import type { FormEventHandler } from "react";
import type { Quest, Step } from "../types/quest";

interface QuestReaderProps {
  selectedQuest: Quest | null;
  questNumber: number;
  currentStep: Step | null;
  currentStepIndex: number;
  showStepForm: boolean;
  stepTitle: string;
  stepDescription: string;
  savingContent: boolean;
  onChangeStep: (direction: -1 | 1) => void;
  onToggleStepForm: () => void;
  onStepTitleChange: (value: string) => void;
  onStepDescriptionChange: (value: string) => void;
  onCreateStep: FormEventHandler<HTMLFormElement>;
}

export default function QuestReader({
  selectedQuest,
  questNumber,
  currentStep,
  currentStepIndex,
  showStepForm,
  stepTitle,
  stepDescription,
  savingContent,
  onChangeStep,
  onToggleStepForm,
  onStepTitleChange,
  onStepDescriptionChange,
  onCreateStep,
}: QuestReaderProps) {
  return (
    <section className="reader-panel" aria-live="polite">
      {!selectedQuest ? (
        <div className="reader-empty">
          <div className="reader-empty-icon" aria-hidden="true">↗</div>
          <h3>Choose a quest</h3>
          <p>Select a quest from the list to open its steps.</p>
        </div>
      ) : (
        <>
          <div className="reader-heading">
            <div>
              <p className="eyebrow">QUEST {String(questNumber).padStart(2, "0")}</p>
              <h3>{selectedQuest.title}</h3>
            </div>
            {selectedQuest.status === "completed" && (
              <span className="completed-pill">✓ Completed</span>
            )}
          </div>
          {selectedQuest.description && (
            <p className="quest-description">{selectedQuest.description}</p>
          )}

          {currentStep ? (
            <article className="step-card">
              <div className="step-card-topline">
                <span className="step-kicker">CURRENT STEP</span>
                <span className="step-position">
                  {currentStepIndex + 1} / {selectedQuest.steps.length}
                </span>
              </div>
              <span className="step-number">{String(currentStepIndex + 1).padStart(2, "0")}</span>
              <h4>{currentStep.title}</h4>
              {currentStep.description && (
                <p className="step-description">{currentStep.description}</p>
              )}
              <div className="step-navigation">
                <button
                  className="arrow-button"
                  type="button"
                  aria-label="Previous step"
                  disabled={currentStepIndex === 0}
                  onClick={() => onChangeStep(-1)}
                >
                  ←
                </button>
                <span>
                  {currentStepIndex === selectedQuest.steps.length - 1
                    ? "You’re at the final step"
                    : "Keep going"}
                </span>
                <button
                  className="arrow-button next-arrow"
                  type="button"
                  aria-label="Next step"
                  disabled={currentStepIndex >= selectedQuest.steps.length - 1}
                  onClick={() => onChangeStep(1)}
                >
                  →
                </button>
              </div>
            </article>
          ) : (
            <div className="no-steps">
              <span aria-hidden="true">✦</span>
              <h4>No steps added yet</h4>
              <p>{selectedQuest.completion_criteria}</p>
            </div>
          )}
          <div className="add-step-row">
            <button className="small-action" type="button" onClick={onToggleStepForm}>
              {showStepForm ? "Cancel" : "+ Add step"}
            </button>
          </div>
          {showStepForm && (
            <form className="content-form step-form" onSubmit={onCreateStep}>
              <label>
                Step title
                <input
                  required
                  maxLength={200}
                  value={stepTitle}
                  onChange={(event) => onStepTitleChange(event.target.value)}
                />
              </label>
              <label>
                Description
                <textarea
                  value={stepDescription}
                  onChange={(event) => onStepDescriptionChange(event.target.value)}
                />
              </label>
              <button className="primary-button" type="submit" disabled={savingContent}>
                {savingContent ? "Saving…" : "Create step"}
              </button>
            </form>
          )}
        </>
      )}
    </section>
  );
}
