/**
 * Protocol Hook - Global Protocol State Management
 */

import React, { createContext, useContext, useReducer, useCallback, useEffect } from 'react';
import { message } from 'antd';

interface ProtocolState {
  protocols: Record<string, Protocol>;
  selectedProtocol: string | null;
  isLoading: boolean;
  error: string | null;
}

interface Protocol {
  name: string;
  enabled: boolean;
  running: boolean;
  config: ProtocolConfig;
  status: ProtocolStatus | null;
}

interface ProtocolConfig {
  host?: string;
  port?: number;
  [key: string]: any;
}

interface ProtocolStatus {
  running: boolean;
  port: number;
  connections: number;
  messageRate: number;
  lastStarted?: string;
  uptime?: string;
  totalMessages?: number;
  bytesSent?: number;
  bytesReceived?: number;
  errors?: number;
}

interface ProtocolAction {
  type: string;
  payload?: any;
}

const initialState: ProtocolState = {
  protocols: {},
  selectedProtocol: null,
  isLoading: false,
  error: null,
};

const protocolReducer = (state: ProtocolState, action: ProtocolAction): ProtocolState => {
  switch (action.type) {
    case 'SET_PROTOCOLS':
      return { ...state, protocols: action.payload };
    
    case 'SELECT_PROTOCOL':
      return { ...state, selectedProtocol: action.payload };
    
    case 'UPDATE_PROTOCOL':
      return {
        ...state,
        protocols: {
          ...state.protocols,
          [action.payload.name]: {
            ...state.protocols[action.payload.name],
            ...action.payload,
          },
        },
      };
    
    case 'SET_PROTOCOL_STATUS':
      return {
        ...state,
        protocols: {
          ...state.protocols,
          [action.payload.name]: {
            ...state.protocols[action.payload.name],
            status: action.payload.status,
            running: action.payload.status?.running || false,
          },
        },
      };
    
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    
    case 'SET_ERROR':
      return { ...state, error: action.payload, isLoading: false };
    
    default:
      return state;
  }
};

// Context
const ProtocolContext = createContext<{
  state: ProtocolState;
  dispatch: React.Dispatch<ProtocolAction>;
  loadProtocols: () => Promise<void>;
  updateProtocol: (name: string, data: Partial<Protocol>) => Promise<void>;
  startProtocol: (name: string) => Promise<void>;
  stopProtocol: (name: string) => Promise<void>;
  getProtocolStatus: (name: string) => ProtocolStatus | null;
  testProtocol: (name: string) => Promise<boolean>;
} | null>(null);

// Provider
export const ProtocolProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(protocolReducer, initialState);

  const loadProtocols = useCallback(async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      const response = await fetch('/api/v1/protocols');
      const data = await response.json();
      dispatch({ type: 'SET_PROTOCOLS', payload: data.protocols || {} });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load protocols' });
      message.error('Failed to load protocols');
    }
  }, []);

  const updateProtocol = useCallback(async (name: string, data: Partial<Protocol>) => {
    try {
      const response = await fetch(`/api/v1/protocols/${name}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      
      if (response.ok) {
        dispatch({ type: 'UPDATE_PROTOCOL', payload: { name, ...data } });
        message.success(`${name} updated successfully`);
      } else {
        message.error(`Failed to update ${name}`);
      }
    } catch (error) {
      message.error(`Error updating ${name}`);
    }
  }, []);

  const startProtocol = useCallback(async (name: string) => {
    try {
      const response = await fetch(`/api/v1/protocols/${name}/start`, {
        method: 'POST',
      });
      
      if (response.ok) {
        message.success(`${name} started`);
        // Refresh status
        await loadProtocols();
      } else {
        message.error(`Failed to start ${name}`);
      }
    } catch (error) {
      message.error(`Error starting ${name}`);
    }
  }, [loadProtocols]);

  const stopProtocol = useCallback(async (name: string) => {
    try {
      const response = await fetch(`/api/v1/protocols/${name}/stop`, {
        method: 'POST',
      });
      
      if (response.ok) {
        message.success(`${name} stopped`);
        await loadProtocols();
      } else {
        message.error(`Failed to stop ${name}`);
      }
    } catch (error) {
      message.error(`Error stopping ${name}`);
    }
  }, [loadProtocols]);

  const getProtocolStatus = useCallback((name: string): ProtocolStatus | null => {
    return state.protocols[name]?.status || null;
  }, [state.protocols]);

  const testProtocol = useCallback(async (name: string): Promise<boolean> => {
    try {
      const response = await fetch(`/api/v1/protocols/${name}/test`, {
        method: 'POST',
      });
      
      const result = await response.json();
      if (result.success) {
        message.success(`${name} test passed`);
      } else {
        message.error(`${name} test failed: ${result.message}`);
      }
      return result.success;
    } catch (error) {
      message.error(`Error testing ${name}`);
      return false;
    }
  }, []);

  useEffect(() => {
    loadProtocols();
  }, [loadProtocols]);

  return (
    <ProtocolContext.Provider
      value={{
        state,
        dispatch,
        loadProtocols,
        updateProtocol,
        startProtocol,
        stopProtocol,
        getProtocolStatus,
        testProtocol,
      }}
    >
      {children}
    </ProtocolContext.Provider>
  );
};

// Hook
export const useProtocolStore = () => {
  const context = useContext(ProtocolContext);
  if (!context) {
    throw new Error('useProtocolStore must be used within ProtocolProvider');
  }
  return context;
};

// Selector hooks
export const useProtocol = (name: string) => {
  const { state } = useProtocolStore();
  return state.protocols[name];
};

export const useSelectedProtocol = () => {
  const { state } = useProtocolStore();
  const selected = state.selectedProtocol;
  return selected ? state.protocols[selected] : null;
};

export const useProtocolList = () => {
  const { state } = useProtocolStore();
  return Object.values(state.protocols);
};

export const useProtocolByType = (type: string) => {
  const { state } = useProtocolStore();
  return Object.values(state.protocols).filter(p => p.name === type);
};

export default ProtocolProvider;
