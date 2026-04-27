import type { WSMessage, ClientMessage } from '../types/ws';

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private url: string;
  private onMessage: ((msg: WSMessage) => void) | null = null;

  constructor(roomId: string, playerId: string) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.url = `${protocol}//${window.location.host}/ws/${roomId}/${playerId}`;
  }

  connect(onMessage: (msg: WSMessage) => void) {
    this.onMessage = onMessage;
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data) as WSMessage;
      if (this.onMessage) {
        this.onMessage(msg);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket closed');
    };
  }

  send(message: ClientMessage) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}
