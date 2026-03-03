"""Scrape article tool."""

from pydantic import BaseModel

from agent.tools.base import Tool, ToolOutput
from services.scraper import scrape_article


class ScrapeInput(BaseModel):
    """Input for scrape tool."""

    url: str
    tier: int = 1


class ScrapeOutput(ToolOutput):
    """Output from scrape tool."""

    title: str = ""
    content: str = ""
    sections: list = []
    tier: int = 1


class ScrapeTool(Tool):
    """Tool for scraping articles."""

    def __init__(self):
        super().__init__(
            name="scrape_article",
            description="Scrape content from a URL. Use tier=1 for fast initial load, tier=2 for full content.",
            input_model=ScrapeInput,
            output_model=ScrapeOutput,
        )

    async def execute(self, session_id: str, state, **kwargs) -> ScrapeOutput:
        url = kwargs.get("url")
        tier = kwargs.get("tier", 1)

        if not url:
            return ScrapeOutput(success=False, error="URL is required")

        try:
            result = await scrape_article(url, tier=tier)

            return ScrapeOutput(
                success=True,
                title=result.get("title", ""),
                content=result.get("content", ""),
                sections=result.get("sections", []),
                tier=result.get("tier", tier),
            )
        except Exception as e:
            return ScrapeOutput(success=False, error=str(e))
