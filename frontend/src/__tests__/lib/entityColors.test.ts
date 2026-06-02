import { describe, expect, it, beforeEach } from 'vitest';
import {
  buildEntityLegendPayload,
  getEntityColor,
  normalizeEntityKey,
  orderEntitiesForDisplay,
} from '@/lib/entityColors';
import { useVisualIdentityStore } from '@/stores/visualIdentityStore';

describe('entityColors (session visual identity)', () => {
  beforeEach(() => {
    useVisualIdentityStore.getState().reset();
    useVisualIdentityStore.getState().bindSession('test-session');
  });

  it('normalizes keys for lookup', () => {
    expect(normalizeEntityKey('  Qdrant ')).toBe('qdrant');
    expect(normalizeEntityKey('Pine-Cone')).toBe('pine-cone');
  });

  it('returns stable session colors for the same entity', () => {
    useVisualIdentityStore.getState().ensureEntities(['qdrant', 'pinecone'], ['qdrant', 'pinecone']);
    const a = getEntityColor('qdrant');
    const b = getEntityColor('qdrant');
    expect(a).toBe(b);
  });

  it('assigns distinct colors by ranking order', () => {
    useVisualIdentityStore.getState().ensureEntities(
      ['milvus', 'qdrant', 'weaviate'],
      ['qdrant', 'weaviate', 'milvus']
    );
    const q = getEntityColor('qdrant');
    const w = getEntityColor('weaviate');
    const m = getEntityColor('milvus');
    expect(q).not.toBe(w);
    expect(w).not.toBe(m);
  });

  it('orders entities by ranking then remainder', () => {
    expect(
      orderEntitiesForDisplay(['milvus', 'qdrant', 'weaviate'], ['qdrant', 'weaviate', 'pinecone', 'milvus'])
    ).toEqual(['qdrant', 'weaviate', 'pinecone', 'milvus']);
  });

  it('keeps legend colors aligned with ranking chips', () => {
    const ranking = ['qdrant', 'weaviate', 'pinecone', 'milvus'];
    const modules = ['milvus', 'pinecone', 'weaviate', 'qdrant'];
    const order = orderEntitiesForDisplay(modules, ranking);
    const legend = buildEntityLegendPayload(modules, ranking);

    expect(legend.map((l) => l.id)).toEqual(order);
    for (const slug of ranking) {
      const chipColor = getEntityColor(slug);
      const legendEntry = legend.find((l) => l.id === slug);
      expect(legendEntry?.color).toBe(chipColor);
    }
  });
});
