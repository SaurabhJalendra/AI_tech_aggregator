'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Background,
  BackgroundVariant,
  Controls,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  type Node,
  type NodeMouseHandler,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import ArchModuleNode from './ArchModuleNode';
import ArchStageGroupNode from './ArchStageGroupNode';
import BlueprintComparisonWorkspace from './BlueprintComparisonWorkspace';
import BlueprintConsultingContinuity from './BlueprintConsultingContinuity';
import BlueprintEvolutionHistory from './BlueprintEvolutionHistory';
import BlueprintStrategicForecasts from './BlueprintStrategicForecasts';
import BlueprintStrategyBranches from './BlueprintStrategyBranches';
import BlueprintArchitectureSandbox from './BlueprintArchitectureSandbox';
import BlueprintStrategicIntelligence from './BlueprintStrategicIntelligence';
import BlueprintStrategicTimeline from './BlueprintStrategicTimeline';
import BlueprintStrategyComparison from './BlueprintStrategyComparison';
import BlueprintStrategyWorkspace from './BlueprintStrategyWorkspace';
import BlueprintTradeoffSimulator from './BlueprintTradeoffSimulator';
import BlueprintConsultingHeader from './BlueprintConsultingHeader';
import BlueprintDecisionTimeline from './BlueprintDecisionTimeline';
import BlueprintEvolutionPanel from './BlueprintEvolutionPanel';
import BlueprintFlowLegend from './BlueprintFlowLegend';
import BlueprintGuidedNarrative from './BlueprintGuidedNarrative';
import BlueprintOnboardingHint from './BlueprintOnboardingHint';
import BlueprintOperationalPosture from './BlueprintOperationalPosture';
import BlueprintProactiveInsights from './BlueprintProactiveInsights';
import BlueprintScenarioStrip from './BlueprintScenarioStrip';
import BlueprintSimulationBanner from './BlueprintSimulationBanner';
import { useBlueprintFlowPulse } from '@/hooks/useBlueprintFlowPulse';
import { resolveNodeDecision } from '@/lib/architectureConsultingPayload';
import NodeDetailsDrawer from './NodeDetailsDrawer';
import { buildArchitectureFlow } from '@/lib/architectureLayout';
import {
  buildBlueprintConsultingSummary,
  buildGuidedPipelineSteps,
} from '@/lib/architectureBlueprintNarrative';
import { getActiveStageId, getFocusNodeIds } from '@/lib/architectureFocus';
import { getStageIdForCategory } from '@/lib/architectureStages';
import {
  filterSimpleArchitecture,
  parseArchitecturePayload,
} from '@/lib/architecturePayload';
import { useChatStore } from '@/stores/chatStore';
import type { ArchNode } from '@/types/chat';

const nodeTypes = {
  archModule: ArchModuleNode,
  stageGroup: ArchStageGroupNode,
};

type ViewMode = 'simple' | 'technical';

interface ArchitectureCanvasInnerProps {
  data: Record<string, unknown>;
  showCodeDrawer?: boolean;
  immersive?: boolean;
}

