"""Main semantic block builder pipeline."""

import logging
from uuid import uuid4
from typing import List, Dict
from storage.models import Document
from semantic.models import SemanticBlock
from semantic.context import build_heading_paths
from semantic.splitter import split_semantically
from semantic.heuristics import infer_block_type
from semantic.tokenizer import estimate_tokens
from semantic.validator import validate_blocks, get_validation_stats

logger = logging.getLogger(__name__)


def create_semantic_block(
    chunk: str,
    doc_id: str,
    section_id: str,
    heading_path: List[str],
    order_index: int,
    original_type: str
) -> SemanticBlock:
    """Create a semantic block from a text chunk.
    
    Args:
        chunk: Text content
        doc_id: Document ID
        section_id: Section ID
        heading_path: Full heading hierarchy
        order_index: Position in document
        original_type: Original content block type
        
    Returns:
        SemanticBlock instance
    """
    return SemanticBlock(
        block_id=uuid4().hex[:12],  # Shorter ID for readability
        doc_id=doc_id,
        section_id=section_id,
        text=chunk,
        block_type=infer_block_type(chunk, original_type),
        heading_path=heading_path,
        order_index=order_index,
        token_estimate=estimate_tokens(chunk)
    )


def build_semantic_blocks(document: Document) -> List[SemanticBlock]:
    """Transform a document into semantic blocks.
    
    Pipeline:
    1. Build heading paths for context
    2. Iterate through sections
    3. Split content semantically
    4. Create semantic blocks with metadata
    5. Validate blocks
    
    Args:
        document: Document from Phase 1
        
    Returns:
        List of semantic blocks
    """
    logger.info(f"Building semantic blocks for document: {document.id}")
    
    # Convert sections to list of dicts for easier processing
    sections_data = [
        {
            "section_id": s.section_id,
            "heading": s.heading,
            "level": s.level,
            "content_blocks": [
                {
                    "type": cb.type,
                    "text": cb.text
                }
                for cb in s.content_blocks
            ]
        }
        for s in document.sections
    ]
    
    # Build heading context
    heading_paths = build_heading_paths(sections_data)
    logger.debug(f"Built heading paths for {len(heading_paths)} sections")
    
    # Process sections and build blocks
    blocks = []
    order_counter = 0
    
    for section_dict in sections_data:
        section_id = section_dict["section_id"]
        heading_path = heading_paths.get(section_id, [section_dict["heading"]])
        
        # Process each content block in section
        for content_block in section_dict["content_blocks"]:
            # Split into semantic chunks
            chunks = split_semantically(content_block)
            
            # Create semantic block for each chunk
            for chunk in chunks:
                order_counter += 1
                block = create_semantic_block(
                    chunk=chunk,
                    doc_id=document.id,
                    section_id=section_id,
                    heading_path=heading_path,
                    order_index=order_counter,
                    original_type=content_block["type"]
                )
                blocks.append(block)
    
    # Validate blocks
    validate_blocks(blocks)
    
    # Log statistics
    stats = get_validation_stats(blocks)
    logger.info(
        f"Created {stats['total_blocks']} semantic blocks "
        f"(avg tokens: {stats['avg_tokens']}, max: {stats['max_tokens']})"
    )
    logger.info(f"Block type distribution: {stats['block_type_distribution']}")
    
    return blocks


def print_block_summary(blocks: List[SemanticBlock], max_display: int = 5) -> None:
    """Print a summary of semantic blocks for debugging.
    
    Args:
        blocks: List of semantic blocks
        max_display: Maximum number of blocks to display in detail
    """
    if not blocks:
        print("No semantic blocks created.")
        return
    
    stats = get_validation_stats(blocks)
    
    print(f"\n{'='*70}")
    print("SEMANTIC BLOCKS SUMMARY")
    print(f"{'='*70}")
    print(f"Total blocks: {stats['total_blocks']}")
    print(f"Average tokens: {stats['avg_tokens']}")
    print(f"Max tokens: {stats['max_tokens']}")
    print(f"\nBlock type distribution:")
    for block_type, count in stats['block_type_distribution'].items():
        percentage = (count / stats['total_blocks']) * 100
        print(f"  {block_type}: {count} ({percentage:.1f}%)")
    
    print(f"\nFirst {min(max_display, len(blocks))} blocks:")
    print(f"{'-'*70}")
    
    for i, block in enumerate(blocks[:max_display]):
        path_str = " > ".join(block.heading_path)
        preview = block.text[:100] + "..." if len(block.text) > 100 else block.text
        
        print(f"\n[{i+1}] {block.block_type.upper()}")
        print(f"Path: {path_str}")
        print(f"Tokens: {block.token_estimate}")
        print(f"Text: {preview}")
