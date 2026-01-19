# Architecture & Design Document

## System Overview

The Vector Database & Metadata-Driven Search System is a production-ready backend that manages document embeddings, metadata, and enables multiple search strategies through a clean API.

## Design Principles

1. **Separation of Concerns** - API, Service, and Repository layers
2. **Clean Architecture** - Each layer has single responsibility
3. **Type Safety** - Pydantic models for all inputs/outputs
4. **Error Handling** - Comprehensive validation and error responses
5. **Persistence** - Vector index survives container restarts
6. **Scalability** - HNSW index for O(log n) queries

## Layer Architecture

### 1. API Layer (`app/api/routes.py`)

**Responsibility**: HTTP request handling and response formatting

**Components**:
- `/vector/index` - Index document chunks
- `/vector/search/`- Vector similarity search or Metadata-based filtering or Combined(hybrid) search
- `/vector/stats` - Database statistics

**Error Handling**:
- 400: Bad Request (validation errors)
- 500: Internal Server Error (processing errors)

### 2. Service Layer (`app/services/`)

**Responsibility**: Business logic and orchestration

**Components**:

#### VectorService (`vector_service.py`)
- Orchestrates chunking, embedding, and search
- Formats results
- Timing and logging

#### ChunkingService (`chunking_service.py`)
- Splits text into configurable chunks
- Maintains overlap for context
- Algorithm: Sliding window with step size = chunk_size - overlap
- Time: O(n) where n = text length

#### EmbeddingService (`embedding_service.py`)
- Generates embeddings using Sentence Transformers
- Batch processing for efficiency
- Returns 384-dimensional vectors

### 3. Repository Layer (`app/repository/vector_repo.py`)

**Responsibility**: Direct database operations

**Components**:

#### VectorRepository
- Chroma client management
- Index creation and persistence
- Search algorithm implementations

**Search Implementations**:

1. **Semantic Search**
   ```
   Query Text → Embedding → HNSW Index → k-NN Search → Results
   Time: O(log n) average
   ```

2. **Metadata Search**
   ```
   Filters → DuckDB Query → Matching Chunks
   Time: O(m) where m = total chunks
   ```

3. **Hybrid Search**
   ```
   Both searches → Combine scores → Top k results
   Time: O(log n + m)
   ```

### 4. Data Models (`app/models/schemas.py`)

**Pydantic Models**:
- `ChunkModel` - Document chunk with metadata
- `MetadataModel` - Rich metadata for chunks
- `SearchResult` - Search result format
- `*Request` - Request schemas for validation
- `SearchResponse` - Standardized response format

## Database Design

### Chroma Collection Schema

```
Collection: "document_chunks"

Document Fields:
- id: chunk_id (string)
- content: text content (string)
- embedding: auto-generated (384-dim vector)

Metadata Fields:
- document_id (string)
- user_id (string)
- source (string: pdf|ocr|image)
- page_number (integer)
- chunk_index (integer)
- created_at (ISO string)
- tags (JSON array as string)

Index Type: HNSW
Space: cosine
```

### Persistence Strategy

**File Structure**:
```
chroma_db/
├── document_chunks/
│   ├── data/           # Parquet files
│   ├── index/          # HNSW index
│   └── metadata.json   # Collection metadata
```

**Persistence Mechanism**:
- DuckDB + Parquet backend
- Automatic disk flushing
- Docker volume mount: `./chroma_db:/app/chroma_db`

## Algorithm Complexity Analysis

### Time Complexity

| Operation | Best | Average | Worst |
|-----------|------|---------|-------|
| Semantic Search | O(1) | O(log n) | O(log n) |
| Metadata Search | O(1) | O(m) | O(m) |
| Hybrid Search | O(log n) | O(log n + m) | O(log n + m) |
| Indexing | O(n) | O(n log n) | O(n log n) |
| Chunking | O(n) | O(n) | O(n) |

Where:
- n = total chunks in database
- m = chunks matching metadata filters

### Space Complexity

| Component | Space |
|-----------|-------|
| Embedding (per chunk) | 384 × 4 bytes = 1.5 KB |
| Metadata (per chunk) | ~200 bytes |
| HNSW Index overhead | ~50 bytes per chunk |
| **Total per chunk** | **~2 KB** |

Example: 1 million chunks = ~2 GB

## Performance Characteristics

### Query Latency (Typical)

| Search Type | Small DB | Large DB | Notes |
|-------------|----------|----------|-------|
| Semantic | 20-40ms | 40-100ms | Single query embedding |
| Metadata | 5-15ms | 10-30ms | No vector computation |
| Hybrid | 30-60ms | 60-120ms | Sum of both |

