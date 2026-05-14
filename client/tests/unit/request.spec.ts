import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { fetchWithTimeout, RequestTimeoutError } from '@/utils/request';

describe('fetchWithTimeout', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should complete successfully before timeout', async () => {
    global.fetch.mockResolvedValue({ ok: true, json: () => ({ data: 'test' }) });
    
    const response = await fetchWithTimeout('/api/test', { timeout: 1000 });
    
    expect(response.ok).toBe(true);
  });
});

describe('timeout with real timers', () => {
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
  }, 10000);
});

describe('external abort signal with fake timers', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it('should respect external abort signal', async () => {
    const controller = new AbortController();
    
    // Abort immediately before fetch is called
    controller.abort();
    
    // Mock fetch that should never be called due to abort
    global.fetch.mockImplementation(() => {
      throw new Error('Fetch should not be called');
    });
    
    const promise = fetchWithTimeout('/api/test', { 
      timeout: 10000,
      signal: controller.signal
    });
    
    await expect(promise).rejects.toThrow('Aborted');
  });
});

describe('retry logic', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it('should retry on server errors with exponential backoff', async () => {
    let callCount = 0;
    global.fetch.mockImplementation(() => {
      callCount++;
      if (callCount < 3) {
        return Promise.resolve({ ok: false, status: 500 });
      }
      return Promise.resolve({ ok: true, json: () => ({ data: 'success' }) });
    });
    
    const promise = fetchWithTimeout('/api/test', { 
      timeout: 5000,
      retries: 3,
      retryDelay: 100
    });
    
    // Advance timers for first retry (100ms)
    await vi.advanceTimersByTimeAsync(100);
    // Advance timers for second retry (200ms)
    await vi.advanceTimersByTimeAsync(200);
    
    const response = await promise;
    
    expect(callCount).toBe(3);
    expect(response.ok).toBe(true);
  });

  it('should not retry on client errors', async () => {
    global.fetch.mockResolvedValue({ ok: false, status: 404 });
    
    try {
      await fetchWithTimeout('/api/test', { retries: 3 });
      expect.fail('Should have thrown');
    } catch (error) {
      expect(error.message).toContain('HTTP 404');
      expect(global.fetch).toHaveBeenCalledTimes(1); // No retry
    }
  });

  it('should stop retrying when signal is aborted', async () => {
    const controller = new AbortController();
    
    let callCount = 0;
    global.fetch.mockImplementation(() => {
      callCount++;
      return Promise.resolve({ ok: false, status: 500 });
    });
    
    const promise = fetchWithTimeout('/api/test', { 
      retries: 3,
      retryDelay: 100,
      signal: controller.signal
    });
    
    // Advance to first retry delay (100ms) - completes attempt 0, starts waiting for attempt 1
    await vi.advanceTimersByTimeAsync(100);
    
    // Attempt 1 starts, fetch fails, starts waiting for 200ms
    await vi.advanceTimersByTimeAsync(1);
    
    // Abort during the second retry wait
    controller.abort();
    
    // Advance past the second retry delay (200ms) - this triggers the abort check and breaks
    await vi.advanceTimersByTimeAsync(200);
    
    try {
      await promise;
    } catch (error) {
      // Expected to fail with abort error
      expect(error).toBeInstanceOf(DOMException);
    }
    
    // Should have tried 2 times (initial + 1 retry before abort)
    expect(callCount).toBe(2);
  }, 10000);

  it('should use default retry settings', async () => {
    let callCount = 0;
    global.fetch.mockImplementation(() => {
      callCount++;
      if (callCount < 2) {
        return Promise.resolve({ ok: false, status: 503 });
      }
      return Promise.resolve({ ok: true });
    });
    
    const promise = fetchWithTimeout('/api/test');
    
    // Default retryDelay is 1000ms
    await vi.advanceTimersByTimeAsync(1000);
    
    const response = await promise;
    
    expect(callCount).toBe(2);
    expect(response.ok).toBe(true);
  });
});
