/**
 * Protocol Configuration Panel
 * Real-time protocol configuration interface
 */

import React, { useState, useEffect } from 'react';
import { Card, Form, Input, Select, Switch, Button, Space, Tabs, Modal, InputNumber, Divider, Tag, Tooltip } from 'antd';
import { 
  SettingOutlined, 
  SaveOutlined, 
  ReloadOutlined, 
  PlayCircleOutlined, 
  StopOutlined,
  InfoCircleOutlined 
} from '@ant-design/icons';
import { useProtocolStore } from '../../hooks/useProtocol';

const { Option } = Select;
const { TabPane } = Tabs;

interface ProtocolConfigProps {
  protocol: string;
  onSave?: (config: any) => void;
}

export const ProtocolConfig: React.FC<ProtocolConfigProps> = ({ protocol, onSave }) => {
  const { protocols, updateProtocol, startProtocol, stopProtocol, getProtocolStatus } = useProtocolStore();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  
  const currentProtocol = protocols[protocol] || {};
  const status = getProtocolStatus(protocol);

  useEffect(() => {
    form.setFieldsValue(currentProtocol.config || {});
  }, [protocol, currentProtocol]);

  const handleSave = async () => {
    setLoading(true);
    try {
      const values = await form.validateFields();
      updateProtocol(protocol, { config: values });
      onSave?.(values);
    } catch (error) {
      console.error('Validation failed:', error);
    }
    setLoading(false);
  };

  const handleStart = () => {
    startProtocol(protocol);
  };

  const handleStop = () => {
    stopProtocol(protocol);
  };

  const renderCommonConfig = () => (
    <>
      <Form.Item label="Host" name="host" rules={[{ required: true }]}>
        <Input placeholder="0.0.0.0" />
      </Form.Item>
      <Form.Item label="Port" name="port" rules={[{ required: true }]}>
        <InputNumber min={1} max={65535} style={{ width: '100%' }} />
      </Form.Item>
      <Form.Item label="Auto Start" name="autoStart" valuePropName="checked">
        <Switch />
      </Form.Item>
    </>
  );

  const renderModbusConfig = () => (
    <>
      {renderCommonConfig()}
      <Divider>Modbus Settings</Divider>
      <Form.Item label="Unit ID" name="unitId">
        <InputNumber min={1} max={247} style={{ width: '100%' }} />
      </Form.Item>
      <Form.Item label="Timeout (ms)" name="timeout">
        <InputNumber min={100} max={10000} style={{ width: '100%' }} />
      </Form.Item>
      <Form.Item label="Simulate Registers" name="simulateRegisters" valuePropName="checked">
        <Switch />
      </Form.Item>
      <Form.Item label="Register Count" name="registerCount">
        <InputNumber min={1} max={10000} style={{ width: '100%' }} />
      </Form.Item>
    </>
  );

  const renderMQTTConfig = () => (
    <>
      {renderCommonConfig()}
      <Divider>MQTT Settings</Divider>
      <Form.Item label="Broker ID" name="brokerId">
        <Input placeholder="mqtt-broker" />
      </Form.Item>
      <Form.Item label="Username" name="username">
        <Input />
      </Form.Item>
      <Form.Item label="Password" name="password">
        <Input.Password />
      </Form.Item>
      <Form.Item label="QoS" name="qos">
        <Select>
          <Option value={0}>0 - At most once</Option>
          <Option value={1}>1 - At least once</Option>
          <Option value={2}>2 - Exactly once</Option>
        </Select>
      </Form.Item>
      <Form.Item label="Retain Messages" name="retain" valuePropName="checked">
        <Switch />
      </Form.Item>
      <Form.Item label="Max Connections" name="maxConnections">
        <InputNumber min={1} max={10000} style={{ width: '100%' }} />
      </Form.Item>
    </>
  );

  const renderOPCUAConfig = () => (
    <>
      {renderCommonConfig()}
      <Divider>OPC UA Settings</Divider>
      <Form.Item label="Application URI" name="applicationUri">
        <Input placeholder="urn:iot:simulator" />
      </Form.Item>
      <Form.Item label="Security Policy" name="securityPolicy">
        <Select>
          <Option value="None">None</Option>
          <Option value="Basic256">Basic256</Option>
          <Option value="Aes256_Sha256">Aes256_Sha256</Option>
        </Select>
      </Form.Item>
      <Form.Item label="Authentication Mode" name="authMode">
        <Select>
          <Option value="anonymous">Anonymous</Option>
          <Option value="userpass">Username/Password</Option>
          <Option value="certificate">Certificate</Option>
        </Select>
      </Form.Item>
      <Form.Item label="Simulate Nodes" name="simulateNodes" valuePropName="checked">
        <Switch />
      </Form.Item>
      <Form.Item label="Node Count" name="nodeCount">
        <InputNumber min={1} max={1000} style={{ width: '100%' }} />
      </Form.Item>
    </>
  );

  const renderBACnetConfig = () => (
    <>
      {renderCommonConfig()}
      <Divider>BACnet Settings</Divider>
      <Form.Item label="Device ID" name="deviceId">
        <InputNumber min={1} max={4194303} style={{ width: '100%' }} />
      </Form.Item>
      <Form.Item label="Vendor ID" name="vendorId">
        <InputNumber min={0} max={65535} style={{ width: '100%' }} />
      </Form.Item>
      <Form.Item label="Broadcast Address" name="broadcastAddress">
        <Input placeholder="255.255.255.255" />
      </Form.Item>
      <Form.Item label="Segment Timeout (ms)" name="segmentTimeout">
        <InputNumber min={100} max={10000} style={{ width: '100%' }} />
      </Form.Item>
    </>
  );

  const renderCoAPConfig = () => (
    <>
      {renderCommonConfig()}
      <Divider>CoAP Settings</Divider>
      <Form.Item label="Resource Directory" name="resourceDir">
        <Input placeholder="/" />
      </Form.Item>
      <Form.Item label="Max Message Size" name="maxMessageSize">
        <InputNumber min={64} max={65536} style={{ width: '100%' }} />
      </Form.Item>
      <Form.Item label="Block Size" name="blockSize">
        <Select>
          <Option value={16}>16</Option>
          <Option value={32}>32</Option>
          <Option value={64}>64</Option>
          <Option value={128}>128</Option>
        </Select>
      </Form.Item>
      <Form.Item label="Observe Max Age" name="observeMaxAge">
        <InputNumber min={1} max={86400} style={{ width: '100%' }} />
      </Form.Item>
    </>
  );

  const renderTCPConfig = () => (
    <>
      {renderCommonConfig()}
      <Divider>TCP Settings</Divider>
      <Form.Item label="Protocol Type" name="protocolType">
        <Select>
          <Option value="raw">Raw TCP</Option>
          <Option value="json">JSON Line</Option>
          <Option value="http">HTTP</Option>
        </Select>
      </Form.Item>
      <Form.Item label="Max Connections" name="maxConnections">
        <InputNumber min={1} max={10000} style={{ width: '100%' }} />
      </Form.Item>
      <Form.Item label="Connection Timeout (s)" name="connectionTimeout">
        <InputNumber min={1} max={3600} style={{ width: '100%' }} />
      </Form.Item>
      <Form.Item label="Message Delimiter" name="messageDelimiter">
        <Input placeholder="\n" />
      </Form.Item>
    </>
  );

  const getProtocolIcon = (proto: string) => {
    const icons: Record<string, string> = {
      modbus: '🔧',
      mqtt: '📡',
      opcua: '🏭',
      bacnet: '🌐',
      coap: '📶',
      tcp: '🔌',
    };
    return icons[proto] || '📟';
  };

  const getProtocolDescription = (proto: string) => {
    const descriptions: Record<string, string> = {
      modbus: 'Industrial protocol for PLC communication',
      mqtt: 'Lightweight messaging for IoT',
      opcua: 'Industrial interoperability standard',
      bacnet: 'Building automation protocol',
      coap: 'Constrained application protocol',
      tcp: 'Raw TCP connection simulation',
    };
    return descriptions[proto] || 'IoT Protocol';
  };

  const renderProtocolConfig = () => {
    switch (protocol) {
      case 'modbus':
        return renderModbusConfig();
      case 'mqtt':
        return renderMQTTConfig();
      case 'opcua':
        return renderOPCUAConfig();
      case 'bacnet':
        return renderBACnetConfig();
      case 'coap':
        return renderCoAPConfig();
      case 'tcp':
        return renderTCPConfig();
      default:
        return renderCommonConfig();
    }
  };

  return (
    <div className="protocol-config">
      <Card
        title={
          <Space>
            <span>{getProtocolIcon(protocol)} {protocol.toUpperCase()}</span>
            <Tag color={status?.running ? 'green' : 'red'}>
              {status?.running ? 'Running' : 'Stopped'}
            </Tag>
          </Space>
        }
        extra={
          <Space>
            <Tooltip title={status?.running ? 'Stop' : 'Start'}>
              <Button
                type={status?.running ? 'primary' : 'default'}
                danger={status?.running}
                icon={status?.running ? <StopOutlined /> : <PlayCircleOutlined />}
                onClick={status?.running ? handleStop : handleStart}
              />
            </Tooltip>
            <Tooltip title="Save">
              <Button
                icon={<SaveOutlined />}
                onClick={handleSave}
                loading={loading}
              />
            </Tooltip>
            <Tooltip title="Reload">
              <Button icon={<ReloadOutlined />} />
            </Tooltip>
          </Space>
        }
      >
        <Form form={form} layout="vertical" initialValues={currentProtocol.config}>
          <Tabs defaultActiveKey="1">
            <TabPane tab="Configuration" key="1">
              {renderProtocolConfig()}
            </TabPane>
            <TabPane tab="Status" key="2">
              <div className="protocol-status">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <strong>Status:</strong> <Tag color={status?.running ? 'green' : 'red'}>
                      {status?.running ? 'Active' : 'Inactive'}
                    </Tag>
                  </div>
                  <div><strong>Port:</strong> {status?.port || 'N/A'}</div>
                  <div><strong>Connections:</strong> {status?.connections || 0}</div>
                  <div><strong>Message Rate:</strong> {status?.messageRate?.toFixed(2) || 0} msg/s</div>
                  <div><strong>Last Started:</strong> {status?.lastStarted || 'Never'}</div>
                  <div><strong>Uptime:</strong> {status?.uptime || '0s'}</div>
                </Space>
              </div>
            </TabPane>
            <TabPane tab="Statistics" key="3">
              <div className="protocol-stats">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div><strong>Total Messages:</strong> {status?.totalMessages || 0}</div>
                  <div><strong>Bytes Sent:</strong> {(status?.bytesSent || 0).toLocaleString()}</div>
                  <div><strong>Bytes Received:</strong> {(status?.bytesReceived || 0).toLocaleString()}</div>
                  <div><strong>Errors:</strong> {status?.errors || 0}</div>
                </Space>
              </div>
            </TabPane>
          </Tabs>
        </Form>
      </Card>
    </div>
  );
};

export default ProtocolConfig;
