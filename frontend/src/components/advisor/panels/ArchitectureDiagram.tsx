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

const CATEGORY_COLORS: Record<string, { fill: string; stroke: string; text: string }> = {
  data_ingestion: { fill: '#fffbeb', stroke: '#f59e0b', text: '#92400e' },
  chunking: { fill: '#fff7ed', stroke: '#fb923c', text: '#9a3412' },
  embeddings: { fill: '#fefce8', stroke: '#eab308', text: '#854d0e' },
  vector_databases: { fill: '#ecfdf5', stroke: '#34d399', text: '#065f46' },
  retrieval: { fill: '#f0fdfa', stroke: '#2dd4bf', text: '#115e59' },
  rag_architectures: { fill: '#ecfeff', stroke: '#22d3ee', text: '#155e75' },
  llm_layer: { fill: '#eff6ff', stroke: '#60a5fa', text: '#1e40af' },
  agent_systems: { fill: '#f5f3ff', stroke: '#8b5cf6', text: '#5b21b6' },
  evaluation: { fill: '#faf5ff', stroke: '#a855f7', text: '#6b21a8' },
  caching: { fill: '#fdf2f8', stroke: '#ec4899', text: '#9d174d' },
  deployment: { fill: '#fff1f2', stroke: '#fb7185', text: '#9f1239' },
  default: { fill: '#f9fafb', stroke: '#9ca3af', text: '#1f2937' },
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
                  fill="#6b7280"
                  fontSize={12}
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
                fill={color.fill}
                stroke={color.stroke}
                strokeWidth={2}
                style={{ filter: 'drop-shadow(0 1px 2px rgb(0 0 0 / 0.1))' }}
              />
              <text
                x={p.x + nodeWidth / 2}
                y={p.y + nodeHeight / 2 - 6}
                textAnchor="middle"
                fill={color.text}
                fontSize={14}
                fontWeight={600}
              >
                {node.label}
              </text>
              <text
                x={p.x + nodeWidth / 2}
                y={p.y + nodeHeight / 2 + 14}
                textAnchor="middle"
                fill="#9ca3af"
                fontSize={12}
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
