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
      {currentPanel !== 'welcome' && (
        <div className="flex items-center gap-3 border-b border-gray-200 px-6 py-3 dark:border-gray-800">
          {panelHistory.length > 0 && (
            <button
              onClick={goBack}
              className="rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-800 dark:hover:text-gray-300"
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
      <div className="flex-1 overflow-y-auto">
        {renderPanel(currentPanel)}
      </div>
    </div>
  );
}
