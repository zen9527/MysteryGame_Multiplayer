export class RequestTimeoutError extends Error {
  constructor(url: string) {
    super(`Request timeout: ${url}`);
    this.name = 'RequestTimeoutError';
  }
}

export interface RequestOptions {
  timeout?: number; // milliseconds, default 30s
  signal?: AbortSignal;
}

export async function fetchWithTimeout(
  url: string,
  options: RequestInit & RequestOptions = {}
): Promise<Response> {
  const { timeout = 30000, signal: externalSignal, ...fetchOptions } = options;
  
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
    return response;
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError' && controller.signal.aborted && !externalSignal?.aborted) {
      throw new RequestTimeoutError(url);
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}
