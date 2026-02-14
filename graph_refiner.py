"""Phase 6: Graph Refinement & Final Assembly CLI

Refines and assembles the final knowledge graph from canonical concepts and relationships.
"""

import json
import argparse
from pathlib import Path
from typing import Optional, List, Dict
from graph.pipeline import GraphRefinementPipeline


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


def save_graph(graph, output_path: Path, viz_format: bool = False):
    """Save graph to JSON file.
    
    Args:
        graph: FinalGraph object
        output_path: Path to save JSON file
        viz_format: If True, save minimal visualization format
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get appropriate dict format
    if viz_format:
        data = graph.to_viz_dict()
        print(f"  Saving visualization format (minimal payload)")
    else:
        data = graph.to_dict()
        print(f"  Saving full format (with metadata)")
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved final graph to: {output_path}")


def list_available_data():
    """List available documents with both canonical concepts and relationships."""
    data_dir = Path("data")
    
    canonical_dir = data_dir / "canonical"
    relationships_dir = data_dir / "relationships"
    
    if not canonical_dir.exists() or not relationships_dir.exists():
        print("❌ Data directories not found. Run Phases 4 and 5 first.")
        return
    
    # Find documents with both files
    canonical_files = {f.stem.replace("_canonical", ""): f for f in canonical_dir.glob("*_canonical.json")}
    relationship_files = {f.stem.replace("_relationships", ""): f for f in relationships_dir.glob("*_relationships.json")}
    
    # Find intersection
    available_docs = set(canonical_files.keys()) & set(relationship_files.keys())
    
    if not available_docs:
        print("❌ No documents ready for Phase 6.")
        print("   Documents need both canonical concepts (Phase 4) and relationships (Phase 5).")
        return
    
    print("\n📂 Available documents for graph refinement:")
    print("=" * 70)
    
    for doc_id in sorted(available_docs):
        # Load to get info
        canonical_data = load_json(canonical_files[doc_id])
        relationship_data = load_json(relationship_files[doc_id])
        
        if canonical_data and relationship_data:
            num_concepts = len(canonical_data)
            num_relationships = len(relationship_data)
            print(f"\n📄 {doc_id}")
            print(f"   Canonical concepts: {num_concepts}")
            print(f"   Relationships: {num_relationships}")


def refine_graph_for_doc(doc_id: str, 
                        min_confidence: float = 0.55,
                        prune_isolated: bool = True,
                        viz_format: bool = False,
                        debug: bool = False):
    """Refine graph for a single document.
    
    Args:
        doc_id: Document identifier
        min_confidence: Minimum edge confidence threshold
        prune_isolated: If True, prune isolated nodes
        viz_format: If True, save in visualization format
        debug: If True, print detailed progress
    """
    data_dir = Path("data")
    
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
    
    # Load relationships
    relationships_path = data_dir / "relationships" / f"{doc_id}_relationships.json"
    if not relationships_path.exists():
        print(f"❌ Relationships not found: {relationships_path}")
        print(f"   Run Phase 5 first: python relationship_extractor.py {doc_id}")
        return
    
    relationships = load_json(relationships_path)
    if not relationships:
        print(f"❌ Failed to load relationships from {relationships_path}")
        return
    
    print(f"\n📄 Processing document: {doc_id}")
    print(f"   Canonical concepts: {len(canonical_concepts)}")
    print(f"   Relationships: {len(relationships)}")
    
    # Run refinement pipeline
    try:
        pipeline = GraphRefinementPipeline(
            min_confidence=min_confidence,
            prune_isolated=prune_isolated,
            debug=debug
        )
        
        final_graph = pipeline.build_final_graph(canonical_concepts, relationships)
        
        # Save results
        output_path = data_dir / "graph" / f"{doc_id}_final_graph.json"
        save_graph(final_graph, output_path, viz_format=viz_format)
        
        print(f"\n✅ Graph refinement complete!")
        
    except Exception as e:
        print(f"\n❌ Refinement failed: {e}")
        if debug:
            import traceback
            traceback.print_exc()


def refine_all_graphs(min_confidence: float = 0.55,
                     prune_isolated: bool = True,
                     viz_format: bool = False,
                     debug: bool = False):
    """Refine graphs for all available documents.
    
    Args:
        min_confidence: Minimum edge confidence threshold
        prune_isolated: If True, prune isolated nodes
        viz_format: If True, save in visualization format
        debug: If True, print detailed progress
    """
    data_dir = Path("data")
    canonical_dir = data_dir / "canonical"
    relationships_dir = data_dir / "relationships"
    
    if not canonical_dir.exists() or not relationships_dir.exists():
        print("❌ Data directories not found. Run Phases 4 and 5 first.")
        return
    
    # Find documents with both files
    canonical_files = {f.stem.replace("_canonical", ""): f for f in canonical_dir.glob("*_canonical.json")}
    relationship_files = {f.stem.replace("_relationships", ""): f for f in relationships_dir.glob("*_relationships.json")}
    
    available_docs = set(canonical_files.keys()) & set(relationship_files.keys())
    
    if not available_docs:
        print("❌ No documents ready for processing.")
        return
    
    print(f"\n🚀 Processing {len(available_docs)} documents...")
    
    for i, doc_id in enumerate(sorted(available_docs), 1):
        print(f"\n{'=' * 70}")
        print(f"Document {i}/{len(available_docs)}: {doc_id}")
        print(f"{'=' * 70}")
        
        refine_graph_for_doc(
            doc_id, 
            min_confidence=min_confidence,
            prune_isolated=prune_isolated,
            viz_format=viz_format,
            debug=debug
        )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Phase 6: Refine and assemble final knowledge graph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available documents
  python graph_refiner.py --list
  
  # Refine graph for one document
  python graph_refiner.py abc123 --debug
  
  # Refine for all documents
  python graph_refiner.py --all
  
  # Adjust confidence threshold and save visualization format
  python graph_refiner.py abc123 --min-confidence 0.6 --viz-format
  
  # Keep isolated nodes
  python graph_refiner.py abc123 --no-prune
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
        "--min-confidence",
        type=float,
        default=0.55,
        help="Minimum edge confidence threshold (default: 0.55)"
    )
    
    parser.add_argument(
        "--no-prune",
        action="store_true",
        help="Don't prune isolated nodes"
    )
    
    parser.add_argument(
        "--viz-format",
        action="store_true",
        help="Save in visualization format (minimal payload)"
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
        refine_all_graphs(
            min_confidence=args.min_confidence,
            prune_isolated=not args.no_prune,
            viz_format=args.viz_format,
            debug=args.debug
        )
        return
    
    # Handle single document
    if args.doc_id:
        refine_graph_for_doc(
            args.doc_id, 
            min_confidence=args.min_confidence,
            prune_isolated=not args.no_prune,
            viz_format=args.viz_format,
            debug=args.debug
        )
        return
    
    # No command provided
    parser.print_help()


if __name__ == "__main__":
    main()
