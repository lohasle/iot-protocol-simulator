import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { useAppStore } from '../store';

interface ThroughputChartProps {
  width?: number;
  height?: number;
}

export const ThroughputChart: React.FC<ThroughputChartProps> = ({
  width = 400,
  height = 200,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const { metrics, simulationState } = useAppStore();
  const dataRef = useRef<number[]>([]);

  useEffect(() => {
    // Initialize data
    if (dataRef.current.length === 0) {
      dataRef.current = Array.from({ length: 30 }, () => Math.random() * 100);
    }
  }, []);

  useEffect(() => {
    if (!svgRef.current) return;

    // Update data with new metric value
    const throughput = metrics.find((m) => m.name === 'throughput')?.value ?? 0;
    dataRef.current.push(throughput + (simulationState.running ? Math.random() * 50 : 0));
    dataRef.current.shift();

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = { top: 20, right: 20, bottom: 30, left: 50 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Scales
    const xScale = d3
      .scaleLinear()
      .domain([0, dataRef.current.length - 1])
      .range([0, innerWidth]);

    const yScale = d3
      .scaleLinear()
      .domain([0, Math.max(...dataRef.current, 100)])
      .range([innerHeight, 0]);

    // Area
    const area = d3
      .area<number>()
      .x((_, i) => xScale(i))
      .y0(innerHeight)
      .y1((d) => yScale(d))
      .curve(d3.curveMonotoneX);

    g.append('path')
      .datum(dataRef.current)
      .attr('fill', 'rgba(99, 102, 241, 0.2)')
      .attr('d', area);

    // Line
    const line = d3
      .line<number>()
      .x((_, i) => xScale(i))
      .y((d) => yScale(d))
      .curve(d3.curveMonotoneX);

    g.append('path')
      .datum(dataRef.current)
      .attr('fill', 'none')
      .attr('stroke', '#6366f1')
      .attr('stroke-width', 2)
      .attr('d', line);

    // Axes
    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(xScale).ticks(5))
      .attr('color', '#64748b');

    g.append('g')
      .call(d3.axisLeft(yScale).ticks(5))
      .attr('color', '#64748b');
  }, [metrics, width, height, simulationState.running]);

  return (
    <svg
      ref={svgRef}
      width={width}
      height={height}
      style={{ overflow: 'visible' }}
    />
  );
};
