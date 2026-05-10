import { ref } from 'vue';
import { consumeSSEStream } from '../utils/sse';

/**
 * SSE composable - manages Server-Sent Events streaming
 */
export function useSSE() {
  const isLoading = ref(false);
  const content = ref('');
  const error = ref<string | null>(null);
  const data = ref<any>(null);

  const fetchSSE = async (url: string, options?: RequestInit) => {
    isLoading.value = true;
    content.value = '';
    error.value = null;
    data.value = null;

    try {
      const response = await fetch(url, options);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      await consumeSSEStream(response, {
        onStart: () => {},
        onChunk: (chunk: string) => { content.value += chunk; },
        onDone: (finalData: any) => { data.value = finalData; },
        onError: (err: Error) => { error.value = err.message; }
      });
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error';
    } finally {
      isLoading.value = false;
    }
  };

  return {
    isLoading,
    content,
    error,
    data,
    fetchSSE
  };
}
