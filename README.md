# 🔧 AbaqusGPT

**Your AI-Powered Abaqus Documentation Assistant**

AbaqusGPT is an intelligent chatbot that provides instant, accurate answers from Abaqus 2016 documentation using RAG (Retrieval-Augmented Generation) with a local Ollama LLM. Get context-aware responses with source citations - all running locally with no API costs!

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![Ollama](https://img.shields.io/badge/Ollama-llama3:8b-green)](https://ollama.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-teal)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## ✨ Features

- **🤖 Conversational AI**: Natural, context-aware responses that remember your conversation
- **📚 Comprehensive Knowledge**: Trained on 6,300+ Abaqus 2016 documentation pages
- **🔍 Source Citations**: Every answer includes references to specific documentation
- **⚡ Lightning Fast**: Local processing with optimized retrieval (< 30s responses)
- **💰 Zero Cost**: Runs entirely locally using Ollama - no API fees
- **🎯 Smart Retrieval**: RAG pipeline with 96,500+ indexed chunks for precise answers
- **🎨 Clean UI**: Simple, intuitive chat interface

## Project Structure

```
abaqus/
├── src/
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── crawler.py          # Main crawling logic
│   │   ├── parser.py            # HTML parsing and content extraction
│   │   └── storage.py           # Data storage (JSONL)
│   ├── indexer/
│   │   ├── __init__.py
│   │   ├── chunker.py           # Text chunking logic
│   │   ├── embedder.py          # Embedding generation
│   │   └── vector_store.py      # ChromaDB operations
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── retriever.py         # Document retrieval
│   │   ├── llm_client.py        # Ollama API client
│   │   └── pipeline.py          # End-to-end RAG pipeline
│   └── api/
│       ├── __init__.py
│       ├── main.py              # FastAPI app
│       └── models.py            # Pydantic models
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── scripts/
│   ├── scrape.py                # Run scraper
│   ├── index_docs.py            # Build vector index
│   └── test_query.py            # Test queries
├── data/                        # Created at runtime
│   ├── scraped/                 # Raw scraped data
│   └── chroma_db/               # Vector database
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.11+** installed
2. **Ollama** installed and running ([Download](https://ollama.com/))
3. **llama3:8b model** downloaded:
   ```bash
   ollama pull llama3:8b
   ```

### Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd abaqus
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the application**:
   ```bash
   start.bat
   ```
   
   This will automatically:
   - Start the backend API server (port 8000)
   - Start the frontend UI server (port 3000)
   - Open the chat interface in your browser

That's it! 🎉 Start chatting with AbaqusGPT at `http://localhost:3000`

### Manual Setup (First Time Only)

If you need to build from scratch:

**Step 1: Scrape Documentation**
```bash
python scripts/scrape.py
```
*Crawls 6,300+ Abaqus 2016 documentation pages (~30 min)*

**Step 2: Build Vector Index**
```bash
python scripts/index_docs.py
```
*Generates embeddings for 96,500+ chunks (~2 hours)*

**Step 3: Launch**
```bash
start.bat
```

## 💡 Usage Examples

Try asking AbaqusGPT:

- *"What is Abaqus?"*
- *"How do I define material properties?"*
- *"Explain hyperelastic materials like I'm 5"*
- *"What's the difference between \*STATIC and \*DYNAMIC steps?"*
- *"Help me set up a contact analysis"*
- *"What element types should I use for shell analysis?"*

AbaqusGPT remembers context, so you can have natural follow-up conversations!

## 🛠️ Technology Stack

- **LLM**: Ollama (llama3:8b) - Local inference
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Vector Store**: ChromaDB
- **Backend**: FastAPI + Python 3.11
- **Frontend**: Vanilla JavaScript
- **Scraping**: BeautifulSoup4 + Requests

## 📊 System Statistics

- **Documentation Pages**: 6,322 pages scraped
- **Indexed Chunks**: 96,506 text chunks
- **Embedding Dimensions**: 384-dimensional vectors
- **Response Time**: ~15-30 seconds
- **Context Window**: Last 2 conversation exchanges

## 🔧 API Endpoints

### `POST /ask`
Ask a question with conversation context:
```json
{
  "question": "How do I define material properties?",
  "top_k": 3,
  "temperature": 0.3,
  "conversation_history": []
}
```

### `GET /health`
Health check and system status

### `GET /stats`
Vector store statistics

### `GET /docs`
Interactive API documentation

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## 📝 License

MIT License - feel free to use for your projects!

## 🙏 Acknowledgments

- Abaqus documentation by Dassault Systèmes
- Ollama team for local LLM infrastructure
- ChromaDB for vector storage
- sentence-transformers for embeddings

---

**Made with ❤️ for the Abaqus community**
