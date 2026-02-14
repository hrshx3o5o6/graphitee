"""Ollama LLM integration for concept extraction."""

import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)


class OllamaExtractor:
    """Handles communication with local Ollama API."""
    
    def __init__(
        self,
        model: str = "llama3.1:8b",
        base_url: str = "http://localhost:11434",
        timeout: int = 60
    ):
        """Initialize Ollama extractor.
        
        Args:
            model: Model name to use
            base_url: Ollama API base URL
            timeout: Request timeout in seconds
        """
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.api_url = f"{base_url}/api/generate"
        
        logger.info(f"Initialized Ollama extractor with model: {model}")
    
    def check_connection(self) -> bool:
        """Check if Ollama is running and accessible.
        
        Returns:
            True if Ollama is accessible
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Cannot connect to Ollama: {e}")
            return False
    
    def query(self, prompt: str, temperature: float = 0.1) -> Optional[str]:
        """Query Ollama with a prompt.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature (lower = more deterministic)
            
        Returns:
            Model response text or None on failure
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": 512  # Max tokens to generate
                }
            }
            
            logger.debug(f"Querying Ollama with {len(prompt)} char prompt")
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama request failed: {response.status_code}")
                return None
            
            result = response.json()
            return result.get("response", "")
            
        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out")
            return None
        except Exception as e:
            logger.error(f"Ollama query failed: {e}")
            return None
