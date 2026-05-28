import dagre from 'dagre';
import { MarkerType, type Edge, type Node } from '@xyflow/react';
import type { ArchEdge, ArchNode } from '@/types/chat';
import {
  getConsultingNodeTitle,
  getNodeRoleLine,
  humanizeEdgeLabel,
} from '@/lib/architectureConsulting';
import {
  inferNodeImportance,
  type NodeImportance,
} from '@/lib/architectureNodeHierarchy';
import {
  getStageIdForCategory,
  getStageLabel,
  orderedStageIds,
} from '@/lib/architectureStages';

export const ARCH_NODE_WIDTH = 272;
export const ARCH_NODE_HEIGHT = 118;
const NODE_GAP_Y = 32;
const STAGE_GAP_X = 96;
const STAGE_PAD = 28;
const STAGE_HEADER = 44;

export type ArchFlowNodeData = {
  label: string;
  consultingTitle: string;
  roleLine: string;
  description?: string;
  slug?: string;
  category?: string;
  stageId?: string;
  dimmed?: boolean;
  highlighted?: boolean;
  selected?: boolean;
  hovered?: boolean;
  stageLabel?: string;
  importance?: NodeImportance;
  evolved?: boolean;
  flowActive?: boolean;
  fitStrength?: 'strong' | 'solid' | 'moderate';
};

export type StageGroupData = {
  label: string;
  stageId: string;
  width: number;
  height: number;
  active?: boolean;
  dimmed?: boolean;
  flowActive?: boolean;
};

function topologicalLayers(nodes: ArchNode[], edges: ArchEdge[]): string[][] {
  const inDegree = new Map<string, number>();
  const children = new Map<string, string[]>();
  nodes.forEach((n) => {
    inDegree.set(n.id, 0);
    children.set(n.id, []);
  });
  edges.forEach((e) => {
    inDegree.set(e.to, (inDegree.get(e.to) || 0) + 1);
    children.get(e.from)?.push(e.to);
  });

  const layers: string[][] = [];
  const assigned = new Set<string>();
  let queue = nodes.filter((n) => (inDegree.get(n.id) || 0) === 0).map((n) => n.id);
  if (queue.length === 0 && nodes.length > 0) queue = [nodes[0].id];

  while (queue.length > 0) {
    layers.push([...queue]);
    queue.forEach((id) => assigned.add(id));
    const next: string[] = [];
    for (const id of queue) {
      for (const child of children.get(id) || []) {
        if (!assigned.has(child) && !next.includes(child)) next.push(child);
      }
    }
    queue = next;
  }
  const remaining = nodes.filter((n) => !assigned.has(n.id)).map((n) => n.id);
  if (remaining.length) layers.push(remaining);
  return layers;
}

function orderNodesInStage(
  stageNodes: ArchNode[],
  edges: ArchEdge[],
  globalLayerOrder: string[]
): ArchNode[] {
  const ids = new Set(stageNodes.map((n) => n.id));
  const stageEdges = edges.filter((e) => ids.has(e.from) && ids.has(e.to));
  if (stageNodes.length <= 1 || stageEdges.length === 0) {
    return [...stageNodes].sort(
      (a, b) => globalLayerOrder.indexOf(a.id) - globalLayerOrder.indexOf(b.id)
    );
  }

  const subLayers = topologicalLayers(stageNodes, stageEdges);
  const order = subLayers.flat();
  return [...stageNodes].sort((a, b) => order.indexOf(a.id) - order.indexOf(b.id));
}

