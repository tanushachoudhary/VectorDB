from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from typing import Dict, Any, Optional
import logging
import time
import uuid
from app.models.schemas import (
    IndexRequest, SearchResponse, IndexStats, ErrorResponse,
    SearchRequest,
    ChunkModel, MetadataModel, DocumentChunkingResponse
)
from app.services.vector_service import VectorService
from app.services.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vector", tags=["vector"])

# Initialize services
vector_service = VectorService()
document_processor = DocumentProcessor()


@router.post(
    "/upload",
    response_model=DocumentChunkingResponse,
    responses={
        200: {"description": "Document chunked successfully"},
        400: {"model": ErrorResponse, "description": "Invalid file or parameters"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def upload_document(
    file: UploadFile = File(..., description="Document file (PDF, image, or text)"),
    user_id: str = Form(..., description="User ID who owns the document"),
    tags: Optional[str] = Form(None, description="Comma-separated tags (e.g., 'invoice,financial,2026')")
):
    """
    Upload and chunk a document (without indexing).
    
    Supports:
    - PDF files (text extraction)
    - Images (OCR using Tesseract)
    - Text files
    
    Returns chunks for user to index manually via POST /vector/index.
    """
    extraction_start = time.time()
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Validate file
        document_processor.validate_file(file_content, max_size_mb=10)
        
        # Extract text
        extraction_result = document_processor.extract_text_from_file(
            file_content,
            file.filename,
            file.content_type
        )
        
        extraction_time_ms = (time.time() - extraction_start) * 1000
        
        # Generate document ID
        document_id = f"doc_{uuid.uuid4().hex[:12]}"
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        
        # Create chunks for each page
        all_chunks = []
        chunk_ids = []
        
        for page_data in extraction_result["pages"]:
            page_text = page_data["text"]
            page_number = page_data["page_number"]
            
            # Chunk the text
            chunk_infos = vector_service.chunking_service.chunk_text(page_text, document_id)
            
            # Create ChunkModel objects
            for chunk_info in chunk_infos:
                chunk_id = f"{document_id}_p{page_number}_c{chunk_info['chunk_index']}"
                
                metadata = MetadataModel(
                    source=extraction_result["source"],
                    page_number=page_number,
                    chunk_index=chunk_info['chunk_index'],
                    tags=tag_list
                )
                
                chunk = ChunkModel(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    user_id=user_id,
                    content=chunk_info['content'],
                    metadata=metadata
                )
                
                all_chunks.append(chunk)
                chunk_ids.append(chunk_id)
        
        logger.info(
            f"Chunked document {document_id}: "
            f"{len(all_chunks)} chunks from {extraction_result['total_pages']} pages"
        )
        
        return DocumentChunkingResponse(
            status="success",
            message=f"Document '{file.filename or 'unknown'}' chunked successfully. Use POST /vector/index to index these chunks.",
            document_id=document_id,
            user_id=user_id,
            filename=file.filename or "unknown",
            source=extraction_result["source"],
            total_pages=extraction_result["total_pages"],
            total_chunks=len(all_chunks),
            chunks=all_chunks,
            chunk_ids=chunk_ids,
            extraction_time_ms=round(extraction_time_ms, 2)
        )
    
    except ValueError as e:
        logger.warning(f"Validation error in document upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )


@router.post(
    "/index",
    response_model=Dict[str, Any],
    responses={
        200: {"description": "Chunks indexed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def index_chunks(request: IndexRequest):
    """
    Index document chunks into the vector database.
    
    Takes extracted text chunks and stores them with embeddings and metadata.
    """
    try:
        if not request.chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chunks list cannot be empty"
            )
        
        # Index chunks using repository
        result = vector_service.repository.index_chunks(request.chunks)
        
        return {
            "status": "success",
            "message": f"Successfully indexed {result['chunks_indexed']} chunks",
            **result
        }
    
    except ValueError as e:
        logger.warning(f"Validation error in indexing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Error indexing chunks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error indexing chunks"
        )


@router.post(
    "/search",
    response_model=SearchResponse,
    responses={
        200: {"description": "Search successful"},
        400: {"model": ErrorResponse, "description": "Invalid parameters"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def unified_search(request: SearchRequest):
    """
    Unified search endpoint that auto-selects strategy:
    - Semantic: Only 'query' provided
    - Metadata: Only 'filters' provided
    - Hybrid: Both 'query' and 'filters' provided
    """
    try:
        # Basic validation: must provide at least one
        query = getattr(request, 'query', None)
        filters = getattr(request, 'filters', None)
        if not query and not filters:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide 'query' and/or 'filters'"
            )

        results, query_time_ms = await vector_service.smart_search(request)
        return SearchResponse(
            results=results,
            total_results=len(results),
            query_time_ms=round(query_time_ms, 2)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Search failure: {str(e)}")
        raise HTTPException(status_code=500, detail="Search execution failed.")


@router.get(
    "/stats",
    response_model=IndexStats,
    responses={
        200: {"description": "Stats retrieved successfully"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def get_stats():
    """
    Get statistics about the vector database.
    
    Returns total chunks, documents, users, and configuration details.
    """
    try:
        stats = vector_service.get_stats()
        return IndexStats(**stats)
    
    except Exception as e:
        logger.error(f"Error retrieving stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving database statistics"
        )
