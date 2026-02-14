"""Phase 4: Concept Normalization CLI

Normalizes concept candidates into canonical concepts by:
- Removing duplicates
- Clustering similar concepts
- Verifying with LLM
- Selecting canonical names

Usage:
    python concept_normalizer.py <doc_id>
    python concept_normalizer.py <doc_id> --debug
    python concept_normalizer.py --all
    python concept_normalizer.py <doc_id> --skip-verification
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

from normalization.pipeline import NormalizationPipeline
from normalization.canonicalizer import print_canonical_summary

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


def load_concept_candidates(doc_id: str, concepts_dir: str = "data/concepts") -> List[Dict[str, Any]]:
    """Load concept candidates from JSON file.
    
    Args:
        doc_id: Document ID
        concepts_dir: Directory containing concept files
        
    Returns:
        List of concept candidate dictionaries
    """
    concepts_path = Path(concepts_dir) / f"{doc_id}_concepts.json"
    
    if not concepts_path.exists():
        raise FileNotFoundError(f"Concept candidates not found: {concepts_path}")
    
    with open(concepts_path, "r", encoding="utf-8") as f:
        concepts = json.load(f)
    
    return concepts


def save_canonical_concepts(
    concepts: List,
    doc_id: str,
    output_dir: str = "data/canonical"
) -> None:
    """Save canonical concepts to JSON file.
    
    Args:
        concepts: List of canonical concepts
        doc_id: Document ID
        output_dir: Output directory
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    output_file = output_path / f"{doc_id}_canonical.json"
    
    # Convert to dicts
    concepts_data = [c.to_dict() for c in concepts]
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(concepts_data, f, indent=2, ensure_ascii=False)
    
    logging.info(f"Saved {len(concepts)} canonical concepts to {output_file}")


def process_document(
    doc_id: str,
    pipeline: NormalizationPipeline,
    skip_verification: bool = False,
    debug: bool = False
) -> None:
    """Process a single document to normalize concepts.
    
    Args:
        doc_id: Document ID
        pipeline: Normalization pipeline
        skip_verification: Skip LLM verification
        debug: Print detailed output
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Load concept candidates
        logger.info(f"Loading concept candidates for: {doc_id}")
        candidates = load_concept_candidates(doc_id)
        logger.info(f"Loaded {len(candidates)} concept candidates")
        
        if not candidates:
            logger.warning("No candidates to normalize")
            return
        
        # Normalize concepts
        canonical_concepts = pipeline.normalize(
            candidates,
            skip_verification=skip_verification
        )
        
        if not canonical_concepts:
            logger.warning("No canonical concepts created!")
            return
        
        # Save canonical concepts
        save_canonical_concepts(canonical_concepts, doc_id)
        
        # Print summary
        print_canonical_summary(canonical_concepts, max_display=30 if debug else 15)
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        logger.info("Run Phase 3 (concept_extractor.py) first to extract concepts")
    except Exception as e:
        logger.error(f"Failed to process document {doc_id}: {e}", exc_info=True)


def list_available_documents(concepts_dir: str = "data/concepts") -> List[str]:
    """List available concept candidate files.
    
    Args:
        concepts_dir: Directory containing concept files
        
    Returns:
        List of document IDs
    """
    concepts_path = Path(concepts_dir)
    
    if not concepts_path.exists():
        return []
    
    doc_ids = []
    for f in concepts_path.glob("*_concepts.json"):
        # Remove "_concepts" suffix
        doc_id = f.stem.replace("_concepts", "")
        doc_ids.append(doc_id)
    
    return doc_ids


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 4: Normalize concept candidates into canonical concepts"
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
        "--similarity-threshold",
        type=float,
        default=0.80,
        help="Minimum similarity for clustering (default: 0.80)"
    )
    
    parser.add_argument(
        "--skip-verification",
        action="store_true",
        help="Skip LLM verification (faster, less accurate)"
    )
    
    parser.add_argument(
        "--embedding-model",
        default="all-MiniLM-L6-v2",
        help="Sentence transformer model (default: all-MiniLM-L6-v2)"
    )
    
    parser.add_argument(
        "--llm-model",
        default="llama3.1:8b",
        help="Ollama model for verification (default: llama3.1:8b)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    # List documents if requested
    if args.list or (not args.doc_id and not args.all):
        doc_ids = list_available_documents()
        
        if not doc_ids:
            print("No concept candidates found.")
            print("Run Phase 3 first: python concept_extractor.py <doc_id>")
            return
        
        print(f"\nAvailable documents with concept candidates ({len(doc_ids)}):")
        for doc_id in doc_ids:
            print(f"  - {doc_id}")
        
        print("\nUsage:")
        print("  python concept_normalizer.py <doc_id> [--debug] [--skip-verification]")
        print("  python concept_normalizer.py --all")
        return
    
    try:
        # Initialize pipeline
        logger.info(f"Initializing normalization pipeline")
        logger.info(f"  Embedding model: {args.embedding_model}")
        logger.info(f"  Similarity threshold: {args.similarity_threshold}")
        logger.info(f"  LLM verification: {'disabled' if args.skip_verification else 'enabled'}")
        
        if not args.skip_verification:
            logger.info(f"  LLM model: {args.llm_model}")
            logger.info("  Note: Ollama must be running for verification")
        
        pipeline = NormalizationPipeline(
            embedding_model=args.embedding_model,
            similarity_threshold=args.similarity_threshold,
            verify_with_llm=not args.skip_verification,
            llm_model=args.llm_model
        )
        
        # Process documents
        if args.all:
            doc_ids = list_available_documents()
            logger.info(f"Processing {len(doc_ids)} documents")
            
            for i, doc_id in enumerate(doc_ids, 1):
                logger.info(f"\n{'='*70}")
                logger.info(f"[{i}/{len(doc_ids)}] Processing: {doc_id}")
                logger.info(f"{'='*70}")
                process_document(
                    doc_id,
                    pipeline,
                    skip_verification=args.skip_verification,
                    debug=args.debug
                )
        
        elif args.doc_id:
            process_document(
                args.doc_id,
                pipeline,
                skip_verification=args.skip_verification,
                debug=args.debug
            )
        
        logger.info("\nPhase 4 complete!")
        
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
