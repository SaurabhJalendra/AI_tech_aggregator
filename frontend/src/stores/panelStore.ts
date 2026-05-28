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

  renderPanel: (command: PanelCommand) => void;
  appendNode: (node: ArchNode) => void;
  appendEdge: (edge: ArchEdge) => void;
  highlightNode: (nodeId: string) => void;
  goBack: () => void;
  clearPanel: () => void;
  clearCodeDrawer: () => void;
  setPanel: (panel: PanelType, data?: Record<string, unknown>, title?: string) => void;
}

const RENDER_DEBOUNCE_MS = 80;

function cancelPendingRender(pending: PanelState['pendingRender']) {
  if (pending) clearTimeout(pending.timeout);
}

export const usePanelStore = create<PanelState>((set, get) => {
  /** Commit a pending debounced render exactly once (guards duplicate history pushes). */
  function flushPendingRenderOnce(): boolean {
    const state = get();
    const pending = state.pendingRender;
    if (!pending) return false;

    cancelPendingRender(pending);

    set({
      panelHistory: [
        ...state.panelHistory,
        {
          panel: state.currentPanel,
          data: state.panelData,
          title: state.panelTitle,
        },
      ],
      currentPanel: pending.command.panel,
      panelData: pending.command.data ?? {},
      panelTitle: pending.command.title,
      pendingRender: null,
    });
    return true;
  }

  return {
    currentPanel: 'welcome',
    panelData: {},
    panelTitle: undefined,
    panelHistory: [],
    pendingRender: null,

    renderPanel: (command: PanelCommand) => {
      if (command.action === 'clear') {
        cancelPendingRender(get().pendingRender);
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
          flushPendingRenderOnce();
        }

        if (get().currentPanel !== command.panel) return;

        const subAction = command.data?.subAction as string | undefined;
        if (subAction === 'add_node' && command.data?.node) {
          get().appendNode(command.data.node as ArchNode);
        } else if (subAction === 'add_edge' && command.data?.edge) {
          get().appendEdge(command.data.edge as ArchEdge);
        } else if (subAction === 'highlight' && command.data?.nodeId) {
          get().highlightNode(command.data.nodeId as string);
        } else {
          set((state) => ({
            panelData: { ...state.panelData, ...command.data },
            panelTitle: command.title || state.panelTitle,
          }));
        }
        return;
      }

      // action === 'render' — debounce; only the last render in a burst commits once.
      cancelPendingRender(get().pendingRender);

      const captured = command;
      const timeout = setTimeout(() => {
        const pending = get().pendingRender;
        if (!pending || pending.command !== captured) return;
        flushPendingRenderOnce();
      }, RENDER_DEBOUNCE_MS);

      set({ pendingRender: { command: captured, timeout } });
    },

    appendNode: (node: ArchNode) => {
      set((state) => {
        const nodes = (state.panelData.nodes as ArchNode[]) || [];
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
      cancelPendingRender(pendingRender);
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
      cancelPendingRender(get().pendingRender);
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
      cancelPendingRender(get().pendingRender);
      const { currentPanel, panelData, panelTitle, panelHistory } = get();

      set({
        panelHistory: [
          ...panelHistory,
          { panel: currentPanel, data: panelData, title: panelTitle },
        ],
        currentPanel: panel,
        panelData: data,
        panelTitle: title,
        pendingRender: null,
      });
    },
  };
});
