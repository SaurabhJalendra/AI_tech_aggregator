'use client';

import { usePanelStore } from '@/stores/panelStore';
import WelcomePanel from './panels/WelcomePanel';
import ArchitectureDiagram from './panels/ArchitectureDiagram';
import ComparisonTable from './panels/ComparisonTable';
import ComparisonChart from './panels/ComparisonChart';
import CodePreview from './panels/CodePreview';
import OptionCards from './panels/OptionCards';
import InteractiveArchitecture from './panels/InteractiveArchitecture';
import CodeProject from './panels/CodeProject';
import type { PanelType } from '@/types/chat';

/**
 * MainPanel is the right side (70% width) that dynamically renders the
 * appropriate panel based on the current panel state.
 */
export default function MainPanel() {
  const currentPanel = usePanelStore((s) => s.currentPanel);
  const panelData = usePanelStore((s) => s.panelData);
  const panelTitle = usePanelStore((s) => s.panelTitle);
  const panelHistory = usePanelStore((s) => s.panelHistory);
  const goBack = usePanelStore((s) => s.goBack);

  const isBlueprintPanel =
    currentPanel === 'architecture_diagram' || currentPanel === 'interactive_architecture';

  const renderPanel = (panelType: PanelType) => {
    switch (panelType) {
      case 'welcome':
        return <WelcomePanel />;
      case 'architecture_diagram':
        return <ArchitectureDiagram data={panelData} />;
      case 'comparison_table':
        return <ComparisonTable data={panelData} />;
      case 'comparison_chart':
        return <ComparisonChart data={panelData} />;
      case 'code_preview':
        return <CodePreview data={panelData} />;
      case 'module_detail':
        return (
          <div className="p-6">
            <h2 className="text-xl font-semibold">Module Detail</h2>
            <p className="mt-2 text-gray-500">Module detail panel placeholder</p>
          </div>
        );
      case 'recommendation':
        return (
          <div className="p-6">
            <h2 className="text-xl font-semibold">Recommendation</h2>
            <p className="mt-2 text-gray-500">Recommendation panel placeholder</p>
          </div>
        );
      case 'document':
        return (
          <div className="p-6">
            <h2 className="text-xl font-semibold">Document</h2>
            <p className="mt-2 text-gray-500">Document panel placeholder</p>
          </div>
        );
      case 'option_cards':
        return <OptionCards data={panelData} />;
      case 'interactive_architecture':
        return <InteractiveArchitecture data={panelData} />;
      case 'code_project':
        return <CodeProject data={panelData} />;
      default:
        return <WelcomePanel />;
    }
  };

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Panel header with back button and title */}
      {currentPanel !== 'welcome' && !isBlueprintPanel && (
        <div className="flex items-center gap-3 border-b border-[var(--border-subtle)] bg-[var(--surface-panel)] px-6 py-3">
          {panelHistory.length > 0 && (
            <button
              onClick={goBack}
              className="rounded p-1 text-[var(--text-muted)] hover:bg-[var(--surface-hover)] hover:text-[var(--foreground)]"
              aria-label="Go back"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </button>
          )}
          {panelTitle && (
            <h2 className="text-lg font-semibold">{panelTitle}</h2>
          )}
        </div>
      )}

      {/* Panel content */}
      <div
        className={`relative flex-1 bg-[var(--background)] ${
          isBlueprintPanel
            ? 'blueprint-workspace blueprint-workspace-immersive blueprint-workspace-scroll scrollbar-hidden overflow-y-auto overflow-x-hidden'
            : 'scrollbar-hidden overflow-y-auto'
        }`}
      >
        {renderPanel(currentPanel)}
        {isBlueprintPanel && panelHistory.length > 0 && (
          <button
            type="button"
            onClick={goBack}
            className="blueprint-floating-back absolute left-3 top-3 z-30 rounded-lg border border-[var(--border-subtle)] bg-[var(--surface-panel)]/95 px-2.5 py-1.5 text-xs font-medium text-[var(--text-secondary)] shadow-[var(--shadow-soft)] backdrop-blur-sm hover:bg-[var(--surface-hover)] hover:text-[var(--foreground)]"
            aria-label="Go back"
          >
            ← Back
          </button>
        )}
      </div>
    </div>
  );
}
