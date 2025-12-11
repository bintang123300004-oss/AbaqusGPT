"""ChromaDB vector store for document retrieval"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import logging
import os

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Vector database for storing and retrieving document chunks
    """
    
    def __init__(
        self,
        persist_directory: str = "./data/chroma_db",
        collection_name: str = "abaqus_docs"
    ):
        """
        Initialize ChromaDB vector store
        
        Args:
            persist_directory: Directory to persist the database
            collection_name: Name of the collection
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Create directory if needed
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize client
        logger.info(f"Initializing ChromaDB at {persist_directory}")
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Abaqus 2016 documentation chunks"}
        )
        
        logger.info(f"Collection '{collection_name}' initialized")
    
    def add_documents(
        self,
        chunks: List[Dict],
        embeddings: List[List[float]],
        batch_size: int = 100
    ) -> None:
        """
        Add documents to the vector store
        
        Args:
            chunks: List of chunk dictionaries with 'text' and 'metadata'
            embeddings: List of embedding vectors
            batch_size: Batch size for insertion
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")
        
        logger.info(f"Adding {len(chunks)} documents to vector store")
        
        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]
            
            # Prepare data
            ids = [f"doc_{i + j}" for j in range(len(batch_chunks))]
            documents = [chunk['text'] for chunk in batch_chunks]
            metadatas = [chunk['metadata'] for chunk in batch_chunks]
            
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=batch_embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            if (i + batch_size) % 500 == 0:
                logger.info(f"Added {i + batch_size}/{len(chunks)} documents")
        
        logger.info(f"Successfully added all {len(chunks)} documents")
    
    def query(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> Dict:
        """
        Query the vector store
        
        Args:
            query_embedding: Embedding vector of the query
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            Query results with documents, metadatas, and distances
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        return results
    
    def get_collection_count(self) -> int:
        """Get number of documents in collection"""
        return self.collection.count()
    
    def delete_collection(self) -> None:
        """Delete the entire collection"""
        self.client.delete_collection(self.collection_name)
        logger.info(f"Deleted collection '{self.collection_name}'")
    
    def reset_collection(self) -> None:
        """Reset collection (delete and recreate)"""
        self.delete_collection()
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Abaqus 2016 documentation chunks"}
        )
        logger.info(f"Reset collection '{self.collection_name}'")
