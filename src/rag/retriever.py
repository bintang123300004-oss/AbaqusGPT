"""Document retrieval from vector store"""
from typing import List, Dict
import logging
from ..indexer import VectorStore, Embedder

logger = logging.getLogger(__name__)


class Retriever:
    """
    Retrieve relevant documents from vector store
    """
    
    def __init__(self, vector_store: VectorStore, embedder: Embedder):
        """
        Initialize retriever
        
        Args:
            vector_store: Vector store instance
            embedder: Embedder instance
        """
        self.vector_store = vector_store
        self.embedder = embedder
    
    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Retrieve top-k relevant documents for a query
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            
        Returns:
            List of retrieved documents with metadata
        """
        logger.info(f"Retrieving documents for query: {query[:100]}...")
        
        # Generate query embedding
        query_embedding = self.embedder.embed_single(query)
        
        # Query vector store
        results = self.vector_store.query(
            query_embedding=query_embedding,
            n_results=top_k
        )
        
        # Format results
        documents = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                doc = {
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                }
                documents.append(doc)
        
        logger.info(f"Retrieved {len(documents)} documents")
        return documents
    
    def format_context(self, documents: List[Dict]) -> str:
        """
        Format retrieved documents into compact context string
        Optimized for speed - minimal formatting, essential info only
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            Compact formatted context string
        """
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            metadata = doc.get('metadata', {})
            title = metadata.get('title', 'Unknown')
            heading = metadata.get('heading', '')
            text = doc.get('text', '')
            
            # Compact format: just essential content
            # Remove URL from context (saves tokens, shown in sources anyway)
            doc_str = f"[{i}] {title}"
            if heading:
                doc_str += f" - {heading}"
            doc_str += f"\n{text}\n"
            
            context_parts.append(doc_str)
        
        return "\n---\n".join(context_parts)
    
    def get_sources(self, documents: List[Dict]) -> List[Dict]:
        """
        Extract source information from retrieved documents
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            List of source dictionaries (title, url)
        """
        sources = []
        seen_urls = set()
        
        for doc in documents:
            metadata = doc.get('metadata', {})
            url = metadata.get('url', '')
            title = metadata.get('title', 'Unknown')
            
            if url and url not in seen_urls:
                sources.append({
                    'title': title,
                    'url': url
                })
                seen_urls.add(url)
        
        return sources
