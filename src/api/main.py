"""FastAPI application for Abaqus assistant"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.indexer import VectorStore, Embedder
from src.rag import Retriever, OllamaClient, RAGPipeline
from src.api.models import QuestionRequest, AnswerResponse, HealthResponse, Source, Message
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Abaqus Documentation Assistant API",
    description="RAG-based API for querying Abaqus 2016 documentation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for components
vector_store = None
embedder = None
retriever = None
llm_client = None
rag_pipeline = None


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global vector_store, embedder, retriever, llm_client, rag_pipeline
    
    logger.info("Initializing API components...")
    
    try:
        # Load configuration
        persist_dir = os.getenv('CHROMA_PERSIST_DIR', './data/chroma_db')
        collection_name = os.getenv('COLLECTION_NAME', 'abaqus_docs')
        embedding_model = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
        ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        ollama_model = os.getenv('OLLAMA_MODEL_NAME', 'llama3:8b')
        
        # Initialize components
        logger.info("Loading vector store...")
        vector_store = VectorStore(
            persist_directory=persist_dir,
            collection_name=collection_name
        )
        
        logger.info("Loading embedding model...")
        embedder = Embedder(model_name=embedding_model)
        
        logger.info("Initializing retriever...")
        retriever = Retriever(vector_store=vector_store, embedder=embedder)
        
        logger.info("Initializing Ollama client...")
        llm_client = OllamaClient(base_url=ollama_url, model_name=ollama_model)
        
        # Check Ollama availability
        if not llm_client.check_model_availability():
            logger.warning(
                f"Ollama model {ollama_model} not available. "
                "Make sure Ollama is running and the model is pulled."
            )
        
        logger.info("Initializing RAG pipeline...")
        rag_pipeline = RAGPipeline(retriever=retriever, llm_client=llm_client)
        
        logger.info("API components initialized successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize API components: {e}")
        raise


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Abaqus Documentation Assistant API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint
    
    Returns service status and component availability
    """
    try:
        doc_count = vector_store.get_collection_count() if vector_store else 0
        ollama_ok = llm_client.check_model_availability() if llm_client else False
        
        return HealthResponse(
            status="healthy",
            vector_store_count=doc_count,
            ollama_available=ollama_ok
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask", response_model=AnswerResponse, tags=["Query"])
async def ask_question(request: QuestionRequest):
    """
    Ask a question about Abaqus
    
    This endpoint:
    1. Retrieves relevant documentation chunks (if available)
    2. Uses Ollama LLM to generate a natural answer
    3. Returns the answer with source citations
    4. Can answer general Abaqus questions even without exact doc matches
    """
    if not rag_pipeline:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not initialized. Please check server logs."
        )
    
    try:
        logger.info(f"Received question: {request.question}")
        
        # Run RAG pipeline with flexible retrieval and conversation context
        # Even if retrieval finds limited matches, LLM can use general knowledge
        result = rag_pipeline.query(
            question=request.question,
            top_k=request.top_k,
            temperature=request.temperature,
            conversation_history=[msg.dict() for msg in request.conversation_history] if request.conversation_history else None
        )
        
        # Clean up any "According to" artifacts from response
        answer = result['answer']
        
        # Remove common doc-reference phrases for natural flow
        phrases_to_remove = [
            "According to the provided documentation, ",
            "According to the documentation, ",
            "Based on the provided documentation, ",
            "Based on the documentation, ",
            "The documentation states that ",
            "As per the documentation, ",
            "From the documentation, "
        ]
        
        for phrase in phrases_to_remove:
            if answer.startswith(phrase):
                answer = answer[len(phrase):]
                # Capitalize first letter after removal
                if answer:
                    answer = answer[0].upper() + answer[1:]
                break
        
        # Format response
        response = AnswerResponse(
            answer=answer.strip(),
            sources=[Source(**src) for src in result['sources']]
        )
        
        logger.info("Successfully generated answer")
        return response
    
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", tags=["Stats"])
async def get_stats():
    """Get statistics about the knowledge base"""
    if not vector_store:
        raise HTTPException(status_code=503, detail="Vector store not initialized")
    
    try:
        count = vector_store.get_collection_count()
        return {
            "total_documents": count,
            "collection_name": vector_store.collection_name
        }
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', '8000'))
    
    uvicorn.run(app, host=host, port=port)
