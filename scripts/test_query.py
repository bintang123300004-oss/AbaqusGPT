"""Test script for querying the RAG system"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.indexer import VectorStore, Embedder
from src.rag import Retriever, OllamaClient, RAGPipeline
from dotenv import load_dotenv

load_dotenv()


def main():
    """Test the RAG pipeline"""
    print("=" * 60)
    print("Abaqus Documentation Assistant - Test Query")
    print("=" * 60)
    
    # Initialize components
    print("\nInitializing components...")
    
    vector_store = VectorStore()
    embedder = Embedder()
    retriever = Retriever(vector_store=vector_store, embedder=embedder)
    llm_client = OllamaClient()
    rag_pipeline = RAGPipeline(retriever=retriever, llm_client=llm_client)
    
    doc_count = vector_store.get_collection_count()
    print(f"Vector store contains {doc_count} documents")
    
    if doc_count == 0:
        print("\nERROR: No documents in vector store!")
        print("Please run the indexer first: python scripts/index_docs.py")
        return
    
    # Check Ollama
    if not llm_client.check_model_availability():
        print("\nWARNING: Ollama model not available!")
        print("Make sure Ollama is running: ollama serve")
        return
    
    print("\n" + "=" * 60)
    print("Ready! Ask questions about Abaqus (type 'quit' to exit)")
    print("=" * 60)
    
    # Interactive loop
    while True:
        print("\n")
        question = input("Question: ").strip()
        
        if not question:
            continue
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        print("\nThinking...")
        
        try:
            result = rag_pipeline.query(question)
            
            print("\n" + "=" * 60)
            print("ANSWER:")
            print("=" * 60)
            print(result['answer'])
            
            if result['sources']:
                print("\n" + "-" * 60)
                print("SOURCES:")
                print("-" * 60)
                for i, source in enumerate(result['sources'], 1):
                    print(f"{i}. {source['title']}")
                    print(f"   {source['url']}")
            
            print("=" * 60)
        
        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
