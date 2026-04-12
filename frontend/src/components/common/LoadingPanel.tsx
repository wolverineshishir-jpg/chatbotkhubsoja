type LoadingPanelProps = {
  message?: string;
  hint?: string;
  compact?: boolean;
  fullscreen?: boolean;
};

export function LoadingPanel({
  message = "Loading data...",
  hint = "Please wait while we prepare this view.",
  compact = false,
  fullscreen = false,
}: LoadingPanelProps) {
  const panel = (
    <div
      className={`panel loading-panel ${compact ? "loading-panel-compact" : ""}`.trim()}
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <div className="loading-panel-head">
        <span className="loading-panel-orb" aria-hidden="true" />
        <div>
          <strong>{message}</strong>
          <p>{hint}</p>
        </div>
      </div>
      <div className="loading-panel-skeleton" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
    </div>
  );

  if (!fullscreen) {
    return panel;
  }

  return <div className="loading-panel-shell">{panel}</div>;
}
