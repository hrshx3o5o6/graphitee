"""Phase 3: Concept Extraction CLI

Extracts concept candidates from semantic blocks using local LLM (Ollama).

Usage:
    python concept_extractor.py <doc_id>
    python concept_extractor.py <doc_id> --debug
    python concept_extractor.py --all
    python concept_extractor.py --all --max-blocks 10
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

from concepts.pipeline import ConceptExtractionPipeline
from concepts.models import ConceptCandidate


def setup_logging(debug: bool = False) -> None:
    """Setup logging configuration.
    
    Args:
        debug: Enable debug logging
    """
    level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_semantic_blocks(doc_id: str, blocks_dir: str = "data/semantic_blocks") -> List[Dict[str, Any]]:
    """Load semantic blocks from JSON file.
    
    Args:
        doc_id: Document ID
        blocks_dir: Directory containing semantic block files
        
    Returns:
        List of semantic block dictionaries
    """
    blocks_path = Path(blocks_dir) / f"{doc_id}.json"
    
    if not blocks_path.exists():
        raise FileNotFoundError(f"Semantic blocks not found: {blocks_path}")
    
    with open(blocks_path, "r", encoding="utf-8") as f:
        blocks = json.load(f)
    
    return blocks


def save_concepts(
    concepts: List[ConceptCandidate],
    doc_id: str,
    output_dir: str = "data/concepts"
) -> None:
    """Save concept candidates to JSON file.
    
    Args:
        concepts: List of concept candidates
        doc_id: Document ID
        output_dir: Output directory
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    output_file = output_path / f"{doc_id}_concepts.json"
    
    # Convert to dicts
    concepts_data = [c.to_dict() for c in concepts]
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(concepts_data, f, indent=2, ensure_ascii=False)
    
    logging.info(f"Saved {len(concepts)} concepts to {output_file}")


def print_concept_summary(concepts: List[ConceptCandidate], max_display: int = 10) -> None:
    """Print summary of extracted concepts.
    
    Args:
        concepts: List of concepts
        max_display: Maximum concepts to display
    """
    if not concepts:
        print("\nNo concepts extracted.")
        return
    
    # Calculate stats
    type_dist = {}
    total_confidence = 0.0
    
    for concept in concepts:
        type_dist[concept.type] = type_dist.get(concept.type, 0) + 1
        total_confidence += concept.confidence
    
    avg_confidence = total_confidence / len(concepts) if concepts else 0.0
    
    print(f"\n{'='*70}")
    print("CONCEPT EXTRACTION SUMMARY")
    print(f"{'='*70}")
    print(f"Total concepts: {len(concepts)}")
    print(f"Average confidence: {avg_confidence:.2f}")
    print(f"\nConcept type distribution:")
    for concept_type, count in sorted(type_dist.items(), key=lambda x: -x[1]):
        percentage = (count / len(concepts)) * 100
        print(f"  {concept_type}: {count} ({percentage:.1f}%)")
    
    print(f"\nTop {min(max_display, len(concepts))} concepts:")
    print(f"{'-'*70}")
    
    # Sort by confidence
    sorted_concepts = sorted(concepts, key=lambda c: c.confidence, reverse=True)
    
    for i, concept in enumerate(sorted_concepts[:max_display], 1):
        path_str = " > ".join(concept.heading_path[-2:]) if len(concept.heading_path) > 1 else (concept.heading_path[0] if concept.heading_path else "")
        
        print(f"\n[{i}] {concept.name}")
        print(f"    Type: {concept.type}")
        print(f"    Confidence: {concept.confidence:.2f}")
        print(f"    Context: {path_str}")
        print(f"    Description: {concept.description[:80]}...")


def process_document(
    doc_id: str,
    pipeline: ConceptExtractionPipeline,
    max_blocks: int = None,
    debug: bool = False
) -> None:
    """Process a single document to extract concepts.
    
    Args:
        doc_id: Document ID
        pipeline: Extraction pipeline
        max_blocks: Maximum blocks to process
        debug: Print detailed output
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Load semantic blocks
        logger.info(f"Loading semantic blocks for: {doc_id}")
        blocks = load_semantic_blocks(doc_id)
        logger.info(f"Loaded {len(blocks)} semantic blocks")
        
        if max_blocks:
            logger.info(f"Limiting to first {max_blocks} blocks for testing")
        
        # Extract concepts
        concepts = pipeline.extract_from_blocks(blocks, max_blocks=max_blocks)
        
        if not concepts:
            logger.warning("No concepts extracted!")
            return
        
        # Save concepts
        save_concepts(concepts, doc_id)
        
        # Print summary
        print_concept_summary(concepts, max_display=20 if debug else 10)
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        logger.info("Run Phase 2 (semantic_builder.py) first to create semantic blocks")
    except Exception as e:
        logger.error(f"Failed to process document {doc_id}: {e}", exc_info=True)


def list_available_documents(blocks_dir: str = "data/semantic_blocks") -> List[str]:
    """List available semantic block files.
    
    Args:
        blocks_dir: Directory containing semantic blocks
        
    Returns:
        List of document IDs
    """
    blocks_path = Path(blocks_dir)
    
    if not blocks_path.exists():
        return []
    
    doc_ids = [
        f.stem for f in blocks_path.glob("*.json")
    ]
    
    return doc_ids


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 3: Extract concepts from semantic blocks using Ollama"
    )
    
    parser.add_argument(
        "doc_id",
        nargs="?",
        help="Document ID to process"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all documents"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available documents"
    )
    
    parser.add_argument(
        "--model",
        default="llama3.1:8b",
        help="Ollama model to use (default: llama3.1:8b)"
    )
    
    parser.add_argument(
        "--max-blocks",
        type=int,
        help="Maximum number of blocks to process (for testing)"
    )
    
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.5,
        help="Minimum confidence threshold (default: 0.5)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    # List documents if requested
    if args.list or (not args.doc_id and not args.all):
        doc_ids = list_available_documents()
        
        if not doc_ids:
            print("No semantic blocks found.")
            print("Run Phase 2 first: python semantic_builder.py <doc_id>")
            return
        
        print(f"\nAvailable documents with semantic blocks ({len(doc_ids)}):")
        for doc_id in doc_ids:
            print(f"  - {doc_id}")
        
        print("\nUsage:")
        print("  python concept_extractor.py <doc_id> [--debug]")
        print("  python concept_extractor.py --all [--max-blocks 10]")
        return
    
    try:
        # Initialize pipeline
        logger.info(f"Initializing concept extraction pipeline with model: {args.model}")
        pipeline = ConceptExtractionPipeline(
            model=args.model,
            min_confidence=args.min_confidence
        )
        
        # Check Ollama connection
        logger.info("Checking Ollama connection...")
        if not pipeline.check_ollama():
            logger.error(
                "Cannot connect to Ollama. Make sure it's running:\n"
                "  ollama serve\n"
                "  ollama pull llama3.1:8b"
            )
            sys.exit(1)
        
        logger.info("✓ Ollama is running")
        
        # Process documents
        if args.all:
            doc_ids = list_available_documents()
            logger.info(f"Processing {len(doc_ids)} documents")
            
            for i, doc_id in enumerate(doc_ids, 1):
                logger.info(f"\n{'='*70}")
                logger.info(f"[{i}/{len(doc_ids)}] Processing: {doc_id}")
                logger.info(f"{'='*70}")
                process_document(doc_id, pipeline, args.max_blocks, args.debug)
        
        elif args.doc_id:
            process_document(args.doc_id, pipeline, args.max_blocks, args.debug)
        
        logger.info("\nPhase 3 complete!")
        
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