function ArchitectureCanvasInner({ data, showCodeDrawer, immersive }: ArchitectureCanvasInnerProps) {
  const parsed = useMemo(() => parseArchitecturePayload(data), [data]);
  const sendMessage = useChatStore((s) => s.sendMessage);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const constraintState = useChatStore((s) => s.constraintState);
  const activePlaybookId = useChatStore((s) => s.activePlaybookId);
  const lastExplain = useChatStore((s) => s.lastRecommendationExplain);
  const { fitView, setViewport } = useReactFlow();

  const [viewMode, setViewMode] = useState<ViewMode>('simple');
  const [selectedNode, setSelectedNode] = useState<ArchNode | null>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [canvasRevealed, setCanvasRevealed] = useState(false);
  const [adaptationDismissed, setAdaptationDismissed] = useState(false);
  const [comparisonHidden, setComparisonHidden] = useState(false);
  const [strategyComparisonHidden, setStrategyComparisonHidden] = useState(false);

  const shortlistSlugs = useMemo(() => {
    const fromExplain = lastExplain?.shortlist;
    if (fromExplain?.length) return fromExplain;
    return parsed.shortlistSlugs;
  }, [lastExplain?.shortlist, parsed.shortlistSlugs]);

  const architectureConsulting = parsed.architectureConsulting;

  const consultingSummary = useMemo(
    () =>
      buildBlueprintConsultingSummary({
        title: parsed.title,
        playbookId: activePlaybookId,
        constraintState,
        explain: lastExplain,
        nodes: parsed.nodes,
        consulting: architectureConsulting,
      }),
    [
      parsed.title,
      parsed.nodes,
      activePlaybookId,
      constraintState,
      lastExplain,
      architectureConsulting,
    ]
  );

  const evolution = architectureConsulting?.evolution ?? null;
  const scaleAtmosphere = architectureConsulting?.scale_atmosphere ?? 'production';

  const showEvolution =
    !adaptationDismissed && evolution && evolution.replacements.length > 0;

  useEffect(() => {
    setAdaptationDismissed(false);
  }, [evolution?.summary, architectureConsulting?.adaptation?.message]);

  const { nodes: displayNodes, edges: displayEdges } = useMemo(() => {
    if (viewMode === 'simple') {
      return filterSimpleArchitecture(parsed.nodes, parsed.edges);
    }
    return { nodes: parsed.nodes, edges: parsed.edges };
  }, [parsed.nodes, parsed.edges, viewMode]);

  const focusIds = useMemo(
    () => getFocusNodeIds(selectedNode?.id ?? null, displayEdges),
    [selectedNode?.id, displayEdges]
  );

  const stageIdsPresent = useMemo(() => {
    const ids = new Set<string>();
    displayNodes.forEach((n) => ids.add(getStageIdForCategory(n.category, n.slug)));
    return [...ids].filter((id) => id !== 'other');
  }, [displayNodes]);

  const activeStageId = useMemo(() => {
    if (selectedNode) return getActiveStageId(selectedNode);
    if (hoveredId) {
      const n = displayNodes.find((x) => x.id === hoveredId);
      return n ? getStageIdForCategory(n.category, n.slug) : null;
    }
    return null;
  }, [selectedNode, hoveredId, displayNodes]);

  const guidedSteps = useMemo(
    () => buildGuidedPipelineSteps(displayNodes, stageIdsPresent),
    [displayNodes, stageIdsPresent]
  );

  const evolvedNodeIds = useMemo(() => {
    const set = new Set<string>();
    if (!evolution?.changed_node_ids) return set;
    for (const id of evolution.changed_node_ids) {
      set.add(id);
      const match = displayNodes.find(
        (n) => n.id === id || n.slug === id || n.category === id
      );
      if (match) {
        set.add(match.id);
        if (match.slug) set.add(match.slug);
      }
    }
    return set;
  }, [evolution?.changed_node_ids, displayNodes]);

  const flowPulseStageId = useBlueprintFlowPulse(
    stageIdsPresent,
    Boolean(selectedNode || hoveredId)
  );
  const flowActiveStageId = activeStageId ?? flowPulseStageId;

  const layout = useMemo(
    () =>
      buildArchitectureFlow(displayNodes, displayEdges, {
        viewMode,
        layoutMode: 'stages',
        focusIds: selectedNode
          ? focusIds
          : hoveredId
            ? getFocusNodeIds(hoveredId, displayEdges)
            : null,
        highlightedId: parsed.highlightedNode,
        selectedId: selectedNode?.id,
        activeStageId: selectedNode ? activeStageId : null,
        hoveredId,
        shortlistSlugs,
        evolvedNodeIds,
        flowActiveStageId,
      }),
    [
      displayNodes,
      displayEdges,
      viewMode,
      focusIds,
      parsed.highlightedNode,
      selectedNode?.id,
      activeStageId,
      hoveredId,
      selectedNode,
      shortlistSlugs,
      evolvedNodeIds,
      flowActiveStageId,
    ]
  );

  const flowNodes = useMemo(() => {
    return layout.nodes.map((n) => {
      if (n.type !== 'archModule') return n;
      const arch = displayNodes.find((a) => a.id === n.id);
      if (!arch) return n;
      const decision = resolveNodeDecision(architectureConsulting, arch);
      return {
        ...n,
        data: {
          ...n.data,
          fitStrength: decision?.fit_strength,
        },
      };
    });
  }, [layout.nodes, displayNodes, architectureConsulting]);

  const flowEdges = useMemo(() => layout.edges, [layout.edges]);

  const simulation = architectureConsulting?.simulation;
  const strategyComparison = architectureConsulting?.strategy_comparison;
  const comparisonBaseline = parsed.comparisonBaseline;
  const showComparison =
    !comparisonHidden && comparisonBaseline && parsed.simulationActive && !strategyComparison;
  const showStrategyComparison =
    !strategyComparisonHidden &&
    strategyComparison &&
    parsed.strategyMode === 'dual';

  const nodeById = useMemo(() => {
    const map = new Map<string, ArchNode>();
    displayNodes.forEach((n) => map.set(n.id, n));
    return map;
  }, [displayNodes]);

  const fitDiagram = useCallback(() => {
    fitView({ padding: immersive ? 0.1 : 0.16, duration: 420, maxZoom: 1.05 });
  }, [fitView, immersive]);

  const resetViewport = useCallback(() => {
    setViewport({ x: 0, y: 0, zoom: 1 }, { duration: 360 });
  }, [setViewport]);

  useEffect(() => {
    setCanvasRevealed(false);
    const reveal = window.setTimeout(() => setCanvasRevealed(true), 40);
    return () => window.clearTimeout(reveal);
  }, [viewMode, displayNodes.length]);

  useEffect(() => {
    const t = window.setTimeout(() => fitDiagram(), 120);
    return () => window.clearTimeout(t);
  }, [fitDiagram, flowNodes.length, viewMode, selectedNode?.id]);

  const onNodeClick: NodeMouseHandler = useCallback(
    (_evt, node) => {
      if (node.type !== 'archModule') return;
      const arch = nodeById.get(node.id);
      if (arch) setSelectedNode(arch);
    },
    [nodeById]
  );

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const onNodeMouseEnter: NodeMouseHandler = useCallback((_evt, node) => {
    if (node.type === 'archModule') setHoveredId(node.id);
  }, []);

  const onNodeMouseLeave: NodeMouseHandler = useCallback(() => {
    setHoveredId(null);
  }, []);

  const sendNodeAction = useCallback(
    (action: 'learn' | 'swap' | 'code') => {
      if (!selectedNode || isStreaming) return;
      const label = selectedNode.label;
      const nodeContext = {
        id: selectedNode.id,
        label: selectedNode.label,
        slug: selectedNode.slug,
        category: selectedNode.category,
      };
      const messages = {
        learn: `Explain why ${label} was chosen in this architecture and what tradeoffs apply`,
        swap: `What alternatives can I use instead of ${label} in this stack?`,
        code: `Show integration code and deployment guidance for ${label}`,
      };
      sendMessage(messages[action], {
        focus_module_slug: selectedNode.slug,
        architecture_node: nodeContext,
        current_panel: 'interactive_architecture',
      });
    },
    [selectedNode, isStreaming, sendMessage]
  );

  const hoveredNode = hoveredId ? nodeById.get(hoveredId) : null;

  if (parsed.nodes.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <p className="text-[var(--text-muted)]">No architecture data to display</p>
      </div>
    );
  }

  return (
    <div
      className={`blueprint-root flex flex-col blueprint-scale-${scaleAtmosphere}`}
    >
      {simulation && (
        <BlueprintSimulationBanner label={simulation.label} narrative={simulation.narrative} />
      )}

      {showEvolution && evolution && !simulation && (
        <BlueprintEvolutionPanel
          evolution={evolution}
          adaptationMessage={architectureConsulting?.adaptation?.message}
          onDismiss={() => setAdaptationDismissed(true)}
        />
      )}

      {architectureConsulting?.consulting_continuity && (
        <BlueprintConsultingContinuity message={architectureConsulting.consulting_continuity} />
      )}

      <BlueprintStrategyWorkspace
        consulting={architectureConsulting}
        currentTitle={parsed.title || 'Current architecture'}
        disabled={isStreaming}
      />

      {showStrategyComparison && strategyComparison && (
        <BlueprintStrategyComparison
          comparison={strategyComparison}
          onClose={() => setStrategyComparisonHidden(true)}
        />
      )}

      {showComparison && comparisonBaseline && (
        <BlueprintComparisonWorkspace
          baseline={comparisonBaseline}
          currentTitle={parsed.title || 'Simulated architecture'}
          onClose={() => setComparisonHidden(true)}
        />
      )}

      <BlueprintConsultingHeader
        summary={consultingSummary}
        viewMode={viewMode}
        onViewModeChange={(mode) => {
          setViewMode(mode);
          setSelectedNode(null);
        }}
        onFit={fitDiagram}
        onReset={resetViewport}
      />

      <BlueprintGuidedNarrative steps={guidedSteps} activeStageId={flowActiveStageId} />

      <BlueprintOperationalPosture
        posture={architectureConsulting?.operational_posture}
        stress={architectureConsulting?.operational_stress}
      />

      <BlueprintProactiveInsights insights={architectureConsulting?.proactive_insights ?? []} />

      <BlueprintStrategicForecasts forecasts={architectureConsulting?.strategic_forecasts ?? []} />

      <BlueprintTradeoffSimulator
        levers={architectureConsulting?.tradeoff_simulator}
        disabled={isStreaming}
      />

      <BlueprintArchitectureSandbox
        sandbox={architectureConsulting?.architecture_sandbox}
        disabled={isStreaming}
      />

      <BlueprintStrategicIntelligence consulting={architectureConsulting} />

      <BlueprintStrategicTimeline consulting={architectureConsulting} />

      <BlueprintStrategyBranches branches={architectureConsulting?.strategy_branches ?? []} />

      {!architectureConsulting?.strategic_timeline?.length && (
        <BlueprintEvolutionHistory entries={architectureConsulting?.evolution_history ?? []} />
      )}

      {architectureConsulting?.lifecycle_notes &&
        architectureConsulting.lifecycle_notes.length > 0 && (
          <div className="shrink-0 border-b border-[var(--border-subtle)] px-4 py-2 text-xs text-[var(--text-muted)] md:px-5">
            <span className="font-medium text-[var(--text-secondary)]">Lifecycle · </span>
            {architectureConsulting.lifecycle_notes[0]}
          </div>
        )}

      <BlueprintDecisionTimeline entries={architectureConsulting?.decision_timeline ?? []} />

      <BlueprintScenarioStrip disabled={isStreaming} />

      <BlueprintFlowLegend
        activeStageId={activeStageId}
        flowPulseStageId={flowPulseStageId}
        stageIdsPresent={stageIdsPresent}
      />

      <div
        className={`blueprint-canvas-shell relative flex ${
          showCodeDrawer ? 'min-h-[280px] h-[38vh]' : ''
        }`}
      >
        <div
          className={`blueprint-canvas-area relative h-full min-h-0 w-full flex-1 ${
            canvasRevealed ? 'blueprint-canvas-revealed' : ''
          } ${selectedNode || hoveredId ? 'path-emphasis' : ''}`}
        >
          <ReactFlow
            nodes={flowNodes as Node[]}
            edges={flowEdges}
            nodeTypes={nodeTypes}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            onNodeMouseEnter={onNodeMouseEnter}
            onNodeMouseLeave={onNodeMouseLeave}
            fitView={false}
            minZoom={0.28}
            maxZoom={1.55}
            defaultViewport={{ x: 32, y: 32, zoom: 0.9 }}
            proOptions={{ hideAttribution: true }}
            nodesDraggable={false}
            nodesConnectable={false}
            elementsSelectable
            panOnScroll
            zoomOnScroll
            zoomOnPinch
            panOnDrag
            className={`arch-flow-canvas h-full min-h-[320px] bg-[var(--background)] ${
              selectedNode || hoveredId ? 'arch-path-emphasis' : ''
            }`}
          >
            <Background
              variant={BackgroundVariant.Dots}
              gap={26}
              size={1}
              color="var(--border-subtle)"
            />
            <Controls
              showInteractive={false}
              position="bottom-right"
              className="!rounded-lg !border-[var(--border-subtle)] !bg-[var(--surface-panel)] !shadow-[var(--shadow-soft)]"
            />
          </ReactFlow>

          <BlueprintOnboardingHint />

          {!selectedNode && !hoveredId && (
            <div
              className="blueprint-query-flow-cue pointer-events-none absolute right-4 top-4 z-10 flex items-center gap-1.5 rounded-md border border-[var(--border-subtle)] bg-[var(--surface-panel)]/90 px-2 py-1 text-[10px] text-[var(--text-muted)]"
              aria-hidden
            >
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent)]" />
              Query traversal
            </div>
          )}

          {hoveredNode && !selectedNode && (
            <div
              className="pointer-events-none absolute bottom-16 left-4 z-10 max-w-sm rounded-xl border border-[var(--border-subtle)] px-4 py-3 shadow-[var(--shadow-elevated)] transition-opacity duration-300"
              style={{ background: 'var(--tooltip-bg)' }}
            >
              <p className="text-sm font-semibold text-[var(--foreground)]">{hoveredNode.label}</p>
              {hoveredNode.description && (
                <p className="mt-1 line-clamp-2 text-xs text-[var(--text-secondary)]">
                  {hoveredNode.description}
                </p>
              )}
            </div>
          )}
        </div>

        {selectedNode && (
          <NodeDetailsDrawer
            node={selectedNode}
            consulting={architectureConsulting}
            onClose={() => setSelectedNode(null)}
            onLearn={() => sendNodeAction('learn')}
            onSwap={() => sendNodeAction('swap')}
            onCode={() => sendNodeAction('code')}
            disabled={isStreaming}
          />
        )}
      </div>
    </div>
  );
}

interface ArchitectureCanvasProps {
  data: Record<string, unknown>;
  showCodeDrawer?: boolean;
  immersive?: boolean;
}

export default function ArchitectureCanvas(props: ArchitectureCanvasProps) {
  return (
    <ReactFlowProvider>
      <ArchitectureCanvasInner {...props} />
    </ReactFlowProvider>
  );
}
