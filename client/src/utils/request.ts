export class RequestTimeoutError extends Error {
  constructor(url: string) {
    super(`Request timeout: ${url}`);
    this.name = 'RequestTimeoutError';
  }
}

export interface RequestOptions {
  timeout?: number; // milliseconds, default 30s
  signal?: AbortSignal;
  retries?: number; // default 3
  retryDelay?: number; // base delay in ms, default 1000
}

export async function fetchWithTimeout(
  url: string,
  options: RequestInit & RequestOptions = {}
): Promise<Response> {
  const { 
    timeout = 30000, 
    signal: externalSignal, 
    retries = 3,
    retryDelay = 1000,
    ...fetchOptions 
  } = options;
  
  let lastError: Error | null = null;
  let attempt = 0;
  
  while (attempt <= retries) {
    // Check if external signal is already aborted before starting
    if (externalSignal?.aborted) {
      throw new DOMException('Aborted', 'AbortError');
    }
    
    const controller = new AbortController();
    const signals = [controller.signal];
    if (externalSignal) {
      signals.push(externalSignal);
    }
    const combinedSignal = signals.length === 1 ? signals[0] : AbortSignal.any(signals);
    
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
      const response = await fetch(url, {
        ...fetchOptions,
        signal: combinedSignal,
      });
      
      // Return successful requests immediately
      if (response.ok) {
        return response;
      }
      
      // Client errors (4xx) - throw immediately without retry
      if (response.status >= 400 && response.status < 500) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      // Server errors (5xx) - will retry
      lastError = new Error(`HTTP ${response.status}`);
      
    } catch (error) {
      const err = error as Error;
      // Check if this is a timeout abort (our controller aborted, not external)
      if (controller.signal.aborted && !externalSignal?.aborted) {
        throw new RequestTimeoutError(url);
      }
      // If it's a client error, re-throw immediately
      if (err.message.startsWith('HTTP 4')) {
        throw error;
      }
      lastError = err;
    } finally {
      clearTimeout(timeoutId);
    }
    
    // Wait before retry (exponential backoff)
    if (attempt < retries && !externalSignal?.aborted) {
      const delay = retryDelay * Math.pow(2, attempt);
      await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => resolve(true), delay);
        externalSignal?.addEventListener('abort', () => {
          clearTimeout(timeout);
          reject(new DOMException('Aborted', 'AbortError'));
        }, { once: true });
      });
    }
    
    attempt++;
  }
  
  throw lastError || new Error('Unknown error');
}
