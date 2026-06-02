import { create } from 'zustand';
import {
  assignSessionEntityColors,
  createVisualIdentitySnapshot,
  getEntityChipStyleFromColor,
  getEntityGlowColor,
  getEntityHoverColor,
  getEntityMutedColor,
  getSessionEntityColor,
  type EntityColorMap,
  type VisualIdentitySnapshot,
} from '@/lib/visualIdentity';
import { normalizeEntityKey } from '@/lib/entityDisplay';

interface VisualIdentityState {
  snapshot: VisualIdentitySnapshot;
  bindSession: (sessionKey: string | null) => void;
  ensureEntities: (entities: string[], ranking?: string[] | null) => void;
  reset: () => void;
  getColor: (entityId: string) => string;
  getHoverColor: (entityId: string) => string;
  getGlowColor: (entityId: string) => string;
  getMutedColor: (entityId: string) => string;
  getChipStyle: (entityId: string) => ReturnType<typeof getEntityChipStyleFromColor>;
  getEntityColors: () => EntityColorMap;
}

const initialSnapshot = createVisualIdentitySnapshot(null);

export const useVisualIdentityStore = create<VisualIdentityState>((set, get) => ({
  snapshot: initialSnapshot,

  bindSession: (sessionKey) => {
    const current = get().snapshot.sessionKey;
    if (current === sessionKey) return;
    set({ snapshot: createVisualIdentitySnapshot(sessionKey) });
  },

  ensureEntities: (entities, ranking) => {
    const { snapshot } = get();
    const nextColors = assignSessionEntityColors(
      snapshot.entityColors,
      snapshot.palette,
      entities,
      ranking
    );
    if (nextColors === snapshot.entityColors) return; // same reference when nothing new assigned
    set({
      snapshot: {
        ...snapshot,
        entityColors: nextColors,
      },
    });
  },

  reset: () => {
    set({ snapshot: createVisualIdentitySnapshot(null) });
  },

  /** Read-only — register entities via ensureEntities() during comparison setup. */
  getColor: (entityId) => getSessionEntityColor(get().snapshot, entityId),

  getHoverColor: (entityId) => getEntityHoverColor(get().getColor(entityId)),
  getGlowColor: (entityId) => getEntityGlowColor(get().getColor(entityId)),
  getMutedColor: (entityId) => getEntityMutedColor(get().getColor(entityId)),
  getChipStyle: (entityId) => getEntityChipStyleFromColor(get().getColor(entityId)),
  getEntityColors: () => get().snapshot.entityColors,
}));

/** Non-React access for utilities and Recharts. */
export function getVisualIdentityColor(entityId: string): string {
  return useVisualIdentityStore.getState().getColor(entityId);
}
