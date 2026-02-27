"""Tiered scraper service for progressive article loading."""

import asyncio
import concurrent.futures
from typing import Optional

from scraper.browser import BrowserManager
from scraper.crawler import Crawler


def _extract_text_from_blocks(blocks) -> str:
    """Extract text from content blocks."""
    return "\n".join(block.text for block in blocks)


def _sync_scrape_tier1(url: str, headless: bool = True) -> dict:
    """Sync scrape tier 1 - runs in thread pool."""
    with BrowserManager(headless=headless) as browser:
        crawler = Crawler(browser_manager=browser, max_depth=0, max_pages=1)
        documents = crawler.crawl(url)

        if not documents:
            raise ValueError(f"Failed to scrape {url}")

        doc = documents[0]

        content_parts = []
        for section in doc.sections[:5]:
            text = _extract_text_from_blocks(section.content_blocks)
            content_parts.append(f"## {section.heading}\n{text[:500]}")

        return {
            "url": url,
            "title": doc.title,
            "content": "\n\n".join(content_parts),
            "sections": [
                {"heading": s.heading, "level": s.level} for s in doc.sections[:10]
            ],
            "links": [
                {"text": l.anchor_text[:100], "url": l.target_url}
                for l in doc.links[:20]
            ],
            "tier": 1,
        }


def _sync_scrape_full(url: str, headless: bool = True) -> dict:
    """Sync scrape full - runs in thread pool."""
    with BrowserManager(headless=headless) as browser:
        crawler = Crawler(browser_manager=browser, max_depth=1, max_pages=3)
        documents = crawler.crawl(url)

        if not documents:
            raise ValueError(f"Failed to scrape {url}")

        doc = documents[0]

        # Extract full text from all sections
        all_text = []
        for section in doc.sections:
            text = _extract_text_from_blocks(section.content_blocks)
            all_text.append(f"## {section.heading}\n{text}")
            # Also get children
            for child in section.children:
                child_text = _extract_text_from_blocks(child.content_blocks)
                all_text.append(f"## {child.heading}\n{child_text}")

        return {
            "url": url,
            "title": doc.title,
            "full_content": "\n\n".join(all_text),
            "sections": [
                {
                    "heading": s.heading,
                    "level": s.level,
                    "content": _extract_text_from_blocks(s.content_blocks)[:2000],
                }
                for s in doc.sections
            ],
            "links": [{"text": l.anchor_text, "url": l.target_url} for l in doc.links],
            "tier": 2,
        }


async def scrape_article(url: str, tier: int = 1) -> dict:
    """Scrape article using thread pool to avoid asyncio/sync conflict."""
    loop = asyncio.get_event_loop()

    with concurrent.futures.ThreadPoolExecutor() as pool:
        if tier == 1:
            result = await loop.run_in_executor(pool, _sync_scrape_tier1, url)
        else:
            result = await loop.run_in_executor(pool, _sync_scrape_full, url)

    return result
