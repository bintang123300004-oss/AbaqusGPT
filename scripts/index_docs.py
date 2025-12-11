"""Script to index scraped documentation into vector store"""
import os
import sys
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scraper import DataStorage
from src.indexer import TextChunker, Embedder, VectorStore
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Index scraped documentation"""
    print("=" * 60)
    print("Abaqus Documentation Indexer")
    print("=" * 60)
    
    # Load configuration
    chunk_size = int(os.getenv('CHUNK_SIZE', '1000'))
    chunk_overlap = int(os.getenv('CHUNK_OVERLAP', '200'))
    embedding_model = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    persist_dir = os.getenv('CHROMA_PERSIST_DIR', './data/chroma_db')
    collection_name = os.getenv('COLLECTION_NAME', 'abaqus_docs')
    
    print(f"Chunk size: {chunk_size}")
    print(f"Chunk overlap: {chunk_overlap}")
    print(f"Embedding model: {embedding_model}")
    print(f"Vector DB: {persist_dir}")
    print("=" * 60)
    
    # 1. Load scraped data
    print("\n[1/5] Loading scraped data...")
    storage = DataStorage()
    pages = storage.load_all_pages()
    
    if not pages:
        print("ERROR: No scraped data found!")
        print("Please run the scraper first: python scripts/scrape.py")
        return
    
    print(f"Loaded {len(pages)} pages")
    
    # 2. Chunk documents
    print("\n[2/5] Chunking documents...")
    chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    all_chunks = []
    for page in tqdm(pages, desc="Chunking pages"):
        chunks = chunker.chunk_page(page)
        all_chunks.extend(chunks)
    
    print(f"Created {len(all_chunks)} chunks from {len(pages)} pages")
    
    # 3. Initialize embedder
    print("\n[3/5] Initializing embedding model...")
    embedder = Embedder(model_name=embedding_model)
    
    # 4. Generate embeddings
    print("\n[4/5] Generating embeddings...")
    chunk_texts = [chunk['text'] for chunk in all_chunks]
    embeddings = embedder.embed_texts(chunk_texts, batch_size=32)
    
    print(f"Generated {len(embeddings)} embeddings")
    
    # 5. Store in vector database
    print("\n[5/5] Storing in vector database...")
    vector_store = VectorStore(
        persist_directory=persist_dir,
        collection_name=collection_name
    )
    
    # Check if collection already has data
    existing_count = vector_store.get_collection_count()
    if existing_count > 0:
        print(f"\nWARNING: Collection already contains {existing_count} documents.")
        response = input("Do you want to reset and rebuild? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            vector_store.reset_collection()
        else:
            print("Aborted. Existing data preserved.")
            return
    
    # Add documents
    vector_store.add_documents(chunks=all_chunks, embeddings=embeddings)
    
    final_count = vector_store.get_collection_count()
    
    print("\n" + "=" * 60)
    print("INDEXING COMPLETE!")
    print("=" * 60)
    print(f"Total documents indexed: {final_count}")
    print(f"Vector database: {persist_dir}")
    print("\nYou can now start the API server:")
    print("  python -m uvicorn src.api.main:app --reload")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nIndexing interrupted by user.")
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
