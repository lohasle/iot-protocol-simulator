/**
 * Debug Panel - Wireshark-style Packet Capture Interface
 */

import React, { useState, useEffect, useRef } from 'react';
import { Card, Table, Tag, Space, Button, Input, Select, Switch, Tooltip, Badge, Empty, Drawer } from 'antd';
import { 
  PlayCircleOutlined, 
  PauseCircleOutlined, 
  StopOutlined, 
  ClearOutlined, 
  ExportOutlined,
  SearchOutlined,
  FilterOutlined,
  EyeOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { useWebSocket } from '../hooks/useWebSocket';

const { Search } = Input;

interface CapturedPacket {
  id: string;
  timestamp: string;
  direction: 'inbound' | 'outbound' | 'local';
  source: string;
  destination: string;
  protocol: string;
  length: number;
  info: string;
  payload?: string;
}

interface DebugPanelProps {
  maxPackets?: number;
}

export const DebugPanel: React.FC<DebugPanelProps> = ({ maxPackets = 1000 }) => {
  const [packets, setPackets] = useState<CapturedPacket[]>([]);
  const [isCapturing, setIsCapturing] = useState(false);
  const [filter, setFilter] = useState({ protocol: '', keyword: '' });
  const [selectedPacket, setSelectedPacket] = useState<CapturedPacket | null>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  
  const packetIdRef = useRef(0);
  const { subscribe, isConnected } = useWebSocket();

  useEffect(() => {
    if (isCapturing) {
      const unsubscribe = subscribe('packet', (data) => {
        if (data?.payload) {
          addPacket(data.payload);
        }
      });

      return () => unsubscribe();
    }
  }, [isCapturing, subscribe]);

  const addPacket = (packet: CapturedPacket) => {
    setPackets(prev => {
      const updated = [packet, ...prev];
      return updated.slice(0, maxPackets);
    });
  };

  const handleStartCapture = () => {
    setIsCapturing(true);
  };

  const handleStopCapture = () => {
    setIsCapturing(false);
  };

  const handleClear = () => {
    setPackets([]);
    packetIdRef.current = 0;
  };

  const handleExport = () => {
    const data = JSON.stringify(packets, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `packet-capture-${Date.now()}.json`;
    a.click();
  };

  const filteredPackets = packets.filter(p => {
    if (filter.protocol && p.protocol !== filter.protocol) return false;
    if (filter.keyword && !p.info.toLowerCase().includes(filter.keyword.toLowerCase())) return false;
    return true;
  });

  const getProtocolColor = (protocol: string) => {
    const colors: Record<string, string> = {
      modbus: 'blue',
      mqtt: 'green',
      opcua: 'purple',
      bacnet: 'cyan',
      coap: 'orange',
      tcp: 'geekblue',
      http: 'gold',
      https: 'gold',
      dns: 'lime',
    };
    return colors[protocol.toLowerCase()] || 'default';
  };

  const getDirectionColor = (direction: string) => {
    switch (direction) {
      case 'inbound': return 'green';
      case 'outbound': return 'blue';
      default: return 'default';
    }
  };

  const columns = [
    {
      title: 'No.',
      dataIndex: 'id',
      key: 'id',
      width: 80,
      render: (id: string, record: CapturedPacket, index: number) => (
        <span style={{ color: '#888' }}>{filteredPackets.length - index}</span>
      ),
    },
    {
      title: 'Time',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 120,
      render: (timestamp: string) => {
        const date = new Date(timestamp);
        return `${date.toLocaleTimeString()}.${date.getMilliseconds().toString().padStart(3, '0')}`;
      },
    },
    {
      title: 'Source',
      dataIndex: 'source',
      key: 'source',
      width: 140,
    },
    {
      title: 'Destination',
      dataIndex: 'destination',
      key: 'destination',
      width: 140,
    },
    {
      title: 'Protocol',
      dataIndex: 'protocol',
      key: 'protocol',
      width: 90,
      render: (protocol: string) => (
        <Tag color={getProtocolColor(protocol)}>{protocol.toUpperCase()}</Tag>
      ),
    },
    {
      title: 'Length',
      dataIndex: 'length',
      key: 'length',
      width: 80,
      align: 'right' as const,
    },
    {
      title: 'Info',
      dataIndex: 'info',
      key: 'info',
      ellipsis: true,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 60,
      render: (_: any, record: CapturedPacket) => (
        <Space>
          <Tooltip title="View Details">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => {
                setSelectedPacket(record);
                setDrawerVisible(true);
              }}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div className="debug-panel">
      <Card
        title={
          <Space>
            <span>Packet Capture</span>
            <Badge status={isCapturing ? 'processing' : 'default'} text={isCapturing ? 'Capturing' : 'Stopped'} />
          </Space>
        }
        extra={
          <Space>
            <Input.Group compact>
              <Select
                placeholder="Protocol"
                style={{ width: 120 }}
                allowClear
                value={filter.protocol}
                onChange={(v) => setFilter({ ...filter, protocol: v || '' })}
              >
                <Select.Option value="modbus">Modbus</Select.Option>
                <Select.Option value="mqtt">MQTT</Select.Option>
                <Select.Option value="opcua">OPC UA</Select.Option>
                <Select.Option value="bacnet">BACnet</Select.Option>
                <Select.Option value="coap">CoAP</Select.Option>
                <Select.Option value="tcp">TCP</Select.Option>
              </Select>
              <Search
                placeholder="Filter"
                style={{ width: 150 }}
                prefix={<FilterOutlined />}
                value={filter.keyword}
                onChange={(e) => setFilter({ ...filter, keyword: e.target.value })}
                allowClear
              />
            </Input.Group>
            
            <Tooltip title={isCapturing ? 'Stop Capture' : 'Start Capture'}>
              <Button
                type={isCapturing ? 'primary' : 'default'}
                danger={isCapturing}
                icon={isCapturing ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                onClick={isCapturing ? handleStopCapture : handleStartCapture}
              />
            </Tooltip>
            
            <Tooltip title="Clear">
              <Button icon={<ClearOutlined />} onClick={handleClear} />
            </Tooltip>
            
            <Tooltip title="Export">
              <Button icon={<ExportOutlined />} onClick={handleExport} />
            </Tooltip>
            
            <span style={{ color: '#888', fontSize: 12 }}>
              {filteredPackets.length} packets
            </span>
          </Space>
        }
      >
        <Table
          dataSource={filteredPackets}
          columns={columns}
          rowKey="id"
          size="small"
          scroll={{ x: 900, y: 400 }}
          pagination={false}
          locale={{ emptyText: <Empty description={isCapturing ? 'Waiting for packets...' : 'Start capture to see packets'} /> }}
          onRow={(record) => ({
            onClick: () => {
              setSelectedPacket(record);
              setDrawerVisible(true);
            },
            style: { cursor: 'pointer' },
          })}
        />
      </Card>

      <Drawer
        title="Packet Details"
        placement="right"
        width={500}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        {selectedPacket && (
          <div className="packet-details">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <strong>Packet ID:</strong> {selectedPacket.id}
              </div>
              <div>
                <strong>Timestamp:</strong> {selectedPacket.timestamp}
              </div>
              <div>
                <strong>Direction:</strong>
                <Tag color={getDirectionColor(selectedPacket.direction)}>
                  {selectedPacket.direction}
                </Tag>
              </div>
              <div>
                <strong>Source:</strong> {selectedPacket.source}
              </div>
              <div>
                <strong>Destination:</strong> {selectedPacket.destination}
              </div>
              <div>
                <strong>Protocol:</strong>
                <Tag color={getProtocolColor(selectedPacket.protocol)}>
                  {selectedPacket.protocol.toUpperCase()}
                </Tag>
              </div>
              <div>
                <strong>Length:</strong> {selectedPacket.length} bytes
              </div>
              <div>
                <strong>Info:</strong> {selectedPacket.info}
              </div>
              
              {selectedPacket.payload && (
                <div>
                  <strong>Payload:</strong>
                  <Input.TextArea
                    value={selectedPacket.payload}
                    rows={10}
                    readOnly
                    style={{ fontFamily: 'monospace', marginTop: 8 }}
                  />
                </div>
              )}
            </Space>
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default DebugPanel;
