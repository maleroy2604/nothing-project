import { useState, type FormEvent } from "react";

interface GuideCreateDialogProps {
  creating: boolean;
  error: string | null;
  onClose: () => void;
  onSubmit: (title: string) => Promise<boolean>;
}

export default function GuideCreateDialog({
  creating,
  error,
  onClose,
  onSubmit,
}: GuideCreateDialogProps) {
  const [title, setTitle] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedTitle = title.trim();
    if (!trimmedTitle || creating) return;
    await onSubmit(trimmedTitle);
  }

  return (
    <div className="guide-create-backdrop">
      <form
        className="guide-create-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="guide-create-title"
        onSubmit={(event) => void submit(event)}
      >
        <div className="guide-create-heading">
          <p className="eyebrow">NEW LEARNING GUIDE</p>
          <h2 id="guide-create-title">What would you like to learn?</h2>
          <p>
            Give your guide a name or topic. Ollama will draft it and review it
            before it is added to your library.
          </p>
        </div>
        <label className="guide-create-label" htmlFor="guide-create-name">
          Guide name or learning topic
        </label>
        <input
          id="guide-create-name"
          className="guide-create-input"
          autoFocus
          required
          maxLength={200}
          placeholder="e.g. Build a strong foundation in Python"
          value={title}
          disabled={creating}
          onChange={(event) => setTitle(event.target.value)}
        />
        {error && <p className="guide-create-error" role="alert">{error}</p>}
        <div className="guide-create-actions">
          <button
            className="secondary-button"
            type="button"
            disabled={creating}
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            className="primary-button"
            type="submit"
            disabled={creating || !title.trim()}
          >
            {creating ? "Generating and reviewing..." : "Generate guide"}
          </button>
        </div>
      </form>
    </div>
  );
}
