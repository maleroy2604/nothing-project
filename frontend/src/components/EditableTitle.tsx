import { useState, type FormEvent, type KeyboardEvent } from "react";

interface EditableTitleProps {
  title: string;
  label: string;
  className?: string;
  disabled?: boolean;
  onSelect?: () => void;
  onSave: (title: string) => Promise<boolean>;
  onDelete?: () => void;
}

export default function EditableTitle({
  title,
  label,
  className = "",
  disabled = false,
  onSelect,
  onSave,
  onDelete,
}: EditableTitleProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(title);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextTitle = draft.trim();
    if (!nextTitle) return;
    if (nextTitle === title) {
      setEditing(false);
      return;
    }

    if (await onSave(nextTitle)) setEditing(false);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Escape") {
      setDraft(title);
      setEditing(false);
    }
  }

  return (
    <span className={`editable-title ${className}${editing ? " is-editing" : ""}`}>
      {editing ? (
        <form className="editable-title-form" onSubmit={(event) => void save(event)}>
          <input
            autoFocus
            required
            maxLength={200}
            aria-label={`${label} name`}
            value={draft}
            disabled={disabled}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            className="inline-icon-button"
            type="submit"
            aria-label={`Save ${label} name`}
            title={`Save ${label} name`}
            disabled={disabled || !draft.trim()}
          >
            ✓
          </button>
          <button
            className="inline-icon-button"
            type="button"
            aria-label={`Cancel editing ${label} name`}
            title="Cancel"
            disabled={disabled}
            onClick={() => {
              setDraft(title);
              setEditing(false);
            }}
          >
            ×
          </button>
        </form>
      ) : (
        <>
          {onSelect ? (
            <button
              className="editable-title-display"
              type="button"
              onClick={onSelect}
            >
              {title}
            </button>
          ) : (
            <span className="editable-title-display">{title}</span>
          )}
          <button
            className="inline-icon-button"
            type="button"
            aria-label={`Edit ${label} name`}
            title={`Edit ${label} name`}
            disabled={disabled}
            onClick={() => {
              setDraft(title);
              setEditing(true);
            }}
          >
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <path d="M11.8 2.2a1.4 1.4 0 0 1 2 2L6 12l-3 1 1-3 7.8-7.8Z" />
              <path d="M9.8 4.2l2 2" />
            </svg>
          </button>
          {onDelete && (
            <button
              className="inline-icon-button delete-icon-button"
              type="button"
              aria-label={`Delete ${label}`}
              title={`Delete ${label}`}
              disabled={disabled}
              onClick={onDelete}
            >
              <svg viewBox="0 0 16 16" aria-hidden="true">
                <path d="M2.5 4h11M6 4V2.5h4V4m2.5 0-.6 9.5H4.1L3.5 4m3 2.5v4m3-4v4" />
              </svg>
            </button>
          )}
        </>
      )}
    </span>
  );
}
