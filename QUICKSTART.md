# Abaqus Documentation Assistant - Quick Start Guide

## 🚀 Complete Setup & Usage

### Prerequisites
- Python 3.11+ installed
- Ollama installed and running
- Internet connection (for initial setup)

---

## Step-by-Step Guide

### 1. Verify Ollama is Running

```powershell
# Check if Ollama is running
ollama list

# If not running, start it
ollama serve
```

The model `llama3:8b` should be in the list. ✅

---

### 2. Scrape the Documentation

This will crawl **ALL** Abaqus 2016 documentation pages recursively.

```powershell
python scripts/scrape.py
```

**What happens:**
- Starts from http://130.149.89.49:2080/v2016/index.html
- Follows all internal links recursively
- Extracts text, code examples, and tables
- Saves to `data/scraped/abaqus_docs.jsonl`
- Can be interrupted (Ctrl+C) and resumed later

**Expected time:** Several hours (depends on doc size)

**Progress tracking:**
- Watch the console for crawl statistics
- Check `logs/scraper.log` for detailed logs

---

### 3. Index the Documentation

Once scraping is complete (or has enough data), build the vector index:

```powershell
python scripts/index_docs.py
```

**What happens:**
- Loads scraped pages from JSONL
- Chunks text into ~1000 character segments with overlap
- Generates embeddings using sentence-transformers
- Stores in ChromaDB vector database at `data/chroma_db/`

**Expected time:** 10-30 minutes (depends on number of pages)

---

### 4. Start the API Server

```powershell
python -m uvicorn src.api.main:app --reload
```

**API will be available at:**
- Main API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

**Leave this terminal running!**

---

### 5. Open the Chat UI

Open `frontend/index.html` in your web browser.

**Or serve it with Python:**

```powershell
cd frontend
python -m http.server 8080
```

Then visit: http://localhost:8080

---

## 🧪 Testing the System

### Option 1: Web UI
1. Open the frontend in your browser
2. Ask questions like:
   - "How do I define material properties in Abaqus?"
   - "What is the *MATERIAL keyword?"
   - "How do I create a static analysis step?"

### Option 2: Command Line Test
```powershell
python scripts/test_query.py
```

This provides an interactive CLI for testing queries.

### Option 3: API Test (curl)
```powershell
curl -X POST http://localhost:8000/ask `
  -H "Content-Type: application/json" `
  -d '{"question": "How do I define material properties?"}'
```

---

## 📊 Checking System Status

### Vector Store Stats
```powershell
curl http://localhost:8000/stats
```

### Health Check
```powershell
curl http://localhost:8000/health
```

---

## 🔧 Troubleshooting

### Issue: "Ollama model not available"
```powershell
# Pull the model if needed
ollama pull llama3:8b

# Start Ollama
ollama serve
```

### Issue: "No documents in vector store"
```powershell
# Run the indexer
python scripts/index_docs.py
```

### Issue: "Cannot connect to API"
```powershell
# Start the API server
python -m uvicorn src.api.main:app --reload
```

### Issue: Scraper is too slow
Edit `.env` and increase workers:
```
MAX_WORKERS=10
REQUEST_DELAY=0.3
```

### Issue: Need to rebuild index
```powershell
# The indexer will ask to confirm reset
python scripts/index_docs.py
# Answer "yes" to reset
```

---

## 📁 Project Structure

```
abaqus/
├── src/
│   ├── scraper/        # Web scraping components
│   ├── indexer/        # Text chunking & embeddings
│   ├── rag/            # RAG pipeline & LLM client
│   └── api/            # FastAPI backend
├── frontend/           # Chat UI (HTML/CSS/JS)
├── scripts/            # Utility scripts
├── data/               # Runtime data (created automatically)
│   ├── scraped/        # Scraped JSONL files
│   └── chroma_db/      # Vector database
├── logs/               # Log files
└── .env                # Configuration
```

---

## ⚙️ Configuration

Edit `.env` to customize:

```env
# Scraping
MAX_WORKERS=5           # Concurrent scraping threads
REQUEST_DELAY=0.5       # Delay between requests (seconds)

# Chunking
CHUNK_SIZE=1000         # Characters per chunk
CHUNK_OVERLAP=200       # Overlap between chunks

# API
API_PORT=8000           # API server port

# LLM
OLLAMA_MODEL_NAME=llama3:8b  # Ollama model to use
```

---

## 🎯 How It Works

1. **Scraper** crawls Abaqus docs recursively
2. **Parser** extracts text, code, tables from HTML
3. **Chunker** splits content into semantic chunks
4. **Embedder** generates vector embeddings
5. **VectorStore** indexes chunks in ChromaDB
6. **User asks question** via UI or API
7. **Retriever** finds top-K relevant chunks
8. **LLM** generates answer using retrieved context
9. **User gets answer** with source citations

---

## 🚀 Performance Tips

1. **Scraping:**
   - Increase `MAX_WORKERS` for faster scraping
   - Decrease `REQUEST_DELAY` if server allows
   - Resume interrupted scrapes (already visited URLs are cached)

2. **Indexing:**
   - Adjust `CHUNK_SIZE` based on your needs
   - Larger chunks = more context, fewer chunks
   - Smaller chunks = more granular search

3. **Retrieval:**
   - Increase `top_k` in queries for more context
   - Decrease `temperature` for more deterministic answers

---

## 📝 Example Questions to Try

- "How do I define elastic material properties?"
- "What is the difference between *STATIC and *DYNAMIC?"
- "How do I apply boundary conditions?"
- "What element types are available for shell analysis?"
- "How do I create a contact interaction?"
- "What is the *MATERIAL keyword syntax?"
- "How do I output stress results?"

---

## 🔒 Security Note

This MVP runs locally and doesn't require any external API keys or paid services. Everything is on your machine!

---

## 📚 Next Steps (Beyond MVP)

Future enhancements could include:
- Streaming responses for real-time answer generation
- Chat history and conversation context
- File upload for .inp parsing
- Integration with Abaqus/CAE
- Multi-language support
- Fine-tuned embedding model for Abaqus terminology

---

## ❓ Need Help?

Check the logs:
- Scraper: `logs/scraper.log`
- API: Console output where uvicorn is running

---

**You're all set! Start with step 1 and work through sequentially.** 🎉
