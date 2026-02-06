import React from 'react';
import { Tabs, Form, Input, InputNumber, Switch, Button, Card } from 'antd';
import {
  SettingOutlined,
  ApiOutlined,
  SecurityScanOutlined,
  BellOutlined,
} from '@ant-design/icons';
import { useAppStore } from '../store';

export const SettingsPanel: React.FC = () => {
  const { protocolConfigs, setProtocolConfig } = useAppStore();
  const [form] = Form.useForm();

  const tabItems = [
    {
      key: 'general',
      label: (
        <span>
          <SettingOutlined /> 通用设置
        </span>
      ),
      children: (
        <Form form={form} layout="vertical">
          <Form.Item label="应用名称" name="appName" initialValue="IoT Protocol Simulator">
            <Input />
          </Form.Item>
          <Form.Item label="语言" name="language" initialValue="zh-CN">
            <Input />
          </Form.Item>
          <Form.Item label="时区" name="timezone" initialValue="Asia/Shanghai">
            <Input />
          </Form.Item>
          <Button type="primary">保存设置</Button>
        </Form>
      ),
    },
    {
      key: 'protocols',
      label: (
        <span>
          <ApiOutlined /> 协议配置
        </span>
      ),
      children: (
        <div className="protocol-settings">
          {['modbus', 'mqtt', 'opcua', 'bacnet', 'coap'].map((protocol) => (
            <Card key={protocol} size="small" className="protocol-card">
              <div className="protocol-header">
                <span className="protocol-name">{protocol.toUpperCase()}</span>
                <Switch size="small" defaultChecked />
              </div>
              <Form layout="vertical" size="small">
                <Form.Item label="端口" initialValue={getDefaultPort(protocol)}>
                  <InputNumber style={{ width: '100%' }} />
                </Form.Item>
              </Form>
            </Card>
          ))}
        </div>
      ),
    },
    {
      key: 'security',
      label: (
        <span>
          <SecurityScanOutlined /> 安全设置
        </span>
      ),
      children: (
        <Form layout="vertical">
          <Form.Item label="API 密钥" name="apiKey">
            <Input.Password placeholder="输入 API 密钥" />
          </Form.Item>
          <Form.Item label="启用 JWT 认证" name="jwtEnabled" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item label="CORS 允许来源" name="corsOrigins">
            <Input placeholder="https://example.com" />
          </Form.Item>
          <Button type="primary">保存安全设置</Button>
        </Form>
      ),
    },
    {
      key: 'notifications',
      label: (
        <span>
          <BellOutlined /> 通知设置
        </span>
      ),
      children: (
        <Form layout="vertical">
          <Form.Item label="启用桌面通知" name="desktopNotifications" valuePropName="checked">
            <Switch defaultChecked />
          </Form.Item>
          <Form.Item label="告警声音" name="alertSound" valuePropName="checked">
            <Switch defaultChecked />
          </Form.Item>
          <Form.Item label="最小化到托盘" name="minimizeToTray" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      ),
    },
  ];

  return (
    <Card>
      <Tabs items={tabItems} />
    </Card>
  );
};

function getDefaultPort(protocol: string): number {
  const ports: Record<string, number> = {
    modbus: 502,
    mqtt: 1883,
    opcua: 4840,
    bacnet: 47808,
    coap: 5683,
  };
  return ports[protocol] || 0;
}
