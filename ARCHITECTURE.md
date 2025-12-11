# System Architecture

## Overview

The Abaqus Documentation Assistant is a **Retrieval-Augmented Generation (RAG)** system that provides accurate answers from Abaqus 2016 documentation using a local LLM.

```
┌─────────────────────────────────────────────────────────────────┐
│                     ABAQUS ASSISTANT SYSTEM                      │
└─────────────────────────────────────────────────────────────────┘

1. DATA COLLECTION PHASE
   ┌──────────────┐
   │   Web Docs   │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐     ┌──────────────┐
   │   Crawler    │────▶│    Parser    │
   └──────────────┘     └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                        │ JSONL Storage│
                        └──────────────┘

2. INDEXING PHASE
   ┌──────────────┐
   │ JSONL Files  │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐     ┌──────────────┐
   │   Chunker    │────▶│   Embedder   │
   └──────────────┘     └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  ChromaDB    │
                        │(Vector Store)│
                        └──────────────┘

3. QUERY PHASE
   ┌──────────────┐
   │  User Query  │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐     ┌──────────────┐
   │  Embedder    │────▶│  Retriever   │
   └──────────────┘     └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                        │Retrieved Docs│
                        └──────┬───────┘
                               │
          ┌────────────────────┘
          │
          ▼
   ┌──────────────┐     ┌──────────────┐
   │Build Prompt  │────▶│Ollama (LLM)  │
   └──────────────┘     └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                        │   Answer +   │
                        │   Sources    │
                        └──────────────┘
```

---

## Component Details

### 1. Web Scraper (`src/scraper/`)

**Purpose:** Extract all content from Abaqus documentation website.

**Components:**
- `crawler.py`: Multi-threaded BFS crawler
  - Respects same-domain constraints
  - Caches visited URLs to enable resume
  - Configurable workers and delays
  
- `parser.py`: HTML content extractor
  - Extracts: text, code blocks, tables, headings
  - Preserves document structure
  - Filters non-content pages
  
- `storage.py`: Data persistence
  - Saves to JSONL (one JSON object per line)
  - Tracks visited URLs for resume capability
  - Provides statistics

**Data Flow:**
```
URL → Fetch HTML → Parse Content → Save to JSONL → Discover Links → Queue URLs
```

---

### 2. Indexer (`src/indexer/`)

**Purpose:** Transform scraped documents into searchable vectors.

**Components:**

- `chunker.py`: Text segmentation
  - **Strategy:** Heading-aware + overlapping chunks
  - Splits by headings when possible
  - Falls back to sentence-based splitting
  - Preserves context with overlap (200 chars default)
  - Special handling for code and tables
  
- `embedder.py`: Vector generation
  - Uses `sentence-transformers/all-MiniLM-L6-v2`
  - Generates 384-dimensional embeddings
  - Batch processing for efficiency
  - CPU-friendly model
  
- `vector_store.py`: ChromaDB interface
  - Persistent local storage
  - Automatic metadata indexing
  - Cosine similarity search
  - Batch insertion

**Data Flow:**
```
JSONL → Load Pages → Chunk Text → Generate Embeddings → Store Vectors
```

**Chunking Example:**
```
Original Document (5000 chars):
├── Heading 1 (500 chars) → Chunk 1
├── Heading 2 (2000 chars) → Chunk 2a (1000 chars)
│                          → Chunk 2b (1000 chars with overlap)
└── Code Example (300 chars) → Chunk 3 (code)
```

---

### 3. RAG Pipeline (`src/rag/`)

**Purpose:** Retrieve relevant context and generate answers.

**Components:**

- `retriever.py`: Document search
  - Embeds user query
  - Searches vector store for top-K similar chunks
  - Returns ranked results with metadata
  - Formats context for LLM
  
- `llm_client.py`: Ollama interface
  - RESTful API calls to local Ollama
  - Supports multiple models
  - Configurable temperature
  - Model availability checking
  
- `pipeline.py`: End-to-end orchestration
  - Combines retrieval + generation
  - Builds optimized prompts
  - Extracts source citations
  - Error handling

**RAG Flow:**
```
Query → Embed → Search Vectors → Rank Results → Build Prompt → LLM Generate → Format Response
```

**Prompt Template:**
```
System: You are an Abaqus expert...

Context:
[Document 1]
Source: Material Properties - Elastic Behavior
URL: http://...
Content: To define elastic properties...

[Document 2]
...

Question: How do I define elastic material properties?

Answer: [LLM generates here]
```

---

### 4. FastAPI Backend (`src/api/`)

**Purpose:** REST API for the assistant.

**Endpoints:**

