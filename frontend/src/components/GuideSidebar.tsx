import type { Guide } from "../types/quest";

interface GuideSidebarProps {
  guides: Guide[];
  selectedGuideId: number | null;
  loading: boolean;
  creatingGuide: boolean;
  onCreateGuide: () => void;
  onSelectGuide: (guideId: number) => void;
}

export default function GuideSidebar({
  guides,
  selectedGuideId,
  loading,
  creatingGuide,
  onCreateGuide,
  onSelectGuide,
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
          disabled={creatingGuide}
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
            <button
              className={`guide-nav-item${guide.id === selectedGuideId ? " is-active" : ""}`}
              key={guide.id}
              type="button"
              onClick={() => onSelectGuide(guide.id)}
            >
              <span className="guide-nav-icon" aria-hidden="true">▤</span>
              <span>Guide {guide.id}</span>
              <span className="guide-count">{guide.quests.length}</span>
            </button>
          ))}
        </nav>
      )}
    </aside>
  );
}
