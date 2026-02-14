"""Token estimation for semantic blocks."""


def estimate_tokens(text: str) -> int:
    """Estimate token count for text.
    
    Uses a simple heuristic: word count * 1.3
    This approximates tokenization without needing tiktoken.
    
    Args:
        text: Text to estimate tokens for
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    
    word_count = len(text.split())
    return int(word_count * 1.3)
