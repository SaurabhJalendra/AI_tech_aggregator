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
  pendingRender: {
    command: PanelCommand;
    timeout: ReturnType<typeof setTimeout>;
  } | null;

  // Actions
  renderPanel: (command: PanelCommand) => void;
  appendNode: (node: ArchNode) => void;
  appendEdge: (edge: ArchEdge) => void;
  highlightNode: (nodeId: string) => void;
  goBack: () => void;
  clearPanel: () => void;
  clearCodeDrawer: () => void;
  setPanel: (panel: PanelType, data?: Record<string, unknown>, title?: string) => void;
}

export const usePanelStore = create<PanelState>((set, get) => ({
  currentPanel: 'welcome',
  panelData: {},
  panelTitle: undefined,
  panelHistory: [],
  pendingRender: null,

  renderPanel: (command: PanelCommand) => {
    if (command.action === 'clear') {
      const { pendingRender } = get();
      if (pendingRender) clearTimeout(pendingRender.timeout);
      set({
        currentPanel: 'welcome',
        panelData: {},
        panelTitle: undefined,
        pendingRender: null,
      });
      return;
    }

    if (command.action === 'update') {
      const { pendingRender } = get();
      if (pendingRender && pendingRender.command.panel === command.panel) {
        clearTimeout(pendingRender.timeout);
        commitRender(pendingRender.command);
      }

      if (get().currentPanel !== command.panel) return;

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

    // action === 'render' — debounce so rapid multi-render streams settle on the last panel.
    const { pendingRender } = get();
    if (pendingRender) clearTimeout(pendingRender.timeout);

    const timeout = setTimeout(() => {
      commitRender(command);
    }, 80);

    set({ pendingRender: { command, timeout } });

    function commitRender(renderCommand: PanelCommand) {
      const state = get();
      set({
        panelHistory: [
          ...state.panelHistory,
          {
            panel: state.currentPanel,
            data: state.panelData,
            title: state.panelTitle,
          },
        ],
        currentPanel: renderCommand.panel,
        panelData: renderCommand.data,
        panelTitle: renderCommand.title,
        pendingRender: null,
      });
    }
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
    const { panelHistory, pendingRender } = get();
    if (pendingRender) clearTimeout(pendingRender.timeout);
    if (panelHistory.length === 0) {
      set({
        currentPanel: 'welcome',
        panelData: {},
        panelTitle: undefined,
        pendingRender: null,
      });
      return;
    }

    const previous = panelHistory[panelHistory.length - 1];
    set({
      currentPanel: previous.panel,
      panelData: previous.data,
      panelTitle: previous.title,
      panelHistory: panelHistory.slice(0, -1),
      pendingRender: null,
    });
  },

  clearPanel: () => {
    const { pendingRender } = get();
    if (pendingRender) clearTimeout(pendingRender.timeout);
    set({
      currentPanel: 'welcome',
      panelData: {},
      panelTitle: undefined,
      panelHistory: [],
      pendingRender: null,
    });
  },

  clearCodeDrawer: () => {
    set((state) => {
      if (!state.panelData.codeDrawer) return state;
      const { codeDrawer: _removed, ...rest } = state.panelData;
      return { panelData: rest };
    });
  },

  setPanel: (panel: PanelType, data: Record<string, unknown> = {}, title?: string) => {
    const { currentPanel, panelData, panelTitle, pendingRender } = get();
    if (pendingRender) clearTimeout(pendingRender.timeout);

    set({
      panelHistory: [
        ...get().panelHistory,
        { panel: currentPanel, data: panelData, title: panelTitle },
      ],
      currentPanel: panel,
      panelData: data,
      panelTitle: title,
      pendingRender: null,
    });
  },
}));
