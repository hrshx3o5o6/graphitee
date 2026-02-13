"""Controlled web crawler for internal links."""

import logging
from typing import Set, List
from playwright.sync_api import Page

from storage.models import Document, Link
from scraper.browser import BrowserManager
from scraper.extractor import ContentExtractor
from scraper.section_builder import SectionBuilder
from utils.url_utils import get_domain, is_valid_url, remove_tracking_params

logger = logging.getLogger(__name__)


class Crawler:
    """Controlled crawler for internal links."""
    
    def __init__(
        self,
        browser_manager: BrowserManager,
        max_depth: int = 1,
        max_pages: int = 5
    ):
        """Initialize the crawler.
        
        Args:
            browser_manager: Browser manager instance
            max_depth: Maximum crawl depth
            max_pages: Maximum number of pages to crawl
        """
        self.browser_manager = browser_manager
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.visited: Set[str] = set()
        self.documents: List[Document] = []
    
    def crawl(self, root_url: str) -> List[Document]:
        """Crawl from root URL following internal links.
        
        Args:
            root_url: Starting URL
            
        Returns:
            List of extracted documents
        """
        logger.info(
            f"Starting crawl from {root_url} "
            f"(max_depth={self.max_depth}, max_pages={self.max_pages})"
        )
        
        # Reset state
        self.visited.clear()
        self.documents.clear()
        
        # Start crawling
        self._crawl_recursive(root_url, depth=0, parent_url=None)
        
        logger.info(f"Crawl complete. Extracted {len(self.documents)} documents")
        return self.documents
    
    def _crawl_recursive(
        self,
        url: str,
        depth: int,
        parent_url: str | None
    ) -> None:
        """Recursively crawl a URL and its internal links.
        
        Args:
            url: URL to crawl
            depth: Current depth
            parent_url: Parent URL (for tracking)
        """
        # Check limits
        if depth > self.max_depth:
            logger.debug(f"Max depth reached for {url}")
            return
        
        if len(self.documents) >= self.max_pages:
            logger.info(f"Max pages reached ({self.max_pages})")
            return
        
        # Clean URL
        clean_url = remove_tracking_params(url)
        
        # Check if already visited
        if clean_url in self.visited:
            logger.debug(f"Already visited {clean_url}")
            return
        
        # Validate URL
        if not is_valid_url(clean_url):
            logger.warning(f"Invalid URL: {clean_url}")
            return
        
        # Mark as visited
        self.visited.add(clean_url)
        
        # Extract document
        try:
            doc = self._extract_document(clean_url, depth, parent_url)
            if doc:
                self.documents.append(doc)
                
                # Crawl internal links if within depth limit
                if depth < self.max_depth:
                    self._crawl_internal_links(doc, depth + 1)
                    
        except Exception as e:
            logger.error(f"Failed to extract {clean_url}: {e}")
    
    def _extract_document(
        self,
        url: str,
        depth: int,
        parent_url: str | None
    ) -> Document | None:
        """Extract a document from a URL.
        
        Args:
            url: URL to extract
            depth: Current depth
            parent_url: Parent URL
            
        Returns:
            Extracted Document or None
        """
        logger.info(f"Extracting document: {url} (depth={depth})")
        
        try:
            # Fetch page
            page = self.browser_manager.fetch_page(url)
            
            # Extract content
            extractor = ContentExtractor(page)
            
            title = extractor.extract_title()
            blocks = extractor.extract_content_blocks()
            
            # Build sections
            sections = SectionBuilder.build_sections(blocks)
            
            # Create document
            domain = get_domain(url)
            doc = Document.create(
                url=url,
                title=title,
                domain=domain,
                depth=depth,
                parent_url=parent_url
            )
            
            doc.sections = sections
            
            # Extract links
            doc.links = extractor.extract_links(doc.id)
            
            # Close page
            page.close()
            
            logger.info(
                f"Extracted document '{title}': "
                f"{len(sections)} sections, {len(doc.links)} links"
            )
            
            return doc
            
        except Exception as e:
            logger.error(f"Failed to extract document from {url}: {e}")
            return None
    
    def _crawl_internal_links(self, doc: Document, next_depth: int) -> None:
        """Crawl internal links from a document.
        
        Args:
            doc: Source document
            next_depth: Depth for child pages
        """
        # Filter internal links
        internal_links = [
            link for link in doc.links
            if link.is_internal
        ]
        
        logger.info(
            f"Found {len(internal_links)} internal links in {doc.url}"
        )
        
        # Crawl each internal link
        for link in internal_links:
            # Check page limit
            if len(self.documents) >= self.max_pages:
                break
            
            self._crawl_recursive(
                url=link.target_url,
                depth=next_depth,
                parent_url=doc.url
            )
