import type { WSMessage, ClientMessage } from '../types/ws';
import { WS_MAX_RECONNECT_ATTEMPTS, WS_BASE_RECONNECT_DELAY } from '../constants';

/**
 * WebSocket close codes
 */
export const CLOSE_CODE_ROOM_NOT_FOUND = 4001;
export const CLOSE_CODE_PLAYER_NOT_FOUND = 4002;
export const CLOSE_CODE_GAME_FINISHED = 4003;
export const CLOSE_CODE_INVALID_MESSAGE = 4004;

/**
 * WebSocket Manager with auto-reconnect and exponential backoff
 */
export class WebSocketManager {
  private ws: WebSocket | null = null;
  private url: string;
  private onMessage: ((msg: WSMessage) => void) | null = null;
  private onClose: (() => void) | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = WS_MAX_RECONNECT_ATTEMPTS;
  private baseReconnectDelay = WS_BASE_RECONNECT_DELAY;

  constructor(roomId: string, playerId: string) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.url = `${protocol}//${window.location.host}/ws/${roomId}/${playerId}`;
  }

  connect(
    onMessage: (msg: WSMessage) => void,
    onClose?: () => void
  ) {
    this.onMessage = onMessage;
    this.onClose = onClose || null;
    this.reconnectAttempts = 0;
    this._establishConnection();
  }

  private _establishConnection() {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0; // Reset on successful connection
      console.log('WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as WSMessage;
        if (this.onMessage) {
          this.onMessage(msg);
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = (event) => {
      // Handle different close codes
      if (event.code === CLOSE_CODE_ROOM_NOT_FOUND || 
          event.code === CLOSE_CODE_PLAYER_NOT_FOUND ||
          event.code === CLOSE_CODE_GAME_FINISHED) {
        // Invalid connection - don't reconnect
        this.onClose?.();
        return;
      }

      // Attempt reconnection with exponential backoff
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        const delay = this.baseReconnectDelay * Math.pow(2, this.reconnectAttempts);
        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);
        setTimeout(() => this._establishConnection(), delay);
        this.reconnectAttempts++;
      } else {
        console.error('Max reconnection attempts reached');
        this.onClose?.();
      }
    };
  }

  send(message: ClientMessage) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket not connected');
    }
  }

  disconnect() {
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent auto-reconnect
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}
