# Document Chunking Workflow

## Two-Step Process (No Auto-Indexing)

This system now supports a **two-step workflow**:

### Step 1: Upload & Chunk (`POST /vector/upload`)
Upload a document to extract text and create chunks.

```bash
curl -X POST "http://localhost:8000/vector/upload" \
  -F "file=@contract.pdf" \
  -F "user_id=user_001"
```

**Response:**
```json
{
    "status": "success",
    "message": "Document 'contract.pdf' chunked successfully. Use POST /vector/index to index these chunks.",
    "document_id": "doc_abc123",
    "user_id": "user_001",
    "filename": "contract.pdf",
    "source": "pdf",
    "total_pages": 5,
    "total_chunks": 18,
    "chunks": [
        {
            "chunk_id": "doc_abc123_p1_c0",
            "document_id": "doc_abc123",
            "user_id": "user_001",
            "content": "Contract terms and conditions...",
            "metadata": {
                "source": "pdf",
                "page_number": 1,
                "chunk_index": 0,
                "created_at": "2026-01-15T...",
                "tags": []
            }
        },
        ...more chunks...
    ],
    "chunk_ids": ["doc_abc123_p1_c0", "doc_abc123_p1_c1", ...],
    "extraction_time_ms": 250.5
}
```

### Step 2: Index Chunks (`POST /vector/index`)
Once you have chunks, index them into the vector database.

```bash
curl -X POST "http://localhost:8000/vector/index" \
  -H "Content-Type: application/json" \
  -d '{
    "chunks": [
        {
            "chunk_id": "doc_abc123_p1_c0",
            "document_id": "doc_abc123",
            "user_id": "user_001",
            "content": "Contract terms...",
            "metadata": {...}
        }
    ]
}'
```

**Response:**
```json
{
    "status": "success",
    "message": "Successfully indexed 18 chunks",
    "chunks_indexed": 18,
    "first_chunk_id": "doc_abc123_p1_c0"
}
```

---

## Supported Upload Formats

- **PDF**: Text extraction via pypdf
- **Images** (PNG, JPG, TIFF): OCR via Tesseract
- **Text Files** (TXT, MD): Direct UTF-8 reading

---

## Python Workflow Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Step 1: Upload and chunk
print("Uploading document...")
with open("contract.pdf", "rb") as f:
    files = {"file": f}
    data = {"user_id": "user_001"}
    response = requests.post(f"{BASE_URL}/vector/upload", files=files, data=data)

upload_result = response.json()
print(f"Created {upload_result['total_chunks']} chunks")

# You can now inspect, modify, or filter chunks before indexing
chunks = upload_result["chunks"]
print(f"First chunk: {chunks[0]['content'][:100]}...")

# Step 2: Index the chunks
print("\nIndexing chunks...")
index_response = requests.post(
    f"{BASE_URL}/vector/index",
    json={"chunks": chunks}
)

index_result = index_response.json()
print(f"Indexed: {index_result['message']}")

# Step 3: Search
print("\nSearching...")
search_response = requests.post(
    f"{BASE_URL}/vector/search",
    json={"query": "contract payment terms", "top_k": 3}
)

results = search_response.json()
for result in results["results"]:
    print(f"- {result['similarity_score']}: {result['content'][:50]}...")
```

---

## Benefits of Two-Step Approach

1. **Control**: Inspect chunks before indexing
2. **Filtering**: Remove sensitive content, deduplicate, or modify chunks
3. **Batching**: Upload multiple documents, then index selectively
4. **Cost**: Only index the chunks you need
5. **Custom Processing**: Add custom chunking strategies between steps

---

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/vector/upload` | POST | Extract text and create chunks |
| `/vector/index` | POST | Index chunks into vector DB |
| `/vector/search` | POST | Search (semantic/metadata/hybrid) |
| `/vector/stats` | GET | View database statistics |

---

## Configuration

Chunking parameters in `app/core/config.py`:
- `chunk_size`: 512 characters
- `chunk_overlap`: 50 characters
- `embedding_model`: sentence-transformers/all-MiniLM-L6-v2

These can be modified to use alternative chunking and embedding strategies.
