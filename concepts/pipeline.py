"""Main concept extraction pipeline."""

import logging
from typing import List, Dict, Any
from uuid import uuid4

from concepts.models import ConceptCandidate
from concepts.extractor import OllamaExtractor
from concepts.prompts import build_extraction_prompt
from concepts.parser import parse_llm_output
from concepts.filters import filter_concepts

logger = logging.getLogger(__name__)


class ConceptExtractionPipeline:
    """Main pipeline for extracting concepts from semantic blocks."""
    
    def __init__(
        self,
        model: str = "llama3.1:8b",
        min_confidence: float = 0.5,
        ollama_url: str = "http://localhost:11434"
    ):
        """Initialize the extraction pipeline.
        
        Args:
            model: Ollama model to use
            min_confidence: Minimum confidence threshold
            ollama_url: Ollama API URL
        """
        self.extractor = OllamaExtractor(model=model, base_url=ollama_url)
        self.min_confidence = min_confidence
        self.stats = {
            "blocks_processed": 0,
            "blocks_failed": 0,
            "concepts_extracted": 0,
            "concepts_filtered": 0
        }
    
    def check_ollama(self) -> bool:
        """Check if Ollama is running.
        
        Returns:
            True if Ollama is accessible
        """
        return self.extractor.check_connection()
    
    def extract_from_block(
        self,
        block: Dict[str, Any]
    ) -> List[ConceptCandidate]:
        """Extract concepts from a single semantic block.
        
        Args:
            block: Semantic block dictionary
            
        Returns:
            List of concept candidates
        """
        block_id = block.get("block_id", "unknown")
        block_text = block.get("text", "")
        heading_path = block.get("heading_path", [])
        
        if not block_text or len(block_text.strip()) < 20:
            logger.debug(f"Skipping block {block_id} - too short")
            return []
        
        try:
            # Build prompt
            prompt = build_extraction_prompt(block_text, heading_path)
            
            # Query LLM
            logger.debug(f"Extracting concepts from block {block_id}")
            raw_output = self.extractor.query(prompt)
            
            if not raw_output:
                logger.warning(f"No output from LLM for block {block_id}")
                self.stats["blocks_failed"] += 1
                return []
            
            # Parse output
            concept_dicts = parse_llm_output(raw_output)
            
            if not concept_dicts:
                logger.debug(f"No concepts parsed from block {block_id}")
                return []
            
            # Filter concepts
            filtered_dicts = filter_concepts(concept_dicts, self.min_confidence)
            
            # Convert to ConceptCandidate objects
            concepts = []
            for concept_dict in filtered_dicts:
                concept = self._create_concept_candidate(
                    concept_dict,
                    block
                )
                concepts.append(concept)
            
            self.stats["blocks_processed"] += 1
            self.stats["concepts_extracted"] += len(concept_dicts)
            self.stats["concepts_filtered"] += len(concepts)
            
            logger.info(
                f"Block {block_id}: extracted {len(concept_dicts)} -> "
                f"filtered to {len(concepts)} concepts"
            )
            
            return concepts
            
        except Exception as e:
            logger.error(f"Failed to extract from block {block_id}: {e}")
            self.stats["blocks_failed"] += 1
            return []
    
    def _create_concept_candidate(
        self,
        concept_dict: Dict[str, Any],
        source_block: Dict[str, Any]
    ) -> ConceptCandidate:
        """Create ConceptCandidate from dict and source block.
        
        Args:
            concept_dict: Parsed concept dictionary
            source_block: Source semantic block
            
        Returns:
            ConceptCandidate instance
        """
        return ConceptCandidate(
            concept_id=uuid4().hex[:12],
            name=concept_dict["name"].strip(),
            type=concept_dict.get("type", "core_concept"),
            description=concept_dict.get("description", "").strip(),
            source_block_id=source_block.get("block_id", "unknown"),
            heading_path=source_block.get("heading_path", []),
            confidence=concept_dict.get("confidence", 0.6)
        )
    
    def extract_from_blocks(
        self,
        blocks: List[Dict[str, Any]],
        max_blocks: int = None
    ) -> List[ConceptCandidate]:
        """Extract concepts from multiple semantic blocks.
        
        Args:
            blocks: List of semantic block dictionaries
            max_blocks: Maximum number of blocks to process (for testing)
            
        Returns:
            List of all concept candidates
        """
        logger.info(f"Starting concept extraction from {len(blocks)} blocks")
        
        # Reset stats
        self.stats = {
            "blocks_processed": 0,
            "blocks_failed": 0,
            "concepts_extracted": 0,
            "concepts_filtered": 0
        }
        
        all_concepts = []
        blocks_to_process = blocks[:max_blocks] if max_blocks else blocks
        
        for i, block in enumerate(blocks_to_process, 1):
            logger.info(f"\n[{i}/{len(blocks_to_process)}] Processing block...")
            
            concepts = self.extract_from_block(block)
            all_concepts.extend(concepts)
        
        # Log final stats
        logger.info("\n" + "="*70)
        logger.info("EXTRACTION COMPLETE")
        logger.info("="*70)
        logger.info(f"Blocks processed: {self.stats['blocks_processed']}")
        logger.info(f"Blocks failed: {self.stats['blocks_failed']}")
        logger.info(f"Concepts extracted (raw): {self.stats['concepts_extracted']}")
        logger.info(f"Concepts filtered (final): {self.stats['concepts_filtered']}")
        
        return all_concepts
    
    def get_stats(self) -> Dict[str, int]:
        """Get extraction statistics.
        
        Returns:
            Statistics dictionary
        """
        return self.stats.copy()
