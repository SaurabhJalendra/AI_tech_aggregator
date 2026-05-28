import type {
  ArchitectureComparisonBaseline,
  ArchitectureConsultingPayload,
  ArchEdge,
  ArchNode,
} from '@/types/chat';
import { parseArchitectureConsulting } from '@/lib/architectureConsultingPayload';
import type { CodeBlockData } from '@/components/advisor/panels/CodeBlock';
import { SIMPLE_VIEW_CATEGORIES } from '@/lib/architectureStages';

export interface ParsedArchitecture {
  nodes: ArchNode[];
  edges: ArchEdge[];
  title: string;
  highlightedNode?: string;
  codeDrawer?: CodeBlockData;
  layoutDirection: 'horizontal' | 'vertical';
  selections?: Record<string, string>;
  shortlistSlugs?: string[];
  architectureConsulting: ArchitectureConsultingPayload | null;
  comparisonBaseline: ArchitectureComparisonBaseline | null;
  simulationActive: boolean;
  strategyMode: 'single' | 'dual';
}

function normalizeEdge(raw: Record<string, unknown>): ArchEdge | null {
  const from = (raw.from ?? raw.source) as string | undefined;
  const to = (raw.to ?? raw.target) as string | undefined;
  if (!from || !to) return null;
  return {
    from,
    to,
    label: raw.label as string | undefined,
  };
}

export function parseArchitecturePayload(data: Record<string, unknown>): ParsedArchitecture {
  const rawNodes = (data.nodes as ArchNode[]) || [];
  const rawEdges = Array.isArray(data.edges) ? data.edges : [];
  const edges = rawEdges
    .map((e) => normalizeEdge(e as Record<string, unknown>))
    .filter((e): e is ArchEdge => e != null);

  const layout = (data.layout as string) || 'left-to-right';
  const selections = data.selections as Record<string, string> | undefined;
  const shortlistFromSelections = selections ? Object.values(selections) : undefined;

  return {
    nodes: rawNodes,
    edges,
    title: (data.title as string) || 'Architecture',
    highlightedNode: data.highlightedNode as string | undefined,
    codeDrawer: data.codeDrawer as CodeBlockData | undefined,
    layoutDirection: layout === 'top-to-bottom' ? 'vertical' : 'horizontal',
    selections,
    shortlistSlugs: shortlistFromSelections,
    architectureConsulting: parseArchitectureConsulting(data),
    comparisonBaseline: parseComparisonBaseline(data),
    simulationActive: Boolean(
      (data.architecture_consulting as ArchitectureConsultingPayload | undefined)?.simulation
    ),
    strategyMode: data.strategy_mode === 'dual' ? 'dual' : 'single',
  };
}

function parseComparisonBaseline(
  data: Record<string, unknown>
): ArchitectureComparisonBaseline | null {
  const raw = data.comparison_baseline;
  if (!raw || typeof raw !== 'object') return null;
  const b = raw as ArchitectureComparisonBaseline;
  if (!Array.isArray(b.nodes) || b.nodes.length === 0) return null;
  return b;
}

/** Simple view: core pipeline categories; fallback keeps graph connected. */
export function filterSimpleArchitecture(
  nodes: ArchNode[],
  edges: ArchEdge[]
): { nodes: ArchNode[]; edges: ArchEdge[] } {
  if (nodes.length <= 8) return { nodes, edges };

  let kept = nodes.filter((n) => SIMPLE_VIEW_CATEGORIES.has(n.category ?? ''));
  if (kept.length < 3) {
    kept = nodes.slice(0, Math.min(8, nodes.length));
  }

  const ids = new Set(kept.map((n) => n.id));
  let filteredEdges = edges.filter((e) => ids.has(e.from) && ids.has(e.to));

  if (filteredEdges.length === 0 && edges.length > 0) {
    const pathIds = longestPathNodeIds(nodes, edges);
    kept = nodes.filter((n) => pathIds.has(n.id));
    const pathIdSet = new Set(kept.map((n) => n.id));
    filteredEdges = edges.filter((e) => pathIdSet.has(e.from) && pathIdSet.has(e.to));
  }

  return { nodes: kept, edges: filteredEdges };
}

function longestPathNodeIds(nodes: ArchNode[], edges: ArchEdge[]): Set<string> {
  const ids = nodes.map((n) => n.id);
  const adj = new Map<string, string[]>();
  ids.forEach((id) => adj.set(id, []));
  edges.forEach((e) => {
    const list = adj.get(e.from) ?? [];
    list.push(e.to);
    adj.set(e.from, list);
  });

  const roots = ids.filter((id) => !edges.some((e) => e.to === id));
  const start = roots.length > 0 ? roots : [ids[0]];

  let best: string[] = [];
  const visit = (id: string, path: string[]) => {
    if (path.includes(id)) return;
    const next = [...path, id];
    const children = adj.get(id) ?? [];
    if (children.length === 0) {
      if (next.length > best.length) best = next;
      return;
    }
    children.forEach((c) => visit(c, next));
  };
  start.forEach((r) => visit(r, []));

  return new Set(best.length > 0 ? best : ids.slice(0, 6));
}