/** Stage-column layout (LR pipeline groups) — primary architecture view. */
export function buildStageColumnFlow(
  archNodes: ArchNode[],
  archEdges: ArchEdge[],
  options: {
    focusIds: Set<string> | null;
    highlightedId?: string;
    selectedId?: string;
    activeStageId?: string | null;
    hoveredId?: string | null;
    shortlistSlugs?: string[];
    evolvedNodeIds?: Set<string>;
    flowActiveStageId?: string | null;
  }
): { nodes: Node[]; edges: Edge[]; width: number; height: number } {
  const globalLayerOrder = topologicalLayers(archNodes, archEdges).flat();
  const byStage = new Map<string, ArchNode[]>();

  archNodes.forEach((n) => {
    const stageId = getStageIdForCategory(n.category, n.slug);
    const list = byStage.get(stageId) ?? [];
    list.push(n);
    byStage.set(stageId, list);
  });

  const flowNodes: Node[] = [];
  let cursorX = STAGE_PAD;

  const stageOrder = orderedStageIds().filter((id) => (byStage.get(id)?.length ?? 0) > 0);

  for (const stageId of stageOrder) {
    const stageNodes = orderNodesInStage(
      byStage.get(stageId) ?? [],
      archEdges,
      globalLayerOrder
    );
    const count = stageNodes.length;
    const groupHeight =
      STAGE_HEADER + STAGE_PAD * 2 + count * ARCH_NODE_HEIGHT + (count - 1) * NODE_GAP_Y;
    const groupWidth = ARCH_NODE_WIDTH + STAGE_PAD * 2;

    const stageActive =
      options.activeStageId == null || options.activeStageId === stageId;
    flowNodes.push({
      id: `stage-${stageId}`,
      type: 'stageGroup',
      position: { x: cursorX, y: STAGE_PAD },
      data: {
        label: getStageLabel(stageId),
        stageId,
        width: groupWidth,
        height: groupHeight,
        active: options.activeStageId === stageId,
        dimmed: options.activeStageId != null && !stageActive,
        flowActive: options.flowActiveStageId === stageId,
      } satisfies StageGroupData,
      selectable: false,
      draggable: false,
      focusable: false,
      zIndex: 0,
    });

    stageNodes.forEach((node, idx) => {
      const y = STAGE_PAD + STAGE_HEADER + STAGE_PAD + idx * (ARCH_NODE_HEIGHT + NODE_GAP_Y);
      const inFocus =
        options.focusIds == null || options.focusIds.has(node.id);
      const archNode: ArchNode = node;
      const importance = inferNodeImportance(
        archNode,
        archEdges,
        options.shortlistSlugs
      );
      const evolved =
        options.evolvedNodeIds != null &&
        (options.evolvedNodeIds.has(node.id) ||
          (node.slug != null && options.evolvedNodeIds.has(node.slug)));
      const flowActive = options.flowActiveStageId === stageId;
      flowNodes.push({
        id: node.id,
        type: 'archModule',
        position: { x: cursorX + STAGE_PAD, y },
        data: {
          label: node.label,
          consultingTitle: getConsultingNodeTitle(archNode),
          roleLine: getNodeRoleLine(archNode, importance),
          importance,
          description: node.description,
          slug: node.slug,
          category: node.category,
          stageId,
          dimmed: !inFocus || (options.activeStageId != null && options.activeStageId !== stageId),
          highlighted: options.highlightedId === node.id,
          selected: options.selectedId === node.id,
          hovered: options.hoveredId === node.id,
          stageLabel: getStageLabel(stageId),
          evolved,
          flowActive,
        } satisfies ArchFlowNodeData,
        zIndex:
          options.selectedId === node.id
            ? 4
            : importance === 'primary'
              ? 2
              : 1,
      });
    });

    cursorX += groupWidth + STAGE_GAP_X;
  }

  const edges: Edge[] = archEdges.map((e, i) => {
    const onPath =
      options.focusIds == null ||
      (options.focusIds.has(e.from) && options.focusIds.has(e.to));
    return {
      id: `e-${e.from}-${e.to}-${i}`,
      source: e.from,
      target: e.to,
      type: 'smoothstep',
      className: onPath && options.focusIds ? 'arch-path-active' : undefined,
      label: humanizeEdgeLabel(e.label),
      labelStyle: { fill: 'var(--text-secondary)', fontSize: 11, fontWeight: 500 },
      labelBgStyle: { fill: 'var(--surface-panel)', fillOpacity: 0.95 },
      labelBgPadding: [8, 5] as [number, number],
      labelBgBorderRadius: 6,
      animated: onPath && options.focusIds != null,
      style: {
        stroke: onPath && options.focusIds ? 'var(--accent)' : 'var(--text-muted)',
        strokeWidth: onPath && options.focusIds ? 2.25 : 1.5,
        opacity: options.focusIds ? (onPath ? 0.95 : 0.12) : 0.5,
        transition: 'stroke 0.25s ease, opacity 0.25s ease, stroke-width 0.25s ease',
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: onPath && options.focusIds ? 'var(--accent)' : 'var(--text-muted)',
        width: 16,
        height: 16,
      },
    };
  });

  const width = Math.max(cursorX + STAGE_PAD, 640);
  const maxGroup = flowNodes.filter((n) => n.type === 'stageGroup');
  const height =
    Math.max(
      ...maxGroup.map((n) => (n.position.y + (n.data as StageGroupData).height)),
      ARCH_NODE_HEIGHT + STAGE_PAD * 4
    ) + STAGE_PAD;

  return { nodes: flowNodes, edges, width, height };
}

