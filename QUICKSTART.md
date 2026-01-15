# Quick Start Guide

## 🚀 5-Minute Setup

### Option 1: Local Setup (Python 3.11)

```bash
# 1. Navigate to project
cd "path/to/project"

# 2. Create virtual environment
python3.11 -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5. Visit Swagger UI
open http://localhost:8000/docs
```

### Option 2: Docker (One Command)

```bash
docker-compose up --build
```

Access: http://localhost:8000/docs

---

## 📝 First Steps

### Step 1: Index Your First Document

```bash
curl -X POST "http://localhost:8000/vector/index" \
  -H "Content-Type: application/json" \
  -d '{
    "chunks": [
      {
        "chunk_id": "doc1_chunk0",
        "document_id": "doc_1",
        "user_id": "user_1",
        "content": "Your extracted text here...",
        "metadata": {
          "source": "pdf",
          "page_number": 1,
          "chunk_index": 0,
          "created_at": "2026-01-15T10:00:00",
          "tags": ["invoice"]
        }
      }
    ]
  }'
```

### Step 2: Search Semantically

```bash
curl -X POST "http://localhost:8000/vector/search/semantic" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the amount?",
    "top_k": 5
  }'
```

### Step 3: Filter by Metadata

```bash
curl -X POST "http://localhost:8000/vector/search/metadata" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
      "source": "pdf",
      "tags": ["invoice"]
    },
    "top_k": 5
  }'
```

---

## 🔧 Configuration

Modify `.env` for custom settings:

```env
# Chunking
CHUNK_SIZE=512      # Increase for longer context (slower)
CHUNK_OVERLAP=50    # More overlap = more context but slower

# Database
CHROMA_PERSIST_DIRECTORY=./chroma_db
COLLECTION_NAME=document_chunks

# Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

---

## 📊 Verify Installation

Run the test suite:

```bash
uvicorn app.main:app --reload &
sleep 2
python test_api.py
```

Expected output: All tests pass ✅

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8000 in use | Change port: `--port 8001` |
| ModuleNotFoundError | Activate venv and install deps |
| Permission denied | Check file permissions, use `sudo` if needed |
| Slow queries | Increase `CHUNK_SIZE` or use metadata filters |

---

## Next Steps

1. Read [README.md](README.md) for detailed architecture
2. Check [API_EXAMPLES.md](API_EXAMPLES.md) for endpoint examples
3. Explore `/docs` Swagger UI for interactive testing
