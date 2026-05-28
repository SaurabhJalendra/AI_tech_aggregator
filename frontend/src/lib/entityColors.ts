/**
 * Entity color accessors — delegates to session visual identity store.
 */

import { formatEntityLabel, normalizeEntityKey, orderEntitiesForDisplay } from '@/lib/entityDisplay';
import {
  buildEntityLegendFromSnapshot,
  getEntityChipStyleFromColor,
  getEntityGlowColor as glowFromBase,
  getEntityMutedColor as mutedFromBase,
} from '@/lib/visualIdentity';
import { useVisualIdentityStore } from '@/stores/visualIdentityStore';

export { formatEntityLabel, normalizeEntityKey, orderEntitiesForDisplay };

export function getEntityColor(slug: string): string {
  return useVisualIdentityStore.getState().getColor(slug);
}

export function getEntityHoverColor(slug: string): string {
  return useVisualIdentityStore.getState().getHoverColor(slug);
}

export function getEntityGlowColor(slug: string, alpha?: number): string {
  const base = useVisualIdentityStore.getState().getColor(slug);
  return glowFromBase(base, alpha);
}

export function getEntityMutedColor(slug: string, alpha?: number): string {
  const base = useVisualIdentityStore.getState().getColor(slug);
  return mutedFromBase(base, alpha);
}

export function getEntityChipStyle(slug: string): {
  backgroundColor: string;
  color: string;
  borderColor: string;
} {
  return useVisualIdentityStore.getState().getChipStyle(slug);
}

export function buildEntityLegendPayload(
  entities: string[],
  ranking?: string[] | null
): Array<{ value: string; type: 'square'; color: string; id: string }> {
  useVisualIdentityStore.getState().ensureEntities(entities, ranking);
  const snapshot = useVisualIdentityStore.getState().snapshot;
  return buildEntityLegendFromSnapshot(snapshot, entities, ranking).map((entry) => ({
    ...entry,
    value: formatEntityLabel(entry.id),
  }));
}

export { getEntityChipStyleFromColor };
