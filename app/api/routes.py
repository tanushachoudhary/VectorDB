from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from typing import Dict, Any, Optional
import logging
import time
import uuid
from app.models.schemas import (
    IndexRequest, SearchResponse, IndexStats, ErrorResponse,
    SearchRequest,
    ChunkModel, MetadataModel
)
from app.services.vector_service import VectorService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vector", tags=["vector"])

# Initialize services
vector_service = VectorService()


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
