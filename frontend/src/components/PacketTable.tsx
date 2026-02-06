import React from 'react';
import { Table, Tag, Button, Space } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined, DeleteOutlined } from '@ant-design/icons';
import { Packet } from '../types';
import { useAppStore } from '../store';

const protocolColors: Record<string, string> = {
  modbus: 'blue',
  mqtt: 'green',
  opcua: 'purple',
  bacnet: 'orange',
  coap: 'cyan',
  tcp: 'default',
};

export const PacketTable: React.FC = () => {
  const { packets, clearPackets, simulationState, setSimulationRunning } = useAppStore();

  const columns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 100,
    },
    {
      title: '源地址',
      dataIndex: 'source',
      key: 'source',
      width: 150,
    },
    {
      title: '目标地址',
      dataIndex: 'destination',
      key: 'destination',
      width: 150,
    },
    {
      title: '协议',
      dataIndex: 'protocol',
      key: 'protocol',
      width: 100,
      render: (protocol: string) => (
        <Tag color={protocolColors[protocol.toLowerCase()] || 'default'}>
          {protocol.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: '长度',
      dataIndex: 'length',
      key: 'length',
      width: 80,
    },
    {
      title: '信息',
      dataIndex: 'info',
      key: 'info',
      ellipsis: true,
    },
  ];

  return (
    <div className="packet-table">
      <div className="packet-toolbar">
        <Space>
          <Button
            type={simulationState.running ? 'primary' : 'default'}
            icon={simulationState.running ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
            onClick={() => setSimulationRunning(!simulationState.running)}
          >
            {simulationState.running ? '暂停' : '开始'}
          </Button>
          <Button
            danger
            icon={<DeleteOutlined />}
            onClick={clearPackets}
          >
            清空
          </Button>
        </Space>
      </div>
      <Table
        dataSource={packets}
        columns={columns}
        rowKey="id"
        size="small"
        pagination={{ pageSize: 10 }}
        scroll={{ x: 800 }}
      />
    </div>
  );
};
