import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useGameStore } from '../../src/stores/game';
import { createPinia, setActivePinia } from 'pinia';
import type { WSMessage } from '../../src/types/ws';

describe('Game Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('initializes with correct defaults', () => {
    const store = useGameStore();
    expect(store.phase).toBe('waiting');
    expect(store.act).toBe(1);
    expect(store.currentEvent).toBe('');
    expect(store.publicMessages).toEqual([]);
    expect(store.privateMessages).toEqual([]);
    expect(store.clues).toEqual([]);
    expect(store.roleCard.layer1).toBeNull();
    expect(store.roleCard.layer2).toBeNull();
    expect(store.roleCard.layer3).toBeNull();
  });

  it('handles event message', () => {
    const store = useGameStore();
    store.handleWSMessage({ type: 'event', content: '月光洒在书房地板上' });
    expect(store.currentEvent).toBe('月光洒在书房地板上');
    expect(store.publicMessages.length).toBe(1);
    expect(store.publicMessages[0].from).toBe('🎭 DM');
    expect(store.publicMessages[0].isEvent).toBe(true);
  });

  it('handles chat message', () => {
    const store = useGameStore();
    store.handleWSMessage({ type: 'chat', from: '张三', from_player_id: 'p1', content: '大家好', timestamp: '' });
    expect(store.publicMessages.length).toBe(1);
    expect(store.publicMessages[0].from).toBe('张三');
    expect(store.publicMessages[0].content).toBe('大家好');
  });

  it('deduplicates chat messages', () => {
    const store = useGameStore();
    store.handleWSMessage({ type: 'chat', from: '张三', from_player_id: 'p1', content: '大家好', timestamp: '' });
    store.handleWSMessage({ type: 'chat', from: '张三', from_player_id: 'p1', content: '大家好', timestamp: '' });
    expect(store.publicMessages.length).toBe(1);
  });

  it('handles role_card layer 1', () => {
    const store = useGameStore();
    store.handleWSMessage({ type: 'role_card', layer: '1', player_id: 'p1', data: { name: '林默', description: '神秘侦探' } });
    expect(store.roleCard.layer1).toEqual({ name: '林默', description: '神秘侦探' });
  });

  it('handles role_card layer 2', () => {
    const store = useGameStore();
    store.handleWSMessage({ type: 'role_card', layer: '2', player_id: 'p1', data: { background: '背景', secret_task: '秘密任务', alibi: '不在场证明' } });
    expect(store.roleCard.layer2).toEqual({ background: '背景', secret_task: '秘密任务', alibi: '不在场证明' });
  });

  it('handles role_card layer 3', () => {
    const store = useGameStore();
    store.handleWSMessage({ type: 'role_card', layer: '3', player_id: 'p1', data: { motive: '复仇', relationships: [] } });
    expect(store.roleCard.layer3).toEqual({ motive: '复仇', relationships: [] });
  });

  it('handles dm_private message', () => {
    const store = useGameStore();
    store.handleWSMessage({ type: 'dm_private', from: '__dm__', to: 'p1', content: '你的袖口有血迹' });
    expect(store.privateMessages.length).toBe(1);
    expect(store.privateMessages[0].from).toBe('🎭 DM');
    expect(store.privateMessages[0].content).toBe('你的袖口有血迹');
  });

  it('deduplicates dm_private messages', () => {
    const store = useGameStore();
    store.handleWSMessage({ type: 'dm_private', from: '__dm__', to: 'p1', content: '你的袖口有血迹' });
    store.handleWSMessage({ type: 'dm_private', from: '__dm__', to: 'p1', content: '你的袖口有血迹' });
    expect(store.privateMessages.length).toBe(1);
  });

  it('handles clue_unlock', () => {
    const store = useGameStore();
    store.handleWSMessage({
      type: 'clue_unlock',
      player_id: 'p1',
      clue: { id: 'c1', title: '血迹', content: '地板上有血迹', content_hint: '注意颜色', is_red_herring: false },
    });
    expect(store.clues.length).toBe(1);
    expect(store.clues[0].id).toBe('c1');
    expect(store.clues[0].title).toBe('血迹');
  });

  it('deduplicates clues by id', () => {
    const store = useGameStore();
    store.handleWSMessage({
      type: 'clue_unlock',
      player_id: 'p1',
      clue: { id: 'c1', title: '血迹', content: '地板上有血迹', content_hint: '提示', is_red_herring: false },
    });
    store.handleWSMessage({
      type: 'clue_unlock',
      player_id: 'p1',
      clue: { id: 'c1', title: '血迹', content: '地板上有血迹', content_hint: '提示', is_red_herring: false },
    });
    expect(store.clues.length).toBe(1);
  });

  it('handles phase_unlock', () => {
    const store = useGameStore();
    store.handleWSMessage({ type: 'phase_unlock', phase: 'playing', act: 2 });
    expect(store.phase).toBe('playing');
    expect(store.act).toBe(2);
  });

  it('handles phase_unlock with invalid phase', () => {
    const store = useGameStore();
    store.handleWSMessage({ type: 'phase_unlock', phase: 'invalid_phase', act: 5 });
    expect(store.phase).toBe('waiting');
    expect(store.act).toBe(1);
  });

  it('handles player_joined', () => {
    const store = useGameStore();
    store.handleWSMessage({ type: 'player_joined', player_id: 'p1', player_name: '张三' });
    expect(store.players.has('p1')).toBe(true);
    expect(store.players.get('p1')!.name).toBe('张三');
  });

  it('handles player_left by id', () => {
    const store = useGameStore();
    store.handleWSMessage({ type: 'player_joined', player_id: 'p1', player_name: '张三' });
    store.handleWSMessage({ type: 'player_left', player_id: 'p1', player_name: '张三' });
    expect(store.players.has('p1')).toBe(false);
  });

  it('handles accusation', () => {
    const store = useGameStore();
    store.handleWSMessage({ type: 'accusation', from: '张三', target: '李四', reasoning: '他很可疑' });
    expect(store.publicMessages.length).toBe(1);
    expect(store.publicMessages[0].content).toBe('他很可疑');
  });

  it('handles vote_cast', () => {
    const store = useGameStore();
    store.handleWSMessage({ type: 'vote_cast', from: '张三', from_player_id: 'p1', target: '李四' });
    expect(store.publicMessages.length).toBe(1);
    expect(store.publicMessages[0].content).toBe('');
  });

  it('handles trial_start', () => {
    const store = useGameStore();
    store.handleWSMessage({ type: 'trial_start', accusations: [] });
    expect(store.phase).toBe('trial');
    expect(store.act).toBe(3);
  });

  it('handles reveal', () => {
    const store = useGameStore();
    store.handleWSMessage({ type: 'reveal', truth: {}, player_evaluations: {} });
    expect(store.phase).toBe('revealed');
  });

  it('handles game_over', () => {
    const store = useGameStore();
    store.handleWSMessage({ type: 'game_over', result: 'correct' });
    expect(store.phase).toBe('finished');
  });

  it('handles act_transition with auto-dismiss banner', () => {
    vi.useFakeTimers();
    const store = useGameStore();
    store.handleWSMessage({ type: 'act_transition', act: 2, plot_summary: '调查开始' });
    expect(store.actBanner).toEqual({ act: 2, plot_summary: '调查开始' });
    vi.advanceTimersByTime(8000);
    expect(store.actBanner).toBeNull();
    vi.useRealTimers();
  });

  it('handles private_chat', () => {
    const store = useGameStore();
    store.handleWSMessage({ type: 'private_chat', from: 'p2', content: '私下说两句', timestamp: '' });
    expect(store.privateMessages.length).toBe(1);
    expect(store.privateMessages[0].content).toBe('私下说两句');
  });

  it('loadPublicMessagesFromAPI adds messages', () => {
    const store = useGameStore();
    store.loadPublicMessagesFromAPI([
      { from_player_name: '张三', content: '大家好', type: 'public', timestamp: '2024-01-01' },
      { from_player_name: '🎭 DM', content: '游戏开始', type: 'event', timestamp: '2024-01-01' },
    ]);
    expect(store.publicMessages.length).toBe(2);
  });

  it('loadPublicMessagesFromAPI deduplicates', () => {
    const store = useGameStore();
    store.loadPublicMessagesFromAPI([
      { from_player_name: '张三', content: '大家好', type: 'public', timestamp: '2024-01-01' },
    ]);
    store.loadPublicMessagesFromAPI([
      { from_player_name: '张三', content: '大家好', type: 'public', timestamp: '2024-01-01' },
    ]);
    expect(store.publicMessages.length).toBe(1);
  });

  // Request cancellation tests
  it('should create and track abort controllers', () => {
    const store = useGameStore();
    
    const controller = store.getOrCreateController('test-key');
    
    expect(controller).toBeInstanceOf(AbortController);
    expect(store.requestControllers.has('test-key')).toBe(true);
  });

  it('should cancel existing controller when creating new one with same key', () => {
    const store = useGameStore();
    
    const firstController = store.getOrCreateController('test-key');
    const abortSpy = vi.spyOn(firstController.signal, 'aborted', 'get');
    abortSpy.mockReturnValue(false);
    
    store.getOrCreateController('test-key');
    
    // Old controller should be aborted and removed
    expect(store.requestControllers.has('test-key')).toBe(true);
    expect(store.requestControllers.get('test-key')).not.toBe(firstController);
  });

  it('should cancel specific request by key', () => {
    const store = useGameStore();
    
    const controller = store.getOrCreateController('test-key');
    const abortSpy = vi.fn();
    controller.signal.addEventListener('abort', abortSpy);
    
    store.cancelRequest('test-key');
    
    expect(abortSpy).toHaveBeenCalled();
    expect(store.requestControllers.has('test-key')).toBe(false);
  });

  it('should cancel all requests', () => {
    const store = useGameStore();
    
    const controller1 = store.getOrCreateController('key1');
    const controller2 = store.getOrCreateController('key2');
    const abortSpy1 = vi.fn();
    const abortSpy2 = vi.fn();
    
    controller1.signal.addEventListener('abort', abortSpy1);
    controller2.signal.addEventListener('abort', abortSpy2);
    
    store.cancelAllRequests();
    
    expect(abortSpy1).toHaveBeenCalled();
    expect(abortSpy2).toHaveBeenCalled();
    expect(store.requestControllers.size).toBe(0);
  });

  it('should handle abort errors silently', async () => {
    const store = useGameStore();
    const controller = store.getOrCreateController('test');
    
    // Simulate abort
    controller.abort();
    
    expect(controller.signal.aborted).toBe(true);
  });
});
