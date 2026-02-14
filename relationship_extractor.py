"""Phase 5: Relationship Extraction CLI

Extracts relationships between canonical concepts to build knowledge graph edges.
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from relationships.pipeline import RelationshipPipeline


def load_json(filepath: Path) -> Optional[dict | list]:
    """Load JSON file safely.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Parsed JSON data, or None if file doesn't exist or is invalid
    """
    if not filepath.exists():
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing {filepath}: {e}")
        return None


def save_relationships(edges: List, output_path: Path):
    """Save relationships to JSON file.
    
    Args:
        edges: List of ConceptEdge objects
        output_path: Path to save JSON file
    """
    # Convert edges to dicts
    edges_data = [edge.to_dict() for edge in edges]
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(edges_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved {len(edges_data)} relationships to: {output_path}")


def list_available_data():
    """List available documents with both semantic blocks and canonical concepts."""
    data_dir = Path("data")
    
    semantic_dir = data_dir / "semantic_blocks"
    canonical_dir = data_dir / "canonical"
    
    if not semantic_dir.exists() or not canonical_dir.exists():
        print("❌ Data directories not found. Run Phases 2 and 4 first.")
        return
    
    # Find documents with both semantic blocks and canonical concepts
    semantic_files = {f.stem: f for f in semantic_dir.glob("*.json")}
    canonical_files = {f.stem.replace("_canonical", ""): f for f in canonical_dir.glob("*_canonical.json")}
    
    # Find intersection
    available_docs = set(semantic_files.keys()) & set(canonical_files.keys())
    
    if not available_docs:
        print("❌ No documents ready for Phase 5.")
        print("   Documents need both semantic blocks (Phase 2) and canonical concepts (Phase 4).")
        return
    
    print("\n📂 Available documents for relationship extraction:")
    print("=" * 70)
    
    for doc_id in sorted(available_docs):
        # Load to get document info
        semantic_data = load_json(semantic_files[doc_id])
        canonical_data = load_json(canonical_files[doc_id])
        
        if semantic_data and canonical_data:
            num_blocks = len(semantic_data)
            num_concepts = len(canonical_data)
            print(f"\n📄 {doc_id}")
            print(f"   Semantic blocks: {num_blocks}")
            print(f"   Canonical concepts: {num_concepts}")


def extract_relationships_for_doc(doc_id: str, model: str = "llama3.1:8b", 
                                  debug: bool = False):
    """Extract relationships for a single document.
    
    Args:
        doc_id: Document identifier
        model: Ollama model name
        debug: If True, print detailed progress
    """
    data_dir = Path("data")
    
    # Load semantic blocks
    semantic_path = data_dir / "semantic_blocks" / f"{doc_id}.json"
    if not semantic_path.exists():
        print(f"❌ Semantic blocks not found: {semantic_path}")
        print(f"   Run Phase 2 first: python semantic_builder.py {doc_id}")
        return
    
    semantic_blocks = load_json(semantic_path)
    if not semantic_blocks:
        print(f"❌ Failed to load semantic blocks from {semantic_path}")
        return
    
    # Load canonical concepts
    canonical_path = data_dir / "canonical" / f"{doc_id}_canonical.json"
    if not canonical_path.exists():
        print(f"❌ Canonical concepts not found: {canonical_path}")
        print(f"   Run Phase 4 first: python concept_normalizer.py {doc_id}")
        return
    
    canonical_concepts = load_json(canonical_path)
    if not canonical_concepts:
        print(f"❌ Failed to load canonical concepts from {canonical_path}")
        return
    
    print(f"\n📄 Processing document: {doc_id}")
    print(f"   Semantic blocks: {len(semantic_blocks)}")
    print(f"   Canonical concepts: {len(canonical_concepts)}")
    
    # Run extraction pipeline
    try:
        pipeline = RelationshipPipeline(
            canonical_concepts=canonical_concepts,
            semantic_blocks=semantic_blocks,
            model=model,
            debug=debug
        )
        
        edges = pipeline.extract_relationships()
        
        # Save results
        output_path = data_dir / "relationships" / f"{doc_id}_relationships.json"
        save_relationships(edges, output_path)
        
        print(f"\n✅ Relationship extraction complete!")
        print(f"   Total edges: {len(edges)}")
        
    except Exception as e:
        print(f"\n❌ Extraction failed: {e}")
        if debug:
            import traceback
            traceback.print_exc()


def extract_all_relationships(model: str = "llama3.1:8b", debug: bool = False):
    """Extract relationships for all available documents.
    
    Args:
        model: Ollama model name
        debug: If True, print detailed progress
    """
    data_dir = Path("data")
    semantic_dir = data_dir / "semantic_blocks"
    canonical_dir = data_dir / "canonical"
    
    if not semantic_dir.exists() or not canonical_dir.exists():
        print("❌ Data directories not found. Run Phases 2 and 4 first.")
        return
    
    # Find documents with both files
    semantic_files = {f.stem: f for f in semantic_dir.glob("*.json")}
    canonical_files = {f.stem.replace("_canonical", ""): f for f in canonical_dir.glob("*_canonical.json")}
    
    available_docs = set(semantic_files.keys()) & set(canonical_files.keys())
    
    if not available_docs:
        print("❌ No documents ready for processing.")
        return
    
    print(f"\n🚀 Processing {len(available_docs)} documents...")
    
    for i, doc_id in enumerate(sorted(available_docs), 1):
        print(f"\n{'=' * 70}")
        print(f"Document {i}/{len(available_docs)}: {doc_id}")
        print(f"{'=' * 70}")
        
        extract_relationships_for_doc(doc_id, model=model, debug=debug)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 5: Extract relationships between canonical concepts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available documents
  python relationship_extractor.py --list
  
  # Extract relationships for one document
  python relationship_extractor.py abc123 --debug
  
  # Extract for all documents
  python relationship_extractor.py --all
  
  # Use different model
  python relationship_extractor.py abc123 --model llama3.2:latest
        """
    )
    
    parser.add_argument(
        "doc_id",
        nargs="?",
        help="Document ID to process"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available documents"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all available documents"
    )
    
    parser.add_argument(
        "--model",
        default="llama3.1:8b",
        help="Ollama model to use (default: llama3.1:8b)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print detailed progress information"
    )
    
    args = parser.parse_args()
    
    # Handle list command
    if args.list:
        list_available_data()
        return
    
    # Handle all command
    if args.all:
        extract_all_relationships(model=args.model, debug=args.debug)
        return
    
    # Handle single document
    if args.doc_id:
        extract_relationships_for_doc(args.doc_id, model=args.model, debug=args.debug)
        return
    
    # No command provided
    parser.print_help()


if __name__ == "__main__":
    main()
