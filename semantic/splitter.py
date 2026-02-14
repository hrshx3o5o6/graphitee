"""Semantic text splitting logic.

Splits content into meaningful chunks based on:
- Sentence boundaries
- Transition words
- Maximum sentence count per chunk
"""

import re
from typing import List


# Transition words that indicate semantic boundaries
TRANSITIONS = [
    "however",
    "for example",
    "in contrast",
    "therefore",
    "this means",
    "on the other hand",
    "furthermore",
    "moreover",
    "nevertheless",
    "consequently",
    "in addition",
    "similarly",
    "alternatively",
    "specifically",
    "for instance"
]


def normalize_text(text: str) -> str:
    """Normalize text with minimal cleanup.
    
    Only removes extra whitespace, does NOT modify meaning.
    
    Args:
        text: Raw text
        
    Returns:
        Normalized text
    """
    return " ".join(text.split())


def split_sentences(text: str) -> List[str]:
    """Split text into sentences.
    
    Uses simple regex pattern to split on sentence boundaries.
    
    Args:
        text: Text to split
        
    Returns:
        List of sentences
    """
    # Split on period, exclamation, or question mark followed by whitespace
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def should_split(sentence: str, current_chunk: List[str]) -> bool:
    """Determine if we should start a new semantic chunk.
    
    Split if:
    - Sentence contains a transition word
    - Current chunk has 5+ sentences
    
    Args:
        sentence: Current sentence being processed
        current_chunk: Accumulated sentences in current chunk
        
    Returns:
        True if should split
    """
    lower_sentence = sentence.lower()
    
    # Check for transition words
    if any(transition in lower_sentence for transition in TRANSITIONS):
        return True
    
    # Check sentence count
    if len(current_chunk) >= 5:
        return True
    
    return False


def split_semantically(content_block: dict) -> List[str]:
    """Split a content block into semantic chunks.
    
    Each chunk represents a coherent idea.
    
    Args:
        content_block: Content block from Phase 1
        
    Returns:
        List of text chunks
    """
    text = normalize_text(content_block["text"])
    
    # Don't split code or very short content
    if content_block["type"] == "code" or len(text) < 100:
        return [text]
    
    sentences = split_sentences(text)
    
    # If only 1-2 sentences, don't split
    if len(sentences) <= 2:
        return [text]
    
    chunks = []
    current_chunk = []
    
    for sentence in sentences:
        current_chunk.append(sentence)
        
        # Check if we should start a new chunk
        if should_split(sentence, current_chunk):
            chunks.append(" ".join(current_chunk))
            current_chunk = []
    
    # Add remaining sentences
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks
