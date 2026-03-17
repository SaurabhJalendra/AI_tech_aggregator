'use client';

import { useMemo } from 'react';

interface NodeData {
  id: string;
  label: string;
  category: string;
  module_slug?: string;
}

interface EdgeData {
  source: string;
  target: string;
  label?: string;
}

interface ArchitectureDiagramProps {
  data: Record<string, unknown>;
}

const CATEGORY_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  data_ingestion: { bg: 'bg-amber-50', border: 'border-amber-400', text: 'text-amber-800' },
  chunking: { bg: 'bg-orange-50', border: 'border-orange-400', text: 'text-orange-800' },
  embeddings: { bg: 'bg-yellow-50', border: 'border-yellow-500', text: 'text-yellow-800' },
  vector_databases: { bg: 'bg-emerald-50', border: 'border-emerald-400', text: 'text-emerald-800' },
  retrieval: { bg: 'bg-teal-50', border: 'border-teal-400', text: 'text-teal-800' },
  rag_architectures: { bg: 'bg-cyan-50', border: 'border-cyan-400', text: 'text-cyan-800' },
  llm_layer: { bg: 'bg-blue-50', border: 'border-blue-400', text: 'text-blue-800' },
  agent_systems: { bg: 'bg-violet-50', border: 'border-violet-400', text: 'text-violet-800' },
  evaluation: { bg: 'bg-purple-50', border: 'border-purple-400', text: 'text-purple-800' },
  caching: { bg: 'bg-pink-50', border: 'border-pink-400', text: 'text-pink-800' },
  deployment: { bg: 'bg-rose-50', border: 'border-rose-400', text: 'text-rose-800' },
  default: { bg: 'bg-gray-50', border: 'border-gray-400', text: 'text-gray-800' },
};

function getColor(category: string) {
  return CATEGORY_COLORS[category] || CATEGORY_COLORS.default;
}

export default function ArchitectureDiagram({ data }: ArchitectureDiagramProps) {
  const nodes = (data.nodes as NodeData[]) || [];
  const edges = (data.edges as EdgeData[]) || [];
  const layout = (data.layout as string) || 'left-to-right';
  const isHorizontal = layout === 'left-to-right';

  const positions = useMemo(() => {
    const pos: Record<string, { x: number; y: number }> = {};
    const nodeWidth = 200;
    const nodeHeight = 80;
    const gapX = isHorizontal ? 280 : 220;
    const gapY = isHorizontal ? 120 : 140;

    // Build adjacency for topological layout
    const inDegree: Record<string, number> = {};
    const outEdges: Record<string, string[]> = {};
    nodes.forEach((n) => {
      inDegree[n.id] = 0;
      outEdges[n.id] = [];
    });
    edges.forEach((e) => {
      inDegree[e.target] = (inDegree[e.target] || 0) + 1;
      if (!outEdges[e.source]) outEdges[e.source] = [];
      outEdges[e.source].push(e.target);
    });

    // BFS layers
    const layers: string[][] = [];
    const visited = new Set<string>();
    let current = nodes.filter((n) => (inDegree[n.id] || 0) === 0).map((n) => n.id);
    if (current.length === 0 && nodes.length > 0) {
      current = [nodes[0].id];
    }

    while (current.length > 0) {
      layers.push(current);
      current.forEach((id) => visited.add(id));
      const next: string[] = [];
      for (const id of current) {
        for (const target of outEdges[id] || []) {
          if (!visited.has(target) && !next.includes(target)) {
            next.push(target);
          }
        }
      }
      current = next;
    }

    // Place any unvisited nodes
    const unvisited = nodes.filter((n) => !visited.has(n.id));
    if (unvisited.length > 0) {
      layers.push(unvisited.map((n) => n.id));
    }

    layers.forEach((layer, layerIdx) => {
      layer.forEach((nodeId, nodeIdx) => {
        const offset = (layer.length - 1) / 2;
        if (isHorizontal) {
          pos[nodeId] = {
            x: 40 + layerIdx * gapX,
            y: 40 + (nodeIdx - offset + (layer.length - 1) / 2) * gapY,
          };
        } else {
          pos[nodeId] = {
            x: 40 + (nodeIdx - offset + (layer.length - 1) / 2) * gapX,
            y: 40 + layerIdx * gapY,
          };
        }
      });
    });

    return { pos, nodeWidth, nodeHeight, layers };
  }, [nodes, edges, isHorizontal]);

  if (nodes.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <p className="text-gray-500">No architecture data to display</p>
      </div>
    );
  }

  const { pos, nodeWidth, nodeHeight } = positions;

  // Calculate SVG dimensions
  const allX = Object.values(pos).map((p) => p.x);
  const allY = Object.values(pos).map((p) => p.y);
  const svgWidth = Math.max(...allX) + nodeWidth + 60;
  const svgHeight = Math.max(...allY) + nodeHeight + 60;

  return (
    <div className="flex h-full flex-col overflow-auto p-6">
      <svg
        width={svgWidth}
        height={svgHeight}
        className="mx-auto"
        style={{ minWidth: svgWidth, minHeight: svgHeight }}
      >
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="10"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#9ca3af" />
          </marker>
        </defs>

        {/* Edges */}
        {edges.map((edge, i) => {
          const from = pos[edge.source];
          const to = pos[edge.target];
          if (!from || !to) return null;

          const x1 = from.x + nodeWidth / 2;
          const y1 = from.y + nodeHeight / 2;
          const x2 = to.x + nodeWidth / 2;
          const y2 = to.y + nodeHeight / 2;

          // Calculate edge endpoint on node border
          const dx = x2 - x1;
          const dy = y2 - y1;
          const len = Math.sqrt(dx * dx + dy * dy) || 1;
          const startX = x1 + (dx / len) * (nodeWidth / 2);
          const startY = y1 + (dy / len) * (nodeHeight / 2);
          const endX = x2 - (dx / len) * (nodeWidth / 2 + 10);
          const endY = y2 - (dy / len) * (nodeHeight / 2 + 10);

          return (
            <g key={`edge-${i}`}>
              <line
                x1={startX}
                y1={startY}
                x2={endX}
                y2={endY}
                stroke="#9ca3af"
                strokeWidth={2}
                markerEnd="url(#arrowhead)"
              />
              {edge.label && (
                <text
                  x={(startX + endX) / 2}
                  y={(startY + endY) / 2 - 8}
                  textAnchor="middle"
                  className="fill-gray-500 text-xs"
                >
                  {edge.label}
                </text>
              )}
            </g>
          );
        })}

        {/* Nodes */}
        {nodes.map((node) => {
          const p = pos[node.id];
          if (!p) return null;
          const color = getColor(node.category);

          return (
            <g key={node.id}>
              <rect
                x={p.x}
                y={p.y}
                width={nodeWidth}
                height={nodeHeight}
                rx={8}
                ry={8}
                className={`${color.bg} ${color.border}`}
                fill="white"
                stroke="currentColor"
                strokeWidth={2}
                style={{ filter: 'drop-shadow(0 1px 2px rgb(0 0 0 / 0.1))' }}
              />
              <text
                x={p.x + nodeWidth / 2}
                y={p.y + nodeHeight / 2 - 6}
                textAnchor="middle"
                className={`${color.text} text-sm font-semibold`}
                fill="currentColor"
              >
                {node.label}
              </text>
              <text
                x={p.x + nodeWidth / 2}
                y={p.y + nodeHeight / 2 + 14}
                textAnchor="middle"
                className="fill-gray-400 text-xs"
              >
                {node.category.replace(/_/g, ' ')}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
