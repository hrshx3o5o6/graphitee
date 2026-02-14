"""String normalization and preprocessing."""

import re
import logging
from typing import List
from normalization.models import ConceptCandidate

logger = logging.getLogger(__name__)


def normalize_string(text: str) -> str:
    """Normalize a string for comparison.
    
    Steps:
    - Lowercase
    - Remove punctuation
    - Normalize whitespace
    - Normalize hyphens
    - Basic plural handling
    
    Args:
        text: Input string
        
    Returns:
        Normalized string
    """
    if not text:
        return ""
    
    # Lowercase
    text = text.lower()
    
    # Remove punctuation except hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    
    # Normalize hyphens to spaces
    text = text.replace('-', ' ')
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    # Basic plural normalization (simple cases)
    # "models" -> "model", "processes" -> "process"
    words = text.split()
    normalized_words = []
    
    for word in words:
        # Remove common plural suffixes
        if word.endswith('es') and len(word) > 4:
            # "processes" -> "process"
            normalized_words.append(word[:-2])
        elif word.endswith('s') and len(word) > 3:
            # "models" -> "model"
            normalized_words.append(word[:-1])
        else:
            normalized_words.append(word)
    
    return ' '.join(normalized_words)


def preprocess_candidates(candidates: List[ConceptCandidate]) -> List[ConceptCandidate]:
    """Add normalized names to all concept candidates.
    
    Args:
        candidates: List of concept candidates
        
    Returns:
        Same list with normalized_name field populated
    """
    logger.info(f"Preprocessing {len(candidates)} concept candidates")
    
    for candidate in candidates:
        candidate.normalized_name = normalize_string(candidate.name)
    
    # Log some examples
    if candidates and logger.isEnabledFor(logging.DEBUG):
        for i in range(min(5, len(candidates))):
            logger.debug(
                f"'{candidates[i].name}' -> '{candidates[i].normalized_name}'"
            )
    
    logger.info("Preprocessing complete")
    return candidates


def exact_match_deduplication(candidates: List[ConceptCandidate]) -> List[ConceptCandidate]:
    """Remove exact duplicates based on normalized name.
    
    Keeps the one with highest confidence.
    
    Args:
        candidates: List of concept candidates
        
    Returns:
        Deduplicated list
    """
    logger.info("Performing exact match deduplication")
    
    seen = {}
    
    for candidate in candidates:
        norm_name = candidate.normalized_name
        
        if norm_name not in seen:
            seen[norm_name] = candidate
        else:
            # Keep higher confidence
            if candidate.confidence > seen[norm_name].confidence:
                seen[norm_name] = candidate
    
    result = list(seen.values())
    
    logger.info(f"Deduplicated {len(candidates)} -> {len(result)} concepts")
    return result
