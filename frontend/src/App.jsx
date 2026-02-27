/**
 * Main App Component
 * Orchestrates the graph visualization UI
 */

import { useState, useEffect, useCallback } from 'react';
import GraphView from './GraphView';
import NodePanel from './NodePanel';
import { loadGraphData, listGraphs } from './graphLoader';
import './App.css';

export default function App() {
  const [graphData, setGraphData] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [availableGraphs, setAvailableGraphs] = useState([]);
  const [currentGraphId, setCurrentGraphId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load available graphs on mount
  useEffect(() => {
    const initGraph = async () => {
      // First try to load "current" graph (from CLI)
      try {
        await loadGraph('current');
        // Current graph loaded successfully
        setAvailableGraphs([{ id: 'current', name: 'Current Session' }]);
      } catch {
        // Fall back to list of saved graphs
        try {
          const graphs = await listGraphs();
          setAvailableGraphs(graphs);
          if (graphs.length > 0) {
            await loadGraph(graphs[0].id);
          } else {
            setLoading(false);
            setError('No graphs available. Please run Phase 6 to generate graphs.');
          }
        } catch (err) {
          setLoading(false);
          setError('Failed to load graphs: ' + err.message);
        }
      }
    };
    initGraph();
  }, []);

  // Load specific graph
  const loadGraph = useCallback(async (graphId) => {
    setLoading(true);
    setError(null);
    setSelectedNode(null);
    
    try {
      const data = await loadGraphData(graphId);
      setGraphData(data);
      setCurrentGraphId(graphId);
    } catch (err) {
      setError('Failed to load graph: ' + err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Handle node click
  const handleNodeClick = useCallback((node) => {
    setSelectedNode(node);
  }, []);

  // Handle node navigation from panel
  const handleNodeNavigate = useCallback((node) => {
    setSelectedNode(node);
  }, []);

  // Close panel
  const handleClosePanel = useCallback(() => {
    setSelectedNode(null);
  }, []);

  // Handle graph selection
  const handleGraphSelect = useCallback((e) => {
    const graphId = e.target.value;
    if (graphId) {
      loadGraph(graphId);
    }
  }, [loadGraph]);

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">
            <span className="title-icon">🔮</span>
            Graphitee
          </h1>
          <p className="app-subtitle">Interactive Knowledge Graph Visualization</p>
        </div>
        
        {/* Graph Selector */}
        {availableGraphs.length > 0 && (
          <div className="graph-selector">
            <label htmlFor="graph-select">Graph:</label>
            <select 
              id="graph-select"
              value={currentGraphId || ''}
              onChange={handleGraphSelect}
              disabled={loading}
            >
              {availableGraphs.map(graph => (
                <option key={graph.id} value={graph.id}>
                  {graph.name} ({graph.nodeCount} nodes, {graph.edgeCount} edges)
                </option>
              ))}
            </select>
          </div>
        )}
        
        {/* Stats */}
        {graphData && !loading && (
          <div className="graph-stats">
            <span className="stat">
              <strong>{graphData.nodes.length}</strong> nodes
            </span>
            <span className="stat-separator">•</span>
            <span className="stat">
              <strong>{graphData.links.length}</strong> edges
            </span>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="app-main">
        {loading && (
          <div className="loading-overlay">
            <div className="loading-spinner"></div>
            <p>Loading graph...</p>
          </div>
        )}
        
        {error && (
          <div className="error-overlay">
            <div className="error-icon">⚠️</div>
            <p className="error-message">{error}</p>
          </div>
        )}
        
        {!loading && !error && graphData && (
          <>
            <GraphView 
              graphData={graphData}
              onNodeClick={handleNodeClick}
              selectedNode={selectedNode}
            />
            <NodePanel 
              node={selectedNode}
              graphData={graphData}
              onClose={handleClosePanel}
              onNodeNavigate={handleNodeNavigate}
            />
          </>
        )}
      </main>

      {/* Controls Help */}
      {!loading && !error && (
        <div className="controls-help">
          <div className="help-item">🖱️ Drag to rotate</div>
          <div className="help-item">🔍 Scroll to zoom</div>
          <div className="help-item">👆 Click node for details</div>
          <div className="help-item">👆👆 Double-click to focus</div>
        </div>
      )}

      {/* Legend */}
      {!loading && !error && graphData && (
        <div className="legend">
          <h3 className="legend-title">Node Types</h3>
          <div className="legend-items">
            <div className="legend-item">
              <div className="legend-dot" style={{ background: '#4A90E2' }}></div>
              <span>Core Concept</span>
            </div>
            <div className="legend-item">
              <div className="legend-dot" style={{ background: '#50C878' }}></div>
              <span>Technique</span>
            </div>
            <div className="legend-item">
              <div className="legend-dot" style={{ background: '#FF8C42' }}></div>
              <span>Metric</span>
            </div>
            <div className="legend-item">
              <div className="legend-dot" style={{ background: '#9B59B6' }}></div>
              <span>Process</span>
            </div>
            <div className="legend-item">
              <div className="legend-dot" style={{ background: '#E74C3C' }}></div>
              <span>Assumption</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
