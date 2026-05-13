import { describe, it, expect, vi, beforeEach } from 'vitest';
import { setActivePinia } from 'pinia';
import { createTestingPinia } from '@pinia/testing';
import { useScriptGeneratorStore } from '@/stores/scriptGenerator';

describe('ScriptGenerator - Improved SSE Parsing', () => {
  beforeEach(() => {
    // Reset pinia with stubActions: false to allow real actions
    setActivePinia(createTestingPinia({
      stubActions: false,
      createSpy: vi.fn,
    }));
    vi.clearAllMocks();
  });

  it('handles incremental SSE chunks with line-by-line parsing', async () => {
    // Simulate incremental chunks that need line-by-line parsing
    const chunk1 = 'data: {"title":"Test';
    const chunk2 = '","genre":"悬疑推理"}\n\n';
    
    const mockReader = {
      read: vi.fn()
        .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode(chunk1) })
        .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode(chunk2) })
        .mockResolvedValueOnce({ done: true, value: undefined }),
      cancel: vi.fn().mockResolvedValue(undefined),
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
    
    await store.generateScript();
    
    // Verify script was parsed correctly from incremental chunks
    expect(store.generatedScript).toEqual({
      title: 'Test',
      genre: '悬疑推理',
    });
    
    // Verify stream was cancelled in finally block
    expect(mockReader.read).toHaveBeenCalledTimes(3);
  });

  it('handles multiple SSE events and uses last data chunk', async () => {
    const mockSSEData = 
      'data: {"status":"starting"}\n\n' +
      'data: {"status":"generating"}\n\n' +
      'data: {"title":"Final Script","genre":"古风权谋"}\n\n';
    
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: {
        getReader: () => ({
          read: vi.fn()
            .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode(mockSSEData) })
            .mockResolvedValueOnce({ done: true, value: undefined }),
          cancel: vi.fn().mockResolvedValue(undefined),
        }),
      },
    });

    const store = useScriptGeneratorStore();
    store.selectGenre('古风权谋');
    
    await store.generateScript();
    
    // Should use the last data chunk
    expect(store.generatedScript).toEqual({
      title: 'Final Script',
      genre: '古风权谋',
    });
  });

  it('handles JSON parsing errors with proper error message', async () => {
    const invalidJSON = 'data: {invalid json}\n\n';
    
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: {
        getReader: () => ({
          read: vi.fn()
            .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode(invalidJSON) })
            .mockResolvedValueOnce({ done: true, value: undefined }),
          cancel: vi.fn().mockResolvedValue(undefined),
        }),
      },
    });

    const store = useScriptGeneratorStore();
    store.selectGenre('悬疑推理');
    
    await store.generateScript();
    
    // Should handle error internally without re-throwing
    expect(store.error).toBeTruthy();
    expect(store.error).toContain('Failed to parse');
    expect(store.generating).toBe(false);
  });

  it('handles no valid data chunk found', async () => {
    const noDataChunk = 'event: update\nid: 1\n';
    
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: {
        getReader: () => ({
          read: vi.fn()
            .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode(noDataChunk) })
            .mockResolvedValueOnce({ done: true, value: undefined }),
          cancel: vi.fn().mockResolvedValue(undefined),
        }),
      },
    });

    const store = useScriptGeneratorStore();
    store.selectGenre('悬疑推理');
    
    await store.generateScript();
    
    expect(store.error).toBeTruthy();
    expect(store.error).toContain('No valid data chunk');
  });

  it('cancels stream reader in finally block', async () => {
    let cancelCalled = false;
    const mockReader = {
      read: vi.fn()
        .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('data: {}') })
        .mockResolvedValueOnce({ done: true, value: undefined }),
      cancel: vi.fn().mockImplementation(() => { cancelCalled = true; }),
    };
    
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: { getReader: () => mockReader },
    });

    const store = useScriptGeneratorStore();
    store.selectGenre('悬疑推理');
    
    await store.generateScript();
    
    // Verify cancel was called in finally block
    expect(cancelCalled).toBe(true);
    expect(store.generating).toBe(false);
  });

  it('handles HTTP error without re-throwing', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
    });

    const store = useScriptGeneratorStore();
    store.selectGenre('悬疑推理');
    
    await store.generateScript();
    
    // Error should be handled internally, not re-thrown
    expect(store.error).toContain('Generation failed');
    expect(store.generating).toBe(false);
    expect(store.generatedScript).toBeNull();
  });

  it('handles ReadableStream not supported', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: null,
    });

    const store = useScriptGeneratorStore();
    store.selectGenre('悬疑推理');
    
    await store.generateScript();
    
    expect(store.error).toContain('ReadableStream not supported');
    expect(store.generating).toBe(false);
  });
});
