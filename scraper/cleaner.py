"""DOM cleaning using Playwright."""

import logging
from typing import Optional
from playwright.sync_api import Page, ElementHandle

logger = logging.getLogger(__name__)


class DOMCleaner:
    """Handles DOM cleaning and content area identification."""
    
    # Elements to remove/ignore
    UNWANTED_SELECTORS = [
        "nav", "footer", "header", "aside",
        ".advertisement", ".ad", ".ads",
        ".social-share", ".share-buttons",
        ".comments", ".comment-section",
        "script", "style", "noscript",
        "[role='navigation']",
        "[role='complementary']",
    ]
    
    # Preferred content containers
    CONTENT_SELECTORS = [
        "article",
        "main",
        "[role='main']",
        ".article-content",
        ".post-content",
        ".entry-content",
    ]
    
    @staticmethod
    def find_main_content(page: Page) -> Optional[ElementHandle]:
        """Find the main content container using Playwright.
        
        Args:
            page: Playwright page
            
        Returns:
            ElementHandle of main content area or None
        """
        logger.info("Finding main content area")
        
        # Try preferred content selectors first
        for selector in DOMCleaner.CONTENT_SELECTORS:
            try:
                element = page.query_selector(selector)
                if element:
                    logger.info(f"Found content using selector: {selector}")
                    return element
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
        
        # Fallback: find element with highest text density
        logger.info("Using text density heuristic")
        return DOMCleaner._find_by_text_density(page)
    
    @staticmethod
    def _find_by_text_density(page: Page) -> Optional[ElementHandle]:
        """Find content area by text density heuristic.
        
        Args:
            page: Playwright page
            
        Returns:
            ElementHandle with highest text density
        """
        try:
            # Use JavaScript to find element with most text content
            result = page.evaluate("""
                () => {
                    const candidates = document.querySelectorAll('div, section, article, main');
                    let bestElement = null;
                    let maxDensity = 0;
                    
                    candidates.forEach(el => {
                        const text = el.innerText || '';
                        const textLength = text.length;
                        const childCount = el.querySelectorAll('*').length || 1;
                        const density = textLength / childCount;
                        
                        if (density > maxDensity && textLength > 500) {
                            maxDensity = density;
                            bestElement = el;
                        }
                    });
                    
                    if (bestElement) {
                        bestElement.setAttribute('data-main-content', 'true');
                        return true;
                    }
                    return false;
                }
            """)
            
            if result:
                return page.query_selector('[data-main-content="true"]')
            
        except Exception as e:
            logger.error(f"Text density heuristic failed: {e}")
        
        return None
    
    @staticmethod
    def should_ignore_element(element: ElementHandle) -> bool:
        """Check if an element should be ignored during extraction.
        
        Args:
            element: Element to check
            
        Returns:
            True if element should be ignored
        """
        try:
            tag_name = element.evaluate("el => el.tagName.toLowerCase()")
            
            # Check against unwanted tags
            unwanted_tags = ['nav', 'footer', 'header', 'aside', 'script', 'style', 'noscript']
            if tag_name in unwanted_tags:
                return True
            
            # Check class names
            class_name = element.evaluate("el => el.className") or ""
            unwanted_classes = ['ad', 'advertisement', 'social', 'share', 'comment']
            
            if any(cls in class_name.lower() for cls in unwanted_classes):
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Error checking element: {e}")
            return False
