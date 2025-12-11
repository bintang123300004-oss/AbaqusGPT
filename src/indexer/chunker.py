"""Text chunking for documentation"""
from typing import List, Dict
import re


class TextChunker:
    """
    Intelligent text chunking that preserves context
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_page(self, page_data: Dict) -> List[Dict]:
        """
        Chunk a single page into smaller segments
        
        Args:
            page_data: Page data from scraper
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        
        # Extract basic info
        url = page_data.get('url', '')
        title = page_data.get('title', 'Untitled')
        content = page_data.get('content', '')
        headings = page_data.get('headings', [])
        code_examples = page_data.get('code_examples', [])
        tables = page_data.get('tables', [])
        
        # Chunk main content by headings first
        heading_chunks = self._chunk_by_headings(content, headings)
        
        # Further split large chunks
        for heading_chunk in heading_chunks:
            text = heading_chunk['text']
            heading = heading_chunk.get('heading', '')
            
            if len(text) <= self.chunk_size:
                # Small enough, keep as is
                chunks.append({
                    'text': text,
                    'metadata': {
                        'url': url,
                        'title': title,
                        'heading': heading,
                        'type': 'text'
                    }
                })
            else:
                # Split into smaller chunks
                sub_chunks = self._split_text(text)
                for i, sub_chunk in enumerate(sub_chunks):
                    chunks.append({
                        'text': sub_chunk,
                        'metadata': {
                            'url': url,
                            'title': title,
                            'heading': heading,
                            'chunk_index': i,
                            'type': 'text'
                        }
                    })
        
        # Add code examples as separate chunks
        for i, code in enumerate(code_examples):
            code_text = code.get('content', '')
            if code_text:
                chunks.append({
                    'text': f"Code example:\n{code_text}",
                    'metadata': {
                        'url': url,
                        'title': title,
                        'type': 'code',
                        'language': code.get('language', 'unknown'),
                        'code_index': i
                    }
                })
        
        # Add tables as chunks
        for i, table in enumerate(tables):
            table_text = table.get('text', '')
            if table_text:
                chunks.append({
                    'text': f"Table:\n{table_text}",
                    'metadata': {
                        'url': url,
                        'title': title,
                        'type': 'table',
                        'table_index': i
                    }
                })
        
        return chunks
    
    def _chunk_by_headings(self, content: str, headings: List[Dict]) -> List[Dict]:
        """Split content by headings when possible"""
        if not headings:
            return [{'text': content, 'heading': ''}]
        
        chunks = []
        lines = content.split('\n')
        
        # Find heading positions
        heading_texts = [h['text'] for h in headings]
        current_heading = ''
        current_chunk = []
        
        for line in lines:
            # Check if this line is a heading
            is_heading = False
            for heading_text in heading_texts:
                if heading_text.strip() in line.strip():
                    # Save previous chunk
                    if current_chunk:
                        chunks.append({
                            'text': '\n'.join(current_chunk),
                            'heading': current_heading
                        })
                    
                    # Start new chunk
                    current_heading = heading_text
                    current_chunk = [line]
                    is_heading = True
                    break
            
            if not is_heading:
                current_chunk.append(line)
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'text': '\n'.join(current_chunk),
                'heading': current_heading
            })
        
        return chunks if chunks else [{'text': content, 'heading': ''}]
    
    def _split_text(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap
        Tries to split on sentence/paragraph boundaries
        """
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))
                
                # Start new chunk with overlap
                # Keep last few sentences for context
                overlap_sentences = []
                overlap_length = 0
                
                for sent in reversed(current_chunk):
                    if overlap_length + len(sent) <= self.chunk_overlap:
                        overlap_sentences.insert(0, sent)
                        overlap_length += len(sent)
                    else:
                        break
                
                current_chunk = overlap_sentences
                current_length = overlap_length
            
            current_chunk.append(sentence)
            current_length += sentence_length
        
        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def chunk_all_pages(self, pages: List[Dict]) -> List[Dict]:
        """Chunk all pages"""
        all_chunks = []
        
        for page in pages:
            chunks = self.chunk_page(page)
            all_chunks.extend(chunks)
        
        return all_chunks
