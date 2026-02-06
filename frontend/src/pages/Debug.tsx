import React, { useState } from 'react';
import { Card, Button, Space, Select, Row, Col } from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import { PacketTable } from '../components/PacketTable';
import { useAppStore } from '../store';

export const Debug: React.FC = () => {
  const { simulationState, setSimulationRunning } = useAppStore();
  const [protocolFilter, setProtocolFilter] = useState<string | null>(null);

  return (
    <div className="debug-page">
      <div className="page-header">
        <h2>调试工具</h2>
        <Space>
          <Select
            placeholder="过滤协议"
            style={{ width: 120 }}
            allowClear
            value={protocolFilter}
            onChange={setProtocolFilter}
            options={[
              { value: 'modbus', label: 'Modbus' },
              { value: 'mqtt', label: 'MQTT' },
              { value: 'opcua', label: 'OPC UA' },
              { value: 'bacnet', label: 'BACnet' },
              { value: 'coap', label: 'CoAP' },
            ]}
          />
          <Button
            type={simulationState.running ? 'primary' : 'default'}
            icon={simulationState.running ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
            onClick={() => setSimulationRunning(!simulationState.running)}
          >
            {simulationState.running ? '暂停捕获' : '开始捕获'}
          </Button>
        </Space>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24}>
          <Card title="数据包捕获" size="small">
            <PacketTable />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="十六进制视图" size="small">
            <pre className="hex-view" style={{ fontFamily: 'monospace', fontSize: 12 }}>
              0000  00 1A 2B 3C 4D 5E 6F 70 81 92 A3 B4 C5 D6 E7   . , &lt; ^ p .....
              0010  F8 E9 DA CB BC AD 9E 8F 70 61 52 43 34 25 16   x y Z Y ...
              0020  07 18 29 3A 4B 5C 6D 7E 8F 90 A1 B2 C3 D4 E5 F6   . . ) : K \ m ~
              0030  07 18 29 3A 4B 5C 6D 7E 8F 90 A1 B2 C3 D4 E5 F6   . . ) : K \ m ~
            </pre>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="协议解析" size="small">
            <div className="protocol-details">
              <p><strong>协议:</strong> Modbus TCP</p>
              <p><strong>事务 ID:</strong> 0x0001</p>
              <p><strong>协议标识符:</strong> 0x0000</p>
              <p><strong>长度:</strong> 6</p>
              <p><strong>单元标识符:</strong> 0x01</p>
              <p><strong>功能码:</strong> 0x03 (Read Holding Registers)</p>
              <p><strong>起始地址:</strong> 0x0000</p>
              <p><strong>寄存器数量:</strong> 2</p>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};
