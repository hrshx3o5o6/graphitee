"""Heuristic-based block type inference.

NO AI or LLM usage - purely rule-based classification.
"""

from typing import Literal


BlockType = Literal["definition", "explanation", "example", "code", "list"]


def infer_block_type(text: str, original_type: str) -> BlockType:
    """Infer semantic block type using heuristics.
    
    Rules:
    - Code blocks stay as code
    - Text with "is defined as" or "refers to" → definition
    - Text with "for example" or "consider" → example
    - Everything else → explanation
    
    Args:
        text: Text content
        original_type: Original content block type from Phase 1
        
    Returns:
        Inferred block type
    """
    # Preserve code blocks
    if original_type == "code":
        return "code"
    
    # List items
    if original_type == "list":
        return "list"
    
    lower_text = text.lower()
    
    # Definition patterns
    definition_patterns = [
        "is defined as",
        "refers to",
        "is called",
        "means that",
        "can be defined as",
        "is known as",
        "we define",
        "definition:"
    ]
    
    if any(pattern in lower_text for pattern in definition_patterns):
        return "definition"
    
    # Example patterns
    example_patterns = [
        "for example",
        "for instance",
        "consider",
        "let's say",
        "suppose",
        "imagine that",
        "e.g.",
        "such as"
    ]
    
    if any(pattern in lower_text for pattern in example_patterns):
        return "example"
    
    # Default to explanation
    return "explanation"