### Throughput

- Embedding generation: ~5,000 sentences/sec (CPU)
- Chroma queries: ~100-500 queries/sec
- Network overhead: <5ms (local)

### Memory Usage

- Empty collection: ~50 MB
- + 1M chunks: ~2 GB total
- HNSW overhead: Minimal (<5%)

## Metadata Filtering Strategy

### Filter Logic

```python
if filters.source and filters.page_number:
    # AND logic for different fields
    WHERE source = 'pdf' AND page_number = 1
elif filters.tags:
    # Tags use OR logic (matches any tag)
    WHERE tags CONTAINS 'invoice' OR tags CONTAINS 'paid'
```

### Index Optimization

- DuckDB maintains hash index on document_id, user_id
- Sequential scan for tags (JSON array search)
- No additional index maintenance needed

### Filter Performance

```
Single Filter: O(n)
Combined Filters: O(n) for first filter + O(m) for each additional
Multiple Tags: O(n) JSON array scan
```

## Embedding Model Selection

### Chosen Model: `sentence-transformers/all-MiniLM-L6-v2`

**Why This Model?**
- Fast inference (5000 sentences/sec)
- Good accuracy (semantic understanding)
- Small size (33 MB)
- Production-ready
- 384 dimensions (good balance)

**Trade-offs Considered**:
- Larger models: Better accuracy, slower, more memory
- Smaller models: Faster, less accuracy
- Domain-specific models: Optimal for specific use cases

### Alternatives

| Model | Dims | Speed | Size | Accuracy |
|-------|------|-------|------|----------|
| all-MiniLM-L6-v2 | 384 | ⭐⭐⭐⭐⭐ | 33 MB | ⭐⭐⭐⭐ |
| all-mpnet-base-v2 | 768 | ⭐⭐⭐ | 438 MB | ⭐⭐⭐⭐⭐ |
| all-roberta-large-v1 | 1024 | ⭐⭐ | 498 MB | ⭐⭐⭐⭐⭐ |
| DistilBERT | 384 | ⭐⭐⭐⭐⭐ | 67 MB | ⭐⭐⭐ |

## HNSW Index Explanation

### What is HNSW?

**Hierarchical Navigable Small World**
- Approximate Nearest Neighbor (ANN) algorithm
- Probabilistic data structure
- Multi-layer graph approach

### How It Works

```
Layer 2:    [X] -------- [Y]
            /              \
Layer 1:   [X] --- [A] --- [Y]
           / \     / \     / \
Layer 0:  [X]-[B]-[A]-[C]-[Y]-[Z]
          (All points)

Search: Start from top, navigate down to nearest neighbors
```

### Performance Gains

- **Naive approach**: Compare query to all chunks O(n)
- **HNSW approach**: Hierarchical search O(log n)
- **Speedup**: 1000x faster for 1M chunks

### Trade-offs

- Small accuracy loss (~1-2%)
- No false negatives (finds actual NNs)
- Can miss very close neighbors occasionally

## Error Handling Strategy

### Validation Errors

```python
if not query or not query.strip():
    raise HTTPException(400, "Query cannot be empty")

if top_k < 1:
    raise HTTPException(400, "top_k must be at least 1")
```

### Processing Errors

```python
try:
    results = vector_service.search(...)
except Exception as e:
    logger.error(f"Search failed: {e}")
    raise HTTPException(500, "Error performing search")
```

### Error Response Format

```json
{
    "detail": "Descriptive error message"
}
```

## Docker Deployment Strategy

### Image Design

- **Base**: Python 3.11-slim (minimal size)
- **Dependencies**: Installed in one layer
- **Health Check**: Automatic verification every 30s
- **Entrypoint**: Uvicorn production server

### Volume Persistence

```yaml
volumes:
  - ./chroma_db:/app/chroma_db  # Vector index
  - ./app:/app/app               # Application code (dev)
  - ./logs:/app/logs             # Application logs
```

### Resource Optimization

- Multi-stage build not needed (Python slim is efficient)
- Layer caching for faster rebuilds
- <500 MB final image size

## Scalability Roadmap

### Current Limitations

- Single-instance deployment
- No horizontal scaling
- All data in one collection

### Future Enhancements

1. **Multi-collection Support**
   - Separate collections per user
   - Parallel searches

2. **Distributed Vector Database**
   - Milvus or Weaviate for scaling
   - Sharding across nodes

3. **Caching Layer**
   - Redis for query results
   - Popular queries cached

4. **Batch Indexing**
   - Async task queue (Celery/RQ)
   - Bulk operations optimization
