# Document Upload Feature

## Overview

The Vector Database system now supports direct document uploads with automatic text extraction, chunking, and indexing.

## Endpoint

**POST** `/vector/upload`

Upload a document and automatically:
1. Validate file (size, format)
2. Extract text (PDF parsing or OCR)
3. Chunk text into manageable pieces
4. Generate embeddings
5. Index into vector database

## Supported Formats

| Format | Extension | Processing Method | Notes |
|--------|-----------|-------------------|-------|
| PDF | `.pdf` | pypdf text extraction | Fast, accurate for text PDFs |
| Images | `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.gif` | Tesseract OCR | Requires Tesseract installed |
| Text | `.txt` | Direct reading | Fastest processing |

## Request Parameters

**Form Data** (multipart/form-data):

- `file` (required) - The document file to upload
- `user_id` (required) - User ID who owns the document
- `tags` (optional) - Comma-separated tags (e.g., "invoice,financial")
- `document_id` (optional) - Custom document ID (auto-generated if not provided)

## Example Usage

### cURL

```bash
# Upload PDF with tags
curl -X POST "http://localhost:8000/vector/upload" \
  -F "file=@invoice.pdf" \
  -F "user_id=user_001" \
  -F "tags=invoice,financial,2026"

# Upload image for OCR
curl -X POST "http://localhost:8000/vector/upload" \
  -F "file=@receipt.jpg" \
  -F "user_id=user_002" \
  -F "tags=receipt,expense"

# Upload with custom document ID
curl -X POST "http://localhost:8000/vector/upload" \
  -F "file=@contract.pdf" \
  -F "user_id=user_003" \
  -F "tags=contract,legal" \
  -F "document_id=contract_2026_001"
```

### Python

```python
import requests

url = "http://localhost:8000/vector/upload"

# Upload a PDF
with open("invoice.pdf", "rb") as f:
    files = {"file": ("invoice.pdf", f, "application/pdf")}
    data = {
        "user_id": "user_001",
        "tags": "invoice,financial"
    }
    
    response = requests.post(url, files=files, data=data)
    result = response.json()
    
    print(f"Document ID: {result['document_id']}")
    print(f"Total chunks: {result['total_chunks']}")
    print(f"Processing time: {result['extraction_time_ms'] + result['indexing_time_ms']}ms")

# Upload an image
with open("receipt.jpg", "rb") as f:
    files = {"file": ("receipt.jpg", f, "image/jpeg")}
    data = {"user_id": "user_002", "tags": "receipt"}
    
    response = requests.post(url, files=files, data=data)
    result = response.json()
```

### JavaScript (Fetch API)

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('user_id', 'user_001');
formData.append('tags', 'invoice,financial');

fetch('http://localhost:8000/vector/upload', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log('Document ID:', data.document_id);
    console.log('Total chunks:', data.total_chunks);
});
```

## Response

```json
{
    "status": "success",
    "message": "Document 'invoice.pdf' uploaded and indexed successfully",
    "document_id": "doc_a1b2c3d4e5f6",
    "user_id": "user_001",
    "filename": "invoice.pdf",
    "source": "pdf",
    "total_pages": 3,
    "total_chunks": 12,
    "chunk_ids": [
        "doc_a1b2c3d4e5f6_p1_c0",
        "doc_a1b2c3d4e5f6_p1_c1",
        "doc_a1b2c3d4e5f6_p2_c0",
        "..."
    ],
    "extraction_time_ms": 450.5,
    "indexing_time_ms": 120.3
}
```

## Error Handling

### File Too Large (400)

```json
{
    "detail": "File too large: 12.5MB. Maximum allowed: 10MB"
}
```

### Unsupported Format (400)

```json
{
    "detail": "Unsupported file type: application/zip. Supported types: PDF, images, and text files."
}
```

### No Text Detected (400)

```json
{
    "detail": "Failed to extract text from image: No text detected in image"
}
```

### Server Error (500)

```json
{
    "detail": "Error processing document: [error details]"
}
```

## Processing Pipeline

```
┌─────────────────┐
│  Upload File    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Validate File  │ ← Max 10MB, check format
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Extract Text   │ ← PDF parsing / OCR
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Chunk Text     │ ← 512 char chunks, 50 overlap
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Generate IDs   │ ← doc_xxx_p1_c0 format
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Create Chunks   │ ← With metadata
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Index to Chroma │ ← Generate embeddings
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Return Stats   │
└─────────────────┘
```

## Chunk ID Format

Chunks are named with a hierarchical format:

```
{document_id}_p{page_number}_c{chunk_index}
```

Examples:
- `doc_abc123_p1_c0` - Document abc123, page 1, chunk 0
- `doc_abc123_p1_c1` - Document abc123, page 1, chunk 1
- `doc_abc123_p2_c0` - Document abc123, page 2, chunk 0

## Performance

| File Type | Size | Extraction Time | Indexing Time | Total |
|-----------|------|-----------------|---------------|-------|
| PDF (text) | 500KB | ~200ms | ~100ms | ~300ms |
| PDF (scanned) | 500KB | ~2000ms (OCR) | ~100ms | ~2100ms |
| Image (JPG) | 200KB | ~800ms (OCR) | ~80ms | ~880ms |
| Text | 50KB | ~10ms | ~50ms | ~60ms |

*Times are approximate and depend on hardware*

## OCR Requirements

For image processing, Tesseract OCR must be installed:

### Windows
```bash
# Download installer from:
# https://github.com/UB-Mannheim/tesseract/wiki

