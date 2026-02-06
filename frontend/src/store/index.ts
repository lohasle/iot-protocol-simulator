import { create } from 'zustand';
import { Device, Packet, Alert, Metric, SimulationState, ProtocolConfig } from '../types';

interface AppStore {
  // State
  devices: Device[];
  packets: Packet[];
  alerts: Alert[];
  metrics: Metric[];
  simulationState: SimulationState;
  selectedDevice: Device | null;
  protocolConfigs: ProtocolConfig[];
  sidebarCollapsed: boolean;

  // Actions
  setDevices: (devices: Device[]) => void;
  addDevice: (device: Device) => void;
  updateDevice: (id: string, updates: Partial<Device>) => void;
  removeDevice: (id: string) => void;

  addPacket: (packet: Packet) => void;
  clearPackets: () => void;

  addAlert: (alert: Alert) => void;
  dismissAlert: (id: string) => void;

  updateMetric: (metric: Metric) => void;

  setSelectedDevice: (device: Device | null) => void;

  setSimulationRunning: (running: boolean) => void;
  updateSimulationState: (updates: Partial<SimulationState>) => void;

  setProtocolConfig: (config: ProtocolConfig) => void;

  toggleSidebar: () => void;
}

export const useAppStore = create<AppStore>((set) => ({
  // Initial State
  devices: [],
  packets: [],
  alerts: [],
  metrics: [],
  selectedDevice: null,
  protocolConfigs: [],
  sidebarCollapsed: false,

  simulationState: {
    running: false,
    packetsPerSecond: 0,
    activeDevices: 0,
  },

  // Actions
  setDevices: (devices) => set({ devices }),

  addDevice: (device) => set((state) => ({
    devices: [...state.devices, device],
  })),

  updateDevice: (id, updates) => set((state) => ({
    devices: state.devices.map((d) =>
      d.id === id ? { ...d, ...updates } : d
    ),
  })),

  removeDevice: (id) => set((state) => ({
    devices: state.devices.filter((d) => d.id !== id),
    selectedDevice: state.selectedDevice?.id === id ? null : state.selectedDevice,
  })),

  addPacket: (packet) => set((state) => ({
    packets: [...state.packets.slice(-99), packet],
  })),

  clearPackets: () => set({ packets: [] }),

  addAlert: (alert) => set((state) => ({
    alerts: [alert, ...state.alerts.slice(0, 9)],
  })),

  dismissAlert: (id) => set((state) => ({
    alerts: state.alerts.filter((a) => a.id !== id),
  })),

  updateMetric: (metric) => set((state) => ({
    metrics: [...state.metrics.filter((m) => m.name !== metric.name), metric],
  })),

  setSelectedDevice: (device) => set({ selectedDevice: device }),

  setSimulationRunning: (running) => set((state) => ({
    simulationState: { ...state.simulationState, running },
  })),

  updateSimulationState: (updates) => set((state) => ({
    simulationState: { ...state.simulationState, ...updates },
  })),

  setProtocolConfig: (config) => set((state) => ({
    protocolConfigs: state.protocolConfigs.map((c) =>
      c.protocol === config.protocol ? config : c
    ).concat(
      state.protocolConfigs.find((c) => c.protocol === config.protocol) ? [] : [config]
    ),
  })),

  toggleSidebar: () => set((state) => ({
    sidebarCollapsed: !state.sidebarCollapsed,
  })),
}));
