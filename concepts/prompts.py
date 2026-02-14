"""Prompt templates for concept extraction."""

from typing import List


def build_extraction_prompt(block_text: str, heading_path: List[str]) -> str:
    """Build prompt for concept extraction from semantic block.
    
    The prompt is designed to:
    - Extract ONLY explicit concepts
    - Avoid summarization
    - Return strict JSON format
    - Include heading context for better understanding
    
    Args:
        block_text: Text content of semantic block
        heading_path: Full heading hierarchy for context
        
    Returns:
        Formatted extraction prompt
    """
    heading_context = " > ".join(heading_path) if heading_path else "No heading context"
    
    prompt = f"""You are an information extraction system.

Task:
Extract ONLY technical concepts explicitly mentioned in the text below.

Rules:
- Do NOT summarize.
- Do NOT infer unstated ideas.
- Extract only concepts clearly present in the text.
- Ignore generic words like "model", "system", "data" unless they are specific technical terms.
- Focus on concrete technical concepts, not vague ideas.

Allowed concept types:
- core_concept: Fundamental technical ideas or phenomena
- technique: Specific methods or approaches
- metric: Measurements or evaluation criteria
- process: Procedures or workflows
- assumption: Preconditions or constraints

Return STRICT JSON ONLY. No explanations, no markdown, just JSON.

JSON format:
{{
  "concepts": [
    {{
      "name": "Concept Name",
      "type": "core_concept",
      "description": "Brief factual description (max 25 words)",
      "confidence": 0.85
    }}
  ]
}}

Heading context:
{heading_context}

Text:
{block_text}

JSON output:"""
    
    return prompt


def build_fallback_prompt(block_text: str) -> str:
    """Build a simpler fallback prompt for difficult cases.
    
    Args:
        block_text: Text content
        
    Returns:
        Simplified extraction prompt
    """
    return f"""Extract technical concepts from this text.

Return JSON format:
{{
  "concepts": [
    {{"name": "...", "type": "core_concept", "description": "...", "confidence": 0.8}}
  ]
}}

Text:
{block_text}

JSON:"""
