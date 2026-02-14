"""Phase 2: Semantic Block Builder CLI

Transforms Phase 1 documents into semantic blocks.

Usage:
    python semantic_builder.py <doc_id>
    python semantic_builder.py <doc_id> --debug
    python semantic_builder.py --all
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from storage.json_store import JSONStore
from semantic.builder import build_semantic_blocks, print_block_summary


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


def save_semantic_blocks(blocks: list, doc_id: str, output_dir: str = "data/semantic_blocks") -> None:
    """Save semantic blocks to JSON file.
    
    Args:
        blocks: List of semantic blocks
        doc_id: Document ID
        output_dir: Output directory
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    output_file = output_path / f"{doc_id}.json"
    
    # Convert blocks to dicts for JSON serialization
    blocks_data = [block.to_dict() for block in blocks]
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(blocks_data, f, indent=2, ensure_ascii=False)
    
    logging.info(f"Saved {len(blocks)} semantic blocks to {output_file}")


def process_document(doc_id: str, store: JSONStore, debug: bool = False) -> None:
    """Process a single document to create semantic blocks.
    
    Args:
        doc_id: Document ID to process
        store: JSON store instance
        debug: Print detailed output
    """
    logger = logging.getLogger(__name__)
    
    # Load document
    logger.info(f"Loading document: {doc_id}")
    document = store.load_document(doc_id)
    
    if not document:
        logger.error(f"Document not found: {doc_id}")
        return
    
    logger.info(f"Processing: {document.title}")
    logger.info(f"Sections: {len(document.sections)}")
    
    # Build semantic blocks
    blocks = build_semantic_blocks(document)
    
    # Save blocks
    save_semantic_blocks(blocks, doc_id)
    
    # Print summary
    if debug:
        print_block_summary(blocks, max_display=10)
    else:
        print_block_summary(blocks, max_display=3)


def process_all_documents(store: JSONStore, debug: bool = False) -> None:
    """Process all documents in storage.
    
    Args:
        store: JSON store instance
        debug: Print detailed output
    """
    logger = logging.getLogger(__name__)
    
    doc_ids = store.list_documents()
    
    if not doc_ids:
        logger.warning("No documents found in storage")
        return
    
    logger.info(f"Processing {len(doc_ids)} documents")
    
    for i, doc_id in enumerate(doc_ids, 1):
        logger.info(f"\n[{i}/{len(doc_ids)}] Processing {doc_id}")
        try:
            process_document(doc_id, store, debug=debug)
        except Exception as e:
            logger.error(f"Failed to process {doc_id}: {e}", exc_info=True)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 2: Transform documents into semantic blocks"
    )
    
    parser.add_argument(
        "doc_id",
        nargs="?",
        help="Document ID to process (omit to see available documents)"
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
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    # Initialize storage
    store = JSONStore()
    
    # List documents if requested
    if args.list or (not args.doc_id and not args.all):
        doc_ids = store.list_documents()
        if not doc_ids:
            print("No documents found. Run Phase 1 first to scrape articles.")
            return
        
        print(f"\nAvailable documents ({len(doc_ids)}):")
        for doc_id in doc_ids:
            doc = store.load_document(doc_id)
            if doc:
                print(f"  - {doc_id}: {doc.title}")
        print("\nUsage: python semantic_builder.py <doc_id> [--debug]")
        print("       python semantic_builder.py --all [--debug]")
        return
    
    try:
        if args.all:
            process_all_documents(store, debug=args.debug)
        elif args.doc_id:
            process_document(args.doc_id, store, debug=args.debug)
        
        logger.info("Phase 2 complete")
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
