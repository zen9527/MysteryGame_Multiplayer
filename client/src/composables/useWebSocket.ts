import { ref, onUnmounted } from 'vue';
import { WebSocketManager } from '../utils/ws';
import type { WSMessage, ClientMessage } from '../types/ws';

/**
 * WebSocket composable - manages WebSocket connection with auto-reconnect
 */
export function useWebSocket(roomId: string, playerId: string) {
  const wsManager = new WebSocketManager(roomId, playerId);
  const isConnected = ref(false);
  const messages = ref<WSMessage[]>([]);
  const error = ref<string | null>(null);

  const connect = () => {
    wsManager.connect(
      (msg: WSMessage) => {
        messages.value.push(msg);
      },
      () => {
        isConnected.value = false;
      }
    );
    isConnected.value = true;
  };

  const disconnect = () => {
    wsManager.disconnect();
    isConnected.value = false;
  };

  const send = (msg: ClientMessage) => {
    wsManager.send(msg);
  };

  onUnmounted(() => {
    disconnect();
  });

  return {
    isConnected,
    messages,
    error,
    connect,
    disconnect,
    send
  };
}
