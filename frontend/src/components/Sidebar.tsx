import React, { useState } from 'react';
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  ApiOutlined,
  CloudServerOutlined,
  BugOutlined,
  SettingOutlined,
  ExperimentOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAppStore } from '../store';

const { Sider } = Layout;

export const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { sidebarCollapsed, toggleSidebar } = useAppStore();

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: '/devices',
      icon: <CloudServerOutlined />,
      label: '设备管理',
    },
    {
      key: '/topology',
      icon: <ApiOutlined />,
      label: '网络拓扑',
    },
    {
      key: '/protocols',
      icon: <ExperimentOutlined />,
      label: '协议模拟',
    },
    {
      key: '/debug',
      icon: <BugOutlined />,
      label: '调试工具',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
  ];

  return (
    <Sider
      collapsed={sidebarCollapsed}
      onCollapse={toggleSidebar}
      style={{
        background: 'linear-gradient(180deg, #1e293b 0%, #0f172a 100%)',
      }}
    >
      <div
        style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        <h1
          style={{
            color: '#6366f1',
            fontSize: sidebarCollapsed ? 16 : 20,
            fontWeight: 700,
            margin: 0,
            whiteSpace: 'nowrap',
          }}
        >
          {sidebarCollapsed ? 'IoT' : 'IoT Simulator'}
        </h1>
      </div>
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={({ key }) => navigate(key)}
        style={{ background: 'transparent', borderRight: 'none' }}
      />
    </Sider>
  );
};
