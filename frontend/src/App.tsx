import { useEffect, useState, type FormEvent } from "react";
import QuestList from "./components/QuestList";
import { apiRequest } from "./services/api";
import type { Quest, QuestCreate } from "./types/quest";

export default function App() {
  const [quests, setQuests] = useState<Quest[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadQuests() {
      try {
        setQuests(await apiRequest<Quest[]>("/quests/"));
      } catch (requestError) {
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to load quests.",
        );
      } finally {
        setLoading(false);
      }
    }

    void loadQuests();
  }, []);

  async function addQuest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSaving(true);

    try {
      const data: QuestCreate = { title: title.trim(), description: description.trim() };
      const quest = await apiRequest<Quest>("/quests/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      setQuests((currentQuests) => [...currentQuests, quest]);
      setTitle("");
      setDescription("");
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to add quest.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <main>
      <h1>Quests</h1>
      <form onSubmit={addQuest}>
        <h2>Add a quest</h2>
        <label>
          Title
          <input
            required
            maxLength={200}
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
        </label>
        <label>
          Description
          <textarea
            required
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
        </label>
        <button type="submit" disabled={saving}>
          {saving ? "Adding..." : "Add quest"}
        </button>
      </form>
      {error && <p role="alert">{error}</p>}
      <h2>Your quests</h2>
      {loading ? <p>Loading quests...</p> : <QuestList quests={quests} />}
    </main>
  );
}
