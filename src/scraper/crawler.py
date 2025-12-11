"""Web crawler for Abaqus documentation"""
import requests
from urllib.parse import urljoin, urlparse, urldefrag
from typing import Set, List, Optional
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, Empty
import threading

from .parser import ContentParser
from .storage import DataStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AbaqusCrawler:
    """
    Comprehensive crawler for Abaqus documentation
    Recursively crawls all documentation pages
    """
    
    def __init__(
        self,
        base_url: str,
        max_workers: int = 5,
        request_delay: float = 0.5,
        output_dir: str = "data/scraped"
    ):
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.base_path = self._get_base_path(base_url)
        
        self.max_workers = max_workers
        self.request_delay = request_delay
        
        # Initialize components
        self.parser = ContentParser()
        self.storage = DataStorage(output_dir)
        
        # Track URLs
        self.to_visit = Queue()
        self.visited = set()
        self.failed = set()
        self.lock = threading.Lock()
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Statistics
        self.stats = {
            'pages_scraped': 0,
            'pages_failed': 0,
            'urls_found': 0
        }
    
    def _get_base_path(self, url: str) -> str:
        """Extract base path from URL (e.g., /v2016/)"""
        parsed = urlparse(url)
        path_parts = parsed.path.rstrip('/').split('/')
        if len(path_parts) > 1:
            return '/' + path_parts[1] + '/'
        return '/'
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Check if URL should be crawled
        - Must be same domain
        - Must be within documentation path
        - Must be HTML (not PDF, images, etc.)
        - ENHANCED: Accepts ALL documentation paths (books, guides, references, etc.)
        """
        parsed = urlparse(url)
        
        # Same domain
        if parsed.netloc and parsed.netloc != self.base_domain:
            return False
        
        # Within documentation path - EXPANDED to catch everything
        # Accept any path under /v2016/ to get ALL documentation
        if not parsed.path.startswith(self.base_path):
            return False
        
        # Skip non-HTML resources (but allow .htm, .html, no extension)
        skip_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.css', '.js', '.zip', '.tar', '.gz', '.xml']
        if any(parsed.path.lower().endswith(ext) for ext in skip_extensions):
            return False
        
        # Skip specific patterns (minimal - we want EVERYTHING)
        skip_patterns = ['javascript:', 'mailto:', 'texis/search']
        if any(pattern in url.lower() for pattern in skip_patterns):
            return False
        
        # Log which sections we're crawling to verify breadth
        if '/books/' in parsed.path:
            logger.debug(f"Crawling book section: {parsed.path}")
        
        return True
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL (remove fragments, trailing slashes, etc.)"""
        # Remove fragment
        url, _ = urldefrag(url)
        
        # Remove trailing slash for comparison
        url = url.rstrip('/')
        
        return url
    
    def _extract_links(self, html_content: str, current_url: str) -> List[str]:
        """Extract all valid links from HTML content"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'lxml')
        links = []
        
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            
            # Make absolute URL
            absolute_url = urljoin(current_url, href)
            
            # Normalize
            normalized_url = self._normalize_url(absolute_url)
            
            # Validate
            if self._is_valid_url(normalized_url):
                links.append(normalized_url)
        
        return links
    
    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a single page"""
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type.lower():
                logger.warning(f"Non-HTML content: {url} ({content_type})")
                return None
            
            return response.text
        
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def _process_page(self, url: str) -> None:
        """Process a single page: fetch, parse, extract links, save"""
        
        # Fetch HTML
        html_content = self._fetch_page(url)
        if not html_content:
            with self.lock:
                self.failed.add(url)
                self.stats['pages_failed'] += 1
            return
        
        # Parse content
        page_data = self.parser.parse(html_content, url)
        
        # Check if valid documentation page
        self.parser.soup = None  # Reset parser
        from bs4 import BeautifulSoup
        self.parser.soup = BeautifulSoup(html_content, 'lxml')
        
        if self.parser.is_valid_documentation_page():
            # Save page
            self.storage.save_page(page_data)
            
            with self.lock:
                self.stats['pages_scraped'] += 1
        else:
            logger.info(f"Skipping non-content page: {url}")
        
        # Extract links
        links = self._extract_links(html_content, url)
        
        # Add new links to queue
        new_links = 0
        with self.lock:
            for link in links:
                if link not in self.visited and link not in self.failed:
                    self.to_visit.put(link)
                    self.visited.add(link)
                    new_links += 1
            
            self.stats['urls_found'] += new_links
        
        logger.info(f"Found {new_links} new links from {url}")
        
        # If this is a frameset default.htm, also fetch and parse toc.js
        if url.endswith('/default.htm'):
            self._process_toc_file(url)
        
        # Respectful delay
        time.sleep(self.request_delay)
    
    def _process_toc_file(self, default_htm_url: str) -> None:
        """Fetch and parse toc.js file from the same directory as default.htm"""
        import re
        
        # Construct toc.js URL (same directory as default.htm)
        toc_url = default_htm_url.replace('/default.htm', '/toc.js')
        
        try:
            logger.info(f"Fetching TOC file: {toc_url}")
            response = self.session.get(toc_url, timeout=30)
            response.raise_for_status()
            
            # Extract all .html file references from the JavaScript
            # Pattern matches strings like "ch13abk03.html" in the toc.js arrays
            html_files = re.findall(r'"([^"]+\.html?(?:#[^"]*)?)"', response.text)
            
            # Construct full URLs and add to queue
            base_dir = default_htm_url.rsplit('/', 1)[0]
            new_links = 0
            
            with self.lock:
                for html_file in html_files:
                    # Remove anchor if present for URL construction
                    file_name = html_file.split('#')[0]
                    full_url = f"{base_dir}/{file_name}"
                    normalized_url = self._normalize_url(full_url)
                    
                    if normalized_url not in self.visited and normalized_url not in self.failed:
                        self.to_visit.put(normalized_url)
                        self.visited.add(normalized_url)
                        new_links += 1
                
                self.stats['urls_found'] += new_links
            
            logger.info(f"Found {new_links} content pages from {toc_url}")
            
        except requests.RequestException as e:
            logger.warning(f"Could not fetch toc.js at {toc_url}: {e}")
    
    def crawl(self) -> None:
        """
        Start crawling from base URL
        Uses breadth-first search with multiple workers
        """
        logger.info(f"Starting crawl from: {self.base_url}")
        logger.info(f"Using {self.max_workers} workers")
        
        # Add base URL to queue
        self.to_visit.put(self.base_url)
        self.visited.add(self.base_url)
        
        # Worker function
        def worker():
            while True:
                try:
                    url = self.to_visit.get(timeout=5)
                    
                    # Skip if already scraped (from previous runs)
                    if self.storage.is_visited(url):
                        logger.info(f"Already scraped (cached): {url}")
                        self.to_visit.task_done()
                        continue
                    
                    self._process_page(url)
                    self.to_visit.task_done()
                    
                except Empty:
                    # Queue is empty, might be done
                    break
                except Exception as e:
                    logger.error(f"Worker error: {e}")
                    self.to_visit.task_done()
        
        # Start workers
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(worker) for _ in range(self.max_workers)]
            
            # Monitor progress
            while True:
                time.sleep(5)
                queue_size = self.to_visit.qsize()
                
                with self.lock:
                    logger.info(
                        f"Progress - Queue: {queue_size}, "
                        f"Scraped: {self.stats['pages_scraped']}, "
                        f"Failed: {self.stats['pages_failed']}, "
                        f"URLs found: {self.stats['urls_found']}"
                    )
                
                # Check if all workers are done
                if queue_size == 0 and all(f.done() for f in futures):
                    break
        
        logger.info("Crawling complete!")
        self._print_final_stats()
    
    def _print_final_stats(self):
        """Print final crawling statistics"""
        storage_stats = self.storage.get_stats()
        
        logger.info("=" * 60)
        logger.info("CRAWLING COMPLETE - Final Statistics")
        logger.info("=" * 60)
        logger.info(f"Total pages scraped: {self.stats['pages_scraped']}")
        logger.info(f"Total pages failed: {self.stats['pages_failed']}")
        logger.info(f"Total URLs found: {self.stats['urls_found']}")
        logger.info(f"Total unique URLs visited: {len(self.visited)}")
        logger.info("-" * 60)
        logger.info(f"Stored pages: {storage_stats['total_pages']}")
        logger.info(f"Total text length: {storage_stats['total_text_length']:,} chars")
        logger.info(f"Total code blocks: {storage_stats['total_code_blocks']}")
        logger.info(f"Total tables: {storage_stats['total_tables']}")
        logger.info("=" * 60)
        logger.info("Scraped sections include:")
        logger.info("   - User Guides (CAE, Analysis, Scripting, etc.)")
        logger.info("   - Reference Manuals (Keywords, Theory, Verification)")
        logger.info("   - Example Problems and Benchmarks")
        logger.info("   - Tutorials and Getting Started")
        logger.info("   - Installation and Licensing")
        logger.info("=" * 60)
