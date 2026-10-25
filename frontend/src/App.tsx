import { useEffect, useMemo, useState, type FormEvent } from "react";
import AppHeader from "./components/AppHeader";
import GuideSidebar from "./components/GuideSidebar";
import QuestPanel from "./components/QuestPanel";
import QuestReader from "./components/QuestReader";
import { apiRequest } from "./services/api";
import type { Guide, Quest, QuestStatus, Step } from "./types/quest";

const PROGRESS_STORAGE_KEY = "nothing-project-guide-progress";

function readProgress(): Record<number, number> {
  try {
    const saved = localStorage.getItem(PROGRESS_STORAGE_KEY);
    if (!saved) return {};

    const parsed: unknown = JSON.parse(saved);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return {};

    const progress: Record<number, number> = {};
    for (const [questId, stepIndex] of Object.entries(parsed)) {
      if (
        typeof stepIndex === "number" &&
        Number.isInteger(stepIndex) &&
        stepIndex >= 0
      ) {
        progress[Number(questId)] = stepIndex;
      }
    }
    return progress;
  } catch {
    return {};
  }
}

function getErrorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

export default function App() {
  const [guides, setGuides] = useState<Guide[]>([]);
  const [selectedGuideId, setSelectedGuideId] = useState<number | null>(null);
  const [selectedQuestId, setSelectedQuestId] = useState<number | null>(null);
  const [stepPositions, setStepPositions] = useState<Record<number, number>>(readProgress);
  const [showQuestForm, setShowQuestForm] = useState(false);
  const [showStepForm, setShowStepForm] = useState(false);
  const [questTitle, setQuestTitle] = useState("");
  const [questDescription, setQuestDescription] = useState("");
  const [completionCriteria, setCompletionCriteria] = useState("");
  const [stepTitle, setStepTitle] = useState("");
  const [stepDescription, setStepDescription] = useState("");
  const [loading, setLoading] = useState(true);
  const [creatingGuide, setCreatingGuide] = useState(false);
  const [savingContent, setSavingContent] = useState(false);
  const [updatingQuestId, setUpdatingQuestId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadGuides() {
      try {
        const loadedGuides = await apiRequest<Guide[]>("/guides/?limit=100");
        setGuides(loadedGuides);
        setSelectedGuideId(loadedGuides[0]?.id ?? null);
      } catch (requestError) {
        setError(getErrorMessage(requestError, "Unable to load guides."));
      } finally {
        setLoading(false);
      }
    }

    void loadGuides();
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(PROGRESS_STORAGE_KEY, JSON.stringify(stepPositions));
    } catch {
      setError("Step progress could not be saved in this browser.");
    }
  }, [stepPositions]);

  const selectedGuide =
    guides.find((guide) => guide.id === selectedGuideId) ?? null;
  const quests = selectedGuide?.quests ?? [];
  const selectedQuest =
    quests.find((quest) => quest.id === selectedQuestId) ?? quests[0] ?? null;
  const allSteps = useMemo(
    () => quests.flatMap((quest) => quest.steps),
    [quests],
  );
  const currentStepIndex = selectedQuest
    ? Math.min(stepPositions[selectedQuest.id] ?? 0, Math.max(selectedQuest.steps.length - 1, 0))
    : 0;
  const currentStep = selectedQuest?.steps[currentStepIndex] ?? null;
  const globalStepIndex = currentStep
    ? allSteps.findIndex((step) => step.id === currentStep.id)
    : -1;
  const completedQuestCount = quests.filter(
    (quest) => quest.status === "completed",
  ).length;
  const progressPercent =
    allSteps.length > 0 && globalStepIndex >= 0
      ? ((globalStepIndex + 1) / allSteps.length) * 100
      : 0;

  async function createGuide() {
    setCreatingGuide(true);
    setError(null);
    try {
      const guide = await apiRequest<Guide>("/guides/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      setGuides((current) => [...current, guide]);
      setSelectedGuideId(guide.id);
      setSelectedQuestId(null);
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Unable to create a guide."));
    } finally {
      setCreatingGuide(false);
    }
  }

  async function updateQuestStatus(quest: Quest, checked: boolean) {
    const status: QuestStatus = checked ? "completed" : "not_started";
    setUpdatingQuestId(quest.id);
    setError(null);
    try {
      const updatedQuest = await apiRequest<Quest>(`/quests/${quest.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      setGuides((currentGuides) =>
        currentGuides.map((guide) => ({
          ...guide,
          quests: guide.quests.map((item) =>
            item.id === updatedQuest.id ? updatedQuest : item,
          ),
        })),
      );
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Unable to update quest status."));
    } finally {
      setUpdatingQuestId(null);
    }
  }

  async function createQuest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedGuide) return;

    setSavingContent(true);
    setError(null);
    try {
      const quest = await apiRequest<Quest>("/quests/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          guide_id: selectedGuide.id,
          position: quests.length + 1,
          title: questTitle.trim(),
          description: questDescription.trim(),
          completion_criteria: completionCriteria.trim() || questTitle.trim(),
          steps: [],
        }),
      });
      setGuides((currentGuides) =>
        currentGuides.map((guide) =>
          guide.id === selectedGuide.id
            ? { ...guide, quests: [...guide.quests, quest] }
            : guide,
        ),
      );
      setSelectedQuestId(quest.id);
      setQuestTitle("");
      setQuestDescription("");
      setCompletionCriteria("");
      setShowQuestForm(false);
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Unable to create a quest."));
    } finally {
      setSavingContent(false);
    }
  }

  async function createStep(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedQuest) return;

    setSavingContent(true);
    setError(null);
    try {
      const step = await apiRequest<Step>(
        `/quests/${selectedQuest.id}/steps/`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            position: selectedQuest.steps.length + 1,
            title: stepTitle.trim(),
            description: stepDescription.trim(),
          }),
        },
      );
      setGuides((currentGuides) =>
        currentGuides.map((guide) => ({
          ...guide,
          quests: guide.quests.map((quest) =>
            quest.id === selectedQuest.id
              ? { ...quest, steps: [...quest.steps, step] }
              : quest,
          ),
        })),
      );
      setStepPositions((current) => ({ ...current, [selectedQuest.id]: 0 }));
      setStepTitle("");
      setStepDescription("");
      setShowStepForm(false);
    } catch (requestError) {
      setError(getErrorMessage(requestError, "Unable to create a step."));
    } finally {
      setSavingContent(false);
    }
  }

  function selectGuide(guideId: number) {
    setSelectedGuideId(guideId);
    setSelectedQuestId(null);
  }

  function selectQuest(questId: number) {
    setSelectedQuestId(questId);
  }

  function changeStep(direction: -1 | 1) {
    if (!selectedQuest) return;
    const nextIndex = Math.max(
      0,
      Math.min(currentStepIndex + direction, selectedQuest.steps.length - 1),
    );
    setStepPositions((current) => ({ ...current, [selectedQuest.id]: nextIndex }));
  }

  return (
    <main className="app-shell">
      <AppHeader />

      <div className="workspace">
        <GuideSidebar
          guides={guides}
          selectedGuideId={selectedGuideId}
          loading={loading}
          creatingGuide={creatingGuide}
          onCreateGuide={() => void createGuide()}
          onSelectGuide={selectGuide}
        />

        <section className="content">
          {error && (
            <div className="error-banner" role="alert">
              {error}
              <button type="button" aria-label="Dismiss error" onClick={() => setError(null)}>
                ×
              </button>
            </div>
          )}

          {loading ? (
            <div className="center-state">Loading your guidebook…</div>
          ) : !selectedGuide ? (
            <div className="welcome-state">
              <div className="welcome-icon" aria-hidden="true">✦</div>
              <p className="eyebrow">WELCOME TO YOUR GUIDEBOOK</p>
              <h2>Start a new adventure</h2>
              <p>Create a guide to organize quests and follow every step.</p>
              <button
                className="primary-button"
                type="button"
                disabled={creatingGuide}
                onClick={() => void createGuide()}
              >
                {creatingGuide ? "Creating…" : "Create a guide"}
              </button>
            </div>
          ) : (
            <>
              <div className="page-heading">
                <div>
                  <p className="eyebrow">YOUR ADVENTURE</p>
                  <h2>Guide {selectedGuide.id}</h2>
                  <p className="page-subtitle">
                    {quests.length === 0
                      ? "Your quests will appear here."
                      : `${completedQuestCount} of ${quests.length} quests completed`}
                  </p>
                </div>
                <div className="quest-count-badge">
                  <span>{quests.length}</span>
                  <span>{quests.length === 1 ? "QUEST" : "QUESTS"}</span>
                </div>
              </div>

              {allSteps.length > 0 && (
                <section className="progress-panel" aria-label="Guide progress">
                  <div className="progress-meta">
                    <span>GUIDE PROGRESS</span>
                    <span>
                      {globalStepIndex >= 0 ? globalStepIndex + 1 : 0}/{allSteps.length} steps
                    </span>
                  </div>
                  <div
                    className="progress-track"
                    role="progressbar"
                    aria-label="Guide step progress"
                    aria-valuemin={0}
                    aria-valuemax={allSteps.length}
                    aria-valuenow={globalStepIndex >= 0 ? globalStepIndex + 1 : 0}
                  >
                    <span style={{ width: `${progressPercent}%` }} />
                  </div>
                </section>
              )}

              <div className="guide-layout">
                <QuestPanel
                  quests={quests}
                  selectedQuestId={selectedQuest?.id ?? null}
                  showQuestForm={showQuestForm}
                  questTitle={questTitle}
                  questDescription={questDescription}
                  completionCriteria={completionCriteria}
                  savingContent={savingContent}
                  updatingQuestId={updatingQuestId}
                  onToggleQuestForm={() => setShowQuestForm((shown) => !shown)}
                  onQuestTitleChange={setQuestTitle}
                  onQuestDescriptionChange={setQuestDescription}
                  onCompletionCriteriaChange={setCompletionCriteria}
                  onCreateQuest={(event) => void createQuest(event)}
                  onUpdateQuestStatus={(quest, checked) =>
                    void updateQuestStatus(quest, checked)
                  }
                  onSelectQuest={selectQuest}
                />

                <QuestReader
                  selectedQuest={selectedQuest}
                  questNumber={selectedQuest ? quests.indexOf(selectedQuest) + 1 : 0}
                  currentStep={currentStep}
                  currentStepIndex={currentStepIndex}
                  showStepForm={showStepForm}
                  stepTitle={stepTitle}
                  stepDescription={stepDescription}
                  savingContent={savingContent}
                  onChangeStep={changeStep}
                  onToggleStepForm={() => setShowStepForm((shown) => !shown)}
                  onStepTitleChange={setStepTitle}
                  onStepDescriptionChange={setStepDescription}
                  onCreateStep={(event) => void createStep(event)}
                />
              </div>
            </>
          )}
        </section>
      </div>
    </main>
  );
}
