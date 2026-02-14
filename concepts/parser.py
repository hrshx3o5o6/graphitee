"""Parse LLM output into structured concepts."""

import json
import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def extract_json_from_text(text: str) -> str:
    """Extract JSON from text that might contain extra content.
    
    LLMs sometimes add markdown formatting or explanations.
    This tries to extract just the JSON part.
    
    Args:
        text: Raw text from LLM
        
    Returns:
        Extracted JSON string
    """
    # Try to find JSON between ```json and ``` markers
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    
    # Try to find JSON object
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    
    return text


def parse_llm_output(raw_output: str) -> List[Dict[str, Any]]:
    """Parse LLM output into list of concept dictionaries.
    
    Handles various failure modes gracefully:
    - Invalid JSON
    - Missing fields
    - Wrong structure
    
    Args:
        raw_output: Raw text from LLM
        
    Returns:
        List of concept dictionaries (may be empty on failure)
    """
    if not raw_output or not raw_output.strip():
        logger.warning("Empty LLM output")
        return []
    
    try:
        # Try to extract JSON from potential markdown/explanation
        json_text = extract_json_from_text(raw_output)
        
        # Parse JSON
        data = json.loads(json_text)
        
        # Extract concepts list
        if isinstance(data, dict):
            concepts = data.get("concepts", [])
        elif isinstance(data, list):
            concepts = data
        else:
            logger.error(f"Unexpected JSON structure: {type(data)}")
            return []
        
        # Validate each concept has required fields
        valid_concepts = []
        for concept in concepts:
            if not isinstance(concept, dict):
                continue
            
            # Check required fields
            if "name" not in concept:
                logger.debug("Skipping concept without name")
                continue
            
            # Add defaults for missing fields
            concept.setdefault("type", "core_concept")
            concept.setdefault("description", concept.get("name", ""))
            concept.setdefault("confidence", 0.6)
            
            # Clamp confidence to valid range
            confidence = concept["confidence"]
            if not isinstance(confidence, (int, float)):
                concept["confidence"] = 0.6
            else:
                concept["confidence"] = max(0.0, min(1.0, float(confidence)))
            
            # Truncate description if too long
            if len(concept["description"].split()) > 25:
                words = concept["description"].split()[:25]
                concept["description"] = " ".join(words) + "..."
            
            valid_concepts.append(concept)
        
        logger.debug(f"Parsed {len(valid_concepts)} concepts from LLM output")
        return valid_concepts
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        logger.debug(f"Raw output: {raw_output[:200]}...")
        return []
    except Exception as e:
        logger.error(f"Unexpected parsing error: {e}")
        return []


def validate_concept_dict(concept: Dict[str, Any]) -> bool:
    """Validate a concept dictionary has required fields.
    
    Args:
        concept: Concept dictionary
        
    Returns:
        True if valid
    """
    required_fields = ["name", "type", "description", "confidence"]
    
    for field in required_fields:
        if field not in concept:
            return False
    
    # Check types
    if not isinstance(concept["name"], str) or not concept["name"].strip():
        return False
    
    if not isinstance(concept["confidence"], (int, float)):
        return False
    
    return True
