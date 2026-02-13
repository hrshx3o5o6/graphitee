"""Main execution script for the semantic article ingestion system."""

import argparse
import logging
import sys
from typing import List

from scraper.browser import BrowserManager
from scraper.crawler import Crawler
from scraper.section_builder import SectionBuilder
from storage.json_store import JSONStore
from storage.models import Document


def setup_logging(debug: bool = False) -> None:
    """Setup logging configuration.
    
    Args:
        debug: Enable debug logging
    """
    level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def print_document_summary(doc: Document, debug: bool = False) -> None:
    """Print a summary of an extracted document.
    
    Args:
        doc: Document to summarize
        debug: Print detailed debug info
    """
    print(f"\n{'='*70}")
    print(f"Document: {doc.title}")
    print(f"URL: {doc.url}")
    print(f"Depth: {doc.depth}")
    if doc.parent_url:
        print(f"Parent: {doc.parent_url}")
    print(f"Sections: {len(doc.sections)}")
    print(f"Links: {len(doc.links)} ({sum(1 for l in doc.links if l.is_internal)} internal)")
    
    if debug:
        print(f"\nSection Structure:")
        print_section_structure(doc.sections, indent=0)
        
        print(f"\nInternal Links:")
        for link in [l for l in doc.links if l.is_internal][:10]:
            print(f"  - {link.anchor_text[:50]} -> {link.target_url}")
        
        if len([l for l in doc.links if l.is_internal]) > 10:
            print(f"  ... and {len([l for l in doc.links if l.is_internal]) - 10} more")


def print_section_structure(sections: List, indent: int = 0) -> None:
    """Print section structure recursively.
    
    Args:
        sections: Sections to print
        indent: Current indentation level
    """
    for section in sections:
        prefix = "  " * indent
        print(
            f"{prefix}[{section.section_id}] "
            f"H{section.level}: {section.heading} "
            f"({len(section.content_blocks)} blocks)"
        )
        
        if section.children:
            print_section_structure(section.children, indent + 1)


def print_crawl_summary(documents: List[Document]) -> None:
    """Print a summary of the crawl results.
    
    Args:
        documents: Crawled documents
    """
    print(f"\n{'='*70}")
    print("CRAWL SUMMARY")
    print(f"{'='*70}")
    print(f"Total documents: {len(documents)}")
    print(f"Total sections: {sum(len(doc.sections) for doc in documents)}")
    print(f"Total links: {sum(len(doc.links) for doc in documents)}")
    
    # Depth distribution
    depths = {}
    for doc in documents:
        depths[doc.depth] = depths.get(doc.depth, 0) + 1
    
    print("\nDepth distribution:")
    for depth in sorted(depths.keys()):
        print(f"  Depth {depth}: {depths[depth]} documents")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Semantic article ingestion system using Playwright"
    )
    
    parser.add_argument(
        "url",
        help="Root URL to crawl"
    )
    
    parser.add_argument(
        "--depth",
        type=int,
        default=1,
        help="Maximum crawl depth (default: 1)"
    )
    
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Maximum number of pages to crawl (default: 5)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )
    
    parser.add_argument(
        "--headless",
        type=bool,
        default=True,
        help="Run browser in headless mode (default: True)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting semantic article ingestion from {args.url}")
    
    try:
        # Initialize storage
        store = JSONStore()
        
        # Initialize browser and crawler
        with BrowserManager(headless=args.headless) as browser:
            crawler = Crawler(
                browser_manager=browser,
                max_depth=args.depth,
                max_pages=args.max_pages
            )
            
            # Crawl
            documents = crawler.crawl(args.url)
            
            # Save documents
            logger.info(f"Saving {len(documents)} documents")
            for doc in documents:
                store.save_document(doc)
                
                if args.debug:
                    print_document_summary(doc, debug=True)
            
            # Print summary
            if not args.debug:
                for doc in documents:
                    print_document_summary(doc, debug=False)
            
            print_crawl_summary(documents)
            
        logger.info("Ingestion complete")
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
