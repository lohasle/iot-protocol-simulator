import React, { useEffect, useRef, useState } from 'react';
import { Card, Button, Space, ZoomInOutlined, ZoomOutOutlined, FullscreenOutlined } from '@ant-design/icons';
import { useAppStore } from '../store';
import { DeviceType } from '../types';

export const Topology: React.FC = () => {
  const svgRef = useRef<SVGSVGElement>(null);
  const { devices, addDevice } = useAppStore();
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });

  // Initialize with sample devices
  useEffect(() => {
    if (devices.length === 0) {
      const sampleDevices: DeviceType[] = ['plc', 'gateway', 'sensor', 'actuator'];
      sampleDevices.forEach((type, index) => {
        addDevice({
          id: `device-${index}`,
          name: `${type.toUpperCase()}-${index + 1}`,
          type,
          status: 'online',
          ip: `192.168.1.${10 + index}`,
          protocols: [type === 'plc' ? 'modbus' : 'mqtt'],
          lastSeen: new Date().toLocaleString(),
        });
      });
    }
  }, [devices.length, addDevice]);

  const handleZoomIn = () => setZoom((z) => Math.min(z + 0.1, 2));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 0.1, 0.5));
  const handleReset = () => { setZoom(1); setPan({ x: 0, y: 0 }); };

  const typeIcons: Record<DeviceType, string> = {
    plc: '🏭',
    sensor: '🌡️',
    actuator: '⚙️',
    gateway: '🌉',
    server: '🖥️',
  };

  const getDevicePosition = (index: number) => {
    const positions = [
      { x: 100, y: 150 },
      { x: 300, y: 150 },
      { x: 500, y: 100 },
      { x: 500, y: 200 },
    ];
    return positions[index] || { x: 100 + index * 150, y: 150 };
  };

  return (
    <div className="topology-page">
      <div className="page-header">
        <h2>网络拓扑</h2>
        <Space>
          <Button icon={<ZoomOutOutlined />} onClick={handleZoomOut} />
          <span>{Math.round(zoom * 100)}%</span>
          <Button icon={<ZoomInOutlined />} onClick={handleZoomIn} />
          <Button icon={<FullscreenOutlined />} onClick={handleReset} />
        </Space>
      </div>

      <Card className="topology-card">
        <svg
          ref={svgRef}
          width="100%"
          height={400}
          style={{
            transform: `scale(${zoom}) translate(${pan.x}px, ${pan.y}px)`,
            transition: 'transform 0.2s ease',
          }}
        >
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="7"
              refX="9"
              refY="3.5"
              orient="auto"
            >
              <polygon points="0 0, 10 3.5, 0 7" fill="#6366f1" />
            </marker>
          </defs>

          {/* Grid background */}
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path
              d="M 40 0 L 0 0 0 40"
              fill="none"
              stroke="rgba(99, 102, 241, 0.1)"
              strokeWidth="1"
            />
          </pattern>
          <rect width="100%" height="100%" fill="url(#grid)" />

          {/* Connections */}
          {devices.slice(0, 3).map((device, index) => (
            <line
              key={`connection-${index}`}
              x1={getDevicePosition(index).x + 40}
              y1={getDevicePosition(index).y + 25}
              x2={getDevicePosition(index + 1).x - 40}
              y2={getDevicePosition(index + 1).y + 25}
              stroke="#6366f1"
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
              opacity="0.6"
            />
          ))}

          {/* Device nodes */}
          {devices.map((device, index) => {
            const pos = getDevicePosition(index);
            return (
              <g key={device.id} transform={`translate(${pos.x}, ${pos.y})`}>
                <rect
                  x="0"
                  y="0"
                  width="80"
                  height="50"
                  rx="8"
                  fill="#1e293b"
                  stroke={device.status === 'online' ? '#10b981' : '#ef4444'}
                  strokeWidth="2"
                  style={{ cursor: 'pointer' }}
                />
                <text x="40" y="18" textAnchor="middle" fontSize="20">
                  {typeIcons[device.type]}
                </text>
                <text
                  x="40"
                  y="38"
                  textAnchor="middle"
                  fill="#e2e8f0"
                  fontSize="10"
                >
                  {device.name}
                </text>
                <circle
                  cx="70"
                  cy="10"
                  r="4"
                  fill={device.status === 'online' ? '#10b981' : '#ef4444'}
                />
              </g>
            );
          })}

          {/* Placeholder if no devices */}
          {devices.length === 0 && (
            <text
              x="50%"
              y="50%"
              textAnchor="middle"
              fill="#64748b"
              fontSize="14"
            >
              暂无设备，请先添加设备
            </text>
          )}
        </svg>
      </Card>
    </div>
  );
};
