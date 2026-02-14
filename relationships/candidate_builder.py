"""Build candidate concept pairs for relationship extraction."""

from itertools import combinations
from typing import List, Dict, Set
from relationships.models import RelationshipCandidate, BlockConceptMapping


class CandidateBuilder:
    """Maps concepts to blocks and generates candidate pairs."""
    
    def __init__(self, canonical_concepts: List[dict], semantic_blocks: List[dict]):
        """Initialize with canonical concepts and semantic blocks.
        
        Args:
            canonical_concepts: List of canonical concept dicts from Phase 4
            semantic_blocks: List of semantic block dicts from Phase 2
        """
        self.canonical_concepts = canonical_concepts
        self.semantic_blocks = semantic_blocks
        
        # Build lookup structures
        self._build_concept_lookup()
        
    def _build_concept_lookup(self):
        """Build lookup structures for efficient concept matching."""
        # Map concept names (canonical + aliases) to concept IDs
        self.name_to_concept = {}
        
        for concept in self.canonical_concepts:
            concept_id = concept["canonical_id"]
            canonical_name = concept["canonical_name"].lower()
            
            # Add canonical name
            self.name_to_concept[canonical_name] = concept_id
            
            # Add all aliases
            for alias in concept.get("aliases", []):
                self.name_to_concept[alias.lower()] = concept_id
    
    def map_concepts_to_blocks(self) -> List[BlockConceptMapping]:
        """Map each block to concepts that appear in it.
        
        Returns:
            List of BlockConceptMapping objects
        """
        mappings = []
        
        for block in self.semantic_blocks:
            block_id = block["block_id"]
            block_text = block["text"].lower()
            
            # Find all concepts that appear in this block
            found_concepts = set()
            found_names = []
            
            for name, concept_id in self.name_to_concept.items():
                if name in block_text:
                    if concept_id not in found_concepts:
                        found_concepts.add(concept_id)
                        # Store the actual name for display
                        found_names.append(self._get_canonical_name(concept_id))
            
            if len(found_concepts) >= 2:  # Only map blocks with 2+ concepts
                mappings.append(BlockConceptMapping(
                    block_id=block_id,
                    concept_ids=list(found_concepts),
                    concept_names=found_names
                ))
        
        return mappings
    
    def generate_candidate_pairs(self, mappings: List[BlockConceptMapping]) -> List[RelationshipCandidate]:
        """Generate candidate concept pairs from block-concept mappings.
        
        Args:
            mappings: List of BlockConceptMapping
            
        Returns:
            List of RelationshipCandidate objects
        """
        candidates = []
        
        for mapping in mappings:
            # Get the block data
            block = self._get_block(mapping.block_id)
            if not block:
                continue
            
            # Generate all pairs of concepts in this block
            concept_pairs = list(combinations(range(len(mapping.concept_ids)), 2))
            
            for i, j in concept_pairs:
                concept_a_id = mapping.concept_ids[i]
                concept_a_name = mapping.concept_names[i]
                concept_b_id = mapping.concept_ids[j]
                concept_b_name = mapping.concept_names[j]
                
                candidates.append(RelationshipCandidate(
                    concept_a_id=concept_a_id,
                    concept_a_name=concept_a_name,
                    concept_b_id=concept_b_id,
                    concept_b_name=concept_b_name,
                    block_id=mapping.block_id,
                    block_text=block["text"]
                ))
        
        return candidates
    
    def _get_canonical_name(self, concept_id: str) -> str:
        """Get canonical name for a concept ID."""
        for concept in self.canonical_concepts:
            if concept["canonical_id"] == concept_id:
                return concept["canonical_name"]
        return ""
    
    def _get_block(self, block_id: str) -> dict:
        """Get block data by ID."""
        for block in self.semantic_blocks:
            if block["block_id"] == block_id:
                return block
        return None
    
    def print_statistics(self, mappings: List[BlockConceptMapping], 
                        candidates: List[RelationshipCandidate]):
        """Print candidate generation statistics."""
        print(f"\n📊 Candidate Generation Statistics")
        print(f"=" * 50)
        print(f"Total semantic blocks: {len(self.semantic_blocks)}")
        print(f"Blocks with 2+ concepts: {len(mappings)}")
        print(f"Total candidate pairs: {len(candidates)}")
        
        if mappings:
            concepts_per_block = [len(m.concept_ids) for m in mappings]
            print(f"Avg concepts per block: {sum(concepts_per_block) / len(concepts_per_block):.1f}")
            print(f"Max concepts in block: {max(concepts_per_block)}")
