"""Graph metrics computation using NetworkX."""

import networkx as nx
from typing import List, Dict
from graph.models import GraphNode, GraphEdge


class GraphMetrics:
    """Computes graph-level and node-level metrics."""
    
    def __init__(self, debug: bool = False):
        """Initialize metrics computer.
        
        Args:
            debug: If True, print metric details
        """
        self.debug = debug
    
    def compute_metrics(self, nodes: List[GraphNode], 
                       edges: List[GraphEdge]) -> Dict[str, float]:
        """Compute graph metrics and update node properties.
        
        Args:
            nodes: List of GraphNode objects
            edges: List of GraphEdge objects
            
        Returns:
            Dictionary of graph-level metrics
        """
        print("\n📊 Computing graph metrics...")
        
        # Build NetworkX graph
        G = self._build_networkx_graph(nodes, edges)
        
        if len(G.nodes()) == 0:
            print("  ⚠️  Empty graph, skipping metrics")
            return {}
        
        # Compute node-level metrics
        self._compute_node_metrics(G, nodes)
        
        # Compute graph-level metrics
        graph_metrics = self._compute_graph_metrics(G)
        
        if self.debug:
            self._print_metrics(graph_metrics)
        
        return graph_metrics
    
    def _build_networkx_graph(self, nodes: List[GraphNode], 
                             edges: List[GraphEdge]) -> nx.DiGraph:
        """Build NetworkX directed graph.
        
        Args:
            nodes: List of GraphNode objects
            edges: List of GraphEdge objects
            
        Returns:
            NetworkX DiGraph
        """
        G = nx.DiGraph()
        
        # Add nodes
        for node in nodes:
            G.add_node(node.id, label=node.label, type=node.type)
        
        # Add edges
        for edge in edges:
            G.add_edge(
                edge.source, 
                edge.target, 
                relation=edge.relation_type,
                weight=edge.confidence
            )
        
        return G
    
    def _compute_node_metrics(self, G: nx.DiGraph, nodes: List[GraphNode]):
        """Compute node-level metrics and update node objects.
        
        Args:
            G: NetworkX graph
            nodes: List of GraphNode objects to update
        """
        # Create node ID to node object mapping
        node_map = {node.id: node for node in nodes}
        
        # Compute centrality metrics
        try:
            degree_cent = nx.degree_centrality(G)
            betweenness_cent = nx.betweenness_centrality(G)
            clustering_coef = nx.clustering(G.to_undirected())
            
            # Update node objects
            for node_id, node in node_map.items():
                if node_id in G.nodes():
                    node.degree_centrality = degree_cent.get(node_id, 0.0)
                    node.betweenness_centrality = betweenness_cent.get(node_id, 0.0)
                    node.clustering_coefficient = clustering_coef.get(node_id, 0.0)
        
        except Exception as e:
            print(f"  ⚠️  Error computing metrics: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
    
    def _compute_graph_metrics(self, G: nx.DiGraph) -> Dict[str, float]:
        """Compute graph-level metrics.
        
        Args:
            G: NetworkX graph
            
        Returns:
            Dictionary of graph metrics
        """
        metrics = {
            "num_nodes": G.number_of_nodes(),
            "num_edges": G.number_of_edges(),
            "density": 0.0,
            "avg_degree": 0.0,
            "num_connected_components": 0
        }
        
        if G.number_of_nodes() == 0:
            return metrics
        
        # Density
        try:
            metrics["density"] = nx.density(G)
        except:
            pass
        
        # Average degree
        if G.number_of_nodes() > 0:
            degrees = [d for n, d in G.degree()]
            metrics["avg_degree"] = sum(degrees) / len(degrees) if degrees else 0.0
        
        # Connected components (using undirected version)
        try:
            G_undirected = G.to_undirected()
            metrics["num_connected_components"] = nx.number_connected_components(G_undirected)
        except:
            pass
        
        return metrics
    
    def _print_metrics(self, metrics: Dict[str, float]):
        """Print graph metrics.
        
        Args:
            metrics: Dictionary of graph metrics
        """
        print(f"\n  Graph Metrics:")
        print(f"    Nodes: {metrics.get('num_nodes', 0)}")
        print(f"    Edges: {metrics.get('num_edges', 0)}")
        print(f"    Density: {metrics.get('density', 0.0):.3f}")
        print(f"    Avg Degree: {metrics.get('avg_degree', 0.0):.2f}")
        print(f"    Connected Components: {metrics.get('num_connected_components', 0)}")
