"""LLM-based relationship extractor using Ollama."""

import requests
import json
from typing import List, Optional
from relationships.models import RelationshipCandidate
from relationships.prompts import build_relationship_prompt


class OllamaRelationshipExtractor:
    """Extracts relationships using local Ollama LLM."""
    
    def __init__(self, model: str = "llama3.1:8b", base_url: str = "http://localhost:11434"):
        """Initialize Ollama extractor.
        
        Args:
            model: Ollama model name
            base_url: Ollama API base URL
        """
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
    
    def extract_from_candidate(self, candidate: RelationshipCandidate) -> Optional[str]:
        """Extract relationships from a single candidate pair.
        
        Args:
            candidate: RelationshipCandidate with concept pair and block text
            
        Returns:
            Raw LLM response string, or None if extraction failed
        """
        # Build the prompt
        concept_names = [candidate.concept_a_name, candidate.concept_b_name]
        prompt = build_relationship_prompt(concept_names, candidate.block_text)
        
        # Query Ollama
        try:
            response = self._query_ollama(prompt)
            return response
        except Exception as e:
            print(f"  ⚠️  Ollama error: {e}")
            return None
    
    def extract_from_block(self, block_text: str, concept_names: List[str]) -> Optional[str]:
        """Extract relationships from a block with multiple concepts.
        
        Args:
            block_text: The semantic block text
            concept_names: List of concept names in the block
            
        Returns:
            Raw LLM response string, or None if extraction failed
        """
        prompt = build_relationship_prompt(concept_names, block_text)
        
        try:
            response = self._query_ollama(prompt)
            return response
        except Exception as e:
            print(f"  ⚠️  Ollama error: {e}")
            return None
    
    def _query_ollama(self, prompt: str, timeout: int = 30) -> str:
        """Query Ollama API.
        
        Args:
            prompt: The prompt to send
            timeout: Request timeout in seconds
            
        Returns:
            Response text from LLM
            
        Raises:
            Exception: If API call fails
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature for more consistent extraction
                "num_predict": 500    # Limit output length
            }
        }
        
        response = requests.post(
            self.api_url,
            json=payload,
            timeout=timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama API returned {response.status_code}: {response.text}")
        
        result = response.json()
        return result.get("response", "")
    
    def test_connection(self) -> bool:
        """Test if Ollama is accessible.
        
        Returns:
            True if Ollama is running and responsive
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def check_model(self) -> bool:
        """Check if the required model is available.
        
        Returns:
            True if model is installed
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                return any(self.model in m for m in models)
            return False
        except:
            return False
