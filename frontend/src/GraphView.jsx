/**
 * GraphView Component
 * 3D force-directed graph visualization
 */

import { useRef, useEffect, useState, useCallback } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import { 
  getNodeColor, 
  getEdgeColor, 
  getNodeSize, 
  getEdgeWidth 
} from './graphLoader';

export default function GraphView({ graphData, onNodeClick, selectedNode }) {
  const fgRef = useRef();
  const [highlightNodes, setHighlightNodes] = useState(new Set());
  const [highlightLinks, setHighlightLinks] = useState(new Set());
  const [hoverNode, setHoverNode] = useState(null);

  // Update highlight when selected node changes
  useEffect(() => {
    if (selectedNode && graphData) {
      const neighbors = new Set();
      const links = new Set();
      
      // Find connected nodes and links
      graphData.links.forEach(link => {
        if (link.source.id === selectedNode.id || link.target.id === selectedNode.id) {
          links.add(link);
          neighbors.add(link.source.id === selectedNode.id ? link.target.id : link.source.id);
        }
      });
      
      setHighlightNodes(neighbors);
      setHighlightLinks(links);
    } else {
      setHighlightNodes(new Set());
      setHighlightLinks(new Set());
    }
  }, [selectedNode, graphData]);

  // Handle node hover
  const handleNodeHover = useCallback((node) => {
    setHoverNode(node);
    if (node && !selectedNode) {
      // Highlight neighbors on hover (only if no node is selected)
      const neighbors = new Set();
      const links = new Set();
      
      graphData.links.forEach(link => {
        if (link.source.id === node.id || link.target.id === node.id) {
          links.add(link);
          neighbors.add(link.source.id === node.id ? link.target.id : link.source.id);
        }
      });
      
      setHighlightNodes(neighbors);
      setHighlightLinks(links);
    } else if (!node && !selectedNode) {
      setHighlightNodes(new Set());
      setHighlightLinks(new Set());
    }
  }, [graphData, selectedNode]);

  // Handle double-click to focus on node
  const handleNodeDoubleClick = useCallback((node) => {
    if (fgRef.current) {
      // Camera focus animation
      const distance = 150;
      fgRef.current.cameraPosition(
        { x: node.x, y: node.y, z: node.z + distance },
        node,
        1000 // Animation duration in ms
      );
    }
  }, []);

  // Node color with highlighting
  const nodeColor = useCallback((node) => {
    if (selectedNode && node.id === selectedNode.id) {
      return '#FFD700'; // Gold for selected
    }
    if (hoverNode && node.id === hoverNode.id) {
      return '#FFA500'; // Orange for hover
    }
    if (highlightNodes.size > 0 && !highlightNodes.has(node.id) && (!selectedNode || node.id !== selectedNode.id)) {
      return '#666666'; // Dim non-highlighted nodes
    }
    return getNodeColor(node);
  }, [selectedNode, hoverNode, highlightNodes]);

  // Node opacity with highlighting
  const nodeOpacity = useCallback((node) => {
    if (highlightNodes.size === 0) return 1;
    if (selectedNode && node.id === selectedNode.id) return 1;
    if (highlightNodes.has(node.id)) return 1;
    return 0.3; // Dim non-highlighted nodes
  }, [selectedNode, highlightNodes]);

  // Link color with highlighting
  const linkColor = useCallback((link) => {
    if (highlightLinks.has(link)) {
      return getEdgeColor(link);
    }
    if (highlightLinks.size > 0) {
      return '#333333'; // Dim non-highlighted links
    }
    return getEdgeColor(link);
  }, [highlightLinks]);

  // Link opacity
  const linkOpacity = useCallback((link) => {
    if (highlightLinks.size === 0) return 0.3;
    if (highlightLinks.has(link)) return 0.8;
    return 0.1;
  }, [highlightLinks]);

  // Node label - always show on hover, show selected node name
  const nodeLabel = useCallback((node) => {
    return node.label || node.name || node.id;
  }, []);

  if (!graphData) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100%',
        color: '#ffffff'
      }}>
        Loading graph...
      </div>
    );
  }

  return (
    <ForceGraph3D
      ref={fgRef}
      graphData={graphData}
      nodeLabel={nodeLabel}
      nodeVal={getNodeSize}
      nodeColor={nodeColor}
      nodeOpacity={nodeOpacity}
      onNodeClick={onNodeClick}
      onNodeHover={handleNodeHover}
      onNodeDoubleClick={handleNodeDoubleClick}
      linkColor={linkColor}
      linkOpacity={linkOpacity}
      linkWidth={getEdgeWidth}
      linkDirectionalArrowLength={3.5}
      linkDirectionalArrowRelPos={1}
      linkCurvature={0.1}
      backgroundColor="#000000"
      showNavInfo={false}
      enableNodeDrag={true}
      enableNavigationControls={true}
      cooldownTicks={100}
      onEngineStop={() => fgRef.current && fgRef.current.zoomToFit(400)}
    />
  );
}
