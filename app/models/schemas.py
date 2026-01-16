from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class MetadataModel(BaseModel):
    """Metadata for a document chunk."""
    source: str = Field(..., description="Source type: ocr, pdf, or image")
    page_number: int = Field(..., description="Page number in the document")
    chunk_index: int = Field(..., description="Index of chunk within document")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="ISO timestamp")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "pdf",
                "page_number": 1,
                "chunk_index": 0,
                "created_at": "2026-01-15T10:30:00",
                "tags": ["invoice", "financial"]
            }
        }


class ChunkModel(BaseModel):
    """A text chunk with embedding metadata."""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Document this chunk belongs to")
    user_id: str = Field(..., description="User who owns this document")
    content: str = Field(..., description="Text content of the chunk")
    metadata: MetadataModel = Field(..., description="Rich metadata for the chunk")
    
    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "chunk_001",
                "document_id": "doc_001",
                "user_id": "u1",
                "content": "This is the extracted text content...",
                "metadata": {
                    "source": "pdf",
                    "page_number": 1,
                    "chunk_index": 0,
                    "created_at": "2026-01-15T10:30:00",
                    "tags": ["invoice"]
                }
            }
        }


class IndexRequest(BaseModel):
    """Request to index document chunks."""
    chunks: List[ChunkModel] = Field(..., description="List of chunks to index")
    
    class Config:
        json_schema_extra = {
            "example": {
                "chunks": [
                    {
                        "chunk_id": "chunk_001",
                        "document_id": "doc_001",
                        "user_id": "u1",
                        "content": "Invoice details...",
                        "metadata": {
                            "source": "pdf",
                            "page_number": 1,
                            "chunk_index": 0,
                            "created_at": "2026-01-15T10:30:00",
                            "tags": ["invoice"]
                        }
                    }
                ]
            }
        }


class SearchResult(BaseModel):
    """A single search result."""
    chunk_id: str
    document_id: str
    user_id: str
    content: str
    metadata: MetadataModel
    similarity_score: float = Field(..., description="Similarity score (0-1)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "chunk_001",
                "document_id": "doc_001",
                "user_id": "u1",
                "content": "Invoice details...",
                "metadata": {
                    "source": "pdf",
                    "page_number": 1,
                    "chunk_index": 0,
                    "created_at": "2026-01-15T10:30:00",
                    "tags": ["invoice"]
                },
                "similarity_score": 0.95
            }
        }


class MetadataFilter(BaseModel):
    """Metadata filter for search."""
    source: Optional[str] = Field(None, description="Filter by source type")
    page_number: Optional[int] = Field(None, description="Filter by page number")
    tags: Optional[List[str]] = Field(None, description="Filter by tags (OR operation)")
    document_id: Optional[str] = Field(None, description="Filter by document ID")
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "pdf",
                "page_number": 1,
                "tags": ["invoice"],
                "document_id": "doc_001",
                "user_id": "u1"
            }
        }


class SemanticSearchRequest(BaseModel):
    """Request for semantic search."""
    query: str = Field(..., description="Search query text")
    top_k: int = Field(default=5, ge=1, le=100, description="Number of results to return")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "invoice amount",
                "top_k": 5
            }
        }


class MetadataSearchRequest(BaseModel):
    """Request for metadata-filtered search."""
    filters: MetadataFilter = Field(..., description="Metadata filters")
    top_k: int = Field(default=5, ge=1, le=100, description="Number of results to return")
    
    class Config:
        json_schema_extra = {
            "example": {
                "filters": {
                    "source": "pdf",
                    "page_number": 1,
                    "tags": ["invoice"]
                },
                "top_k": 5
            }
        }


class HybridSearchRequest(BaseModel):
    """Request for hybrid search (vector + metadata)."""
    query: str = Field(..., description="Search query text")
    filters: MetadataFilter = Field(..., description="Metadata filters")
    top_k: int = Field(default=5, ge=1, le=100, description="Number of results to return")
    weight_vector: float = Field(default=0.7, ge=0, le=1, description="Weight for vector search (0-1)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "invoice amount",
                "filters": {
                    "source": "pdf",
                    "tags": ["invoice"]
                },
                "top_k": 5,
                "weight_vector": 0.7
            }
        }

from typing import Union

# This defines SearchRequest as any of the three specific types
SearchRequest = Union[HybridSearchRequest, SemanticSearchRequest, MetadataSearchRequest]
class SearchResponse(BaseModel):
    """Response containing search results."""
    results: List[SearchResult]
    total_results: int
    query_time_ms: float = Field(..., description="Query execution time in milliseconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "results": [],
                "total_results": 0,
                "query_time_ms": 45.2
            }
        }


class IndexStats(BaseModel):
    """Statistics about the vector database."""
    total_chunks: int
    total_documents: int
    total_users: int
    collection_name: str
    embedding_dimension: int
    chunk_size: int
    chunk_overlap: int
    embedding_model: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_chunks": 150,
                "total_documents": 10,
                "total_users": 5,
                "collection_name": "document_chunks",
                "embedding_dimension": 384,
                "chunk_size": 512,
                "chunk_overlap": 50,
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
            }
        }


class DocumentChunkingResponse(BaseModel):
    """Response for document chunking."""
    status: str
    message: str
    document_id: str
    user_id: str
    filename: str
    source: str
    total_pages: int
    total_chunks: int
    chunks: List[ChunkModel]
    chunk_ids: List[str]
    extraction_time_ms: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Document chunked successfully",
                "document_id": "doc_123",
                "user_id": "u1",
                "filename": "invoice.pdf",
                "source": "pdf",
                "total_pages": 3,
                "total_chunks": 12,
                "chunks": [],
                "chunk_ids": ["doc_123_p1_c0", "doc_123_p1_c1"],
                "extraction_time_ms": 450.5
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid request",
                "detail": "Query cannot be empty"
            }
        }


class DocumentUploadResponse(BaseModel):
    """Response for document upload."""
    status: str
    message: str
    document_id: str
    user_id: str
    filename: str
    source: str
    total_pages: int
    total_chunks: int
    chunk_ids: List[str]
    extraction_time_ms: float
    indexing_time_ms: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Document uploaded and indexed successfully",
                "document_id": "doc_123",
                "user_id": "u1",
                "filename": "invoice.pdf",
                "source": "pdf",
                "total_pages": 3,
                "total_chunks": 12,
                "chunk_ids": ["doc_123_chunk_0", "doc_123_chunk_1"],
                "extraction_time_ms": 450.5,
                "indexing_time_ms": 120.3
            }
        }

