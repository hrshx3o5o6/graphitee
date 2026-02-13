"""URL utilities for normalization and validation."""

from urllib.parse import urlparse, urljoin, urlunparse
import logging

logger = logging.getLogger(__name__)


def normalize_url(url: str, base_url: str = "") -> str:
    """Normalize a URL by converting relative to absolute and removing fragments.
    
    Args:
        url: URL to normalize
        base_url: Base URL for resolving relative URLs
        
    Returns:
        Normalized absolute URL
    """
    # Convert relative to absolute
    if base_url:
        url = urljoin(base_url, url)
    
    # Parse URL
    parsed = urlparse(url)
    
    # Remove fragment
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        parsed.query,
        ""  # Remove fragment
    ))
    
    return normalized


def get_domain(url: str) -> str:
    """Extract domain from URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain name
    """
    parsed = urlparse(url)
    return parsed.netloc


def is_same_domain(url1: str, url2: str) -> bool:
    """Check if two URLs are from the same domain.
    
    Args:
        url1: First URL
        url2: Second URL
        
    Returns:
        True if same domain
    """
    return get_domain(url1) == get_domain(url2)


def is_valid_url(url: str) -> bool:
    """Check if URL is valid (has scheme and netloc).
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid
    """
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except Exception as e:
        logger.warning(f"Invalid URL {url}: {e}")
        return False


def remove_tracking_params(url: str) -> str:
    """Remove common tracking parameters from URL.
    
    Args:
        url: URL with potential tracking params
        
    Returns:
        Clean URL
    """
    parsed = urlparse(url)
    
    if not parsed.query:
        return url
    
    # Common tracking parameters to remove
    tracking_params = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'fbclid', 'gclid', 'msclkid', 'ref', 'source'
    }
    
    # Parse query string
    from urllib.parse import parse_qs, urlencode
    params = parse_qs(parsed.query)
    
    # Filter out tracking params
    clean_params = {
        k: v for k, v in params.items()
        if k not in tracking_params
    }
    
    # Rebuild URL
    clean_query = urlencode(clean_params, doseq=True)
    
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        clean_query,
        ""
    ))
