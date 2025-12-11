"""Data storage for scraped content"""
import json
import os
from typing import Dict, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DataStorage:
    """Handles storage of scraped documentation"""
    
    def __init__(self, output_dir: str = "data/scraped"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = self.output_dir / "abaqus_docs.jsonl"
        self.url_cache_file = self.output_dir / "visited_urls.txt"
        
        # Load already visited URLs
        self.visited_urls = self._load_visited_urls()
    
    def _load_visited_urls(self) -> set:
        """Load set of already visited URLs"""
        if self.url_cache_file.exists():
            with open(self.url_cache_file, 'r', encoding='utf-8') as f:
                return set(line.strip() for line in f)
        return set()
    
    def save_page(self, page_data: Dict) -> None:
        """
        Save a single page to JSONL file
        
        Args:
            page_data: Dictionary with page content
        """
        # Append to JSONL file
        with open(self.output_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(page_data, ensure_ascii=False) + '\n')
        
        # Add to visited URLs cache
        url = page_data.get('url')
        if url and url not in self.visited_urls:
            self.visited_urls.add(url)
            with open(self.url_cache_file, 'a', encoding='utf-8') as f:
                f.write(url + '\n')
        
        logger.info(f"Saved page: {page_data.get('title', 'Unknown')}")
    
    def is_visited(self, url: str) -> bool:
        """Check if URL has already been scraped"""
        return url in self.visited_urls
    
    def load_all_pages(self) -> List[Dict]:
        """Load all scraped pages from JSONL file"""
        pages = []
        
        if not self.output_file.exists():
            return pages
        
        with open(self.output_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    pages.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse line: {line[:100]}")
        
        return pages
    
    def get_stats(self) -> Dict:
        """Get statistics about scraped data"""
        pages = self.load_all_pages()
        
        total_pages = len(pages)
        total_text_length = sum(len(p.get('content', '')) for p in pages)
        total_code_blocks = sum(len(p.get('code_examples', [])) for p in pages)
        total_tables = sum(len(p.get('tables', [])) for p in pages)
        
        return {
            'total_pages': total_pages,
            'total_text_length': total_text_length,
            'total_code_blocks': total_code_blocks,
            'total_tables': total_tables,
            'visited_urls': len(self.visited_urls)
        }
