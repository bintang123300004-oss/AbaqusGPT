"""HTML content parser for Abaqus documentation"""
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import re


class ContentParser:
    """Parses HTML content and extracts structured data"""
    
    def __init__(self):
        self.soup = None
    
    def parse(self, html_content: str, url: str) -> Dict:
        """
        Parse HTML and extract all relevant content
        
        Args:
            html_content: Raw HTML string
            url: URL of the page
            
        Returns:
            Dictionary with extracted content
        """
        self.soup = BeautifulSoup(html_content, 'lxml')
        
        return {
            'url': url,
            'title': self._extract_title(),
            'content': self._extract_main_content(),
            'code_examples': self._extract_code_blocks(),
            'tables': self._extract_tables(),
            'headings': self._extract_headings(),
            'metadata': self._extract_metadata()
        }
    
    def _extract_title(self) -> str:
        """Extract page title"""
        # Try multiple possible title locations
        title = self.soup.find('title')
        if title:
            return title.get_text().strip()
        
        # Try h1
        h1 = self.soup.find('h1')
        if h1:
            return h1.get_text().strip()
        
        return "Untitled"
    
    def _extract_main_content(self) -> str:
        """Extract main text content, preserving structure"""
        # Remove script and style elements
        for script in self.soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Find main content area (Abaqus docs usually in specific divs/tables)
        main_content = None
        
        # Try common content containers
        for selector in ['#main', '.content', 'body']:
            main_content = self.soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            main_content = self.soup.body if self.soup.body else self.soup
        
        # Extract text while preserving some structure
        text = main_content.get_text(separator='\n', strip=True)
        
        # Clean up excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def _extract_code_blocks(self) -> List[Dict]:
        """Extract code examples and input file snippets"""
        code_blocks = []
        
        # Find pre, code tags
        for tag_name in ['pre', 'code']:
            for tag in self.soup.find_all(tag_name):
                code_text = tag.get_text().strip()
                if code_text and len(code_text) > 10:  # Filter out tiny snippets
                    code_blocks.append({
                        'type': tag_name,
                        'content': code_text,
                        'language': tag.get('class', [''])[0] if tag.get('class') else 'unknown'
                    })
        
        return code_blocks
    
    def _extract_tables(self) -> List[Dict]:
        """Extract tables with their content"""
        tables = []
        
        for table in self.soup.find_all('table'):
            # Extract table as text
            rows = []
            for tr in table.find_all('tr'):
                cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append(cells)
            
            if rows:
                tables.append({
                    'rows': rows,
                    'text': '\n'.join([' | '.join(row) for row in rows])
                })
        
        return tables
    
    def _extract_headings(self) -> List[Dict]:
        """Extract all headings for structure"""
        headings = []
        
        for level in range(1, 7):
            for heading in self.soup.find_all(f'h{level}'):
                text = heading.get_text().strip()
                if text:
                    headings.append({
                        'level': level,
                        'text': text
                    })
        
        return headings
    
    def _extract_metadata(self) -> Dict:
        """Extract metadata from page"""
        metadata = {}
        
        # Meta tags
        for meta in self.soup.find_all('meta'):
            name = meta.get('name', meta.get('property', ''))
            content = meta.get('content', '')
            if name and content:
                metadata[name] = content
        
        return metadata
    
    def is_valid_documentation_page(self) -> bool:
        """
        Check if page contains actual documentation content
        (not just navigation/index pages)
        """
        if not self.soup:
            return False
        
        # Check for substantial content
        text = self.soup.get_text()
        
        # Must have reasonable amount of text
        if len(text.strip()) < 200:
            return False
        
        # Should have some headings
        if not self.soup.find(['h1', 'h2', 'h3']):
            return False
        
        return True
