"""Playwright browser manager."""

import logging
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Playwright

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages Playwright browser lifecycle."""
    
    def __init__(self, headless: bool = True, timeout: int = 60000):
        """Initialize the browser manager.
        
        Args:
            headless: Run browser in headless mode
            timeout: Default timeout in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def start(self) -> None:
        """Start the browser with stealth configuration to bypass bot detection."""
        self.playwright = sync_playwright().start()

        # Stealth launch arguments to avoid detection
        launch_args = [
            "--disable-blink-features=AutomationControlled",  # Hide automation
            "--disable-dev-shm-usage",  # Avoid detection via /dev/shm
            "--no-sandbox",  # Often needed in containers
            "--disable-setuid-sandbox",
            "--disable-web-security",  # Disable CORS (optional)
            "--disable-features=IsolateOrigins,site-per-process",
        ]

        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=launch_args
        )

        # Create context with stealth properties
        self.context = self.browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York",
            permissions=["geolocation"],
            ignore_https_errors=True,
        )

        # Inject stealth scripts to mask automation flags
        self.context.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });

            // Override plugins to appear normal
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
                configurable: true
            });

            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
                configurable: true
            });

            // Hide automation flags
            window.navigator.chrome = {
                runtime: {}
            };

            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

        self.context.set_default_timeout(self.timeout)
        logger.info("Browser started with stealth configuration")
    
    def close(self) -> None:
        """Close the browser and cleanup."""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Browser closed")
    
    def fetch_page(self, url: str, scroll: bool = True) -> Page:
        """Fetch a page with full loading.
        
        Args:
            url: URL to fetch
            scroll: Whether to scroll to trigger lazy loading
            
        Returns:
            Playwright Page object
            
        Raises:
            Exception: If page cannot be loaded
        """
        if not self.context:
            raise RuntimeError("Browser not started. Call start() first.")
        
        logger.info(f"Fetching page: {url}")
        page = self.context.new_page()
        
        try:
            # Navigate to URL - wait for domcontentloaded (faster)
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)

            # Wait for Cloudflare challenge to complete (if present)
            try:
                # Check for Cloudflare challenge elements and wait for them to disappear
                page.wait_for_selector("#cf-challenge-running, .challenge-running", timeout=5000)
                logger.info("Detected Cloudflare challenge, waiting...")
                page.wait_for_selector("#cf-challenge-running, .challenge-running", state="hidden", timeout=30000)
            except Exception:
                pass  # No challenge present, continue

            # Try to wait for network idle, but don't fail if it times out
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
                logger.debug("Network idle achieved")
            except Exception as e:
                logger.warning(f"Network idle timeout (this is usually ok): {e}")
                # Wait a bit for content to load
                page.wait_for_timeout(2000)
            
            # Optional: Scroll to trigger lazy loading
            if scroll:
                self._scroll_page(page)
            
            logger.info(f"Page loaded successfully: {url}")
            return page
            
        except Exception as e:
            logger.error(f"Failed to fetch page {url}: {e}")
            page.close()
            raise
    
    def _scroll_page(self, page: Page) -> None:
        """Scroll page to trigger lazy loading.
        
        Args:
            page: Page to scroll
        """
        try:
            page.evaluate("""
                () => {
                    const scrollHeight = document.body.scrollHeight;
                    const steps = 5;
                    const stepSize = scrollHeight / steps;
                    
                    for (let i = 0; i <= steps; i++) {
                        window.scrollTo(0, stepSize * i);
                    }
                    
                    // Scroll back to top
                    window.scrollTo(0, 0);
                }
            """)
            
            # Give it a moment to load
            page.wait_for_timeout(500)
            
        except Exception as e:
            logger.warning(f"Failed to scroll page: {e}")
