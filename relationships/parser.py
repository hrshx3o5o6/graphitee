"""Parser for LLM relationship extraction output."""

import json
import re
from typing import List, Dict, Optional
from relationships.models import VALID_RELATION_TYPES


class RelationshipParser:
    """Parses and validates LLM output for relationship extraction."""
    
    def __init__(self, debug: bool = False):
        """Initialize parser.
        
        Args:
            debug: If True, print detailed parsing information
        """
        self.debug = debug
    
    def parse_llm_output(self, llm_response: str) -> List[Dict]:
        """Parse LLM response into relationship dictionaries.
        
        Args:
            llm_response: Raw text response from LLM
            
        Returns:
            List of relationship dictionaries with keys:
            - source (str)
            - target (str)
            - relation_type (str)
            - confidence (float)
        """
        if not llm_response or not llm_response.strip():
            return []
        
        # Try to extract JSON from the response
        json_data = self._extract_json(llm_response)
        if not json_data:
            if self.debug:
                print(f"  ⚠️  No valid JSON found in response")
            return []
        
        # Parse and validate relationships
        relationships = json_data.get("relationships", [])
        if not isinstance(relationships, list):
            if self.debug:
                print(f"  ⚠️  'relationships' is not a list")
            return []
        
        valid_relationships = []
        for rel in relationships:
            validated = self._validate_relationship(rel)
            if validated:
                valid_relationships.append(validated)
        
        return valid_relationships
    
    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON object from text that may contain markdown or other content.
        
        Args:
            text: Raw text that should contain JSON
            
        Returns:
            Parsed JSON dict, or None if extraction failed
        """
        # Remove markdown code fences
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        # Try to find JSON object
        json_pattern = r'\{[^{}]*\{[^{}]*\}[^{}]*\}'  # Nested object
        match = re.search(json_pattern, text, re.DOTALL)
        
        if not match:
            # Try simpler pattern
            json_pattern = r'\{.*\}'
            match = re.search(json_pattern, text, re.DOTALL)
        
        if not match:
            return None
        
        json_str = match.group(0)
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            if self.debug:
                print(f"  ⚠️  JSON decode error: {e}")
            return None
    
    def _validate_relationship(self, rel: Dict) -> Optional[Dict]:
        """Validate a single relationship dictionary.
        
        Args:
            rel: Raw relationship dict from LLM
            
        Returns:
            Validated and normalized dict, or None if invalid
        """
        # Check required fields
        if not isinstance(rel, dict):
            return None
        
        source = rel.get("source", "").strip()
        target = rel.get("target", "").strip()
        relation_type = rel.get("relation_type", "").strip().upper()
        confidence = rel.get("confidence", 0.6)
        
        # Validate source and target
        if not source or not target:
            if self.debug:
                print(f"  ⚠️  Missing source or target")
            return None
        
        # Check for self-loops
        if source.lower() == target.lower():
            if self.debug:
                print(f"  ⚠️  Self-loop detected: {source}")
            return None
        
        # Validate relation type
        if relation_type not in VALID_RELATION_TYPES:
            if self.debug:
                print(f"  ⚠️  Invalid relation type: {relation_type}")
            return None
        
        # Validate and clamp confidence
        try:
            confidence = float(confidence)
            confidence = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            confidence = 0.6  # Default confidence
        
        return {
            "source": source,
            "target": target,
            "relation_type": relation_type,
            "confidence": confidence
        }
    
    def print_parse_stats(self, total_responses: int, total_extracted: int, 
                         total_valid: int):
        """Print parsing statistics.
        
        Args:
            total_responses: Number of LLM responses received
            total_extracted: Number of relationships extracted from responses
            total_valid: Number of relationships that passed validation
        """
        print(f"\n📝 Parsing Statistics")
        print(f"=" * 50)
        print(f"LLM responses: {total_responses}")
        print(f"Relationships extracted: {total_extracted}")
        print(f"Relationships valid: {total_valid}")
        if total_extracted > 0:
            valid_rate = (total_valid / total_extracted) * 100
            print(f"Validation rate: {valid_rate:.1f}%")