- `POST /ask`: Main query endpoint
  ```json
  Request:
  {
    "question": "How do I define materials?",
    "top_k": 5,
    "temperature": 0.3
  }
  
  Response:
  {
    "answer": "To define materials in Abaqus...",
    "sources": [
      {
        "title": "Material Definition Guide",
        "url": "http://..."
      }
    ]
  }
  ```

- `GET /health`: System health check
- `GET /stats`: Vector store statistics

**Startup:**
- Initializes all components
- Loads embedding model
- Connects to vector store
- Checks Ollama availability

---

### 5. Frontend (`frontend/`)

**Purpose:** Simple chat interface.

**Features:**
- Clean, responsive UI
- Real-time message display
- Source link rendering
- Error handling
- Loading states
- Example questions

**Technologies:**
- Vanilla JavaScript (no frameworks)
- CSS with gradient styling
- Fetch API for backend calls

---

## Data Formats

### Scraped Page (JSONL)
```json
{
  "url": "http://130.149.89.49:2080/v2016/books/...",
  "title": "Material Properties",
  "content": "To define material properties...",
  "code_examples": [
    {
      "type": "pre",
      "content": "*MATERIAL, NAME=Steel\n*ELASTIC\n210000, 0.3",
      "language": "unknown"
    }
  ],
  "tables": [...],
  "headings": [
    {"level": 1, "text": "Material Definition"},
    {"level": 2, "text": "Elastic Properties"}
  ],
  "metadata": {...}
}
```

### Chunk (in Vector Store)
```json
{
  "text": "To define elastic material properties...",
  "metadata": {
    "url": "http://...",
    "title": "Material Properties",
    "heading": "Elastic Properties",
    "type": "text",
    "chunk_index": 0
  }
}
```

---

## Key Design Decisions

### 1. Why JSONL over Database?
- Simple to inspect and debug
- Easy to process incrementally
- No database setup required
- Portable across systems

### 2. Why ChromaDB?
- Local-first (no cloud required)
- Simple Python API
- Persistent storage
- Good for MVP scale

### 3. Why sentence-transformers?
- CPU-friendly
- Fast inference
- Good general-purpose embeddings
- Small model size (~80MB)

### 4. Why Overlapping Chunks?
- Prevents context loss at boundaries
- Improves retrieval quality
- Helps with questions spanning sections

### 5. Why Low Temperature (0.3)?
- More deterministic answers
- Reduces hallucination
- Better for technical content
- Can be adjusted per query

---

## Performance Characteristics

### Scraping
- **Speed:** ~5-10 pages/second (5 workers)
- **Memory:** ~200MB
- **Disk:** ~1-2MB per 100 pages (JSONL)

### Indexing
- **Speed:** ~50-100 chunks/second
- **Memory:** ~2GB (embedding model loaded)
- **Disk:** Vector DB ~500MB per 10K chunks

### Query
- **Latency:**
  - Retrieval: ~100ms
  - LLM generation: 2-10s (depends on answer length)
  - Total: ~3-12s per query
- **Memory:** ~3GB (embedder + vector store + LLM via Ollama)

---

## Scaling Considerations

### Current MVP Limits
- ~10,000 documentation pages
- ~100,000 chunks in vector store
- Single-user queries (no concurrency optimization)

### To Scale Up:
1. **More documents:**
   - Use production vector DB (Qdrant, Weaviate)
   - Implement pagination in retrieval
   
2. **More users:**
   - Add caching layer (Redis)
   - Load balance multiple API instances
   - Use async processing
   
3. **Better quality:**
   - Fine-tune embedding model on Abaqus terms
   - Implement re-ranking
   - Add query expansion
   - Use larger LLM model

---

## Security & Privacy

✅ **Fully Local:**
- No external API calls (except during scraping)
- No data leaves your machine
- No API keys required

⚠️ **Production Considerations:**
- Add authentication to API
- Rate limiting
- Input validation & sanitization
- CORS restrictions
- HTTPS for frontend

---

## Error Handling

**Scraper:**
- Failed requests → logged, added to failed set
- Connection errors → retry logic
- Malformed HTML → skip and continue

**Indexer:**
- Invalid chunks → skipped
- Embedding failures → logged, continue with others
- Vector store errors → abort with clear message

**API:**
- Empty results → friendly "not found" message
- LLM errors → return error to user
- Vector store down → HTTP 503

---

## Monitoring & Debugging

**Logs:**
- `logs/scraper.log`: Scraping activity
- Console: API requests and responses

**Metrics to Watch:**
- Vector store document count
- Query latency
- Retrieval quality (manual inspection)
- LLM token usage

**Debugging Tools:**
- `scripts/test_query.py`: Test retrieval + generation
- `/stats` endpoint: Check document count
- `/health` endpoint: Component status
- FastAPI `/docs`: Interactive API testing

---

This architecture provides a solid foundation for a production-grade documentation assistant!
