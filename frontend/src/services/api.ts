import axios from 'axios';
import { Device, Packet, Alert, Metric, ProtocolConfig, SimulationState } from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
});

// Devices
export const deviceApi = {
  getAll: () => api.get<Device[]>('/devices'),
  getById: (id: string) => api.get<Device>(`/devices/${id}`),
  create: (device: Partial<Device>) => api.post<Device>('/devices', device),
  update: (id: string, data: Partial<Device>) => api.put<Device>(`/devices/${id}`, data),
  delete: (id: string) => api.delete(`/devices/${id}`),
  getStatus: (id: string) => api.get(`/devices/${id}/status`),
};

// Packets
export const packetApi = {
  getAll: () => api.get<Packet[]>('/packets'),
  getById: (id: string) => api.get<Packet>(`/packets/${id}`),
  clear: () => api.delete('/packets'),
  export: (format: 'json' | 'pcap') => api.get(`/packets/export?format=${format}`, { responseType: 'blob' }),
};

// Protocols
export const protocolApi = {
  getConfigs: () => api.get<ProtocolConfig[]>('/protocols'),
  updateConfig: (config: ProtocolConfig) => api.put<ProtocolConfig>(`/protocols/${config.protocol}`, config),
  getStatus: (protocol: string) => api.get(`/protocols/${protocol}/status`),
  start: (protocol: string) => api.post(`/protocols/${protocol}/start`),
  stop: (protocol: string) => api.post(`/protocols/${protocol}/stop`),
};

// Simulation
export const simulationApi = {
  getState: () => api.get<SimulationState>('/simulation/state'),
  start: () => api.post('/simulation/start'),
  stop: () => api.post('/simulation/stop'),
  reset: () => api.post('/simulation/reset'),
};

// Metrics
export const metricsApi = {
  getAll: () => api.get<Metric[]>('/metrics'),
  getByName: (name: string) => api.get<Metric>(`/metrics/${name}`),
  getHistory: (name: string, duration: string) => api.get<Metric[]>(`/metrics/${name}/history?duration=${duration}`),
};

// Alerts
export const alertApi = {
  getAll: () => api.get<Alert[]>('/alerts'),
  dismiss: (id: string) => api.delete(`/alerts/${id}`),
  clear: () => api.delete('/alerts'),
};

export default api;
