/**
 * WebSocket Service
 * Real-time communication for IoT data
 */

import { message } from 'antd';

interface WSMessage {
  type: string;
  [key: string]: any;
}

type WSHandler = (data: WSMessage) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private handlers: Map<string, Set<WSHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnecting = false;
  private messageQueue: WSMessage[] = [];
  private simulationInterval: NodeJS.Timeout | null = null;

  constructor(url: string = 'ws://localhost:8000/ws') {
    this.url = url;
    this.setupDefaultHandlers();
  }

  private setupDefaultHandlers() {
    this.handlers.set('packet', new Set());
    this.handlers.set('metric', new Set());
    this.handlers.set('alert', new Set());
    this.handlers.set('device_status', new Set());
    this.handlers.set('connection', new Set());
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      if (this.isConnecting) {
        resolve();
        return;
      }

      this.isConnecting = true;

      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          
          // Send queued messages
          while (this.messageQueue.length > 0) {
            const msg = this.messageQueue.shift();
            if (msg) this.send(msg);
          }
          
          this.notifyHandlers('connection', { status: 'connected' });
          resolve();
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason);
          this.isConnecting = false;
          this.notifyHandlers('connection', { status: 'disconnected' });
          
          // Attempt reconnection
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.isConnecting = false;
          reject(error);
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data) as WSMessage;
            this.handleMessage(data);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  private scheduleReconnect() {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        this.connect().catch(console.error);
      }
    }, delay);
  }

  disconnect() {
    if (this.simulationInterval) {
      clearInterval(this.simulationInterval);
      this.simulationInterval = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(message: WSMessage | object) {
    const msg = typeof message === 'object' ? message : { type: message };
    
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    } else {
      // Queue message for later
      this.messageQueue.push(msg as WSMessage);
    }
  }

  private handleMessage(data: WSMessage) {
    const { type, ...rest } = data;
    
    // Notify type-specific handlers
    this.notifyHandlers(type, data);
    
    // Notify wildcard handlers
    this.notifyHandlers('*', data);
  }

  private notifyHandlers(type: string, data: WSMessage) {
    const handlers = this.handlers.get(type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`Error in handler for ${type}:`, error);
        }
      });
    }
  }

  subscribe(type: string | '*', handler: WSHandler) {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);
    
    return () => this.unsubscribe(type, handler);
  }

  unsubscribe(type: string, handler: WSHandler) {
    const handlers = this.handlers.get(type);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  // Simulation for demo mode
  startSimulation() {
    if (this.simulationInterval) return;
    
    this.simulationInterval = setInterval(() => {
      // Simulate packets
      const packetTypes = ['modbus', 'mqtt', 'opcua', 'bacnet', 'coap'];
      const protocols = packetTypes[Math.floor(Math.random() * packetTypes.length)];
      
      this.notifyHandlers('packet', {
        type: 'packet',
        payload: {
          id: `pkt-${Date.now()}`,
          protocol: protocols,
          source: `192.168.1.${Math.floor(Math.random() * 100)}`,
          destination: '192.168.1.100',
          length: Math.floor(Math.random() * 500) + 50,
          info: `${protocols.toUpperCase()} message`,
          timestamp: new Date().toISOString(),
        },
      });

      // Simulate metrics
      this.notifyHandlers('metric', {
        type: 'metric',
        metric: 'throughput',
        value: Math.random() * 1000 + 500,
        unit: 'msg/s',
      });

      // Simulate occasional alerts
      if (Math.random() > 0.95) {
        const alertTypes = ['warning', 'critical', 'info'];
        const alertType = alertTypes[Math.floor(Math.random() * alertTypes.length)];
        
        this.notifyHandlers('alert', {
          type: 'alert',
          payload: {
            id: `alert-${Date.now()}`,
            type: alertType,
            title: `${alertType.toUpperCase()} Alert`,
            description: 'Simulated alert for testing',
            timestamp: new Date().toISOString(),
          },
        });
      }
    }, 1000);
  }

  stopSimulation() {
    if (this.simulationInterval) {
      clearInterval(this.simulationInterval);
      this.simulationInterval = null;
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  getStatus(): { connected: boolean; reconnectAttempts: number } {
    return {
      connected: this.isConnected(),
      reconnectAttempts: this.reconnectAttempts,
    };
  }
}

// Singleton instance
let wsService: WebSocketService | null = null;

export const getWebSocketService = (): WebSocketService => {
  if (!wsService) {
    wsService = new WebSocketService();
  }
  return wsService;
};

export default WebSocketService;
