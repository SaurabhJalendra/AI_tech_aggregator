import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { usePanelStore } from '@/stores/panelStore';

describe('panelStore', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    usePanelStore.setState({
      currentPanel: 'welcome',
      panelData: {},
      panelTitle: undefined,
      panelHistory: [],
      pendingRender: null,
    });
  });

  afterEach(() => {
    const pending = usePanelStore.getState().pendingRender;
    if (pending) clearTimeout(pending.timeout);
    vi.useRealTimers();
  });

  it('should initialize with welcome panel', () => {
    const state = usePanelStore.getState();
    expect(state.currentPanel).toBe('welcome');
    expect(state.panelData).toEqual({});
  });

  it('should render a new panel and push history', () => {
    usePanelStore.getState().renderPanel({
      action: 'render',
      panel: 'comparison_chart',
      data: { modules: ['a', 'b'] },
      title: 'Compare',
    });
    vi.runAllTimers();

    const state = usePanelStore.getState();
    expect(state.currentPanel).toBe('comparison_chart');
    expect(state.panelData).toEqual({ modules: ['a', 'b'] });
    expect(state.panelTitle).toBe('Compare');
    expect(state.panelHistory).toHaveLength(1);
    expect(state.panelHistory[0].panel).toBe('welcome');
  });

  it('should update current panel data', () => {
    usePanelStore.getState().renderPanel({
      action: 'render',
      panel: 'code_preview',
      data: { code: 'hello' },
    });
    vi.runAllTimers();

    usePanelStore.getState().renderPanel({
      action: 'update',
      panel: 'code_preview',
      data: { language: 'python' },
    });

    const state = usePanelStore.getState();
    expect(state.panelData).toEqual({ code: 'hello', language: 'python' });
  });

  it('should clear panel to welcome', () => {
    usePanelStore.getState().renderPanel({
      action: 'render',
      panel: 'code_preview',
      data: { code: 'test' },
    });
    vi.runAllTimers();

    usePanelStore.getState().renderPanel({
      action: 'clear',
      panel: 'welcome',
      data: {},
    });

    expect(usePanelStore.getState().currentPanel).toBe('welcome');
  });

  it('should go back in history', () => {
    usePanelStore.getState().renderPanel({
      action: 'render',
      panel: 'comparison_chart',
      data: { x: 1 },
    });
    vi.runAllTimers();
    usePanelStore.getState().renderPanel({
      action: 'render',
      panel: 'code_preview',
      data: { y: 2 },
    });
    vi.runAllTimers();

    usePanelStore.getState().goBack();

    const state = usePanelStore.getState();
    expect(state.currentPanel).toBe('comparison_chart');
    expect(state.panelData).toEqual({ x: 1 });
    expect(state.panelHistory).toHaveLength(1);
  });

  it('should go back to welcome when history is empty', () => {
    usePanelStore.getState().renderPanel({
      action: 'render',
      panel: 'code_preview',
      data: {},
    });
    vi.runAllTimers();

    usePanelStore.getState().goBack();

    expect(usePanelStore.getState().currentPanel).toBe('welcome');
    expect(usePanelStore.getState().panelHistory).toHaveLength(0);
  });

  it('should apply only the last render in a burst', () => {
    usePanelStore.getState().renderPanel({
      action: 'render',
      panel: 'comparison_chart',
      data: { first: true },
    });
    usePanelStore.getState().renderPanel({
      action: 'render',
      panel: 'code_preview',
      data: { second: true },
    });

    vi.runAllTimers();

    const state = usePanelStore.getState();
    expect(state.currentPanel).toBe('code_preview');
    expect(state.panelData).toEqual({ second: true });
  });

  it('should ignore stale updates for inactive panels', () => {
    usePanelStore.getState().renderPanel({
      action: 'render',
      panel: 'code_preview',
      data: { code: 'hello' },
    });
    vi.runAllTimers();

    usePanelStore.getState().renderPanel({
      action: 'update',
      panel: 'interactive_architecture',
      data: {
        subAction: 'add_node',
        node: { id: 'n1', label: 'Node' },
      },
    });

    expect(usePanelStore.getState().panelData).toEqual({ code: 'hello' });
  });

  it('should flush pending render before matching incremental update', () => {
    usePanelStore.getState().renderPanel({
      action: 'render',
      panel: 'interactive_architecture',
      data: { nodes: [], edges: [] },
    });

    usePanelStore.getState().renderPanel({
      action: 'update',
      panel: 'interactive_architecture',
      data: {
        subAction: 'add_node',
        node: { id: 'n1', label: 'Node' },
      },
    });

    const state = usePanelStore.getState();
    expect(state.currentPanel).toBe('interactive_architecture');
    expect(state.panelData.nodes).toEqual([{ id: 'n1', label: 'Node' }]);
  });

  it('should set panel directly', () => {
    usePanelStore.getState().setPanel('architecture_diagram', { nodes: [] }, 'Arch');

    const state = usePanelStore.getState();
    expect(state.currentPanel).toBe('architecture_diagram');
    expect(state.panelTitle).toBe('Arch');
    expect(state.panelHistory).toHaveLength(1);
  });
});
