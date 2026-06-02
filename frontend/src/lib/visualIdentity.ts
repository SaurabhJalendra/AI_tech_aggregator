/**

 * Session-scoped visual identity — muted tonal families for calm comparison UI.

 * Frontend-only — backend supplies rankings/scores, not colors.

 */



import { normalizeEntityKey, orderEntitiesForDisplay } from '@/lib/entityDisplay';



/** Muted tonal palette — dusty, harmonious, non-neon. */

export const PREMIUM_BASE_PALETTE = [

  '#7c8db5', // dusty blue

  '#6f9f9a', // muted teal

  '#c4a484', // warm sand

  '#9d8fb8', // lavender gray

  '#7d98a1', // soft slate cyan

  '#b78b7a', // clay coral

  '#8fa97b', // sage green

  '#a4a0b8', // muted stone purple

] as const;



/** Default opacities — subtle atmospheric emphasis only. */

export const ENTITY_GLOW_ALPHA = 0.08;

export const ENTITY_MUTED_ALPHA = 0.1;

export const ENTITY_CHIP_BG_ALPHA = 0.12;

export const ENTITY_CHIP_BORDER_ALPHA = 0.18;



export type EntityColorMap = Record<string, string>;



export interface VisualIdentitySnapshot {

  sessionKey: string | null;

  palette: string[];

  entityColors: EntityColorMap;

}



function stableHash(key: string): number {

  let h = 0;

  for (let i = 0; i < key.length; i += 1) {

    h = (Math.imul(31, h) + key.charCodeAt(i)) >>> 0;

  }

  return h;

}



function parseHex(hex: string): { r: number; g: number; b: number } | null {

  const raw = hex.replace('#', '').trim();

  if (raw.length !== 6) return null;

  const n = Number.parseInt(raw, 16);

  if (Number.isNaN(n)) return null;

  return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };

}



function toHex(r: number, g: number, b: number): string {

  const clamp = (v: number) => Math.max(0, Math.min(255, Math.round(v)));

  return `#${[clamp(r), clamp(g), clamp(b)]

    .map((c) => c.toString(16).padStart(2, '0'))

    .join('')}`;

}



export function generateSessionPalette(sessionKey: string | null): string[] {

  const base = [...PREMIUM_BASE_PALETTE];

  if (!sessionKey) return base;

  const offset = stableHash(sessionKey) % base.length;

  return [...base.slice(offset), ...base.slice(0, offset)];

}



function paletteIndexForEntity(

  entityId: string,

  ranking: string[] | undefined,

  paletteLength: number

): number {

  const key = normalizeEntityKey(entityId);

  if (ranking?.length) {

    const normalizedRanking = ranking.map(normalizeEntityKey);

    const rankIdx = normalizedRanking.indexOf(key);

    if (rankIdx >= 0) return rankIdx % paletteLength;

  }

  return stableHash(key) % paletteLength;

}



export function assignSessionEntityColors(

  entityColors: EntityColorMap,

  palette: string[],

  entities: string[],

  ranking?: string[] | null

): EntityColorMap {

  const order = orderEntitiesForDisplay(entities, ranking ?? undefined);

  let changed = false;

  const next: EntityColorMap = { ...entityColors };



  for (const raw of order) {

    const id = normalizeEntityKey(raw);

    if (!id || next[id]) continue;

    const idx = paletteIndexForEntity(id, ranking?.map(normalizeEntityKey), palette.length);

    next[id] = palette[idx];

    changed = true;

  }



  return changed ? next : entityColors;

}



export function createVisualIdentitySnapshot(sessionKey: string | null): VisualIdentitySnapshot {

  return {

    sessionKey,

    palette: generateSessionPalette(sessionKey),

    entityColors: {},

  };

}



export function getSessionEntityColor(

  snapshot: VisualIdentitySnapshot,

  entityId: string

): string {

  const key = normalizeEntityKey(entityId);

  if (!key) return snapshot.palette[0] ?? PREMIUM_BASE_PALETTE[0];

  return (

    snapshot.entityColors[key] ??

    snapshot.palette[paletteIndexForEntity(key, undefined, snapshot.palette.length)] ??

    PREMIUM_BASE_PALETTE[0]

  );

}



/** Gentle brighten on hover — no neon lift. */

export function getEntityHoverColor(base: string): string {

  const rgb = parseHex(base);

  if (!rgb) return base;

  return toHex(rgb.r * 0.94 + 255 * 0.06, rgb.g * 0.94 + 255 * 0.06, rgb.b * 0.94 + 255 * 0.06);

}



export function getEntityGlowColor(base: string, alpha = ENTITY_GLOW_ALPHA): string {

  const rgb = parseHex(base);

  if (!rgb) return base;

  return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`;

}



export function getEntityMutedColor(base: string, alpha = ENTITY_MUTED_ALPHA): string {

  const rgb = parseHex(base);

  if (!rgb) return base;

  return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`;

}



export function getEntityTextColor(base: string): string {

  const rgb = parseHex(base);

  if (!rgb) return base;

  const luminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255;

  return luminance > 0.58 ? '#1f2937' : base;

}



export function getEntityChipStyleFromColor(base: string): {

  backgroundColor: string;

  color: string;

  borderColor: string;

} {

  return {

    backgroundColor: getEntityMutedColor(base, ENTITY_CHIP_BG_ALPHA),

    color: getEntityTextColor(base),

    borderColor: getEntityMutedColor(base, ENTITY_CHIP_BORDER_ALPHA),

  };

}



export function buildEntityLegendFromSnapshot(

  snapshot: VisualIdentitySnapshot,

  entities: string[],

  ranking?: string[] | null

): Array<{ value: string; type: 'square'; color: string; id: string }> {

  return orderEntitiesForDisplay(entities, ranking ?? undefined).map((slug) => ({

    id: slug,

    value: slug.replace(/_/g, ' '),

    type: 'square' as const,

    color: getSessionEntityColor(snapshot, slug),

  }));

}


