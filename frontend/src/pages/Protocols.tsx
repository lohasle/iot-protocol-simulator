import React from 'react';
import { Card, Row, Col, Switch, Form, InputNumber, Button, Tag } from 'antd';
import { SettingOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { SettingsPanel } from '../components/SettingsPanel';
import { useAppStore } from '../store';

export const Protocols: React.FC = () => {
  const { protocolConfigs, setProtocolConfig } = useAppStore();

  const protocols = [
    {
      key: 'modbus',
      name: 'Modbus',
      description: '工业通信协议，支持 TCP/RTU',
      port: 502,
      icon: '🔌',
      color: '#3b82f6',
    },
    {
      key: 'mqtt',
      name: 'MQTT',
      description: '消息队列遥测传输协议',
      port: 1883,
      icon: '📡',
      color: '#10b981',
    },
    {
      key: 'opcua',
      name: 'OPC UA',
      description: '开放平台通信统一架构',
      port: 4840,
      icon: '🌐',
      color: '#8b5cf6',
    },
    {
      key: 'bacnet',
      name: 'BACnet',
      description: '楼宇自动化控制网络协议',
      port: 47808,
      icon: '🏢',
      color: '#f59e0b',
    },
    {
      key: 'coap',
      name: 'CoAP',
      description: '约束应用协议',
      port: 5683,
      icon: '📱',
      color: '#06b6d4',
    },
    {
      key: 'tcp',
      name: 'TCP',
      description: '自定义 TCP 协议模拟',
      port: 8080,
      icon: '🔹',
      color: '#64748b',
    },
  ];

  return (
    <div className="protocols-page">
      <div className="page-header">
        <h2>协议模拟</h2>
      </div>

      <Row gutter={[16, 16]}>
        {protocols.map((protocol) => (
          <Col xs={24} sm={12} lg={8} key={protocol.key}>
            <Card
              className="protocol-card"
              style={{ borderLeft: `4px solid ${protocol.color}` }}
            >
              <div className="protocol-header">
                <span className="protocol-icon">{protocol.icon}</span>
                <div className="protocol-info">
                  <h3>{protocol.name}</h3>
                  <p>{protocol.description}</p>
                </div>
                <Switch size="small" defaultChecked />
              </div>
              <div className="protocol-body">
                <Tag color={protocol.color}>端口: {protocol.port}</Tag>
                <Tag icon={<CheckCircleOutlined />}>已配置</Tag>
              </div>
              <div className="protocol-actions">
                <Button size="small">配置</Button>
                <Button size="small" type="primary">启动</Button>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <div style={{ marginTop: 24 }}>
        <SettingsPanel />
      </div>
    </div>
  );
};
