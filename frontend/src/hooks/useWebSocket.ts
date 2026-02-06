import { useEffect, useRef, useCallback } from 'react';
import { useAppStore } from '../store';
import { Packet, Metric, Alert } from '../types';

interface WebSocketMessage {
  type: string;
  payload?: unknown;
}

export function useWebSocket(url: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const { addPacket, updateMetric, addAlert } = useAppStore();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        reconnectAttempts.current = 0;
      };

      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, 3000);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      wsRef.current.onmessage = (event) => {
        const message: WebSocketMessage = JSON.parse(event.data);
        handleMessage(message);
      };
    } catch (error) {
      console.error('WebSocket connection failed:', error);
    }
  }, [url]);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'packet':
        addPacket(message.payload as Packet);
        break;
      case 'metric':
        const metric = message.payload as Metric;
        updateMetric(metric);
        break;
      case 'alert':
        addAlert(message.payload as Alert);
        break;
      default:
        console.log('Unknown message type:', message.type);
    }
  }, [addPacket, updateMetric, addAlert]);

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { send, disconnect, reconnect: connect };
}
