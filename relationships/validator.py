"""Validator for concept edges."""

from typing import List, Dict, Set
from relationships.models import ConceptEdge, VALID_RELATION_TYPES


class EdgeValidator:
    """Validates and deduplicates concept edges."""
    
    def __init__(self, canonical_concepts: List[Dict], debug: bool = False):
        """Initialize validator.
        
        Args:
            canonical_concepts: List of canonical concept dicts
            debug: If True, print validation details
        """
        self.canonical_concepts = canonical_concepts
        self.debug = debug
        
        # Build concept ID and name sets
        self._build_concept_sets()
    
    def _build_concept_sets(self):
        """Build sets of valid concept IDs and names."""
        self.valid_concept_ids = set()
        self.valid_concept_names = set()
        self.name_to_id = {}
        
        for concept in self.canonical_concepts:
            concept_id = concept["canonical_id"]
            canonical_name = concept["canonical_name"]
            
            self.valid_concept_ids.add(concept_id)
            self.valid_concept_names.add(canonical_name.lower())
            self.name_to_id[canonical_name.lower()] = concept_id
            
            # Add aliases
            for alias in concept.get("aliases", []):
                self.valid_concept_names.add(alias.lower())
                self.name_to_id[alias.lower()] = concept_id
    
    def validate_edge(self, edge: ConceptEdge) -> bool:
        """Validate a single edge.
        
        Args:
            edge: ConceptEdge to validate
            
        Returns:
            True if edge is valid, False otherwise
        """
        # Check source and target exist
        if edge.source_concept_id not in self.valid_concept_ids:
            if self.debug:
                print(f"  ⚠️  Invalid source ID: {edge.source_concept_id}")
            return False
        
        if edge.target_concept_id not in self.valid_concept_ids:
            if self.debug:
                print(f"  ⚠️  Invalid target ID: {edge.target_concept_id}")
            return False
        
        # Check for self-loops
        if edge.source_concept_id == edge.target_concept_id:
            if self.debug:
                print(f"  ⚠️  Self-loop: {edge.source_concept_id}")
            return False
        
        # Check relation type
        if edge.relation_type not in VALID_RELATION_TYPES:
            if self.debug:
                print(f"  ⚠️  Invalid relation type: {edge.relation_type}")
            return False
        
        # Check confidence range
        if not (0.0 <= edge.confidence <= 1.0):
            if self.debug:
                print(f"  ⚠️  Confidence out of range: {edge.confidence}")
            return False
        
        return True
    
    def resolve_concept_name(self, name: str) -> str:
        """Resolve a concept name to its canonical ID.
        
        Args:
            name: Concept name (canonical or alias)
            
        Returns:
            Canonical concept ID, or empty string if not found
        """
        return self.name_to_id.get(name.lower(), "")
    
    def deduplicate_edges(self, edges: List[ConceptEdge]) -> List[ConceptEdge]:
        """Deduplicate edges by merging duplicates.
        
        Edges with same (source, target, relation_type) are merged:
        - Confidence is averaged
        - Evidence blocks are combined (not stored in ConceptEdge)
        
        Args:
            edges: List of ConceptEdge objects
            
        Returns:
            Deduplicated list of ConceptEdge objects
        """
        # Group edges by (source, target, relation_type)
        edge_groups = {}
        
        for edge in edges:
            key = (edge.source_concept_id, edge.target_concept_id, edge.relation_type)
            
            if key not in edge_groups:
                edge_groups[key] = []
            edge_groups[key].append(edge)
        
        # Merge duplicates
        deduplicated = []
        
        for key, group in edge_groups.items():
            if len(group) == 1:
                deduplicated.append(group[0])
            else:
                # Merge multiple edges
                merged = self._merge_edges(group)
                deduplicated.append(merged)
        
        return deduplicated
    
    def _merge_edges(self, edges: List[ConceptEdge]) -> ConceptEdge:
        """Merge multiple edges with same source, target, and relation type.
        
        Args:
            edges: List of ConceptEdge objects to merge
            
        Returns:
            Single merged ConceptEdge
        """
        # Use first edge as template
        first = edges[0]
        
        # Average confidences
        avg_confidence = sum(e.confidence for e in edges) / len(edges)
        
        # Collect evidence blocks (use the first one for the edge)
        # In a full implementation, you might want to track all evidence blocks
        evidence_blocks = [e.evidence_block_id for e in edges]
        
        return ConceptEdge(
            edge_id=first.edge_id,
            source_concept_id=first.source_concept_id,
            target_concept_id=first.target_concept_id,
            relation_type=first.relation_type,
            evidence_block_id=first.evidence_block_id,  # Keep first
            confidence=round(avg_confidence, 2)
        )
    
    def print_validation_stats(self, initial_count: int, valid_count: int, 
                              final_count: int):
        """Print validation statistics.
        
        Args:
            initial_count: Number of edges before validation
            valid_count: Number of edges that passed validation
            final_count: Number of edges after deduplication
        """
        print(f"\n✅ Edge Validation Statistics")
        print(f"=" * 50)
        print(f"Initial edges: {initial_count}")
        print(f"Valid edges: {valid_count}")
        print(f"Final edges (after dedup): {final_count}")
        
        if initial_count > 0:
            valid_rate = (valid_count / initial_count) * 100
            print(f"Validation rate: {valid_rate:.1f}%")
        
        if valid_count > 0 and final_count < valid_count:
            duplicates = valid_count - final_count
            dedup_rate = (duplicates / valid_count) * 100
            print(f"Duplicates removed: {duplicates} ({dedup_rate:.1f}%)")
