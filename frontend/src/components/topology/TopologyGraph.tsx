/**
 * Enhanced Network Topology Visualization with D3.js
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Card, Button, Space, Slider, Tooltip, Badge, Select, Switch, Spin } from 'antd';
import { 
  ZoomInOutlined, 
  ZoomOutOutlined, 
  FullscreenOutlined,
  ReloadOutlined,
  PauseOutlined,
  NodeIndexOutlined,
  ApiOutlined
} from '@ant-design/icons';
import * as d3 from 'd3';

interface Node {
  id: string;
  name: string;
  type: 'gateway' | 'sensor' | 'plc' | 'actuator' | 'server' | 'cloud' | 'edge';
  status: 'online' | 'offline' | 'warning';
  protocols: string[];
  x?: number;
  y?: number;
}

interface Link {
  id: string;
  source: string;
  target: string;
  latency?: number;
  packetLoss?: number;
  status: 'active' | 'inactive' | 'congested';
}

interface TopologyData {
  nodes: Node[];
  links: Link[];
}

interface TopologyGraphProps {
  data?: TopologyData;
  width?: number;
  height?: number;
  onNodeClick?: (node: Node) => void;
  onLinkClick?: (link: Link) => void;
  autoRefresh?: boolean;
}

const NODE_ICONS: Record<string, string> = {
  gateway: '🌉',
  sensor: '🌡️',
  plc: '🏭',
  actuator: '⚙️',
  server: '🖥️',
  cloud: '☁️',
  edge: '📡',
};

const NODE_COLORS: Record<string, string> = {
  online: '#52c41a',
  offline: '#ff4d4f',
  warning: '#faad14',
};

const LINK_COLORS: Record<string, string> = {
  active: '#722ed1',
  congested: '#f5222d',
  inactive: '#8c8c8c',
};

export const TopologyGraph: React.FC<TopologyGraphProps> = ({
  data,
  width = 900,
  height = 500,
  onNodeClick,
  onLinkClick,
  autoRefresh = false,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [zoom, setZoom] = useState(1);
  const [showLabels, setShowLabels] = useState(true);
  const [showLatency, setShowLatency] = useState(false);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Simulation data
  const defaultData: TopologyData = {
    nodes: [
      { id: 'cloud', name: 'Cloud Server', type: 'cloud', status: 'online', protocols: ['mqtt', 'https'] },
      { id: 'gateway', name: 'Main Gateway', type: 'gateway', status: 'online', protocols: ['mqtt', 'tcp', 'modbus'] },
      { id: 'edge', name: 'Edge Node', type: 'edge', status: 'online', protocols: ['mqtt', 'bacnet'] },
      { id: 'plc1', name: 'PLC-001', type: 'plc', status: 'online', protocols: ['modbus', 'opcua'] },
      { id: 'plc2', name: 'PLC-002', type: 'plc', status: 'warning', protocols: ['modbus'] },
      { id: 'sensor1', name: 'Temp-1', type: 'sensor', status: 'online', protocols: ['mqtt'] },
      { id: 'sensor2', name: 'Temp-2', type: 'sensor', status: 'offline', protocols: ['mqtt'] },
      { id: 'sensor3', name: 'Pressure-1', type: 'sensor', status: 'online', protocols: ['mqtt', 'coap'] },
      { id: 'actuator1', name: 'Valve-1', type: 'actuator', status: 'online', protocols: ['modbus'] },
    ],
    links: [
      { id: 'l1', source: 'cloud', target: 'gateway', latency: 50, status: 'active' },
      { id: 'l2', source: 'gateway', target: 'edge', latency: 5, status: 'active' },
      { id: 'l3', source: 'edge', target: 'plc1', latency: 2, status: 'active' },
      { id: 'l4', source: 'edge', target: 'plc2', latency: 3, status: 'congested' },
      { id: 'l5', source: 'gateway', target: 'sensor1', latency: 10, status: 'active' },
      { id: 'l6', source: 'gateway', target: 'sensor2', latency: 15, status: 'inactive' },
      { id: 'l7', source: 'gateway', target: 'sensor3', latency: 8, status: 'active' },
      { id: 'l8', source: 'plc1', target: 'actuator1', latency: 1, status: 'active' },
    ],
  };

  const graphData = data || defaultData;

  // D3 Rendering
  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const g = svg.append('g')
      .attr('transform', `translate(${width / 2}, ${height / 2}) scale(${zoom})`);

    // Arrow marker
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '-0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .append('path')
      .attr('d', 'M 0,-5 L 10,0 L 0,5')
      .attr('fill', '#722ed1');

    // Create force simulation
    const simulation = d3.forceSimulation(graphData.nodes as any)
      .force('link', d3.forceLink(graphData.links).id((d: any) => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(0, 0))
      .force('collision', d3.forceCollide().radius(50));

    // Draw links
    const link = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(graphData.links)
      .enter()
      .append('line')
      .attr('stroke', (d: any) => LINK_COLORS[d.status])
      .attr('stroke-width', 2)
      .attr('stroke-opacity', 0.6)
      .attr('marker-end', 'url(#arrowhead)');

    // Draw link labels
    if (showLatency) {
      const linkLabels = g.append('g')
        .attr('class', 'link-labels')
        .selectAll('text')
        .data(graphData.links)
        .enter()
        .append('text')
        .attr('font-size', 10)
        .attr('fill', '#888')
        .attr('text-anchor', 'middle')
        .text((d: any) => `${d.latency || 0}ms`);
    }

    // Draw nodes
    const node = g.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(graphData.nodes)
      .enter()
      .append('g')
      .attr('cursor', 'pointer')
      .call(d3.drag<SVGGElement, Node>()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }));

    // Node circles
    node.append('circle')
      .attr('r', 25)
      .attr('fill', (d: any) => NODE_COLORS[d.status])
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .on('click', (event, d) => {
        setSelectedNode(d.id);
        onNodeClick?.(d);
      });

    // Node icons
    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', 8)
      .attr('font-size', 20)
      .text((d: any) => NODE_ICONS[d.type] || '📟');

    // Node labels
    if (showLabels) {
      node.append('text')
        .attr('dy', 45)
        .attr('text-anchor', 'middle')
        .attr('font-size', 11)
        .attr('fill', '#fff')
        .text((d: any) => d.name);
    }

    // Status indicator
    node.append('circle')
      .attr('cx', 18)
      .attr('cy', -18)
      .attr('r', 5)
      .attr('fill', (d: any) => NODE_COLORS[d.status]);

    // Simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      if (showLatency) {
        linkLabels
          .attr('x', (d: any) => (d.source.x + d.target.x) / 2)
          .attr('y', (d: any) => (d.source.y + d.target.y) / 2);
      }

      node.attr('transform', (d: any) => `translate(${d.x}, ${d.y})`);
    });

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [graphData, zoom, showLabels, showLatency]);

  const handleZoomIn = () => setZoom(z => Math.min(z + 0.1, 2));
  const handleZoomOut = () => setZoom(z => Math.max(z - 0.1, 0.5));
  const handleReset = () => setZoom(1);
  const handleRefresh = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 500);
  };

  const getSelectedNodeInfo = () => {
    if (!selectedNode) return null;
    return graphData.nodes.find(n => n.id === selectedNode);
  };

  return (
    <div className="topology-graph" ref={containerRef}>
      <Card
        title={
          <Space>
            <NodeIndexOutlined />
            <span>Network Topology</span>
            <Badge count={graphData.nodes.length} style={{ backgroundColor: '#52c41a' }} />
          </Space>
        }
        extra={
          <Space>
            <Tooltip title="Show Labels">
              <Switch
                size="small"
                checked={showLabels}
                onChange={setShowLabels}
              />
            </Tooltip>
            <Tooltip title="Show Latency">
              <Switch
                size="small"
                checked={showLatency}
                onChange={setShowLatency}
              />
            </Tooltip>
            <Button size="small" icon={<ZoomOutOutlined />} onClick={handleZoomOut} />
            <span>{Math.round(zoom * 100)}%</span>
            <Button size="small" icon={<ZoomInOutlined />} onClick={handleZoomIn} />
            <Button size="small" icon={<FullscreenOutlined />} onClick={handleReset} />
            <Button size="small" icon={<ReloadOutlined />} onClick={handleRefresh} />
          </Space>
        }
      >
        <div style={{ position: 'relative', textAlign: 'center' }}>
          {loading && (
            <div style={{ position: 'absolute', top: '50%', left: '50%', zIndex: 10 }}>
              <Spin />
            </div>
          )}
          <svg
            ref={svgRef}
            width={width}
            height={height}
            style={{ background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)', borderRadius: 8 }}
          />
          
          {/* Legend */}
          <div style={{
            position: 'absolute',
            bottom: 10,
            left: 10,
            background: 'rgba(0,0,0,0.7)',
            padding: 10,
            borderRadius: 4,
            fontSize: 12,
          }}>
            <div style={{ marginBottom: 5 }}><strong>Status</strong></div>
            <Space>
              <span style={{ color: NODE_COLORS.online }}>●</span> Online
            </Space>
            <Space>
              <span style={{ color: NODE_COLORS.warning }}>●</span> Warning
            </Space>
            <Space>
              <span style={{ color: NODE_COLORS.offline }}>●</span> Offline
            </Space>
            <div style={{ marginTop: 5 }}><strong>Links</strong></div>
            <Space>
              <span style={{ color: LINK_COLORS.active }}>●</span> Active
            </Space>
            <Space>
              <span style={{ color: LINK_COLORS.congested }}>●</span> Congested
            </Space>
          </div>
        </div>
      </Card>

      {/* Selected Node Info */}
      {getSelectedNodeInfo() && (
        <Card size="small" style={{ marginTop: 10 }}>
          <Space direction="vertical">
            <div><strong>Selected Node:</strong> {getSelectedNodeInfo()?.name}</div>
            <div><strong>Type:</strong> {getSelectedNodeInfo()?.type}</div>
            <div><strong>Status:</strong> 
              <Badge status={getSelectedNodeInfo()?.status === 'online' ? 'success' : 
                getSelectedNodeInfo()?.status === 'warning' ? 'warning' : 'error'} 
                text={getSelectedNodeInfo()?.status}
              />
            </div>
            <div><strong>Protocols:</strong> 
              {getSelectedNodeInfo()?.protocols.map(p => (
                <Tag key={p} style={{ marginLeft: 5 }}>{p}</Tag>
              ))}
            </div>
          </Space>
        </Card>
      )}
    </div>
  );
};

export default TopologyGraph;
