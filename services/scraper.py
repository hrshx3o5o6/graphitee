"""Tiered scraper service for progressive article loading."""

import asyncio
import concurrent.futures
import logging

from scraper.browser import BrowserManager
from scraper.crawler import Crawler

logger = logging.getLogger(__name__)


def _extract_text_from_blocks(blocks) -> str:
    """Extract text from content blocks."""
    return "\n".join(block.text for block in blocks)


def _iter_sections(sections):
    """Yield sections recursively in document order."""
    for section in sections:
        yield section
        if section.children:
            yield from _iter_sections(section.children)


def _sanitize_url(url: str) -> str:
    """Normalize user-provided URL input and trim common paste artifacts."""
    cleaned = (url or "").strip().strip("<>")

    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {"'", '"'}:
        cleaned = cleaned[1:-1].strip()

    while cleaned and cleaned[-1] in {"'", '"', ",", ";"}:
        cleaned = cleaned[:-1].rstrip()

    while cleaned.endswith(")") and cleaned.count("(") < cleaned.count(")"):
        cleaned = cleaned[:-1].rstrip()
    while cleaned.endswith("]") and cleaned.count("[") < cleaned.count("]"):
        cleaned = cleaned[:-1].rstrip()

    return cleaned


def _is_likely_error_page(title: str, content: str) -> bool:
    """Detect common error/blocked pages that should not be ingested."""
    title_lower = (title or "").lower()
    content_lower = (content or "").lower()

    title_signals = [
        "404",
        "not found",
        "access denied",
        "forbidden",
        "just a moment",
        "attention required",
        "error",
        "captcha",
        "blocked",
    ]
    content_signals = [
        "page not found",
        "access denied",
        "forbidden",
        "just a moment",
        "attention required",
        "verify you are human",
        "captcha",
        "request blocked",
        "error 404",
    ]

    if any(signal in title_lower for signal in title_signals):
        return True
    if any(signal in content_lower[:2000] for signal in content_signals):
        return True

    return False


def _sync_scrape_tier1(url: str, headless: bool = True) -> dict:
    """Sync scrape tier 1 - runs in thread pool."""
    with BrowserManager(headless=headless) as browser:
        crawler = Crawler(browser_manager=browser, max_depth=0, max_pages=1)
        documents = crawler.crawl(url)

        if not documents:
            raise ValueError(f"Failed to scrape {url}")

        doc = documents[0]

        content_parts = []
        section_summaries = []

        for section in _iter_sections(doc.sections):
            text = _extract_text_from_blocks(section.content_blocks).strip()
            if not text:
                continue

            content_parts.append(f"## {section.heading}\n{text[:700]}")
            section_summaries.append({"heading": section.heading, "level": section.level})

            if len(content_parts) >= 8:
                break

        content = "\n\n".join(content_parts)

        if _is_likely_error_page(doc.title, content):
            raise ValueError(
                f"The URL appears to be an error/blocked page (title: '{doc.title}'). "
                "Please verify the URL and try again."
            )

        return {
            "url": url,
            "title": doc.title,
            "content": content,
            "sections": section_summaries[:10],
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

        # Extract full text from all sections (recursive)
        all_text = []
        all_sections = list(_iter_sections(doc.sections))

        for section in all_sections:
            text = _extract_text_from_blocks(section.content_blocks)
            if not text.strip():
                continue
            all_text.append(f"## {section.heading}\n{text}")

        full_content = "\n\n".join(all_text)

        if _is_likely_error_page(doc.title, full_content):
            raise ValueError(
                f"The URL appears to be an error/blocked page (title: '{doc.title}'). "
                "Please verify the URL and try again."
            )

        return {
            "url": url,
            "title": doc.title,
            "full_content": full_content,
            "sections": [
                {
                    "heading": s.heading,
                    "level": s.level,
                    "content": _extract_text_from_blocks(s.content_blocks)[:2000],
                }
                for s in all_sections
                if _extract_text_from_blocks(s.content_blocks).strip()
            ],
            "links": [{"text": l.anchor_text, "url": l.target_url} for l in doc.links],
            "tier": 2,
        }


async def scrape_article(url: str, tier: int = 1) -> dict:
    """Scrape article using thread pool to avoid asyncio/sync conflict."""
    loop = asyncio.get_event_loop()
    cleaned_url = _sanitize_url(url)

    if cleaned_url != url:
        logger.info("Sanitized URL from '%s' to '%s'", url, cleaned_url)

    if not cleaned_url:
        raise ValueError("URL is empty after sanitization")

    with concurrent.futures.ThreadPoolExecutor() as pool:
        if tier == 1:
            result = await loop.run_in_executor(pool, _sync_scrape_tier1, cleaned_url)
        else:
            result = await loop.run_in_executor(pool, _sync_scrape_full, cleaned_url)

    return result