# Or via chocolatey:
choco install tesseract

# Set path in code:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

### macOS
```bash
brew install tesseract
```

## Configuration

Adjust in `.env`:

```env
# Maximum upload size (MB)
MAX_UPLOAD_SIZE=10

# Chunking
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

## Testing

Run the upload test suite:

```bash
python test_upload.py
```

Creates a test text file and:
1. Uploads it
2. Searches semantically
3. Filters by metadata
4. Performs hybrid search
5. Shows statistics

## Integration Example

Complete workflow from upload to search:

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Upload document
with open("invoice.pdf", "rb") as f:
    files = {"file": f}
    data = {"user_id": "user_001", "tags": "invoice,paid"}
    
    upload_response = requests.post(
        f"{BASE_URL}/vector/upload",
        files=files,
        data=data
    )
    
    doc_id = upload_response.json()["document_id"]
    print(f"Uploaded: {doc_id}")

# 2. Search immediately
search_response = requests.post(
    f"{BASE_URL}/vector/search/semantic",
    json={
        "query": "What is the total amount?",
        "top_k": 3
    }
)

results = search_response.json()
for result in results["results"]:
    print(f"Score: {result['similarity_score']}")
    print(f"Content: {result['content'][:100]}")

# 3. Filter by document
filter_response = requests.post(
    f"{BASE_URL}/vector/search/metadata",
    json={
        "filters": {"document_id": doc_id},
        "top_k": 100
    }
)

chunks = filter_response.json()
print(f"Document has {chunks['total_results']} chunks")
```

## Advantages

✅ **Single API Call** - Upload and index in one step
✅ **Automatic Processing** - No manual chunking needed
✅ **Format Detection** - Auto-detects file type
✅ **OCR Support** - Extract text from images
✅ **Metadata Rich** - Tags, source type, pages tracked
✅ **Performance Metrics** - Timing included in response

## Use Cases

- **Invoice Processing** - Upload invoices, search for amounts/dates
- **Document Management** - Upload contracts, search clauses
- **Receipt Tracking** - Upload receipt photos, extract via OCR
- **Knowledge Base** - Upload PDFs, enable semantic search
- **Email Attachments** - Process attached documents
- **Scanned Documents** - OCR historical paper documents

## Next Steps

1. Add authentication/authorization
2. Implement rate limiting
3. Add virus scanning
4. Support more formats (DOCX, Excel, etc.)
5. Batch upload endpoint
6. Delete document endpoint
7. Update document endpoint
8. Progress tracking for long uploads

## See Also

- [README.md](README.md) - Full system documentation
- [API_EXAMPLES.md](API_EXAMPLES.md) - More API examples
- [QUICKSTART.md](QUICKSTART.md) - Setup instructions
