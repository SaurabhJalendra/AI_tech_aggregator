import { describe, it, expect, beforeEach } from 'vitest';
import { usePanelStore } from '@/stores/panelStore';

describe('panelStore', () => {
  beforeEach(() => {
    usePanelStore.setState({
      currentPanel: 'welcome',
      panelData: {},
      panelTitle: undefined,
      panelHistory: [],
    });
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
    usePanelStore.getState().renderPanel({
      action: 'render',
      panel: 'code_preview',
      data: { y: 2 },
    });

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

    usePanelStore.getState().goBack();

    expect(usePanelStore.getState().currentPanel).toBe('welcome');
    expect(usePanelStore.getState().panelHistory).toHaveLength(0);
  });

  it('should set panel directly', () => {
    usePanelStore.getState().setPanel('architecture_diagram', { nodes: [] }, 'Arch');

    const state = usePanelStore.getState();
    expect(state.currentPanel).toBe('architecture_diagram');
    expect(state.panelTitle).toBe('Arch');
    expect(state.panelHistory).toHaveLength(1);
  });
});
