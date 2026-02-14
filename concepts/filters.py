"""Filter and clean extracted concepts."""

import logging
from typing import List, Dict, Any, Set

logger = logging.getLogger(__name__)


# Generic terms to filter out
STOP_CONCEPTS: Set[str] = {
    "model",
    "data",
    "system",
    "learning",
    "process",
    "method",
    "approach",
    "technique",  # Too generic without specifics
    "algorithm",  # Too generic without specifics
    "problem",
    "solution",
    "value",
    "result",
    "output",
    "input",
    "parameter",
    "function",
    "variable",
    "training",
    "testing",
    "validation",  # Unless specific like "Cross Validation"
    "performance",
    "accuracy",
    "error",
    "loss",
    "feature",
    "sample",
    "dataset",
    "example",
    "task",
    "goal",
    "objective"
}


def is_generic_concept(name: str) -> bool:
    """Check if concept name is too generic.
    
    Args:
        name: Concept name
        
    Returns:
        True if generic/should be filtered
    """
    name_lower = name.lower().strip()
    
    # Check against stop list
    if name_lower in STOP_CONCEPTS:
        return True
    
    # Single word generic terms
    if len(name_lower.split()) == 1 and name_lower in STOP_CONCEPTS:
        return True
    
    # Very short names (likely too vague)
    if len(name_lower) < 3:
        return True
    
    return False


def filter_concepts(
    concepts: List[Dict[str, Any]],
    min_confidence: float = 0.5
) -> List[Dict[str, Any]]:
    """Filter and clean concept list.
    
    Removes:
    - Generic/stop concepts
    - Duplicate names (keep highest confidence)
    - Low confidence concepts
    - Concepts with invalid names
    
    Args:
        concepts: List of concept dictionaries
        min_confidence: Minimum confidence threshold
        
    Returns:
        Filtered concept list
    """
    if not concepts:
        return []
    
    filtered = []
    seen_names: Dict[str, float] = {}  # Track best confidence per name
    
    for concept in concepts:
        name = concept.get("name", "").strip()
        confidence = concept.get("confidence", 0.0)
        
        # Skip empty names
        if not name:
            logger.debug("Skipping concept with empty name")
            continue
        
        # Skip generic concepts
        if is_generic_concept(name):
            logger.debug(f"Filtering generic concept: {name}")
            continue
        
        # Skip low confidence
        if confidence < min_confidence:
            logger.debug(f"Filtering low confidence concept: {name} ({confidence})")
            continue
        
        # Handle duplicates - keep highest confidence
        name_lower = name.lower()
        if name_lower in seen_names:
            if confidence <= seen_names[name_lower]:
                logger.debug(f"Skipping duplicate concept: {name}")
                continue
            else:
                # Remove previous lower-confidence version
                filtered = [c for c in filtered if c["name"].lower() != name_lower]
        
        seen_names[name_lower] = confidence
        filtered.append(concept)
    
    logger.info(f"Filtered {len(concepts)} -> {len(filtered)} concepts")
    return filtered


def deduplicate_across_blocks(
    all_concepts: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Deduplicate concepts across multiple blocks.
    
    Keeps the highest confidence version of each concept name.
    
    Args:
        all_concepts: All concepts from all blocks
        
    Returns:
        Deduplicated list (still allows duplicates - normalization in Phase 4)
    """
    # For Phase 3, we allow duplicates across blocks
    # Phase 4 will handle proper merging and normalization
    # Just do basic deduplication per exact name
    
    seen: Dict[str, Dict[str, Any]] = {}
    
    for concept in all_concepts:
        name = concept.get("name", "").strip()
        confidence = concept.get("confidence", 0.0)
        
        if not name:
            continue
        
        if name not in seen or confidence > seen[name].get("confidence", 0.0):
            seen[name] = concept
    
    return list(seen.values())
