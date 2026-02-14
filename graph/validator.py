"""Graph validation logic."""

from typing import List, Set, Tuple
from graph.models import GraphNode, GraphEdge


class GraphValidator:
    """Validates graph structure and integrity."""
    
    def __init__(self, debug: bool = False):
        """Initialize validator.
        
        Args:
            debug: If True, print validation details
        """
        self.debug = debug
    
    def validate_graph(self, nodes: List[GraphNode], 
                      edges: List[GraphEdge]) -> Tuple[List[GraphNode], List[GraphEdge]]:
        """Validate nodes and edges, removing invalid elements.
        
        Args:
            nodes: List of GraphNode objects
            edges: List of GraphEdge objects
            
        Returns:
            Tuple of (valid_nodes, valid_edges)
        """
        print("\n🔍 Validating graph structure...")
        
        # Step 1: Validate nodes
        valid_nodes = self._validate_nodes(nodes)
        
        # Build set of valid node IDs
        valid_node_ids = {node.id for node in valid_nodes}
        
        # Step 2: Validate edges
        valid_edges = self._validate_edges(edges, valid_node_ids)
        
        # Print summary
        self._print_validation_summary(nodes, edges, valid_nodes, valid_edges)
        
        return valid_nodes, valid_edges
    
    def _validate_nodes(self, nodes: List[GraphNode]) -> List[GraphNode]:
        """Validate nodes.
        
        Args:
            nodes: List of GraphNode objects
            
        Returns:
            List of valid GraphNode objects
        """
        seen_ids = set()
        valid_nodes = []
        duplicate_count = 0
        
        for node in nodes:
            # Check for duplicate IDs
            if node.id in seen_ids:
                duplicate_count += 1
                if self.debug:
                    print(f"  ⚠️  Duplicate node ID: {node.id}")
                continue
            
            # Check required fields
            if not node.id or not node.label:
                if self.debug:
                    print(f"  ⚠️  Node missing required fields: {node.id}")
                continue
            
            seen_ids.add(node.id)
            valid_nodes.append(node)
        
        if duplicate_count > 0:
            print(f"  Removed {duplicate_count} duplicate nodes")
        
        return valid_nodes
    
    def _validate_edges(self, edges: List[GraphEdge], 
                       valid_node_ids: Set[str]) -> List[GraphEdge]:
        """Validate edges.
        
        Args:
            edges: List of GraphEdge objects
            valid_node_ids: Set of valid node IDs
            
        Returns:
            List of valid GraphEdge objects
        """
        valid_edges = []
        invalid_count = 0
        self_loop_count = 0
        bad_confidence_count = 0
        
        for edge in edges:
            # Check for self-loops
            if edge.source == edge.target:
                self_loop_count += 1
                if self.debug:
                    print(f"  ⚠️  Self-loop: {edge.source} -> {edge.target}")
                continue
            
            # Check if nodes exist
            if edge.source not in valid_node_ids:
                invalid_count += 1
                if self.debug:
                    print(f"  ⚠️  Invalid source node: {edge.source}")
                continue
            
            if edge.target not in valid_node_ids:
                invalid_count += 1
                if self.debug:
                    print(f"  ⚠️  Invalid target node: {edge.target}")
                continue
            
            # Check confidence range
            if not (0.0 <= edge.confidence <= 1.0):
                bad_confidence_count += 1
                if self.debug:
                    print(f"  ⚠️  Invalid confidence: {edge.confidence}")
                # Clamp it instead of removing
                edge.confidence = max(0.0, min(1.0, edge.confidence))
            
            valid_edges.append(edge)
        
        if self_loop_count > 0:
            print(f"  Removed {self_loop_count} self-loops")
        if invalid_count > 0:
            print(f"  Removed {invalid_count} edges with invalid node references")
        if bad_confidence_count > 0:
            print(f"  Clamped {bad_confidence_count} edges with out-of-range confidence")
        
        return valid_edges
    
    def _print_validation_summary(self, original_nodes: List[GraphNode], 
                                 original_edges: List[GraphEdge],
                                 valid_nodes: List[GraphNode], 
                                 valid_edges: List[GraphEdge]):
        """Print validation summary.
        
        Args:
            original_nodes: Original node list
            original_edges: Original edge list
            valid_nodes: Valid node list
            valid_edges: Valid edge list
        """
        nodes_removed = len(original_nodes) - len(valid_nodes)
        edges_removed = len(original_edges) - len(valid_edges)
        
        print(f"\n  Initial: {len(original_nodes)} nodes, {len(original_edges)} edges")
        print(f"  Valid: {len(valid_nodes)} nodes, {len(valid_edges)} edges")
        
        if nodes_removed > 0 or edges_removed > 0:
            print(f"  Removed: {nodes_removed} nodes, {edges_removed} edges")
