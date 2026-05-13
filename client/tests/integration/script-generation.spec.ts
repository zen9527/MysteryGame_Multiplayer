import { describe, it, expect, vi, beforeEach } from 'vitest';
import { setActivePinia } from 'pinia';
import { createTestingPinia } from '@pinia/testing';
import { useScriptGeneratorStore } from '@/stores/scriptGenerator';

describe('ScriptGenerator - SSE Generation', () => {
  beforeEach(() => {
    // Reset pinia with stubActions: false to allow real actions
    setActivePinia(createTestingPinia({
      stubActions: false,
      createSpy: vi.fn,
    }));
    vi.clearAllMocks();
  });

  it('calls generation API with form data and parses SSE response', async () => {
    // Mock SSE stream response
    const mockSSEData = 'data: {"title":"Test Script","genre":"悬疑推理","difficulty":"中等","player_count":5}\n\n';
    
    const mockReader = {
      read: vi.fn()
        .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode(mockSSEData) })
        .mockResolvedValueOnce({ done: true, value: undefined }),
    };
    
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: { getReader: () => mockReader },
    });

    const store = useScriptGeneratorStore();
    
    // Set form data
    store.selectGenre('悬疑推理');
    store.selectDifficulty('中等');
    store.setPlayerCount(5);
    
    // Call generateScript directly
    await store.generateScript();
    
    // Verify fetch was called with correct parameters
    expect(global.fetch).toHaveBeenCalledWith('/api/scripts/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        genre: '悬疑推理',
        difficulty: '中等',
        player_count: 5,
      }),
    });
    
    // Verify script was parsed and stored
    expect(store.generatedScript).toEqual({
      title: 'Test Script',
      genre: '悬疑推理',
      difficulty: '中等',
      player_count: 5,
    });
    
    // Verify state changes
    expect(store.generating).toBe(false);
    expect(store.error).toBeNull();
  });

  it('handles generation error and sets error state', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
    });

    const store = useScriptGeneratorStore();
    
    // Set form data
    store.selectGenre('悬疑推理');
    store.selectDifficulty('中等');
    store.setPlayerCount(4);
    
    // Call generateScript - it should throw but also set error state
    let thrownError: Error | null = null;
    try {
      await store.generateScript();
    } catch (err) {
      thrownError = err instanceof Error ? err : new Error(String(err));
    }
    
    // Verify error was thrown
    expect(thrownError).toBeTruthy();
    expect(thrownError?.message).toContain('Generation failed');
    
    // Verify error state
    expect(store.error).toContain('Generation failed');
    expect(store.generating).toBe(false);
    expect(store.generatedScript).toBeNull();
  });

  it('updates status during generation', async () => {
    const mockSSEData = 'data: {}\n\n';
    
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: {
        getReader: () => ({
          read: vi.fn()
            .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode(mockSSEData) })
            .mockResolvedValueOnce({ done: true, value: undefined }),
        }),
      },
    });

    const store = useScriptGeneratorStore();
    
    // Set form data
    store.selectGenre('悬疑推理');
    store.setPlayerCount(4);
    
    // Start generation
    await store.generateScript();
    
    // Verify final state
    expect(store.generating).toBe(false);
    expect(store.generatedScript).not.toBeNull();
  });

  it('provides retry capability by calling generateScript again', async () => {
    let callCount = 0;
    global.fetch = vi.fn().mockImplementation(() => {
      callCount++;
      if (callCount === 1) {
        return Promise.resolve({ ok: false, status: 500 });
      }
      return Promise.resolve({
        ok: true,
        body: {
          getReader: () => ({
            read: vi.fn()
              .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('data: {"title":"Retry Success"}\n\n') })
              .mockResolvedValueOnce({ done: true, value: undefined }),
          }),
        },
      });
    });

    const store = useScriptGeneratorStore();
    
    // Set form data
    store.selectGenre('悬疑推理');
    store.setPlayerCount(4);
    
    // First attempt - should fail
    try {
      await store.generateScript();
    } catch (e) {
      // Expected to fail
    }
    expect(store.error).not.toBeNull();
    
    // Clear error and retry
    store.error = null;
    await store.generateScript();
    
    // Verify success on retry
    expect(store.generatedScript?.title).toBe('Retry Success');
    expect(store.error).toBeNull();
    expect(callCount).toBe(2);
  });
});
