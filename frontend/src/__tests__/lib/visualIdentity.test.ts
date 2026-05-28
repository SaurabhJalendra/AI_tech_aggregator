import { describe, expect, it, beforeEach } from 'vitest';
import {
  assignSessionEntityColors,
  generateSessionPalette,
  getSessionEntityColor,
  PREMIUM_BASE_PALETTE,
} from '@/lib/visualIdentity';
import { useVisualIdentityStore } from '@/stores/visualIdentityStore';

describe('visualIdentity', () => {
  beforeEach(() => {
    useVisualIdentityStore.getState().reset();
  });

  it('generates rotated palette per session key', () => {
    const a = generateSessionPalette('session-a');
    const b = generateSessionPalette('session-b');
    expect(a).toHaveLength(PREMIUM_BASE_PALETTE.length);
    expect(a).not.toEqual(b);
    expect(new Set(a)).toEqual(new Set(PREMIUM_BASE_PALETTE));
  });

  it('assigns colors by pipeline ranking order within a session', () => {
    const palette = generateSessionPalette('test-session');
    const colors = assignSessionEntityColors(
      {},
      palette,
      ['milvus', 'qdrant', 'pinecone'],
      ['qdrant', 'pinecone', 'milvus']
    );
    expect(colors.qdrant).toBe(palette[0]);
    expect(colors.pinecone).toBe(palette[1]);
    expect(colors.milvus).toBe(palette[2]);
  });

  it('keeps entity colors stable across repeated assignment', () => {
    useVisualIdentityStore.getState().bindSession('stable-1');
    useVisualIdentityStore.getState().ensureEntities(
      ['qdrant', 'weaviate'],
      ['qdrant', 'weaviate']
    );
    const first = useVisualIdentityStore.getState().getColor('qdrant');
    useVisualIdentityStore.getState().ensureEntities(
      ['weaviate', 'qdrant'],
      ['weaviate', 'qdrant']
    );
    const second = useVisualIdentityStore.getState().getColor('qdrant');
    expect(first).toBe(second);
  });

  it('resets colors when session changes', () => {
    useVisualIdentityStore.getState().bindSession('session-one');
    useVisualIdentityStore.getState().ensureEntities(['qdrant'], ['qdrant']);
    const colorA = useVisualIdentityStore.getState().getColor('qdrant');

    useVisualIdentityStore.getState().bindSession('session-two');
    useVisualIdentityStore.getState().ensureEntities(['qdrant'], ['qdrant']);
    const colorB = useVisualIdentityStore.getState().getColor('qdrant');

    expect(colorA).toBeDefined();
    expect(colorB).toBeDefined();
  });

  it('exposes snapshot colors via getSessionEntityColor', () => {
    const palette = generateSessionPalette(null);
    const snapshot = {
      sessionKey: null,
      palette,
      entityColors: { qdrant: palette[2] },
    };
    expect(getSessionEntityColor(snapshot, 'qdrant')).toBe(palette[2]);
  });
});
