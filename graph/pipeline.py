"""Main pipeline for graph refinement and assembly."""

from typing import List, Dict, Tuple
from graph.models import GraphNode, GraphEdge, FinalGraph
from graph.validator import GraphValidator
from graph.edge_refiner import EdgeRefiner
from graph.metrics import GraphMetrics
from graph.scoring import ImportanceScorer
from graph.assembler import GraphAssembler


class GraphRefinementPipeline:
    """Orchestrates graph refinement and final assembly."""
    
    def __init__(self, 
                 min_confidence: float = 0.55,
                 prune_isolated: bool = True,
                 debug: bool = False):
        """Initialize pipeline.
        
        Args:
            min_confidence: Minimum edge confidence threshold
            prune_isolated: If True, prune isolated nodes
            debug: If True, print detailed progress
        """
        self.min_confidence = min_confidence
        self.prune_isolated = prune_isolated
        self.debug = debug
        
        # Initialize components
        self.validator = GraphValidator(debug=debug)
        self.edge_refiner = EdgeRefiner(min_confidence=min_confidence, debug=debug)
        self.metrics_computer = GraphMetrics(debug=debug)
        self.scorer = ImportanceScorer(debug=debug)
        self.assembler = GraphAssembler(prune_isolated=prune_isolated, debug=debug)
    
    def build_final_graph(self, canonical_concepts: List[Dict], 
                         relationships: List[Dict]) -> FinalGraph:
        """Build final refined graph from canonical concepts and relationships.
        
        Args:
            canonical_concepts: List of canonical concept dicts from Phase 4
            relationships: List of relationship dicts from Phase 5
            
        Returns:
            FinalGraph object
        """
        print("🚀 Starting Graph Refinement Pipeline")
        print("=" * 70)
        
        # Step 1: Convert to graph models
        print("\n📦 Step 1: Converting to graph models...")
        nodes = self._convert_to_nodes(canonical_concepts)
        edges = self._convert_to_edges(relationships)
        print(f"  Loaded: {len(nodes)} nodes, {len(edges)} edges")
        
        # Step 2: Validate graph structure
        nodes, edges = self.validator.validate_graph(nodes, edges)
        
        # Step 3: Refine edges
        edges = self.edge_refiner.refine_edges(edges)
        
        # Step 4: Compute graph metrics
        graph_metrics = self.metrics_computer.compute_metrics(nodes, edges)
        
        # Step 5: Score node importance
        nodes = self.scorer.score_nodes(nodes)
        
        # Step 6: Assemble and prune
        nodes, edges = self.assembler.assemble(nodes, edges)
        
        # Build final graph
        final_graph = FinalGraph(
            nodes=nodes,
            edges=edges,
            metadata={
                "num_nodes": len(nodes),
                "num_edges": len(edges),
                "graph_metrics": graph_metrics,
                "min_confidence": self.min_confidence,
                "pruned_isolated": self.prune_isolated
            }
        )
        
        print("\n✅ Graph refinement complete!")
        self._print_summary(final_graph)
        
        return final_graph
    
    def _convert_to_nodes(self, canonical_concepts: List[Dict]) -> List[GraphNode]:
        """Convert canonical concepts to GraphNode objects.
        
        Args:
            canonical_concepts: List of canonical concept dicts
            
        Returns:
            List of GraphNode objects
        """
        nodes = []
        
        for concept in canonical_concepts:
            node = GraphNode(
                id=concept.get("canonical_id", ""),
                label=concept.get("canonical_name", ""),
                type=concept.get("type", "unknown"),
                aliases=concept.get("aliases", []),
                occurrence_count=concept.get("total_mentions", 1)
            )
            nodes.append(node)
        
        return nodes
    
    def _convert_to_edges(self, relationships: List[Dict]) -> List[GraphEdge]:
        """Convert relationships to GraphEdge objects.
        
        Args:
            relationships: List of relationship dicts
            
        Returns:
            List of GraphEdge objects
        """
        edges = []
        
        for rel in relationships:
            edge = GraphEdge(
                id=rel.get("edge_id", ""),
                source=rel.get("source_concept_id", ""),
                target=rel.get("target_concept_id", ""),
                relation_type=rel.get("relation_type", ""),
                confidence=rel.get("confidence", 0.6),
                evidence_blocks=[rel.get("evidence_block_id", "")]
            )
            edges.append(edge)
        
        return edges
    
    def _print_summary(self, graph: FinalGraph):
        """Print final graph summary.
        
        Args:
            graph: FinalGraph object
        """
        print(f"\n📊 Final Graph Summary")
        print(f"=" * 70)
        print(f"Nodes: {len(graph.nodes)}")
        print(f"Edges: {len(graph.edges)}")
        
        if graph.edges:
            avg_confidence = sum(e.confidence for e in graph.edges) / len(graph.edges)
            print(f"Average edge confidence: {avg_confidence:.2f}")
        
        # Edge type distribution
        if graph.edges:
            relation_counts = {}
            for edge in graph.edges:
                rel = edge.relation_type
                relation_counts[rel] = relation_counts.get(rel, 0) + 1
            
            print(f"\nEdge types:")
            for rel_type, count in sorted(relation_counts.items(), 
                                         key=lambda x: x[1], reverse=True):
                print(f"  {rel_type}: {count}")
        
        # Top nodes
        if graph.nodes:
            print(f"\nTop 5 most important concepts:")
            top_nodes = sorted(graph.nodes, 
                             key=lambda n: n.importance_score, 
                             reverse=True)[:5]
            for i, node in enumerate(top_nodes, 1):
                print(f"  {i}. {node.label} (score: {node.importance_score:.2f})")
