import React from 'react';
import { Table, Tag, Button, Space } from 'antd';
import { EditOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons';
import { Device } from '../types';
import { useAppStore } from '../store';

const typeIcons: Record<string, string> = {
  plc: '🏭',
  sensor: '🌡️',
  actuator: '⚙️',
  gateway: '🌉',
  server: '🖥️',
};

const statusColors: Record<string, string> = {
  online: 'success',
  offline: 'error',
  error: 'warning',
};

export const DeviceList: React.FC = () => {
  const { devices, selectedDevice, setSelectedDevice, removeDevice } = useAppStore();

  const columns = [
    {
      title: '设备',
      key: 'device',
      render: (_: unknown, record: Device) => (
        <Space>
          <span>{typeIcons[record.type] || '📦'}</span>
          <span>{record.name}</span>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag>{type.toUpperCase()}</Tag>
      ),
    },
    {
      title: 'IP 地址',
      dataIndex: 'ip',
      key: 'ip',
    },
    {
      title: '协议',
      dataIndex: 'protocols',
      key: 'protocols',
      render: (protocols: string[]) => (
        <>
          {protocols.map((p) => (
            <Tag key={p} color="blue">{p.toUpperCase()}</Tag>
          ))}
        </>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={statusColors[status] || 'default'}>
          {status === 'online' ? '在线' : status === 'offline' ? '离线' : '错误'}
        </Tag>
      ),
    },
    {
      title: '最后活跃',
      dataIndex: 'lastSeen',
      key: 'lastSeen',
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: unknown, record: Device) => (
        <Space>
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={() => setSelectedDevice(record)}
          />
          <Button
            type="text"
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => removeDevice(record.id)}
          />
        </Space>
      ),
    },
  ];

  return (
    <div className="device-list">
      <div className="device-toolbar">
        <Button type="primary" icon={<PlusOutlined />}>
          添加设备
        </Button>
      </div>
      <Table
        dataSource={devices}
        columns={columns}
        rowKey="id"
        size="small"
        pagination={{ pageSize: 10 }}
        rowClassName={(record) =>
          record.id === selectedDevice?.id ? 'ant-table-row-selected' : ''
        }
        onRow={(record) => ({
          onClick: () => setSelectedDevice(record),
          style: { cursor: 'pointer' },
        })}
      />
    </div>
  );
};
