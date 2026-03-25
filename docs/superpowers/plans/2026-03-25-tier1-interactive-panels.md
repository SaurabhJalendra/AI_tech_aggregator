# Tier 1: Interactive Option Cards + Incremental Architecture Builder

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the advisor from a text chatbot into a visual system designer that builds architectures node-by-node and asks questions via clickable cards.

**Architecture:** Two new panel types (option_cards, interactive_architecture) plus incremental panel_command protocol. The backend agent emits granular commands (add_node, connect, highlight) instead of one big render. The frontend handles bidirectional flow — clicking option cards sends messages back to chat.

**Tech Stack:** React 19, Tailwind CSS, Zustand, FastAPI SSE, Claude tool_use API

---

## File Map

### New Files
| File | Responsibility |
|------|---------------|
| `frontend/src/components/advisor/panels/OptionCards.tsx` | Clickable question cards panel — renders options, sends selection to chat |
| `frontend/src/components/advisor/panels/InteractiveArchitecture.tsx` | Incremental architecture diagram — builds node by node with animations |

### Modified Files
| File | Changes |
|------|---------|
| `frontend/src/types/chat.ts` | Add `option_cards`, `interactive_architecture` to PanelType. Add `OptionCard`, `ArchNode`, `ArchEdge` types |
| `frontend/src/stores/panelStore.ts` | Add `appendNode`, `appendEdge`, `highlightNode` actions for incremental updates. Handle `update` action merging |
| `frontend/src/components/advisor/MainPanel.tsx` | Add cases for new panel types in renderPanel switch |
| `backend/src/agent/tools.py` | Add `present_options` and `build_architecture_step` tool definitions |
| `backend/src/agent/advisor.py` | Add tool handlers for new tools. Update panel command emission |
| `backend/src/agent/prompts.py` | Add instructions for when/how to use interactive tools |

---

## Task 1: Types and Panel Store Foundation

**Files:**
- Modify: `frontend/src/types/chat.ts`
- Modify: `frontend/src/stores/panelStore.ts`

- [ ] **Step 1: Add new types to chat.ts**

Add after the existing `PanelType` definition:

```typescript
// Add to PanelType union
type PanelType =
  | 'welcome'
  | 'architecture_diagram'
  | 'comparison_table'
  | 'comparison_chart'
  | 'code_preview'
  | 'module_detail'
  | 'recommendation'
  | 'document'
  | 'option_cards'
  | 'interactive_architecture';

// New types for option cards
export interface OptionCard {
  id: string;
  label: string;
  description?: string;
  icon?: string;
}

// New types for incremental architecture
export interface ArchNode {
  id: string;
  label: string;
  slug?: string;
  category?: string;
  description?: string;
}

export interface ArchEdge {
  from: string;
  to: string;
  label?: string;
}
```

- [ ] **Step 2: Add incremental actions to panelStore.ts**

Add new actions to the PanelState interface and implementation:

```typescript
// Add to PanelState interface:
appendNode: (node: ArchNode) => void;
appendEdge: (edge: ArchEdge) => void;
highlightNode: (nodeId: string) => void;

// Implementation:
appendNode: (node) => {
  set((state) => {
    const nodes = ((state.panelData.nodes as ArchNode[]) || []);
    // Don't add duplicate nodes
    if (nodes.some((n) => n.id === node.id)) return state;
    return {
      panelData: {
        ...state.panelData,
        nodes: [...nodes, node],
      },
    };
  });
},

appendEdge: (edge) => {
  set((state) => {
    const edges = ((state.panelData.edges as ArchEdge[]) || []);
    return {
      panelData: {
        ...state.panelData,
        edges: [...edges, edge],
      },
    };
  });
},

highlightNode: (nodeId) => {
  set((state) => ({
    panelData: {
      ...state.panelData,
      highlightedNode: nodeId,
    },
  }));
},
```

Update `renderPanel` to handle `update` action with sub-actions:

