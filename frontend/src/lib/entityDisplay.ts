/** Shared entity key normalization and display ordering (no color deps). */

export const SLUG_SAFE = /[^a-z0-9_-]/g;

export function normalizeEntityKey(slug: string): string {
  return slug.trim().toLowerCase().replace(SLUG_SAFE, '_').replace(/_+/g, '_');
}

export function formatEntityLabel(slug: string): string {
  return normalizeEntityKey(slug).replace(/_/g, ' ');
}

export function orderEntitiesForDisplay(
  entities: string[],
  ranking?: string[] | null
): string[] {
  const seen = new Set<string>();
  const ordered: string[] = [];

  const push = (slug: string) => {
    const key = normalizeEntityKey(slug);
    if (!key || seen.has(key)) return;
    seen.add(key);
    ordered.push(key);
  };

  if (ranking?.length) {
    for (const slug of ranking) {
      push(slug);
    }
  }

  for (const slug of entities) {
    push(slug);
  }

  return ordered;
}