/** Dagre LR layout when few stages / dense cross-links. */
export function buildDagreFlow(
  archNodes: ArchNode[],
  archEdges: ArchEdge[],
  options: {
    focusIds: Set<string> | null;
    highlightedId?: string;
    selectedId?: string;
    hoveredId?: string | null;
    shortlistSlugs?: string[];
    direction?: 'LR' | 'TB';
  }
): { nodes: Node[]; edges: Edge[]; width: number; height: number } {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({
    rankdir: options.direction ?? 'LR',
    nodesep: 48,
    ranksep: 72,
    marginx: 32,
    marginy: 32,
  });

  archNodes.forEach((n) => {
    g.setNode(n.id, { width: ARCH_NODE_WIDTH, height: ARCH_NODE_HEIGHT });
  });
  archEdges.forEach((e) => g.setEdge(e.from, e.to));
  dagre.layout(g);

  const flowNodes: Node[] = archNodes.map((node) => {
    const pos = g.node(node.id);
    const inFocus = options.focusIds == null || options.focusIds.has(node.id);
    const importance = inferNodeImportance(node, archEdges, options.shortlistSlugs);
    return {
      id: node.id,
      type: 'archModule',
      position: {
        x: pos.x - ARCH_NODE_WIDTH / 2,
        y: pos.y - ARCH_NODE_HEIGHT / 2,
      },
      data: {
        label: node.label,
        consultingTitle: getConsultingNodeTitle(node),
        roleLine: getNodeRoleLine(node, importance),
        importance,
        description: node.description,
        slug: node.slug,
        category: node.category,
        dimmed: !inFocus,
        highlighted: options.highlightedId === node.id,
        selected: options.selectedId === node.id,
        hovered: options.hoveredId === node.id,
      } satisfies ArchFlowNodeData,
      zIndex: 1,
    };
  });

  const edges: Edge[] = archEdges.map((e, i) => ({
    id: `e-${e.from}-${e.to}-${i}`,
    source: e.from,
    target: e.to,
    type: 'smoothstep',
    label: e.label,
    style: {
      stroke: 'var(--text-muted)',
      strokeWidth: 1.5,
      opacity: options.focusIds
        ? options.focusIds.has(e.from) && options.focusIds.has(e.to)
          ? 1
          : 0.2
        : 0.55,
    },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: 'var(--text-muted)',
    },
  }));

  const graphLabel = g.graph();
  const width = (graphLabel.width ?? 800) + 48;
  const height = (graphLabel.height ?? 400) + 48;
  return { nodes: flowNodes, edges, width, height };
}

export function buildArchitectureFlow(
  archNodes: ArchNode[],
  archEdges: ArchEdge[],
  options: {
    viewMode: 'simple' | 'technical';
    layoutMode: 'stages' | 'dagre';
    focusIds: Set<string> | null;
    highlightedId?: string;
    selectedId?: string;
    activeStageId?: string | null;
    hoveredId?: string | null;
    shortlistSlugs?: string[];
    evolvedNodeIds?: Set<string>;
    flowActiveStageId?: string | null;
  }
): { nodes: Node[]; edges: Edge[]; width: number; height: number } {
  if (archNodes.length === 0) {
    return { nodes: [], edges: [], width: 800, height: 400 };
  }

  if (options.layoutMode === 'dagre') {
    return buildDagreFlow(archNodes, archEdges, {
      ...options,
      direction: 'LR',
    });
  }

  return buildStageColumnFlow(archNodes, archEdges, options);
}
