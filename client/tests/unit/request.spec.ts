import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { fetchWithTimeout, RequestTimeoutError } from '@/utils/request';

describe('fetchWithTimeout', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should abort request after timeout', async () => {
    global.fetch.mockImplementation((url: string, options?: RequestInit) => 
      new Promise((_, reject) => {
        // Simulate hanging request that never resolves
        // The abort signal should interrupt this
        if (options?.signal) {
          options.signal.addEventListener('abort', () => {
            reject(new DOMException('Aborted', 'AbortError'));
          });
        }
      })
    );
    
    await expect(
      fetchWithTimeout('/api/test', { timeout: 100 })
    ).rejects.toThrow(RequestTimeoutError);
  });

  it('should respect external abort signal', async () => {
    const controller = new AbortController();
    
    global.fetch.mockImplementation((url: string, options?: RequestInit) => 
      new Promise((_, reject) => {
        if (options?.signal) {
          options.signal.addEventListener('abort', () => {
            reject(new DOMException('Aborted', 'AbortError'));
          });
        }
      })
    );
    
    const promise = fetchWithTimeout('/api/test', { 
      timeout: 10000,
      signal: controller.signal
    });
    
    controller.abort();
    
    await expect(promise).rejects.toThrow('Aborted');
  });

  it('should complete successfully before timeout', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: () => ({ data: 'test' }) });
    
    const response = await fetchWithTimeout('/api/test', { timeout: 1000 });
    
    expect(response.ok).toBe(true);
  });
});
