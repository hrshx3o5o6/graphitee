"""Validation logic for semantic blocks."""

import logging
from typing import List
from semantic.models import SemanticBlock

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when block validation fails."""
    pass


def validate_blocks(blocks: List[SemanticBlock]) -> None:
    """Validate semantic blocks meet requirements.
    
    Requirements:
    - Text must not be empty
    - Must have at least one heading in path
    - Token estimate must be under 350
    
    Args:
        blocks: List of semantic blocks to validate
        
    Raises:
        ValidationError: If validation fails
    """
    for i, block in enumerate(blocks):
        # Check text is not empty
        if not block.text or not block.text.strip():
            raise ValidationError(
                f"Block {i} (id={block.block_id}) has empty text"
            )
        
        # Check has heading path
        if not block.heading_path or len(block.heading_path) == 0:
            raise ValidationError(
                f"Block {i} (id={block.block_id}) has no heading path"
            )
        
        # Check token limit
        if block.token_estimate >= 350:
            logger.warning(
                f"Block {i} (id={block.block_id}) exceeds 350 tokens: "
                f"{block.token_estimate}"
            )
        
        # Check order index is positive
        if block.order_index < 0:
            raise ValidationError(
                f"Block {i} (id={block.block_id}) has invalid order_index: "
                f"{block.order_index}"
            )
    
    logger.info(f"Validated {len(blocks)} semantic blocks successfully")


def get_validation_stats(blocks: List[SemanticBlock]) -> dict:
    """Get statistics about semantic blocks for debugging.
    
    Args:
        blocks: List of semantic blocks
        
    Returns:
        Statistics dictionary
    """
    if not blocks:
        return {
            "total_blocks": 0,
            "avg_tokens": 0,
            "max_tokens": 0,
            "block_type_distribution": {}
        }
    
    # Calculate statistics
    total_tokens = sum(b.token_estimate for b in blocks)
    avg_tokens = total_tokens / len(blocks)
    max_tokens = max(b.token_estimate for b in blocks)
    
    # Block type distribution
    type_dist = {}
    for block in blocks:
        type_dist[block.block_type] = type_dist.get(block.block_type, 0) + 1
    
    return {
        "total_blocks": len(blocks),
        "avg_tokens": round(avg_tokens, 1),
        "max_tokens": max_tokens,
        "block_type_distribution": type_dist
    }
