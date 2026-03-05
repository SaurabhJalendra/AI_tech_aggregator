import { create } from 'zustand';
import type { PanelType, PanelCommand } from '@/types/chat';

interface PanelHistoryEntry {
  panel: PanelType;
  data: Record<string, unknown>;
  title?: string;
}

interface PanelState {
  currentPanel: PanelType;
  panelData: Record<string, unknown>;
  panelTitle: string | undefined;
  panelHistory: PanelHistoryEntry[];

  // Actions
  renderPanel: (command: PanelCommand) => void;
  goBack: () => void;
  clearPanel: () => void;
  setPanel: (panel: PanelType, data?: Record<string, unknown>, title?: string) => void;
}

export const usePanelStore = create<PanelState>((set, get) => ({
  currentPanel: 'welcome',
  panelData: {},
  panelTitle: undefined,
  panelHistory: [],

  renderPanel: (command: PanelCommand) => {
    const { currentPanel, panelData, panelTitle } = get();

    if (command.action === 'clear') {
      set({
        currentPanel: 'welcome',
        panelData: {},
        panelTitle: undefined,
      });
      return;
    }

    if (command.action === 'update') {
      // Merge new data into current panel data
      set((state) => ({
        panelData: { ...state.panelData, ...command.data },
        panelTitle: command.title || state.panelTitle,
      }));
      return;
    }

    // action === 'render' — push current panel onto history and switch
    set({
      panelHistory: [
        ...get().panelHistory,
        { panel: currentPanel, data: panelData, title: panelTitle },
      ],
      currentPanel: command.panel,
      panelData: command.data,
      panelTitle: command.title,
    });
  },

  goBack: () => {
    const { panelHistory } = get();
    if (panelHistory.length === 0) {
      set({
        currentPanel: 'welcome',
        panelData: {},
        panelTitle: undefined,
      });
      return;
    }

    const previous = panelHistory[panelHistory.length - 1];
    set({
      currentPanel: previous.panel,
      panelData: previous.data,
      panelTitle: previous.title,
      panelHistory: panelHistory.slice(0, -1),
    });
  },

  clearPanel: () => {
    set({
      currentPanel: 'welcome',
      panelData: {},
      panelTitle: undefined,
      panelHistory: [],
    });
  },

  setPanel: (panel: PanelType, data: Record<string, unknown> = {}, title?: string) => {
    const { currentPanel, panelData, panelTitle } = get();

    set({
      panelHistory: [
        ...get().panelHistory,
        { panel: currentPanel, data: panelData, title: panelTitle },
      ],
      currentPanel: panel,
      panelData: data,
      panelTitle: title,
    });
  },
}));