```typescript
renderPanel: (command) => {
  const { action, panel, data, title } = command;

  if (action === 'update') {
    const subAction = data?.subAction as string;
    if (subAction === 'add_node' && data.node) {
      get().appendNode(data.node as ArchNode);
    } else if (subAction === 'add_edge' && data.edge) {
      get().appendEdge(data.edge as ArchEdge);
    } else if (subAction === 'highlight' && data.nodeId) {
      get().highlightNode(data.nodeId as string);
    } else {
      // Generic data merge
      set((state) => ({
        panelData: { ...state.panelData, ...data },
      }));
    }
    return;
  }

  // existing render logic...
}
```

- [ ] **Step 3: Verify frontend builds**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no type errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/chat.ts frontend/src/stores/panelStore.ts
git commit -m "feat: add types and store actions for option cards and incremental architecture"
```

---

## Task 2: Option Cards Panel Component

**Files:**
- Create: `frontend/src/components/advisor/panels/OptionCards.tsx`
- Modify: `frontend/src/components/advisor/MainPanel.tsx`

- [ ] **Step 1: Create OptionCards component**

```typescript
'use client';

import { useChatStore } from '@/stores/chatStore';
import type { OptionCard } from '@/types/chat';

interface OptionCardsProps {
  data: Record<string, unknown>;
}

