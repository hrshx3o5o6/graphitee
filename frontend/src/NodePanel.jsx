/**
 * NodePanel Component
 * Shows detailed information about selected node
 */

import { useMemo } from 'react';
import { TYPE_COLORS, RELATION_COLORS } from './graphLoader';
import './NodePanel.css';

export default function NodePanel({ node, graphData, onClose, onNodeNavigate }) {
  // Find connected nodes
  const connections = useMemo(() => {
    if (!node || !graphData) return { incoming: [], outgoing: [] };
    
    const incoming = [];
    const outgoing = [];
    
    graphData.links.forEach(link => {
      if (link.target.id === node.id) {
        incoming.push({
          node: link.source,
          relation: link.relation,
          weight: link.weight
        });
      } else if (link.source.id === node.id) {
        outgoing.push({
          node: link.target,
          relation: link.relation,
          weight: link.weight
        });
      }
    });
    
    return { incoming, outgoing };
  }, [node, graphData]);

  if (!node) {
    return (
      <div className="node-panel node-panel-empty">
        <div className="panel-hint">
          Click on a node to see details
        </div>
      </div>
    );
  }

  const nodeColor = TYPE_COLORS[node.type] || TYPE_COLORS.unknown;

  return (
    <div className="node-panel">
      {/* Header */}
      <div className="panel-header">
        <div className="panel-title-row">
          <div 
            className="node-color-indicator" 
            style={{ backgroundColor: nodeColor }}
          />
          <h2 className="panel-title">{node.label}</h2>
        </div>
        <button className="close-button" onClick={onClose}>×</button>
      </div>

      {/* Content */}
      <div className="panel-content">
        {/* Type */}
        <div className="info-section">
          <div className="info-label">Type</div>
          <div className="info-value type-badge" style={{ color: nodeColor }}>
            {node.type}
          </div>
        </div>

        {/* Importance */}
        <div className="info-section">
          <div className="info-label">Importance</div>
          <div className="info-value">
            <div className="importance-bar-container">
              <div 
                className="importance-bar" 
                style={{ 
                  width: `${node.importance * 100}%`,
                  backgroundColor: nodeColor 
                }}
              />
            </div>
            <span className="importance-value">{node.importance.toFixed(2)}</span>
          </div>
        </div>

        {/* Aliases */}
        {node.aliases && node.aliases.length > 0 && (
          <div className="info-section">
            <div className="info-label">Aliases</div>
            <div className="info-value">
              {node.aliases.map((alias, i) => (
                <span key={i} className="alias-badge">{alias}</span>
              ))}
            </div>
          </div>
        )}

        {/* Metrics */}
        {node.metrics && Object.keys(node.metrics).length > 0 && (
          <div className="info-section">
            <div className="info-label">Graph Metrics</div>
            <div className="metrics-grid">
              {Object.entries(node.metrics).map(([key, value]) => (
                <div key={key} className="metric-item">
                  <span className="metric-name">
                    {key.replace(/_/g, ' ')}:
                  </span>
                  <span className="metric-value">
                    {typeof value === 'number' ? value.toFixed(3) : value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Incoming Connections */}
        {connections.incoming.length > 0 && (
          <div className="info-section">
            <div className="info-label">
              Incoming ({connections.incoming.length})
            </div>
            <div className="connections-list">
              {connections.incoming.map((conn, i) => (
                <div key={i} className="connection-item">
                  <button 
                    className="connection-node"
                    onClick={() => onNodeNavigate(conn.node)}
                  >
                    {conn.node.label}
                  </button>
                  <span 
                    className="connection-relation"
                    style={{ color: RELATION_COLORS[conn.relation] }}
                  >
                    {conn.relation}
                  </span>
                  <span className="connection-weight">
                    ({conn.weight.toFixed(2)})
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Outgoing Connections */}
        {connections.outgoing.length > 0 && (
          <div className="info-section">
            <div className="info-label">
              Outgoing ({connections.outgoing.length})
            </div>
            <div className="connections-list">
              {connections.outgoing.map((conn, i) => (
                <div key={i} className="connection-item">
                  <button 
                    className="connection-node"
                    onClick={() => onNodeNavigate(conn.node)}
                  >
                    {conn.node.label}
                  </button>
                  <span 
                    className="connection-relation"
                    style={{ color: RELATION_COLORS[conn.relation] }}
                  >
                    {conn.relation}
                  </span>
                  <span className="connection-weight">
                    ({conn.weight.toFixed(2)})
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* No connections message */}
        {connections.incoming.length === 0 && connections.outgoing.length === 0 && (
          <div className="info-section">
            <div className="info-label">Connections</div>
            <div className="info-value empty-state">
              No connections found
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
