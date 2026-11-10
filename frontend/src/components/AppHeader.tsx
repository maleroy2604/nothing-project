interface AppHeaderProps {
  theme: "dark" | "light";
  onToggleTheme: () => void;
}

export default function AppHeader({ theme, onToggleTheme }: AppHeaderProps) {
  return (
    <header className="topbar">
      <a className="brand" href="/" aria-label="Guidebook home">
        <span className="brand-mark">G</span>
        <span>Guidebook</span>
      </a>
      <div className="topbar-actions">
        <span className="topbar-caption">Your adventures, one step at a time</span>
        <button
          className="theme-toggle"
          type="button"
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
          title={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
          onClick={onToggleTheme}
        >
          <span aria-hidden="true">{theme === "dark" ? "☀" : "☾"}</span>
          <span>{theme === "dark" ? "Light" : "Dark"}</span>
        </button>
      </div>
    </header>
  );
}
