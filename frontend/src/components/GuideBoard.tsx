import { useState, type DragEvent } from "react";
import type { Guide, GuideBoardColumn } from "../types/quest";

const columns: { id: GuideBoardColumn; label: string }[] = [
  { id: "backlog", label: "Backlog" },
  { id: "daily", label: "Daily" },
  { id: "weekly", label: "Weekly" },
  { id: "in_progress", label: "In Progress" },
];

interface GuideBoardProps {
  guides: Guide[];
  updatingGuideIds: ReadonlySet<number>;
  creatingGuide: boolean;
  onCreateGuide: () => void;
  onMoveGuide: (guide: Guide, column: GuideBoardColumn) => void;
  onOpenGuide: (guideId: number) => void;
}

export default function GuideBoard({
  guides,
  updatingGuideIds,
  creatingGuide,
  onCreateGuide,
  onMoveGuide,
  onOpenGuide,
}: GuideBoardProps) {
  const [draggingGuideId, setDraggingGuideId] = useState<number | null>(null);
  const [dragOverColumn, setDragOverColumn] = useState<GuideBoardColumn | null>(null);

  function handleDrop(event: DragEvent<HTMLElement>, column: GuideBoardColumn) {
    event.preventDefault();
    const guideId = Number(event.dataTransfer.getData("text/plain"));
    const guide = guides.find((item) => item.id === guideId);
    if (guide && guide.board_column !== column) onMoveGuide(guide, column);
    setDraggingGuideId(null);
    setDragOverColumn(null);
  }

  return (
    <section className="board-view" aria-label="Guide board">
      <header className="board-heading">
        <div>
          <p className="eyebrow">YOUR WORKSPACE</p>
          <h2>Guide board</h2>
          <p className="page-subtitle">Move guides between your planning frames.</p>
        </div>
        <div className="board-heading-actions">
          <span className="board-total">{guides.length} guides</span>
          <button
            className="primary-button"
            type="button"
            disabled={creatingGuide}
            onClick={onCreateGuide}
          >
            {creatingGuide ? "Creating…" : "New guide"}
          </button>
        </div>
      </header>

      <div className="board-columns">
        {columns.map((column) => {
          const columnGuides = guides.filter(
            (guide) => guide.board_column === column.id,
          );
          return (
            <section
              className={`board-column board-column-${column.id}${dragOverColumn === column.id ? " is-drop-target" : ""}`}
              key={column.id}
              aria-label={`${column.label}: ${columnGuides.length} guides`}
              onDragOver={(event) => {
                event.preventDefault();
                setDragOverColumn(column.id);
              }}
              onDrop={(event) => handleDrop(event, column.id)}
            >
              <header className="board-column-heading">
                <h3>{column.label}</h3>
                <span>{columnGuides.length}</span>
              </header>
              <div className="board-card-list">
                {columnGuides.length === 0 ? (
                  <p className="board-empty">Drop a guide here</p>
                ) : (
                  columnGuides.map((guide) => (
                    <article
                      className={`board-card${draggingGuideId === guide.id ? " is-dragging" : ""}`}
                      key={guide.id}
                      draggable={!updatingGuideIds.has(guide.id)}
                      onDragStart={(event) => {
                        event.dataTransfer.setData("text/plain", String(guide.id));
                        event.dataTransfer.effectAllowed = "move";
                        setDraggingGuideId(guide.id);
                      }}
                      onDragEnd={() => {
                        setDraggingGuideId(null);
                        setDragOverColumn(null);
                      }}
                    >
                      <div className="board-card-topline">
                        <span className="board-card-mark" aria-hidden="true">▤</span>
                        <span>
                          {guide.quests.length} {guide.quests.length === 1 ? "quest" : "quests"}
                        </span>
                      </div>
                      <button
                        className="board-card-title"
                        type="button"
                        onClick={() => onOpenGuide(guide.id)}
                      >
                        {guide.title}
                      </button>
                      <label className="board-move-label">
                        Move to
                        <select
                          aria-label={`Move ${guide.title} to`}
                          value={guide.board_column}
                          disabled={updatingGuideIds.has(guide.id)}
                          onChange={(event) => {
                            const nextColumn = columns.find(
                              (option) => option.id === event.target.value,
                            )?.id;
                            if (nextColumn) onMoveGuide(guide, nextColumn);
                          }}
                        >
                          {columns.map((option) => (
                            <option key={option.id} value={option.id}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      </label>
                    </article>
                  ))
                )}
              </div>
            </section>
          );
        })}
      </div>
    </section>
  );
}
