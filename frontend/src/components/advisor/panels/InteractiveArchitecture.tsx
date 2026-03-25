'use client';

import { useMemo } from 'react';
import { useChatStore } from '@/stores/chatStore';
import type { ArchNode, ArchEdge } from '@/types/chat';

const CATEGORY_COLORS: Record<string, { fill: string; stroke: string; text: string }> = {
  data_ingestion:    { fill: '#dbeafe', stroke: '#3b82f6', text: '#1e40af' },
  chunking:          { fill: '#fce7f3', stroke: '#ec4899', text: '#9d174d' },
  embeddings:        { fill: '#fef3c7', stroke: '#f59e0b', text: '#92400e' },
  vector_databases:  { fill: '#d1fae5', stroke: '#10b981', text: '#065f46' },
  retrieval:         { fill: '#e0e7ff', stroke: '#6366f1', text: '#3730a3' },
  rag_architectures: { fill: '#fae8ff', stroke: '#a855f7', text: '#6b21a8' },
  llm_layer:         { fill: '#ffedd5', stroke: '#f97316', text: '#9a3412' },
  agent_systems:     { fill: '#fee2e2', stroke: '#ef4444', text: '#991b1b' },
  evaluation:        { fill: '#ccfbf1', stroke: '#14b8a6', text: '#134e4a' },
  default:           { fill: '#f3f4f6', stroke: '#6b7280', text: '#374151' },
};

function getColor(category?: string) {
  return CATEGORY_COLORS[category || ''] || CATEGORY_COLORS.default;
}

interface InteractiveArchitectureProps {
  data: Record<string, unknown>;
}

export default function InteractiveArchitecture({ data }: InteractiveArchitectureProps) {
  const sendMessage = useChatStore((s) => s.sendMessage);
  const isStreaming = useChatStore((s) => s.isStreaming);

  const nodes = (data.nodes as ArchNode[]) || [];
  const edges = (data.edges as ArchEdge[]) || [];
  const highlightedNode = data.highlightedNode as string | undefined;
  const title = (data.title as string) || 'Architecture';

  // BFS-based layering: roots at top, children below
  const layout = useMemo(() => {
    const NODE_W = 200;
    const NODE_H = 60;
    const GAP_X = 40;
    const GAP_Y = 80;
    const PADDING = 40;

    // Build adjacency for layering
    const inDegree = new Map<string, number>();
    const children = new Map<string, string[]>();
    nodes.forEach((n) => {
      inDegree.set(n.id, 0);
      children.set(n.id, []);
    });
    edges.forEach((e) => {
      inDegree.set(e.to, (inDegree.get(e.to) || 0) + 1);
      const c = children.get(e.from) || [];
      c.push(e.to);
      children.set(e.from, c);
    });

    // BFS layering
    const layers: string[][] = [];
    const assigned = new Set<string>();
    let queue = nodes
      .filter((n) => (inDegree.get(n.id) || 0) === 0)
      .map((n) => n.id);
    // If no roots (e.g., cycle or single node), start with first node
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
    // Add any unassigned nodes
    const remaining = nodes.filter((n) => !assigned.has(n.id));
    if (remaining.length > 0) layers.push(remaining.map((n) => n.id));

    // Position nodes
    const positions = new Map<string, { x: number; y: number }>();
    const maxLayerWidth = Math.max(...layers.map((l) => l.length), 1);
    const svgWidth = Math.max(maxLayerWidth * (NODE_W + GAP_X) + PADDING * 2, 500);

    layers.forEach((layer, layerIdx) => {
      const layerWidth = layer.length * (NODE_W + GAP_X) - GAP_X;
      const startX = (svgWidth - layerWidth) / 2;
      layer.forEach((nodeId, nodeIdx) => {
        positions.set(nodeId, {
          x: startX + nodeIdx * (NODE_W + GAP_X),
          y: PADDING + layerIdx * (NODE_H + GAP_Y),
        });
      });
    });

    const svgHeight = PADDING * 2 + layers.length * (NODE_H + GAP_Y);
    return { positions, svgWidth, svgHeight, NODE_W, NODE_H };
  }, [nodes, edges]);

  const handleNodeClick = (node: ArchNode) => {
    if (isStreaming) return;
    sendMessage(`Tell me more about ${node.label}`);
  };

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-gray-200 px-6 py-3 dark:border-gray-700">
        <h2 className="text-lg font-semibold">{title}</h2>
        <p className="text-xs text-gray-500">Click a node to learn more</p>
      </div>

      <div className="flex-1 overflow-auto p-4">
        <svg
          viewBox={`0 0 ${layout.svgWidth} ${layout.svgHeight}`}
          className="mx-auto"
          style={{ maxHeight: '100%', width: '100%' }}
        >
          <defs>
            <marker
              id="arrow-ia"
              viewBox="0 0 10 7"
              refX="10"
              refY="3.5"
              markerWidth="8"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 3.5 L 0 7 z" fill="#9ca3af" />
            </marker>
          </defs>

          {/* Edges */}
          {edges.map((edge, i) => {
            const from = layout.positions.get(edge.from);
            const to = layout.positions.get(edge.to);
            if (!from || !to) return null;
            const x1 = from.x + layout.NODE_W / 2;
            const y1 = from.y + layout.NODE_H;
            const x2 = to.x + layout.NODE_W / 2;
            const y2 = to.y;
            return (
              <g key={`edge-${i}`} className="animate-fadeIn">
                <line
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke="#9ca3af"
                  strokeWidth={2}
                  markerEnd="url(#arrow-ia)"
                />
                {edge.label && (
                  <text
                    x={(x1 + x2) / 2 + 8}
                    y={(y1 + y2) / 2}
                    fontSize={10}
                    fill="#6b7280"
                  >
                    {edge.label}
                  </text>
                )}
              </g>
            );
          })}

          {/* Nodes */}
          {nodes.map((node) => {
            const pos = layout.positions.get(node.id);
            if (!pos) return null;
            const color = getColor(node.category);
            const isHighlighted = highlightedNode === node.id;

            return (
              <g
                key={node.id}
                className="animate-fadeIn cursor-pointer"
                onClick={() => handleNodeClick(node)}
              >
                <rect
                  x={pos.x}
                  y={pos.y}
                  width={layout.NODE_W}
                  height={layout.NODE_H}
                  rx={10}
                  ry={10}
                  fill={color.fill}
                  stroke={isHighlighted ? '#2563eb' : color.stroke}
                  strokeWidth={isHighlighted ? 3 : 2}
                />
                <text
                  x={pos.x + layout.NODE_W / 2}
                  y={pos.y + 24}
                  textAnchor="middle"
                  fontSize={13}
                  fontWeight={600}
                  fill={color.text}
                >
                  {node.label}
                </text>
                {node.description && (
                  <text
                    x={pos.x + layout.NODE_W / 2}
                    y={pos.y + 42}
                    textAnchor="middle"
                    fontSize={10}
                    fill={color.text}
                    opacity={0.7}
                  >
                    {node.description.slice(0, 30)}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
