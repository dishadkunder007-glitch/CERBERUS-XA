import React, { useState, useRef, useEffect } from 'react';
import { 
  Network, 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  Maximize2, 
  Filter, 
  Info,
  ShieldAlert,
  GitBranch,
  Layers
} from 'lucide-react';

export const KnowledgeGraph = ({ graphData, onSelectNode }) => {
  const [selectedNode, setSelectedNode] = useState(null);
  const [zoom, setZoom] = useState(1);
  const [filterType, setFilterType] = useState('ALL');
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const svgRef = useRef(null);

  // Fallback if graphData is empty
  const nodes = graphData?.nodes || [];
  const links = graphData?.links || [];

  // Computed layout positions for a clean, stable forensic graph representation
  const layoutNodes = React.useMemo(() => {
    const width = 800;
    const height = 480;
    const centerX = width / 2;
    const centerY = height / 2;

    return nodes.map((node, index) => {
      // Position calculation based on type
      let x = centerX;
      let y = centerY;

      if (node.type === 'ENTITY') {
        const angle = (index * 2 * Math.PI) / 3;
        x = centerX + Math.cos(angle) * 110;
        y = centerY + Math.sin(angle) * 80;
      } else if (node.type === 'CONFLICT') {
        const conflictIndex = nodes.filter(n => n.type === 'CONFLICT').indexOf(node);
        const angle = (conflictIndex * (2 * Math.PI / 3)) + Math.PI / 6;
        x = centerX + Math.cos(angle) * 220;
        y = centerY + Math.sin(angle) * 160;
      } else {
        // EVIDENCE nodes on outer perimeter
        const evIndex = nodes.filter(n => n.type === 'EVIDENCE').indexOf(node);
        const totalEv = Math.max(nodes.filter(n => n.type === 'EVIDENCE').length, 1);
        const angle = (evIndex * (2 * Math.PI / totalEv)) - Math.PI / 4;
        x = centerX + Math.cos(angle) * 310;
        y = centerY + Math.sin(angle) * 190;
      }

      return {
        ...node,
        x,
        y
      };
    });
  }, [nodes]);

  const nodeMap = React.useMemo(() => {
    const map = {};
    layoutNodes.forEach(n => {
      map[n.id] = n;
    });
    return map;
  }, [layoutNodes]);

  // Handle pan & drag
  const handleMouseDown = (e) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setSelectedNode(null);
  };

  const getNodeColor = (node) => {
    if (node.type === 'CONFLICT') {
      return {
        fill: '#ef4444',
        stroke: '#f87171',
        glow: 'rgba(239, 68, 68, 0.4)',
        text: '#fca5a5'
      };
    }
    if (node.type === 'ENTITY') {
      return {
        fill: '#06b6d4',
        stroke: '#22d3ee',
        glow: 'rgba(6, 182, 212, 0.4)',
        text: '#a5f3fc'
      };
    }
    // EVIDENCE
    return {
      fill: '#3b82f6',
      stroke: '#60a5fa',
      glow: 'rgba(59, 130, 246, 0.3)',
      text: '#93c5fd'
    };
  };

  const getLinkColor = (link) => {
    if (link.type === 'CONTRADICTS') return '#ef4444';
    if (link.type === 'SUPPORTS') return '#10b981';
    return '#475569';
  };

  return (
    <div className="relative rounded-2xl border border-slate-200 dark:border-dark-700 bg-slate-900 dark:bg-dark-950 overflow-hidden shadow-sm dark:shadow-panel">
      
      {/* Graph Toolbar Header */}
      <div className="p-4 border-b border-slate-800 dark:border-dark-800 bg-slate-950/90 dark:bg-dark-900/80 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-blue-500/10 text-cyan-400 dark:text-accent-blue border border-cyan-500/30 dark:border-blue-500/20">
            <Network className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold font-mono text-white dark:text-slate-100 flex items-center gap-2">
              <span>Multimodal Evidence Graph</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-500/20 text-cyan-300 dark:text-accent-blue border border-cyan-500/30">
                MEMBER 3 CONTRACT
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">
              Interactive topological visualization of entities, evidence modalities, and contradiction edges
            </p>
          </div>
        </div>

        {/* Zoom & Reset Controls */}
        <div className="flex items-center gap-1.5 bg-dark-800/90 border border-dark-700 rounded-lg p-1">
          <button
            onClick={() => setZoom(prev => Math.min(prev + 0.15, 2.0))}
            className="p-1.5 rounded text-slate-400 hover:text-slate-100 hover:bg-dark-700"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setZoom(prev => Math.max(prev - 0.15, 0.5))}
            className="p-1.5 rounded text-slate-400 hover:text-slate-100 hover:bg-dark-700"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <span className="text-[11px] font-mono text-slate-400 px-1">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={resetView}
            className="p-1.5 rounded text-slate-400 hover:text-slate-100 hover:bg-dark-700"
            title="Reset Graph Position"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Legend Bar */}
      <div className="px-4 py-2 border-b border-dark-800/60 bg-dark-900/40 flex flex-wrap items-center gap-4 text-xs font-mono">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
          <span className="text-slate-300">Entity Nodes</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse"></span>
          <span className="text-rose-300">Conflict / Contradiction</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
          <span className="text-slate-300">Multimodal Evidence</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-0.5 border-t-2 border-dashed border-rose-500"></span>
          <span className="text-rose-400">Contradiction Edge</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-0.5 bg-emerald-500"></span>
          <span className="text-emerald-400">Support Edge</span>
        </div>
      </div>

      {/* Interactive SVG Canvas */}
      <div 
        className="w-full h-[480px] cursor-grab active:cursor-grabbing relative overflow-hidden radar-grid select-none"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
      >
        <svg
          ref={svgRef}
          className="w-full h-full"
          viewBox="0 0 800 480"
          preserveAspectRatio="xMidYMid meet"
        >
          <defs>
            <marker
              id="arrow-contradicts"
              viewBox="0 0 10 10"
              refX="22"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#ef4444" />
            </marker>
            <marker
              id="arrow-supports"
              viewBox="0 0 10 10"
              refX="22"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#10b981" />
            </marker>
            <filter id="glow-red" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`} transform-origin="400 240">
            
            {/* Draw Links */}
            {links.map((link, idx) => {
              const src = nodeMap[link.source];
              const tgt = nodeMap[link.target];
              if (!src || !tgt) return null;

              const isContradiction = link.type === 'CONTRADICTS';
              const isSupport = link.type === 'SUPPORTS';
              const color = getLinkColor(link);

              const midX = (src.x + tgt.x) / 2;
              const midY = (src.y + tgt.y) / 2;

              return (
                <g key={`link-${idx}`}>
                  <line
                    x1={src.x}
                    y1={src.y}
                    x2={tgt.x}
                    y2={tgt.y}
                    stroke={color}
                    strokeWidth={isContradiction ? 2 : 1.5}
                    strokeDasharray={isContradiction ? '4 3' : 'none'}
                    markerEnd={isContradiction ? 'url(#arrow-contradicts)' : isSupport ? 'url(#arrow-supports)' : undefined}
                    opacity={0.8}
                  />
                  {link.relation && (
                    <text
                      x={midX}
                      y={midY - 4}
                      fill={isContradiction ? '#fca5a5' : isSupport ? '#86efac' : '#94a3b8'}
                      fontSize="9"
                      fontFamily="monospace"
                      textAnchor="middle"
                      className="pointer-events-none select-none bg-dark-950"
                    >
                      {link.relation}
                    </text>
                  )}
                </g>
              );
            })}

            {/* Draw Nodes */}
            {layoutNodes.map((node) => {
              const colors = getNodeColor(node);
              const isSelected = selectedNode?.id === node.id;
              const isConflict = node.type === 'CONFLICT';

              return (
                <g
                  key={node.id}
                  transform={`translate(${node.x}, ${node.y})`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedNode(node);
                    if (onSelectNode) onSelectNode(node);
                  }}
                  className="cursor-pointer group"
                >
                  {/* Glowing background halo */}
                  <circle
                    r={isSelected ? (node.radius || 22) + 6 : (node.radius || 20) + 3}
                    fill="none"
                    stroke={colors.stroke}
                    strokeWidth={isSelected ? 3 : 1.5}
                    strokeOpacity={isSelected ? 0.9 : 0.4}
                    className={isConflict ? 'animate-pulse' : ''}
                  />

                  {/* Main Node body */}
                  <circle
                    r={node.radius || 20}
                    fill={colors.fill}
                    fillOpacity={0.85}
                    stroke="#0b1224"
                    strokeWidth={2}
                    filter={isConflict ? 'url(#glow-red)' : undefined}
                  />

                  {/* Icon / symbol */}
                  {isConflict ? (
                    <text
                      textAnchor="middle"
                      dy="4"
                      fill="#ffffff"
                      fontSize="14"
                      fontWeight="bold"
                    >
                      !
                    </text>
                  ) : (
                    <circle r="4" fill="#ffffff" opacity="0.8" />
                  )}

                  {/* Label */}
                  <text
                    y={(node.radius || 20) + 14}
                    fill={colors.text}
                    fontSize="10"
                    fontFamily="monospace"
                    textAnchor="middle"
                    className="select-none font-medium"
                  >
                    {node.label.length > 25 ? `${node.label.slice(0, 23)}...` : node.label}
                  </text>
                </g>
              );
            })}

          </g>
        </svg>

        {/* Selected Node Details Drawer / Popover */}
        {selectedNode && (
          <div className="absolute top-4 right-4 max-w-xs w-full bg-dark-900/95 border border-dark-600 rounded-xl p-4 shadow-2xl backdrop-blur-md z-10 animate-fade-in">
            <div className="flex items-center justify-between border-b border-dark-700 pb-2 mb-2.5">
              <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded font-bold ${
                selectedNode.type === 'CONFLICT' 
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' 
                  : selectedNode.type === 'ENTITY'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
              }`}>
                {selectedNode.type} NODE
              </span>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-slate-400 hover:text-white text-xs"
              >
                ✕
              </button>
            </div>

            <h4 className="text-xs font-bold text-slate-100 font-mono">
              {selectedNode.label}
            </h4>
            
            {selectedNode.category && (
              <p className="text-[11px] text-slate-400 mt-1 font-mono">
                Category: <span className="text-slate-200">{selectedNode.category}</span>
              </p>
            )}

            {selectedNode.modality && (
              <p className="text-[11px] text-slate-400 mt-0.5 font-mono">
                Modality: <span className="text-accent-cyan">{selectedNode.modality}</span>
              </p>
            )}

            <div className="mt-3 pt-2 border-t border-dark-800 text-[10px] text-slate-500 font-mono">
              Node ID: {selectedNode.id}
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default KnowledgeGraph;
