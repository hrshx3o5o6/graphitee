"""Edge refinement logic: merging, filtering, conflict resolution."""

from typing import List, Dict, Tuple
from collections import defaultdict
from graph.models import GraphEdge, RELATION_PRIORITY


class EdgeRefiner:
    """Refines edges through merging, filtering, and conflict resolution."""
    
    def __init__(self, min_confidence: float = 0.55, debug: bool = False):
        """Initialize edge refiner.
        
        Args:
            min_confidence: Minimum confidence threshold
            debug: If True, print refinement details
        """
        self.min_confidence = min_confidence
        self.debug = debug
    
    def refine_edges(self, edges: List[GraphEdge]) -> List[GraphEdge]:
        """Apply all refinement steps to edges.
        
        Args:
            edges: List of GraphEdge objects
            
        Returns:
            Refined list of GraphEdge objects
        """
        print(f"\n🔧 Refining edges...")
        print(f"  Initial edge count: {len(edges)}")
        
        # Step 1: Merge duplicate edges
        edges = self._merge_duplicates(edges)
        print(f"  After merging: {len(edges)} edges")
        
        # Step 2: Filter low quality edges
        edges = self._filter_low_quality(edges)
        print(f"  After filtering: {len(edges)} edges")
        
        # Step 3: Resolve conflicts
        edges = self._resolve_conflicts(edges)
        print(f"  After conflict resolution: {len(edges)} edges")
        
        return edges
    
    def _merge_duplicates(self, edges: List[GraphEdge]) -> List[GraphEdge]:
        """Merge duplicate edges with same (source, target, relation_type).
        
        Args:
            edges: List of GraphEdge objects
            
        Returns:
            List with merged edges
        """
        # Group edges by (source, target, relation_type)
        edge_groups = defaultdict(list)
        
        for edge in edges:
            key = (edge.source, edge.target, edge.relation_type)
            edge_groups[key].append(edge)
        
        merged_edges = []
        merge_count = 0
        
        for key, group in edge_groups.items():
            if len(group) == 1:
                merged_edges.append(group[0])
            else:
                # Merge multiple edges
                merged = self._merge_edge_group(group)
                merged_edges.append(merged)
                merge_count += len(group) - 1
        
        if merge_count > 0 and self.debug:
            print(f"    Merged {merge_count} duplicate edges")
        
        return merged_edges
    
    def _merge_edge_group(self, edges: List[GraphEdge]) -> GraphEdge:
        """Merge multiple edges into one.
        
        Args:
            edges: List of GraphEdge objects to merge
            
        Returns:
            Single merged GraphEdge
        """
        # Use first edge as template
        first = edges[0]
        
        # Average confidences
        avg_confidence = sum(e.confidence for e in edges) / len(edges)
        
        # Combine evidence blocks (unique)
        all_evidence = []
        for edge in edges:
            all_evidence.extend(edge.evidence_blocks)
        unique_evidence = list(set(all_evidence))
        
        return GraphEdge(
            id=first.id,
            source=first.source,
            target=first.target,
            relation_type=first.relation_type,
            confidence=avg_confidence,
            evidence_blocks=unique_evidence
        )
    
    def _filter_low_quality(self, edges: List[GraphEdge]) -> List[GraphEdge]:
        """Filter out low-quality edges.
        
        Args:
            edges: List of GraphEdge objects
            
        Returns:
            Filtered list of edges
        """
        filtered_edges = []
        removed_count = 0
        
        for edge in edges:
            # Check confidence threshold
            if edge.confidence < self.min_confidence:
                removed_count += 1
                if self.debug:
                    print(f"    Removed low confidence: {edge.source} -> {edge.target} ({edge.confidence:.2f})")
                continue
            
            # Check evidence blocks
            if not edge.evidence_blocks or len(edge.evidence_blocks) == 0:
                removed_count += 1
                if self.debug:
                    print(f"    Removed no evidence: {edge.source} -> {edge.target}")
                continue
            
            filtered_edges.append(edge)
        
        if removed_count > 0 and self.debug:
            print(f"    Removed {removed_count} low-quality edges")
        
        return filtered_edges
    
    def _resolve_conflicts(self, edges: List[GraphEdge]) -> List[GraphEdge]:
        """Resolve conflicting edges between same node pair.
        
        Args:
            edges: List of GraphEdge objects
            
        Returns:
            List with conflicts resolved
        """
        # Group edges by (source, target) pair
        pair_groups = defaultdict(list)
        
        for edge in edges:
            key = (edge.source, edge.target)
            pair_groups[key].append(edge)
        
        resolved_edges = []
        conflict_count = 0
        
        for key, group in pair_groups.items():
            if len(group) == 1:
                resolved_edges.append(group[0])
            else:
                # Check for conflicts
                if self._has_conflict(group):
                    # Keep edge with higher priority/confidence
                    best = self._select_best_edge(group)
                    resolved_edges.append(best)
                    conflict_count += len(group) - 1
                    
                    if self.debug:
                        relations = [e.relation_type for e in group]
                        print(f"    Resolved conflict {key}: {relations} -> {best.relation_type}")
                else:
                    # No conflict, keep all
                    resolved_edges.extend(group)
        
        if conflict_count > 0 and self.debug:
            print(f"    Resolved {conflict_count} conflicting edges")
        
        return resolved_edges
    
    def _has_conflict(self, edges: List[GraphEdge]) -> bool:
        """Check if edge group has conflicting relation types.
        
        Args:
            edges: List of GraphEdge objects between same nodes
            
        Returns:
            True if conflicts detected
        """
        # Define conflicting pairs
        conflicts = [
            ("CAUSES", "CONTRASTS_WITH"),
            ("DEFINES", "CONTRASTS_WITH"),
            ("PART_OF", "CONTRASTS_WITH")
        ]
        
        relation_types = {e.relation_type for e in edges}
        
        for rel_a, rel_b in conflicts:
            if rel_a in relation_types and rel_b in relation_types:
                return True
        
        return False
    
    def _select_best_edge(self, edges: List[GraphEdge]) -> GraphEdge:
        """Select the best edge from a group.
        
        Priority: relation_priority > confidence
        
        Args:
            edges: List of GraphEdge objects
            
        Returns:
            Best GraphEdge
        """
        def edge_score(edge: GraphEdge) -> Tuple[int, float]:
            priority = RELATION_PRIORITY.get(edge.relation_type, 0)
            return (priority, edge.confidence)
        
        return max(edges, key=edge_score)
