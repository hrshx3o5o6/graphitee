"""Content extraction using Playwright DOM APIs."""

import logging
from typing import List, Tuple
from playwright.sync_api import Page, ElementHandle

from storage.models import ContentBlock, Link
from scraper.cleaner import DOMCleaner
from utils.url_utils import normalize_url, is_same_domain

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Extracts structured content from pages using Playwright."""
    
    # Content tags to extract
    HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
    PARAGRAPH_TAGS = {"p"}
    CODE_TAGS = {"pre", "code"}
    LIST_TAGS = {"ul", "ol", "li"}
    
    def __init__(self, page: Page):
        """Initialize the content extractor.
        
        Args:
            page: Playwright page
        """
        self.page = page
        self.base_url = page.url
    
    def extract_title(self) -> str:
        """Extract page title.
        
        Returns:
            Page title
        """
        try:
            title = self.page.title()
            logger.info(f"Extracted title: {title}")
            return title
        except Exception as e:
            logger.error(f"Failed to extract title: {e}")
            return "Untitled"
    
    def extract_content_blocks(self) -> List[ContentBlock]:
        """Extract all content blocks in reading order.
        
        Returns:
            List of content blocks
        """
        logger.info("Extracting content blocks")
        
        # Find main content area
        main_content = DOMCleaner.find_main_content(self.page)
        
        if not main_content:
            logger.warning("Could not find main content, using body")
            main_content = self.page.query_selector("body")
        
        if not main_content:
            logger.error("No content found")
            return []
        
        # Extract blocks
        blocks = []
        position = 0
        
        # Get all content elements in order
        elements = main_content.query_selector_all(
            "h1, h2, h3, h4, h5, h6, p, pre, code, ul, ol"
        )
        
        for element in elements:
            # Skip if should be ignored
            if DOMCleaner.should_ignore_element(element):
                continue
            
            block = self._extract_block(element, position)
            if block:
                blocks.append(block)
                position += 1
        
        logger.info(f"Extracted {len(blocks)} content blocks")
        return blocks
    
    def _extract_block(
        self,
        element: ElementHandle,
        position: int
    ) -> ContentBlock | None:
        """Extract a single content block from an element.
        
        Args:
            element: Element to extract from
            position: Position in document
            
        Returns:
            ContentBlock or None
        """
        try:
            tag = element.evaluate("el => el.tagName.toLowerCase()")
            text = element.inner_text()
            
            # Skip empty blocks
            if not text or not text.strip():
                return None
            
            # Determine block type
            if tag in self.HEADING_TAGS:
                block_type = "heading"
            elif tag in self.CODE_TAGS:
                block_type = "code"
            elif tag in self.LIST_TAGS:
                block_type = "list"
            elif tag in self.PARAGRAPH_TAGS:
                block_type = "paragraph"
            else:
                # Default to paragraph for unknown tags
                block_type = "paragraph"
            
            return ContentBlock(
                type=block_type,
                tag=tag,
                text=text.strip(),
                position=position
            )
            
        except Exception as e:
            logger.debug(f"Failed to extract block: {e}")
            return None
    
    def extract_links(self, doc_id: str) -> List[Link]:
        """Extract all links from the main content area.
        
        Args:
            doc_id: Source document ID
            
        Returns:
            List of extracted links
        """
        logger.info("Extracting links")
        
        # Find main content area
        main_content = DOMCleaner.find_main_content(self.page)
        
        if not main_content:
            main_content = self.page.query_selector("body")
        
        if not main_content:
            return []
        
        links = []
        
        # Find all anchor tags
        anchor_elements = main_content.query_selector_all("a")
        
        for anchor in anchor_elements:
            link = self._extract_link(anchor, doc_id)
            if link:
                links.append(link)
        
        logger.info(f"Extracted {len(links)} links")
        return links
    
    def _extract_link(
        self,
        anchor: ElementHandle,
        doc_id: str
    ) -> Link | None:
        """Extract a single link from an anchor element.
        
        Args:
            anchor: Anchor element
            doc_id: Source document ID
            
        Returns:
            Link or None
        """
        try:
            href = anchor.get_attribute("href")
            
            if not href:
                return None
            
            # Normalize URL
            target_url = normalize_url(href, self.base_url)
            
            # Get anchor text
            anchor_text = anchor.inner_text() or ""
            anchor_text = anchor_text.strip()
            
            # Determine if internal
            is_internal = is_same_domain(self.base_url, target_url)
            
            return Link(
                source_doc_id=doc_id,
                target_url=target_url,
                anchor_text=anchor_text,
                is_internal=is_internal
            )
            
        except Exception as e:
            logger.debug(f"Failed to extract link: {e}")
            return None
