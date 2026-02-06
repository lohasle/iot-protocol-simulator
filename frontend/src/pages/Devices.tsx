import React, { useState } from 'react';
import { Card, Row, Col, Button, Input, Select, Tag, Modal, Form } from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  DragOutlined,
} from '@ant-design/icons';
import { DeviceList } from '../components/DeviceList';
import { useAppStore } from '../store';
import { Device } from '../types';

export const Devices: React.FC = () => {
  const { devices, addDevice } = useAppStore();
  const [searchText, setSearchText] = useState('');
  const [filterType, setFilterType] = useState<string | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  const filteredDevices = devices.filter((device) => {
    const matchesSearch = device.name.toLowerCase().includes(searchText.toLowerCase()) ||
      device.ip.includes(searchText);
    const matchesType = !filterType || device.type === filterType;
    return matchesSearch && matchesType;
  });

  const handleAddDevice = (values: Partial<Device>) => {
    const newDevice: Device = {
      id: `device-${Date.now()}`,
      name: values.name || '新设备',
      type: values.type || 'sensor',
      status: 'online',
      ip: values.ip || '192.168.1.100',
      protocols: values.protocols || ['mqtt'],
      lastSeen: new Date().toLocaleString(),
    };
    addDevice(newDevice);
    setModalVisible(false);
    form.resetFields();
  };

  return (
    <div className="devices-page">
      <div className=" <h2>page-header">
       设备管理</h2>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setModalVisible(true)}
        >
          添加设备
        </Button>
      </div>

      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={8}>
            <Input
              placeholder="搜索设备名称或IP"
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="筛选类型"
              style={{ width: '100%' }}
              allowClear
              onChange={(value) => setFilterType(value)}
              options={[
                { value: 'plc', label: 'PLC' },
                { value: 'sensor', label: '传感器' },
                { value: 'actuator', label: '执行器' },
                { value: 'gateway', label: '网关' },
                { value: 'server', label: '服务器' },
              ]}
            />
          </Col>
          <Col xs={24} sm={12} md={10}>
            <Tag color="blue">设备总数: {devices.length}</Tag>
            <Tag color="green">在线: {devices.filter((d) => d.status === 'online').length}</Tag>
            <Tag color="red">离线: {devices.filter((d) => d.status === 'offline').length}</Tag>
          </Col>
        </Row>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <DeviceList />
        </Col>
        <Col xs={24} lg={8}>
          <Card title="快速添加" size="small">
            <div className="quick-add-grid">
              {['PLC', '传感器', '执行器', '网关'].map((type) => (
                <Button
                  key={type}
                  block
                  icon={<DragOutlined />}
                  onClick={() => {
                    form.setFieldsValue({ type: type.toLowerCase() });
                    setModalVisible(true);
                  }}
                >
                  {type}
                </Button>
              ))}
            </div>
          </Card>
        </Col>
      </Row>

      <Modal
        title="添加设备"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleAddDevice}>
          <Form.Item
            label="设备名称"
            name="name"
            rules={[{ required: true, message: '请输入设备名称' }]}
          >
            <Input placeholder="输入设备名称" />
          </Form.Item>
          <Form.Item
            label="设备类型"
            name="type"
            rules={[{ required: true, message: '请选择设备类型' }]}
          >
            <Select
              options={[
                { value: 'plc', label: '🏭 PLC' },
                { value: 'sensor', label: '🌡️ 传感器' },
                { value: 'actuator', label: '⚙️ 执行器' },
                { value: 'gateway', label: '🌉 网关' },
                { value: 'server', label: '🖥️ 服务器' },
              ]}
            />
          </Form.Item>
          <Form.Item label="IP 地址" name="ip">
            <Input placeholder="192.168.1.100" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              添加设备
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};
