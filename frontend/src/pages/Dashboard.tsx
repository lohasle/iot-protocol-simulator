import React from 'react';
import { Card, Row, Col, Progress, List, Tag } from 'antd';
import {
  ThunderboltOutlined,
  RiseOutlined,
  FallOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { MetricCards } from '../components/MetricCards';
import { ThroughputChart } from '../components/ThroughputChart';
import { useAppStore } from '../store';

export const Dashboard: React.FC = () => {
  const { alerts, metrics } = useAppStore();

  const alertIcons = {
    critical: <WarningOutlined style={{ color: '#ef4444' }} />,
    warning: <WarningOutlined style={{ color: '#f59e0b' }} />,
    info: <ThunderboltOutlined style={{ color: '#6366f1' }} />,
    success: <RiseOutlined style={{ color: '#10b981' }} />,
  };

  return (
    <div className="dashboard-page">
      <h2>仪表盘</h2>
      
      <MetricCards />

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={16}>
          <Card title="吞吐量趋势" size="small">
            <ThroughputChart width={600} height={200} />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="最近告警" size="small">
            <List
              dataSource={alerts.slice(0, 5)}
              renderItem={(alert) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={alertIcons[alert.type]}
                    title={alert.title}
                    description={alert.description}
                  />
                  <Tag>{alert.type}</Tag>
                </List.Item>
              )}
              locale={{ emptyText: '暂无告警' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small">
            <div className="stat-item">
              <span className="stat-label">CPU 使用率</span>
              <Progress percent={34} size="small" status="active" />
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small">
            <div className="stat-item">
              <span className="stat-label">内存使用</span>
              <Progress percent={67} size="small" status="active" />
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small">
            <div className="stat-item">
              <span className="stat-label">网络带宽</span>
              <Progress percent={45} size="small" status="active" />
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small">
            <div className="stat-item">
              <span className="stat-label">磁盘使用</span>
              <Progress percent={23} size="small" />
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};
