"""LLM prompt templates for relationship extraction."""

from typing import List
from relationships.models import VALID_RELATION_TYPES


def build_relationship_prompt(concept_names: List[str], block_text: str) -> str:
    """Build relationship extraction prompt.
    
    Args:
        concept_names: List of concept names present in the block
        block_text: The text content of the semantic block
        
    Returns:
        Formatted prompt string
    """
    relation_types_str = ", ".join(sorted(VALID_RELATION_TYPES))
    concepts_str = "\n".join(f"- {name}" for name in concept_names)
    
    prompt = f"""You are a relationship extraction system for technical knowledge graphs.

Task:
Identify relationships between technical concepts that are explicitly supported by the text below.

Critical Rules:
- ONLY use concepts from the list provided below
- Do NOT invent new concepts or relationships
- Do NOT infer hidden knowledge or world facts
- Extract ONLY relationships that are clearly stated or directly implied in the text
- Relationships must be directional (source → target)
- Use the most specific relation type that fits

Allowed relation types:
{relation_types_str}

Relation type definitions:
- DEFINES: source explains or formally defines target
- DEPENDS_ON: source requires or needs target to function
- CAUSES: source directly causes or leads to target
- PART_OF: source is a component or subset of target
- USES: source employs or utilizes target
- EXTENDS: source builds upon or inherits from target
- CONTRASTS_WITH: source is explicitly compared or contrasted with target
- MEASURED_BY: source is quantified or evaluated by target
- ASSOCIATED_WITH: source is related to target (use only if no other type fits)

Concepts present in this text:
{concepts_str}

Text to analyze:
\"\"\"
{block_text}
\"\"\"

Return your answer in STRICT JSON format with NO additional text:

{{
  "relationships": [
    {{
      "source": "exact concept name from list",
      "target": "exact concept name from list",
      "relation_type": "one of the allowed types above",
      "confidence": 0.85
    }}
  ]
}}

If no relationships can be extracted, return:
{{
  "relationships": []
}}

JSON output:"""
    
    return prompt


def build_verification_prompt(source: str, target: str, relation_type: str, 
                              evidence_text: str) -> str:
    """Build prompt to verify a specific relationship.
    
    Args:
        source: Source concept name
        target: Target concept name
        relation_type: Type of relationship
        evidence_text: Text that supposedly supports the relationship
        
    Returns:
        Formatted verification prompt
    """
    prompt = f"""Verify if the following relationship is explicitly supported by the text.

Relationship:
{source} --{relation_type}--> {target}

Evidence text:
\"\"\"
{evidence_text}
\"\"\"

Question: Is this relationship clearly stated or directly implied in the text above?

Answer with a single word: YES or NO

Answer:"""
    
    return prompt
