import React from 'react';
import { Layout } from 'antd';
import { Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { Devices } from './pages/Devices';
import { Topology } from './pages/Topology';
import { Protocols } from './pages/Protocols';
import { Debug } from './pages/Debug';
import { Settings } from './pages/Settings';

const { Header, Content } = Layout;

export const App: React.FC = () => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sidebar />
      <Layout>
        <Header className="app-header">
          <div className="header-content">
            <h1>IoT Protocol Simulator</h1>
            <div className="header-actions">
              <span className="ws-status">🟢 已连接</span>
            </div>
          </div>
        </Header>
        <Content className="app-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/devices" element={<Devices />} />
            <Route path="/topology" element={<Topology />} />
            <Route path="/protocols" element={<Protocols />} />
            <Route path="/debug" element={<Debug />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
};

export default App;
