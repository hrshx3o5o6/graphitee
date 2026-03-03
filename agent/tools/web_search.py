"""Web search tool for fact-checking."""

from pydantic import BaseModel

from agent.tools.base import Tool, ToolOutput
from services.tavily import TavilySearch


class WebSearchInput(BaseModel):
    """Input for web search tool."""

    query: str
    max_results: int = 5


class WebSearchOutput(ToolOutput):
    """Output from web search tool."""

    results: list = []


class WebSearchTool(Tool):
    """Tool for web searching (fact-checking)."""

    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the web for information to verify claims or get more context.",
            input_model=WebSearchInput,
            output_model=WebSearchOutput,
        )
        self._searcher = None

    def _get_searcher(self) -> TavilySearch:
        if self._searcher is None:
            try:
                self._searcher = TavilySearch()
            except ValueError as e:
                return None
        return self._searcher

    async def execute(self, session_id: str, state, **kwargs) -> WebSearchOutput:
        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 5)

        if not query:
            return WebSearchOutput(success=False, error="Query is required")

        searcher = self._get_searcher()
        if searcher is None:
            return WebSearchOutput(
                success=False,
                error="Tavily API not configured. Set TAVILY_API_KEY environment variable.",
            )

        try:
            results = await searcher.search(query, max_results=max_results)
            return WebSearchOutput(
                success=True,
                results=[
                    {
                        "title": r.title,
                        "url": r.url,
                        "content": r.content[:200],
                        "score": r.score,
                    }
                    for r in results
                ],
            )
        except Exception as e:
            return WebSearchOutput(success=False, error=str(e))
