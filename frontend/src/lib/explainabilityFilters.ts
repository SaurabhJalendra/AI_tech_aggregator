/** Internal catalog-layer filters — hidden from "Why this recommendation?" */
const INTERNAL_FILTER_MARKERS = [
  'comparison_layer=',
  'mixed abstraction layer',
];

export function isUserVisibleFilterReason(reason: string): boolean {
  const lower = reason.toLowerCase();
  return !INTERNAL_FILTER_MARKERS.some((marker) => lower.includes(marker));
}

export function filterUserVisibleFilters<T extends { reason: string }>(
  items: T[] | undefined | null,
): T[] {
  if (!items?.length) return [];
  return items.filter((item) => isUserVisibleFilterReason(item.reason));
}
