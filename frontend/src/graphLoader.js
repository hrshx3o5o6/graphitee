/**
 * Graph data loader utility
 * Fetches and processes the final graph JSON
 */

export async function loadGraphData(graphId) {
  try {
    const response = await fetch(`/api/graph/${graphId}`);
    
    if (!response.ok) {
      throw new Error(`Failed to load graph: ${response.statusText}`);
    }
    
    const data = await response.json();
    return processGraphData(data);
  } catch (error) {
    console.error('Error loading graph:', error);
    throw error;
  }
}

/**
 * Process raw graph data for visualization
 */
function processGraphData(rawData) {
  // Ensure nodes have required fields
  const nodes = rawData.nodes.map(node => ({
    id: node.id,
    label: node.label,
    type: node.type || 'unknown',
    importance: node.importance || 0.5,
    aliases: node.aliases || [],
    metrics: node.metrics || {}
  }));
  
  // Ensure edges have required fields
  const links = rawData.edges.map(edge => ({
    source: edge.source,
    target: edge.target,
    relation: edge.relation || 'ASSOCIATED_WITH',
    weight: edge.weight || 0.5
  }));
  
  return { nodes, links };
}

/**
 * Get available graphs from the API
 */
export async function listGraphs() {
  try {
    const response = await fetch('/api/graphs');
    if (!response.ok) {
      throw new Error('Failed to list graphs');
    }
    return await response.json();
  } catch (error) {
    console.error('Error listing graphs:', error);
    return [];
  }
}

/**
 * Color mapping for concept types
 */
export const TYPE_COLORS = {
  core_concept: '#4A90E2',     // Blue
  technique: '#50C878',        // Green
  metric: '#FF8C42',           // Orange
  process: '#9B59B6',          // Purple
  assumption: '#E74C3C',       // Red
  unknown: '#95A5A6'           // Gray
};

/**
 * Color mapping for relation types
 */
export const RELATION_COLORS = {
  DEFINES: '#3498DB',          // Blue
  CAUSES: '#E74C3C',           // Red
  DEPENDS_ON: '#F39C12',       // Orange
  PART_OF: '#9B59B6',          // Purple
  USES: '#1ABC9C',             // Teal
  EXTENDS: '#2ECC71',          // Green
  CONTRASTS_WITH: '#E67E22',   // Dark Orange
  MEASURED_BY: '#34495E',      // Dark Gray
  ASSOCIATED_WITH: '#95A5A6'   // Light Gray
};

/**
 * Get node color based on type
 */
export function getNodeColor(node) {
  return TYPE_COLORS[node.type] || TYPE_COLORS.unknown;
}

/**
 * Get edge color based on relation type
 */
export function getEdgeColor(edge) {
  return RELATION_COLORS[edge.relation] || RELATION_COLORS.ASSOCIATED_WITH;
}

/**
 * Get node size based on importance
 */
export function getNodeSize(node) {
  return node.importance * 10 + 2; // Scale importance to reasonable size
}

/**
 * Get edge width based on weight
 */
export function getEdgeWidth(edge) {
  return edge.weight * 2; // Scale weight to visible width
}
