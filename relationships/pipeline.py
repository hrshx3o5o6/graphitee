"""Main pipeline for relationship extraction."""

import uuid
from typing import List, Dict
from relationships.models import ConceptEdge, BlockConceptMapping
from relationships.candidate_builder import CandidateBuilder
from relationships.extractor import OllamaRelationshipExtractor
from relationships.parser import RelationshipParser
from relationships.validator import EdgeValidator


class RelationshipPipeline:
    """Orchestrates relationship extraction from canonical concepts and semantic blocks."""
    
    def __init__(self, canonical_concepts: List[Dict], semantic_blocks: List[Dict],
                 model: str = "llama3.1:8b", debug: bool = False):
        """Initialize pipeline.
        
        Args:
            canonical_concepts: List of canonical concept dicts from Phase 4
            semantic_blocks: List of semantic block dicts from Phase 2
            model: Ollama model name
            debug: If True, print detailed progress information
        """
        self.canonical_concepts = canonical_concepts
        self.semantic_blocks = semantic_blocks
        self.model = model
        self.debug = debug
        
        # Initialize components
        self.candidate_builder = CandidateBuilder(canonical_concepts, semantic_blocks)
        self.extractor = OllamaRelationshipExtractor(model=model)
        self.parser = RelationshipParser(debug=debug)
        self.validator = EdgeValidator(canonical_concepts, debug=debug)
    
    def extract_relationships(self) -> List[ConceptEdge]:
        """Run the full relationship extraction pipeline.
        
        Returns:
            List of validated and deduplicated ConceptEdge objects
        """
        print("🚀 Starting Relationship Extraction Pipeline")
        print("=" * 70)
        
        # Step 1: Check Ollama connection
        if not self._check_ollama():
            raise Exception("Ollama is not accessible. Please start Ollama and try again.")
        
        # Step 2: Map concepts to blocks
        print("\n📍 Step 1: Mapping concepts to blocks...")
        mappings = self.candidate_builder.map_concepts_to_blocks()
        print(f"   Found {len(mappings)} blocks with 2+ concepts")
        
        # Step 3: Generate candidate pairs
        print("\n📍 Step 2: Generating candidate pairs...")
        candidates = self.candidate_builder.generate_candidate_pairs(mappings)
        print(f"   Generated {len(candidates)} candidate pairs")
        
        if self.debug:
            self.candidate_builder.print_statistics(mappings, candidates)
        
        # Step 4: Extract relationships using block-level processing
        print("\n📍 Step 3: Extracting relationships with LLM...")
        edges = self._extract_from_blocks(mappings)
        print(f"   Extracted {len(edges)} raw edges")
        
        # Step 5: Validate edges
        print("\n📍 Step 4: Validating edges...")
        valid_edges = [edge for edge in edges if self.validator.validate_edge(edge)]
        print(f"   {len(valid_edges)} edges passed validation")
        
        # Step 6: Deduplicate edges
        print("\n📍 Step 5: Deduplicating edges...")
        final_edges = self.validator.deduplicate_edges(valid_edges)
        print(f"   {len(final_edges)} unique edges after deduplication")
        
        # Print final statistics
        if self.debug:
            self.validator.print_validation_stats(len(edges), len(valid_edges), 
                                                  len(final_edges))
            self._print_edge_summary(final_edges)
        
        return final_edges
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is running and model is available.
        
        Returns:
            True if Ollama is ready, False otherwise
        """
        print("🔍 Checking Ollama connection...")
        
        if not self.extractor.test_connection():
            print("   ❌ Ollama is not running")
            return False
        
        print("   ✅ Ollama is running")
        
        if not self.extractor.check_model():
            print(f"   ⚠️  Model '{self.model}' not found")
            print(f"   Run: ollama pull {self.model}")
            return False
        
        print(f"   ✅ Model '{self.model}' is available")
        return True
    
    def _extract_from_blocks(self, mappings: List[BlockConceptMapping]) -> List[ConceptEdge]:
        """Extract relationships by processing each block once.
        
        This is more efficient than processing each candidate pair separately.
        
        Args:
            mappings: List of BlockConceptMapping objects
            
        Returns:
            List of ConceptEdge objects
        """
        edges = []
        total_blocks = len(mappings)
        
        for i, mapping in enumerate(mappings, 1):
            if self.debug or (i % 10 == 0):
                print(f"   Processing block {i}/{total_blocks}...")
            
            # Get block text
            block = self._get_block(mapping.block_id)
            if not block:
                continue
            
            # Extract relationships from this block
            block_edges = self._extract_from_single_block(
                block["block_id"],
                block["text"],
                mapping.concept_ids,
                mapping.concept_names
            )
            
            edges.extend(block_edges)
            
            if self.debug and block_edges:
                print(f"      Found {len(block_edges)} relationships")
        
        return edges
    
    def _extract_from_single_block(self, block_id: str, block_text: str,
                                   concept_ids: List[str], 
                                   concept_names: List[str]) -> List[ConceptEdge]:
        """Extract relationships from a single block.
        
        Args:
            block_id: Block identifier
            block_text: Block text content
            concept_ids: List of concept IDs in the block
            concept_names: List of concept names in the block
            
        Returns:
            List of ConceptEdge objects
        """
        # Query LLM
        llm_response = self.extractor.extract_from_block(block_text, concept_names)
        if not llm_response:
            return []
        
        # Parse response
        relationships = self.parser.parse_llm_output(llm_response)
        if not relationships:
            return []
        
        # Convert parsed relationships to ConceptEdge objects
        edges = []
        for rel in relationships:
            # Resolve concept names to IDs
            source_id = self.validator.resolve_concept_name(rel["source"])
            target_id = self.validator.resolve_concept_name(rel["target"])
            
            if not source_id or not target_id:
                if self.debug:
                    print(f"      ⚠️  Could not resolve concepts: {rel['source']} -> {rel['target']}")
                continue
            
            # Create edge
            edge = ConceptEdge(
                edge_id=f"e_{uuid.uuid4().hex[:8]}",
                source_concept_id=source_id,
                target_concept_id=target_id,
                relation_type=rel["relation_type"],
                evidence_block_id=block_id,
                confidence=rel["confidence"]
            )
            
            edges.append(edge)
        
        return edges
    
    def _get_block(self, block_id: str) -> dict:
        """Get block data by ID."""
        for block in self.semantic_blocks:
            if block["block_id"] == block_id:
                return block
        return None
    
    def _print_edge_summary(self, edges: List[ConceptEdge]):
        """Print summary of extracted edges."""
        print(f"\n📊 Edge Summary")
        print(f"=" * 50)
        
        # Count by relation type
        relation_counts = {}
        for edge in edges:
            rel_type = edge.relation_type
            relation_counts[rel_type] = relation_counts.get(rel_type, 0) + 1
        
        print(f"\nRelationships by type:")
        for rel_type, count in sorted(relation_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {rel_type}: {count}")
        
        # Average confidence
        if edges:
            avg_confidence = sum(e.confidence for e in edges) / len(edges)
            print(f"\nAverage confidence: {avg_confidence:.2f}")
            
            # Confidence distribution
            high_conf = sum(1 for e in edges if e.confidence >= 0.8)
            med_conf = sum(1 for e in edges if 0.6 <= e.confidence < 0.8)
            low_conf = sum(1 for e in edges if e.confidence < 0.6)
            
            print(f"\nConfidence distribution:")
            print(f"  High (≥0.8): {high_conf}")
            print(f"  Medium (0.6-0.8): {med_conf}")
            print(f"  Low (<0.6): {low_conf}")
