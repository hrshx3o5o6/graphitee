"""Graph assembly and pruning."""

from typing import List, Set, Tuple
from graph.models import GraphNode, GraphEdge


class GraphAssembler:
    """Assembles and prunes the final graph."""
    
    def __init__(self, prune_isolated: bool = True, debug: bool = False):
        """Initialize assembler.
        
        Args:
            prune_isolated: If True, remove isolated nodes with low occurrence
            debug: If True, print assembly details
        """
        self.prune_isolated = prune_isolated
        self.debug = debug
    
    def assemble(self, nodes: List[GraphNode], 
                edges: List[GraphEdge]) -> Tuple[List[GraphNode], List[GraphEdge]]:
        """Assemble final graph with optional pruning.
        
        Args:
            nodes: List of GraphNode objects
            edges: List of GraphEdge objects
            
        Returns:
            Tuple of (pruned_nodes, pruned_edges)
        """
        print("\n🔨 Assembling final graph...")
        
        # Build node degree map
        node_degrees = self._compute_node_degrees(nodes, edges)
        
        # Prune isolated nodes if enabled
        if self.prune_isolated:
            nodes, edges = self._prune_nodes(nodes, edges, node_degrees)
        
        # Sort nodes by importance
        nodes = sorted(nodes, key=lambda n: n.importance_score, reverse=True)
        
        # Sort edges by confidence
        edges = sorted(edges, key=lambda e: e.confidence, reverse=True)
        
        print(f"  Final graph: {len(nodes)} nodes, {len(edges)} edges")
        
        return nodes, edges
    
    def _compute_node_degrees(self, nodes: List[GraphNode], 
                             edges: List[GraphEdge]) -> dict:
        """Compute degree for each node.
        
        Args:
            nodes: List of GraphNode objects
            edges: List of GraphEdge objects
            
        Returns:
            Dictionary mapping node_id to degree
        """
        degrees = {node.id: 0 for node in nodes}
        
        for edge in edges:
            if edge.source in degrees:
                degrees[edge.source] += 1
            if edge.target in degrees:
                degrees[edge.target] += 1
        
        return degrees
    
    def _prune_nodes(self, nodes: List[GraphNode], edges: List[GraphEdge],
                    node_degrees: dict) -> Tuple[List[GraphNode], List[GraphEdge]]:
        """Prune isolated nodes with low occurrence.
        
        Rule: Remove nodes with degree=0 AND occurrence_count=1
        
        Args:
            nodes: List of GraphNode objects
            edges: List of GraphEdge objects
            node_degrees: Dictionary of node degrees
            
        Returns:
            Tuple of (pruned_nodes, pruned_edges)
        """
        # Identify nodes to remove
        nodes_to_remove = set()
        
        for node in nodes:
            degree = node_degrees.get(node.id, 0)
            
            # Remove isolated nodes with low occurrence
            if degree == 0 and node.occurrence_count <= 1:
                nodes_to_remove.add(node.id)
                if self.debug:
                    print(f"    Pruning isolated: {node.label}")
        
        # Filter nodes
        pruned_nodes = [n for n in nodes if n.id not in nodes_to_remove]
        
        # Filter edges (shouldn't change since isolated nodes have no edges)
        pruned_edges = [e for e in edges 
                       if e.source not in nodes_to_remove 
                       and e.target not in nodes_to_remove]
        
        if nodes_to_remove:
            print(f"  Pruned {len(nodes_to_remove)} isolated nodes")
        
        return pruned_nodes, pruned_edges
