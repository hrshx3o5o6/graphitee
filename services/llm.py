"""LLM service using Ollama."""

import json
from dataclasses import dataclass
from typing import Any, Optional

import requests


@dataclass
class LLMResponse:
    """Response from LLM."""

    content: str
    model: str
    done: bool


class OllamaLLM:
    """LLM interface using Ollama."""

    def __init__(
        self, base_url: str = "http://localhost:11434", model: str = "llama3.1:8b"
    ):
        self.base_url = base_url
        self.model = model

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False,
        **kwargs,
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {"temperature": temperature, **kwargs},
        }

        if system_prompt:
            payload["system"] = system_prompt

        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()

        data = response.json()

        return LLMResponse(
            content=data.get("response", ""),
            model=data.get("model", self.model),
            done=data.get("done", True),
        )

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        **kwargs,
    ) -> dict:
        """Generate JSON response from LLM."""
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": temperature, **kwargs},
        }

        if system_prompt:
            payload["system"] = system_prompt

        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()

        data = response.json()
        content = data.get("response", "")

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
            raise ValueError(f"Invalid JSON response: {content[:100]}")

    def chat(
        self, messages: list[dict[str, str]], temperature: float = 0.7, **kwargs
    ) -> LLMResponse:
        """Chat with the LLM using message format."""
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, **kwargs},
        }

        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()

        data = response.json()

        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            model=data.get("model", self.model),
            done=data.get("done", True),
        )