export default function OptionCards({ data }: OptionCardsProps) {
  const sendMessage = useChatStore((s) => s.sendMessage);
  const isStreaming = useChatStore((s) => s.isStreaming);

  const question = (data.question as string) || '';
  const options = (data.options as OptionCard[]) || [];
  const multiSelect = (data.multi_select as boolean) || false;

  const handleSelect = (option: OptionCard) => {
    if (isStreaming) return;
    sendMessage(option.label);
  };

  return (
    <div className="flex h-full flex-col p-6">
      {question && (
        <h2 className="mb-6 text-xl font-semibold text-gray-900 dark:text-gray-100">
          {question}
        </h2>
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        {options.map((option) => (
          <button
            key={option.id}
            onClick={() => handleSelect(option)}
            disabled={isStreaming}
            className="group flex flex-col items-start gap-2 rounded-xl border-2 border-gray-200 bg-white p-5 text-left transition-all hover:border-blue-500 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-blue-400"
          >
            {option.icon && (
              <span className="text-2xl">{option.icon}</span>
            )}
            <span className="text-sm font-semibold text-gray-900 group-hover:text-blue-600 dark:text-gray-100 dark:group-hover:text-blue-400">
              {option.label}
            </span>
            {option.description && (
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {option.description}
              </span>
            )}
          </button>
        ))}
      </div>

      {multiSelect && (
        <p className="mt-4 text-xs text-gray-400">
          Select one or more options
        </p>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Add OptionCards to MainPanel.tsx**

Add import and case to the switch:

```typescript
import OptionCards from './panels/OptionCards';

// In renderPanel switch:
case 'option_cards':
  return <OptionCards data={panelData} />;
```

- [ ] **Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/advisor/panels/OptionCards.tsx frontend/src/components/advisor/MainPanel.tsx
git commit -m "feat: add OptionCards panel component with click-to-chat"
```

---

## Task 3: Interactive Architecture Panel Component

**Files:**
- Create: `frontend/src/components/advisor/panels/InteractiveArchitecture.tsx`
- Modify: `frontend/src/components/advisor/MainPanel.tsx`

- [ ] **Step 1: Create InteractiveArchitecture component**

This is the key component — an SVG diagram that builds incrementally as nodes and edges arrive via store updates. Each new node fades in with a CSS animation.

```typescript
'use client';

import { useMemo } from 'react';
import { usePanelStore } from '@/stores/panelStore';
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

  // Layout: simple top-to-bottom pipeline
  const layout = useMemo(() => {
    const NODE_W = 200;
    const NODE_H = 60;
    const GAP_X = 40;
    const GAP_Y = 80;
    const PADDING = 40;

    // Build adjacency for layering
    const inDegree = new Map<string, number>();
    const children = new Map<string, string[]>();
    nodes.forEach((n) => { inDegree.set(n.id, 0); children.set(n.id, []); });
    edges.forEach((e) => {
      inDegree.set(e.to, (inDegree.get(e.to) || 0) + 1);
      const c = children.get(e.from) || [];
      c.push(e.to);
      children.set(e.from, c);
    });

    // BFS layering
    const layers: string[][] = [];
    const assigned = new Set<string>();
    let queue = nodes.filter((n) => (inDegree.get(n.id) || 0) === 0).map((n) => n.id);
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
    if (isStreaming || !node.slug) return;
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
            <marker id="arrow-ia" viewBox="0 0 10 7" refX="10" refY="3.5"
              markerWidth="8" markerHeight="6" orient="auto-start-reverse">
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
                <line x1={x1} y1={y1} x2={x2} y2={y2}
                  stroke="#9ca3af" strokeWidth={2}
                  markerEnd="url(#arrow-ia)" />
                {edge.label && (
                  <text x={(x1 + x2) / 2 + 8} y={(y1 + y2) / 2}
                    fontSize={10} fill="#6b7280">{edge.label}</text>
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
              <g key={node.id}
                className="animate-fadeIn cursor-pointer"
                onClick={() => handleNodeClick(node)}
              >
                <rect
                  x={pos.x} y={pos.y}
                  width={layout.NODE_W} height={layout.NODE_H}
                  rx={10} ry={10}
                  fill={color.fill}
                  stroke={isHighlighted ? '#2563eb' : color.stroke}
                  strokeWidth={isHighlighted ? 3 : 2}
                />
                <text
                  x={pos.x + layout.NODE_W / 2}
                  y={pos.y + 24}
                  textAnchor="middle"
                  fontSize={13} fontWeight={600}
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
```

- [ ] **Step 2: Add CSS animation to globals**

Add to `frontend/src/app/globals.css`:

```css
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fadeIn {
  animation: fadeIn 0.4s ease-out forwards;
}
```

- [ ] **Step 3: Add InteractiveArchitecture to MainPanel.tsx**

```typescript
import InteractiveArchitecture from './panels/InteractiveArchitecture';

// In renderPanel switch:
case 'interactive_architecture':
  return <InteractiveArchitecture data={panelData} />;
```

- [ ] **Step 4: Verify build**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/advisor/panels/InteractiveArchitecture.tsx \
       frontend/src/components/advisor/MainPanel.tsx \
       frontend/src/app/globals.css
git commit -m "feat: add InteractiveArchitecture panel with incremental node rendering"
```

---

## Task 4: Backend Tools for Option Cards and Architecture Building

**Files:**
- Modify: `backend/src/agent/tools.py`
- Modify: `backend/src/agent/advisor.py`
- Modify: `backend/src/agent/prompts.py`

- [ ] **Step 1: Add tool definitions to tools.py**

```python
TOOL_PRESENT_OPTIONS = {
    "name": "present_options",
    "description": "Present interactive option cards to the user in the visual panel. Use this instead of listing options as text when you want the user to choose between 2-6 options. Each option becomes a clickable card. The user's selection is automatically sent as a chat message.",
    "input_schema": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question or prompt to display above the cards",
            },
            "options": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string", "description": "Short label (2-5 words)"},
                        "description": {"type": "string", "description": "One-line explanation"},
                        "icon": {"type": "string", "description": "Single emoji"},
                    },
                    "required": ["id", "label"],
                },
                "description": "2-6 options to present as clickable cards",
            },
        },
        "required": ["question", "options"],
    },
}

TOOL_BUILD_ARCHITECTURE_STEP = {
    "name": "build_architecture_step",
    "description": "Add a node or connection to the interactive architecture diagram being built in the visual panel. Call this multiple times to incrementally build a pipeline diagram node by node. First call with action='init' to start a new diagram, then 'add_node' for each component, then 'connect' for each edge, then 'highlight' to draw attention to a specific node.",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["init", "add_node", "connect", "highlight"],
                "description": "init=start new diagram, add_node=add a component, connect=add an edge, highlight=highlight a node",
            },
            "title": {
                "type": "string",
                "description": "Diagram title (only used with init)",
            },
            "node": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "label": {"type": "string"},
                    "slug": {"type": "string", "description": "Module slug if this is a known module"},
                    "category": {"type": "string", "description": "Category slug for coloring"},
                    "description": {"type": "string", "description": "Short description"},
                },
                "description": "Node to add (used with add_node)",
            },
            "edge": {
                "type": "object",
                "properties": {
                    "from": {"type": "string", "description": "Source node id"},
                    "to": {"type": "string", "description": "Target node id"},
                    "label": {"type": "string", "description": "Edge label (e.g. 'embeddings', 'queries')"},
                },
                "description": "Edge to add (used with connect)",
            },
            "node_id": {
                "type": "string",
                "description": "Node to highlight (used with highlight)",
            },
        },
        "required": ["action"],
    },
}
```

Add both to ALL_TOOLS list.

- [ ] **Step 2: Add tool handlers to advisor.py**

```python
async def _tool_present_options(self, tool_input: dict) -> tuple[dict, dict]:
    """Present interactive option cards in the panel."""
    panel_command = {
        "action": "render",
        "panel": "option_cards",
        "title": tool_input.get("question", "Choose an option"),
        "data": {
            "question": tool_input.get("question", ""),
            "options": tool_input.get("options", []),
        },
    }
    return {"status": "options_presented", "option_count": len(tool_input.get("options", []))}, panel_command

async def _tool_build_architecture_step(self, tool_input: dict) -> tuple[dict, dict]:
    """Build architecture diagram incrementally."""
    action = tool_input.get("action", "")

    if action == "init":
        panel_command = {
            "action": "render",
            "panel": "interactive_architecture",
            "title": tool_input.get("title", "Architecture"),
            "data": {"nodes": [], "edges": [], "title": tool_input.get("title", "Architecture")},
        }
        return {"status": "diagram_initialized"}, panel_command

    elif action == "add_node":
        node = tool_input.get("node", {})
        panel_command = {
            "action": "update",
            "panel": "interactive_architecture",
            "data": {"subAction": "add_node", "node": node},
        }
        return {"status": f"node_added: {node.get('label', '')}"}, panel_command

    elif action == "connect":
        edge = tool_input.get("edge", {})
        panel_command = {
            "action": "update",
            "panel": "interactive_architecture",
            "data": {"subAction": "add_edge", "edge": edge},
        }
        return {"status": f"connected: {edge.get('from', '')} -> {edge.get('to', '')}"}, panel_command

    elif action == "highlight":
        node_id = tool_input.get("node_id", "")
        panel_command = {
            "action": "update",
            "panel": "interactive_architecture",
            "data": {"subAction": "highlight", "nodeId": node_id},
        }
        return {"status": f"highlighted: {node_id}"}, panel_command

    return {"error": f"Unknown action: {action}"}, None
```

Add dispatch cases in `_execute_tool`:
```python
elif tool_name == "present_options":
    return await self._tool_present_options(tool_input)
elif tool_name == "build_architecture_step":
    return await self._tool_build_architecture_step(tool_input)
```

- [ ] **Step 3: Update system prompt in prompts.py**

Append to ADVISOR_SYSTEM_PROMPT:

```python
INTERACTIVE_TOOLS_INSTRUCTIONS = """

## Interactive Visual Tools

You have powerful visual tools. USE THEM — don't just write text.

### Option Cards (`present_options`)
When asking the user to choose between options, ALWAYS use `present_options` instead of listing choices in text. This renders clickable cards in the visual panel. The user clicks a card and their selection is sent as a chat message automatically.

Use this for:
- Clarifying questions (budget, scale, team size, etc.)
- Choosing between technology categories
- Selecting architecture patterns
- Any question with 2-6 discrete options

### Architecture Builder (`build_architecture_step`)
When recommending a technology stack or pipeline, BUILD IT VISUALLY node by node.

**Flow:**
1. Call with action="init" to start a new diagram
2. For each component you recommend, call action="add_node" with the module details
3. After adding nodes, call action="connect" to show data flow between them
4. Call action="highlight" to draw attention to the node you're currently discussing

**Example sequence for a RAG pipeline:**
1. init(title="RAG Pipeline for Legal Docs")
2. add_node(id="ingest", label="Unstructured.io", category="data_ingestion", slug="unstructured_io")
3. add_node(id="chunk", label="LlamaIndex Chunker", category="chunking", slug="llamaindex_node_parsers")
4. connect(from="ingest", to="chunk", label="documents")
5. highlight(nodeId="ingest") — while explaining the ingestion choice
6. add_node(id="embed", label="Voyage AI", category="embeddings", slug="voyage_ai")
7. connect(from="chunk", to="embed", label="chunks")
... and so on

This creates an animated, interactive diagram where each node appears as you discuss it. The user can click nodes to learn more.

### Rules
- ALWAYS use present_options for questions with discrete choices
- ALWAYS use build_architecture_step when recommending stacks — never describe architecture in text only
- Build the diagram node by node as you explain each component — don't dump the whole thing at once
- Use module slugs from the catalog so nodes link to real module data
"""
```

Append `INTERACTIVE_TOOLS_INSTRUCTIONS` to the system prompt in `build_system_prompt()`.

- [ ] **Step 4: Verify backend imports**

Run: `cd backend && python -c "from src.main import app; print('OK')"`
Expected: OK

- [ ] **Step 5: Commit**

```bash
git add backend/src/agent/tools.py backend/src/agent/advisor.py backend/src/agent/prompts.py
git commit -m "feat: add present_options and build_architecture_step tools"
```

---

## Task 5: Wire Panel Update Commands Through chatStore

**Files:**
- Modify: `frontend/src/stores/chatStore.ts`

- [ ] **Step 1: Handle `update` action panel commands**

Currently, `chatStore.ts` calls `usePanelStore.getState().renderPanel(command)` for all panel_command events. The `renderPanel` method in panelStore now handles the `update` action (from Task 1). Verify this works by checking the flow:

1. Backend emits: `{"type": "panel_command", "command": {"action": "update", "panel": "interactive_architecture", "data": {"subAction": "add_node", "node": {...}}}}`
2. chatStore receives it, calls `panelStore.renderPanel(command)`
3. panelStore sees `action === 'update'`, dispatches to `appendNode()`
4. InteractiveArchitecture re-renders with the new node

No code change needed in chatStore if the panelStore updates from Task 1 are correct. Verify by reading both files.

- [ ] **Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: PASS

- [ ] **Step 3: Commit (if any changes needed)**

---

## Task 6: E2E Integration Test

- [ ] **Step 1: Restart backend**

```bash
# Kill existing
tasklist | grep python | awk '{print $2}' | while read pid; do taskkill //F //PID $pid; done
sleep 3
# Restart
cd backend && source .venv/Scripts/activate
python -c "import uvicorn; uvicorn.run('src.main:app', host='127.0.0.1', port=8000)" &
sleep 4
```

- [ ] **Step 2: Test option cards via curl**

```bash
curl -s -m 120 -N -X POST http://localhost:8000/api/v1/advisor/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev@example.com" \
  -d '{"message": "I want to build a RAG pipeline"}'
```

Expected output should include:
- `"type": "panel_command"` with `"panel": "option_cards"` (for clarifying questions)
- OR `"type": "panel_command"` with `"panel": "interactive_architecture"` (for architecture building)
- Tool activity events showing tool calls

- [ ] **Step 3: Test architecture building**

```bash
curl -s -m 120 -N -X POST http://localhost:8000/api/v1/advisor/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dev@example.com" \
  -d '{"message": "Build me a RAG architecture for 1M legal documents, budget $500/mo, team of 2"}'
```

Expected: Multiple `panel_command` events — first an `init`, then `add_node` events, then `connect` events.

- [ ] **Step 4: Test in browser**

Open http://localhost:3000/advisor, type "Help me choose a vector database" and verify:
- Option cards appear in the right panel
- Clicking a card sends the selection as a chat message
- The advisor responds to the selection

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: Tier 1 complete — interactive option cards + incremental architecture builder"
git push origin main
```
