"""Tavily web search service for fact-checking."""

import os
from dataclasses import dataclass
from typing import Optional

import aiohttp


@dataclass
class SearchResult:
    """Single search result."""

    title: str
    url: str
    content: str
    score: float


class TavilySearch:
    """Web search using Tavily API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY not set")

    async def search(
        self,
        query: str,
        max_results: int = 5,
        include_answer: bool = True,
        include_raw_content: bool = False,
    ) -> list[SearchResult]:
        """Perform a web search."""
        url = "https://api.tavily.com/search"

        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Tavily API error: {error_text}")

                data = await response.json()

        results = []
        for result in data.get("results", []):
            results.append(
                SearchResult(
                    title=result.get("title", ""),
                    url=result.get("url", ""),
                    content=result.get("content", ""),
                    score=result.get("score", 0.0),
                )
            )

        return results

    async def verify_claim(self, claim: str, context: Optional[str] = None) -> dict:
        """Verify a claim against web search results."""
        search_query = claim
        if context:
            search_query = f"{context} {claim}"

        results = await self.search(search_query, max_results=5)

        # Simple verification logic
        has_supporting = any(r.score > 0.7 for r in results)
        has_contradicting = False  # Would need more sophisticated NLP

        if has_supporting and not has_contradicting:
            verdict = "SUPPORTED"
            confidence = 0.7
        elif has_contradicting:
            verdict = "CONTRADICTED"
            confidence = 0.6
        else:
            verdict = "UNVERIFIED"
            confidence = 0.4

        return {
            "claim": claim,
            "verdict": verdict,
            "confidence": confidence,
            "sources": [
                {"title": r.title, "url": r.url, "score": r.score} for r in results[:3]
            ],
        }
