# API Examples

Complete examples for all API endpoints.

## 1. Index Chunks - POST `/vector/index`

Index multiple document chunks at once.

### Basic Example

```json
POST /vector/index

{
    "chunks": [
        {
            "chunk_id": "doc_1_chunk_0",
            "document_id": "doc_1",
            "user_id": "user_1",
            "content": "Invoice #INV-001 dated January 15, 2026. Total amount: $5,000.00",
            "metadata": {
                "source": "pdf",
                "page_number": 1,
                "chunk_index": 0,
                "created_at": "2026-01-15T10:30:00",
                "tags": ["invoice", "financial"]
            }
        },
        {
            "chunk_id": "doc_1_chunk_1",
            "document_id": "doc_1",
            "user_id": "user_1",
            "content": "Payment terms: Net 30 days. Contact: sales@company.com, Phone: (555) 123-4567",
            "metadata": {
                "source": "pdf",
                "page_number": 1,
                "chunk_index": 1,
                "created_at": "2026-01-15T10:30:00",
                "tags": ["invoice", "contact"]
            }
        }
    ]
}
```

### Response (200 OK)

```json
{
    "status": "success",
    "message": "Successfully indexed 2 chunks",
    "chunks_indexed": 2,
    "first_chunk_id": "doc_1_chunk_0"
}
```

### Python Example

```python
import requests
from datetime import datetime

url = "http://localhost:8000/vector/index"

payload = {
    "chunks": [
        {
            "chunk_id": "doc_1_chunk_0",
            "document_id": "doc_1",
            "user_id": "user_1",
            "content": "Invoice details...",
            "metadata": {
                "source": "pdf",
                "page_number": 1,
                "chunk_index": 0,
                "created_at": datetime.utcnow().isoformat(),
                "tags": ["invoice"]
            }
        }
    ]
}

response = requests.post(url, json=payload)
print(response.json())
```

---

## 2. Semantic Search - POST `/vector/search/semantic`

Find semantically similar content.

### Basic Example

```json
POST /vector/search/semantic

{
    "query": "What is the invoice total and payment deadline?",
    "top_k": 3
}
```

### Response (200 OK)

```json
{
    "results": [
        {
            "chunk_id": "doc_1_chunk_0",
            "document_id": "doc_1",
            "user_id": "user_1",
            "content": "Invoice #INV-001 dated January 15, 2026. Total amount: $5,000.00",
            "metadata": {
                "source": "pdf",
                "page_number": 1,
                "chunk_index": 0,
                "created_at": "2026-01-15T10:30:00",
                "tags": ["invoice", "financial"]
            },
            "similarity_score": 0.9234
        },
        {
            "chunk_id": "doc_1_chunk_1",
            "document_id": "doc_1",
            "user_id": "user_1",
            "content": "Payment terms: Net 30 days. Contact: sales@company.com",
            "metadata": {
                "source": "pdf",
                "page_number": 1,
                "chunk_index": 1,
                "created_at": "2026-01-15T10:30:00",
                "tags": ["invoice", "contact"]
            },
            "similarity_score": 0.8756
        }
    ],
    "total_results": 2,
    "query_time_ms": 45.23
}
```

### Python Example

```python
import requests

url = "http://localhost:8000/vector/search/semantic"

payload = {
    "query": "How much does it cost?",
    "top_k": 5
}

response = requests.post(url, json=payload)
results = response.json()

for result in results["results"]:
    print(f"Score: {result['similarity_score']}")
    print(f"Content: {result['content']}")
    print(f"Tags: {result['metadata']['tags']}\n")
```

### Performance Tips

- Shorter queries (3-10 words) are faster
- Increase `top_k` for more results (slower)
- Use metadata filters for faster results (see Hybrid Search)

---

## 3. Metadata Search - POST `/vector/search/metadata`

Filter by metadata without vector similarity.

### Filter by Source

```json
POST /vector/search/metadata

{
    "filters": {
        "source": "pdf"
    },
    "top_k": 10
}
```

### Filter by Tags

```json
POST /vector/search/metadata

{
    "filters": {
        "tags": ["invoice", "financial"]
    },
    "top_k": 10
}
```

### Filter by Document

```json
POST /vector/search/metadata

{
    "filters": {
        "document_id": "doc_1",
        "user_id": "user_1"
    },
    "top_k": 10
}
```

### Combined Filters

```json
POST /vector/search/metadata

{
    "filters": {
        "source": "pdf",
        "page_number": 1,
        "tags": ["invoice"],
        "document_id": "doc_1",
        "user_id": "user_1"
    },
    "top_k": 5
}
```

### Response (200 OK)

```json
{
    "results": [
        {
            "chunk_id": "doc_1_chunk_0",
            "document_id": "doc_1",
            "user_id": "user_1",
            "content": "Invoice #INV-001...",
            "metadata": {
                "source": "pdf",
                "page_number": 1,
                "chunk_index": 0,
                "created_at": "2026-01-15T10:30:00",
                "tags": ["invoice", "financial"]
            },
            "similarity_score": 1.0
        }
    ],
    "total_results": 1,
    "query_time_ms": 12.45
}
```

### Python Example

```python
import requests

url = "http://localhost:8000/vector/search/metadata"

payload = {
    "filters": {
        "source": "pdf",
        "tags": ["invoice"]
    },
    "top_k": 10
}

response = requests.post(url, json=payload)
results = response.json()

print(f"Found {results['total_results']} matching chunks")
print(f"Query time: {results['query_time_ms']}ms")
```

### Filter Combinations

| Filter | Example Value | Notes |
|--------|---------------|-------|
| source | "pdf", "ocr", "image" | Document source type |
| page_number | 1, 2, 3 | Single page only |
| tags | ["invoice", "paid"] | OR logic - matches any tag |
| document_id | "doc_1" | Exact match |
| user_id | "user_1" | Exact match |

