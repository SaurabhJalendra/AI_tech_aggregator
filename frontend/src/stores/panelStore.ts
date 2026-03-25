import { create } from 'zustand';
import type { PanelType, PanelCommand, ArchNode, ArchEdge } from '@/types/chat';

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
  appendNode: (node: ArchNode) => void;
  appendEdge: (edge: ArchEdge) => void;
  highlightNode: (nodeId: string) => void;
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
      const subAction = command.data?.subAction as string | undefined;
      if (subAction === 'add_node' && command.data.node) {
        get().appendNode(command.data.node as ArchNode);
      } else if (subAction === 'add_edge' && command.data.edge) {
        get().appendEdge(command.data.edge as ArchEdge);
      } else if (subAction === 'highlight' && command.data.nodeId) {
        get().highlightNode(command.data.nodeId as string);
      } else {
        // Generic data merge
        set((state) => ({
          panelData: { ...state.panelData, ...command.data },
          panelTitle: command.title || state.panelTitle,
        }));
      }
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

  appendNode: (node: ArchNode) => {
    set((state) => {
      const nodes = (state.panelData.nodes as ArchNode[]) || [];
      // Don't add duplicate nodes
      if (nodes.some((n) => n.id === node.id)) return state;
      return {
        panelData: {
          ...state.panelData,
          nodes: [...nodes, node],
        },
      };
    });
  },

  appendEdge: (edge: ArchEdge) => {
    set((state) => {
      const edges = (state.panelData.edges as ArchEdge[]) || [];
      return {
        panelData: {
          ...state.panelData,
          edges: [...edges, edge],
        },
      };
    });
  },

  highlightNode: (nodeId: string) => {
    set((state) => ({
      panelData: {
        ...state.panelData,
        highlightedNode: nodeId,
      },
    }));
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
