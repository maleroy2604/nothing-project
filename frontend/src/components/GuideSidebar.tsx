import type { Guide } from "../types/quest";
import EditableTitle from "./EditableTitle";

interface GuideSidebarProps {
  guides: Guide[];
  selectedGuideId: number | null;
  loading: boolean;
  creatingGuide: boolean;
  savingContent: boolean;
  onCreateGuide: () => void;
  onSelectGuide: (guideId: number) => void;
  onUpdateGuideTitle: (guide: Guide, title: string) => Promise<boolean>;
  onDeleteGuide: (guide: Guide) => void;
}

export default function GuideSidebar({
  guides,
  selectedGuideId,
  loading,
  creatingGuide,
  savingContent,
  onCreateGuide,
  onSelectGuide,
  onUpdateGuideTitle,
  onDeleteGuide,
}: GuideSidebarProps) {
  return (
    <aside className="sidebar" aria-label="Guides">
      <div className="sidebar-heading">
        <div>
          <p className="eyebrow">YOUR LIBRARY</p>
          <h1>Guides</h1>
        </div>
        <button
          className="icon-button"
          type="button"
          aria-label="Create guide"
          title="Create guide"
          disabled={creatingGuide || savingContent}
          onClick={onCreateGuide}
        >
          +
        </button>
      </div>

      {loading ? (
        <p className="sidebar-message">Loading your guides…</p>
      ) : guides.length === 0 ? (
        <div className="empty-guides">
          <p>Your guide library is empty.</p>
          <button
            className="text-button"
            type="button"
            disabled={creatingGuide}
            onClick={onCreateGuide}
          >
            Create your first guide
          </button>
        </div>
      ) : (
        <nav className="guide-nav">
          {guides.map((guide) => (
            <div
              className={`guide-nav-item${guide.id === selectedGuideId ? " is-active" : ""}`}
              key={guide.id}
            >
              <span className="guide-nav-icon" aria-hidden="true">▤</span>
              <EditableTitle
                className="guide-nav-actions"
                title={guide.title}
                label={`guide ${guide.id}`}
                disabled={creatingGuide}
                onSelect={() => onSelectGuide(guide.id)}
                onSave={(title) => onUpdateGuideTitle(guide, title)}
                onDelete={() => onDeleteGuide(guide)}
              />
              <span className="guide-count">{guide.quests.length}</span>
            </div>
          ))}
        </nav>
      )}
    </aside>
  );
}