---

## 4. Hybrid Search - POST `/vector/search/hybrid`

Combine semantic search with metadata filtering.

### Basic Example

```json
POST /vector/search/hybrid

{
    "query": "invoice amount due date",
    "filters": {
        "source": "pdf",
        "tags": ["invoice"]
    },
    "top_k": 5,
    "weight_vector": 0.7
}
```

### Weights Explained

- `weight_vector: 1.0` → Pure vector similarity (ignore metadata)
- `weight_vector: 0.7` → 70% vector, 30% metadata (recommended)
- `weight_vector: 0.5` → 50% vector, 50% metadata
- `weight_vector: 0.0` → Pure metadata (same as metadata search)

### Response (200 OK)

```json
{
    "results": [
        {
            "chunk_id": "doc_1_chunk_0",
            "document_id": "doc_1",
            "user_id": "user_1",
            "content": "Invoice #INV-001 dated January 15, 2026. Total amount: $5,000.00",
            "metadata": {
                "source": "pdf",
                "page_number": 1,
                "chunk_index": 0,
                "created_at": "2026-01-15T10:30:00",
                "tags": ["invoice"]
            },
            "similarity_score": 0.8956
        }
    ],
    "total_results": 1,
    "query_time_ms": 58.67
}
```

### Python Example

```python
import requests

url = "http://localhost:8000/vector/search/hybrid"

payload = {
    "query": "payment information",
    "filters": {
        "source": "pdf",
        "tags": ["invoice", "financial"]
    },
    "top_k": 5,
    "weight_vector": 0.6  # Emphasize metadata
}

response = requests.post(url, json=payload)
results = response.json()

print(f"Found {results['total_results']} results")
for r in results["results"]:
    print(f"  - {r['chunk_id']}: {r['similarity_score']}")
```

### When to Use Each

| Search Type | Use Case | Speed | Accuracy |
|-------------|----------|-------|----------|
| Semantic | General questions | Slow | High |
| Metadata | Exact filtering | Fast | Medium |
| Hybrid | Mixed requirements | Medium | High |

---

## 5. Get Statistics - GET `/vector/stats`

Retrieve database statistics.

### Request

```
GET /vector/stats
```

### Response (200 OK)

```json
{
    "total_chunks": 42,
    "total_documents": 8,
    "total_users": 3,
    "collection_name": "document_chunks",
    "embedding_dimension": 384,
    "chunk_size": 512,
    "chunk_overlap": 50,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

### Python Example

```python
import requests

url = "http://localhost:8000/vector/stats"
response = requests.get(url)
stats = response.json()

print(f"Database has {stats['total_chunks']} chunks")
print(f"Across {stats['total_documents']} documents")
print(f"From {stats['total_users']} users")
print(f"Using {stats['embedding_model']}")
```

---

## Error Handling Examples

### Empty Query

```json
POST /vector/search/semantic

{
    "query": "",
    "top_k": 5
}
```

**Response (400 Bad Request)**:
```json
{
    "detail": "Query cannot be empty"
}
```

### Invalid top_k

```json
POST /vector/search/semantic

{
    "query": "test",
    "top_k": -1
}
```

**Response (422 Unprocessable Entity)**:
```json
{
    "detail": [
        {
            "loc": ["body", "top_k"],
            "msg": "ensure this value is greater than or equal to 1",
            "type": "value_error.number.not_ge"
        }
    ]
}
```

### Server Error

**Response (500 Internal Server Error)**:
```json
{
    "detail": "Error performing semantic search"
}
```

---

## Real-World Workflow

```python
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"

# 1. Index documents
print("Indexing documents...")
chunks = {
    "chunks": [
        {
            "chunk_id": "invoice_001_0",
            "document_id": "invoice_001",
            "user_id": "user_001",
            "content": "Invoice #INV-001. Amount: $1500.00",
            "metadata": {
                "source": "pdf",
                "page_number": 1,
                "chunk_index": 0,
                "created_at": datetime.utcnow().isoformat(),
                "tags": ["invoice", "paid"]
            }
        }
    ]
}
requests.post(f"{BASE_URL}/vector/index", json=chunks)

# 2. Check stats
print("Checking stats...")
stats = requests.get(f"{BASE_URL}/vector/stats").json()
print(f"Total chunks indexed: {stats['total_chunks']}")

# 3. Semantic search
print("Semantic search...")
results = requests.post(
    f"{BASE_URL}/vector/search/semantic",
    json={"query": "How much was paid?", "top_k": 3}
).json()

for r in results["results"]:
    print(f"  - {r['similarity_score']}: {r['content'][:50]}")

# 4. Metadata search
print("Metadata search...")
results = requests.post(
    f"{BASE_URL}/vector/search/metadata",
    json={"filters": {"tags": ["invoice"]}, "top_k": 5}
).json()

print(f"  Found {results['total_results']} invoices")

# 5. Hybrid search
print("Hybrid search...")
results = requests.post(
    f"{BASE_URL}/vector/search/hybrid",
    json={
        "query": "invoice payment",
        "filters": {"source": "pdf"},
        "top_k": 5,
        "weight_vector": 0.7
    }
).json()

print(f"  Hybrid results: {results['total_results']}")
```

---

## Rate Limiting Notes

Current implementation has no rate limiting. For production, consider:

- Implement IP-based rate limiting
- Add user authentication and per-user limits
- Use Redis for distributed rate limiting
- Add request queuing for high load

---

## See Also

- [README.md](README.md) - Architecture and design
- [QUICKSTART.md](QUICKSTART.md) - Setup instructions
