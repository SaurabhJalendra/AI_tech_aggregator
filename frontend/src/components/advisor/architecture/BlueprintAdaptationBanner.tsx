'use client';

interface BlueprintAdaptationBannerProps {
  message: string;
  onDismiss?: () => void;
}

export default function BlueprintAdaptationBanner({
  message,
  onDismiss,
}: BlueprintAdaptationBannerProps) {
  return (
    <div
      className="flex shrink-0 items-start justify-between gap-3 border-b border-[var(--accent)]/25 bg-[var(--accent-muted)]/35 px-4 py-2.5 md:px-5"
      role="status"
    >
      <div className="min-w-0">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-[var(--accent)]">
          Architecture updated
        </p>
        <p className="mt-0.5 text-sm text-[var(--text-secondary)]">{message}</p>
      </div>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="shrink-0 rounded-md px-2 py-1 text-xs text-[var(--text-muted)] hover:bg-[var(--surface-hover)]"
        >
          Dismiss
        </button>
      )}
    </div>
  );
}
