import React from 'react';
import { Card } from 'antd';
import { SettingsPanel } from '../components/SettingsPanel';

export const Settings: React.FC = () => {
  return (
    <div className="settings-page">
      <div className="page-header">
        <h2>系统设置</h2>
      </div>
      <SettingsPanel />
    </div>
  );
};
