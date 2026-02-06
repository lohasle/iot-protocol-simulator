import React from 'react';
import { Card, Row, Col, Statistic } from 'antd';
import {
  ServerOutlined,
  ThunderboltOutlined,
  RiseOutlined,
  WifiOutlined,
} from '@ant-design/icons';
import { useAppStore } from '../store';

export const MetricCards: React.FC = () => {
  const { simulationState, metrics } = useAppStore();

  const getMetricValue = (name: string) => {
    const metric = metrics.find((m) => m.name === name);
    return metric?.value ?? 0;
  };

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} lg={6}>
        <Card className="metric-card">
          <Statistic
            title="活跃设备"
            value={simulationState.activeDevices}
            prefix={<ServerOutlined style={{ color: '#6366f1' }} />}
            suffix="台"
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card className="metric-card">
          <Statistic
            title="消息速率"
            value={simulationState.packetsPerSecond}
            prefix={<ThunderboltOutlined style={{ color: '#10b981' }} />}
            suffix="msg/s"
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card className="metric-card">
          <Statistic
            title="吞吐量"
            value={getMetricValue('throughput')}
            prefix={<RiseOutlined style={{ color: '#f59e0b' }} />}
            suffix="KB/s"
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card className="metric-card">
          <Statistic
            title="连接状态"
            value="正常"
            prefix={<WifiOutlined style={{ color: '#10b981' }} />}
            valueStyle={{ color: '#10b981' }}
          />
        </Card>
      </Col>
    </Row>
  );
};
