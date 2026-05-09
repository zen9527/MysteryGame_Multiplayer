/**
 * SSE (Server-Sent Events) utility - unified parser for SSE streams
 */

export interface SSEHandlers {
  onStart?: () => void;
  onChunk?: (content: string) => void;
  onDone?: (data: any) => void;
  onError?: (error: Error) => void;
}

/**
 * Parse a single SSE line
 */
export function parseSSELine(line: string): { type: string; data: any } | null {
  const trimmed = line.trim();
  if (!trimmed.startsWith('data: ')) return null;
  
  try {
    const data = JSON.parse(trimmed.slice(6));
    return { type: data.type || 'chunk', data };
  } catch (e) {
    return null;
  }
}

/**
 * Consume an SSE stream with handlers for different events
 */
export async function consumeSSEStream(
  response: Response,
  handlers: SSEHandlers
): Promise<void> {
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        const parsed = parseSSELine(line);
        if (!parsed) continue;
        
        switch (parsed.type) {
          case 'start':
            handlers.onStart?.();
            break;
          case 'chunk':
            handlers.onChunk?.(parsed.data.content || '');
            break;
          case 'done':
            handlers.onDone?.(parsed.data);
            break;
          case 'error':
            handlers.onError?.(new Error(parsed.data.message || 'SSE error'));
            break;
          default:
            // Handle other message types or raw content
            if (parsed.data.content) {
              handlers.onChunk?.(parsed.data.content);
            }
        }
      }
    }
    
    // Process any remaining buffer
    if (buffer.trim()) {
      const parsed = parseSSELine(buffer);
      if (parsed && parsed.data.content) {
        handlers.onChunk?.(parsed.data.content);
      }
    }
  } catch (err) {
    handlers.onError?.(err instanceof Error ? err : new Error('Unknown SSE error'));
  } finally {
    reader.releaseLock();
  }
}
