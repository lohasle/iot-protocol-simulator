// Types for IoT Protocol Simulator

export interface Device {
  id: string;
  name: string;
  type: DeviceType;
  status: 'online' | 'offline' | 'error';
  ip: string;
  protocols: Protocol[];
  lastSeen: string;
  metadata?: Record<string, unknown>;
}

export type DeviceType = 'plc' | 'sensor' | 'actuator' | 'gateway' | 'server';

export type Protocol = 'modbus' | 'mqtt' | 'opcua' | 'bacnet' | 'coap' | 'tcp';

export interface Packet {
  id: string;
  timestamp: string;
  source: string;
  destination: string;
  protocol: Protocol;
  length: number;
  info: string;
  payload?: string;
}

export interface Metric {
  name: string;
  value: number;
  unit?: string;
  timestamp: string;
}

export interface Alert {
  id: string;
  type: 'critical' | 'warning' | 'info' | 'success';
  title: string;
  description: string;
  timestamp: string;
  deviceId?: string;
}

export interface ProtocolConfig {
  protocol: Protocol;
  enabled: boolean;
  port: number;
  settings: Record<string, unknown>;
}

export interface TopologyNode {
  id: string;
  type: DeviceType;
  x: number;
  y: number;
  connections: string[];
}

export interface Connection {
  id: string;
  sourceId: string;
  targetId: string;
  protocol: Protocol;
  status: 'active' | 'inactive' | 'error';
}

export interface SimulationState {
  running: boolean;
  startTime?: string;
  packetsPerSecond: number;
  activeDevices: number;
}
