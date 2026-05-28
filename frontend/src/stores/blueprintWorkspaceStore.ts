import { create } from 'zustand';

interface BlueprintWorkspaceState {
  focusMode: boolean;
  chatCollapsed: boolean;
  toggleFocusMode: () => void;
  setFocusMode: (on: boolean) => void;
  setChatCollapsed: (on: boolean) => void;
}

export const useBlueprintWorkspaceStore = create<BlueprintWorkspaceState>((set) => ({
  focusMode: false,
  chatCollapsed: false,
  toggleFocusMode: () =>
    set((s) => ({
      focusMode: !s.focusMode,
      chatCollapsed: !s.focusMode ? true : s.chatCollapsed,
    })),
  setFocusMode: (on) =>
    set({
      focusMode: on,
      chatCollapsed: on,
    }),
  setChatCollapsed: (on) => set({ chatCollapsed: on }),
}));
