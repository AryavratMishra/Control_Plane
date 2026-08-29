import { useEffect, useRef, useState, useCallback } from 'react';
import { WS_BASE } from '../services/api';

export interface RiskEvent {
  event: string;
  incident_id?: string;
  application?: string;
  action?: string;
  severity?: string;
  reasons?: string[];
  scores?: {
    performance: number;
    cost: number;
    responsibility: number;
    overall: number;
  };
  timestamp?: string;
  message?: string;
}

export function useWebSocket() {
  const [events, setEvents] = useState<RiskEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const wsUrl = `${WS_BASE || 'ws://localhost:8000'}/ws/control-room`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as RiskEvent;
        if (data.event === 'risk_event') {
          setEvents(prev => [data, ...prev].slice(0, 100)); // keep last 100
        }
      } catch (_) {}
    };

    ws.onclose = () => {
      setConnected(false);
      // Reconnect after 3 seconds
      reconnectTimer.current = setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send('ping');
    }
  }, []);

  return { events, connected, sendPing };
}
