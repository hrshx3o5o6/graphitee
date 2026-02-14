"""Node importance scoring."""

from typing import List
from graph.models import GraphNode


class ImportanceScorer:
    """Computes importance scores for nodes."""
    
    def __init__(self, debug: bool = False):
        """Initialize scorer.
        
        Args:
            debug: If True, print scoring details
        """
        self.debug = debug
    
    def score_nodes(self, nodes: List[GraphNode]) -> List[GraphNode]:
        """Compute importance scores for all nodes.
        
        Formula:
            importance = 0.4 * normalized_occurrence + 
                        0.3 * degree_centrality + 
                        0.3 * betweenness_centrality
        
        Args:
            nodes: List of GraphNode objects
            
        Returns:
            List of GraphNode objects with updated importance scores
        """
        print("\n⭐ Computing importance scores...")
        
        if not nodes:
            return nodes
        
        # Normalize occurrence counts
        max_occurrence = max((n.occurrence_count for n in nodes), default=1)
        
        for node in nodes:
            # Normalize occurrence to [0, 1]
            norm_occurrence = node.occurrence_count / max_occurrence if max_occurrence > 0 else 0.0
            
            # Compute weighted importance
            importance = (
                0.4 * norm_occurrence +
                0.3 * node.degree_centrality +
                0.3 * node.betweenness_centrality
            )
            
            node.importance_score = importance
        
        if self.debug:
            self._print_top_nodes(nodes)
        
        return nodes
    
    def _print_top_nodes(self, nodes: List[GraphNode], top_n: int = 10):
        """Print top N most important nodes.
        
        Args:
            nodes: List of GraphNode objects
            top_n: Number of top nodes to print
        """
        sorted_nodes = sorted(nodes, key=lambda n: n.importance_score, reverse=True)
        
        print(f"\n  Top {top_n} Most Important Nodes:")
        print(f"  {'Rank':<6} {'Label':<30} {'Score':<8} {'Degree':<8} {'Between':<8}")
        print(f"  {'-'*70}")
        
        for i, node in enumerate(sorted_nodes[:top_n], 1):
            print(f"  {i:<6} {node.label[:29]:<30} "
                  f"{node.importance_score:.3f}    "
                  f"{node.degree_centrality:.3f}    "
                  f"{node.betweenness_centrality:.3f}")
