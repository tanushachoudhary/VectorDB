from typing import List, Dict, Any
from datetime import datetime
from app.models.schemas import SearchRequest,SearchResult
from app.models.schemas import (ChunkModel, MetadataModel)
from app.repository.vector_repo import VectorRepository
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
import logging
import time

logger = logging.getLogger(__name__)


class VectorService:
    """Service layer for vector operations."""
    
    def __init__(self):
        """Initialize vector service with repository and external services."""
        self.repository = VectorRepository()
        self.chunking_service = ChunkingService()
        self.embedding_service = EmbeddingService()
    
    def index_document(
        self,
        document_id: str,
        user_id: str,
        content: str,
        source: str = "pdf",
        page_number: int = 1,
        tags: List[str] = None # type: ignore
    ) -> Dict[str, Any]:
        """
        Index a complete document by chunking and embedding.
        
        Args:
            document_id: Unique document ID
            user_id: User who owns the document
            content: Full document text
            source: Source type (ocr, pdf, image)
            page_number: Page number of the document
            tags: List of tags for categorization
            
        Returns:
            Dictionary with indexing results
        """
        if not content or not content.strip():
            raise ValueError("Content cannot be empty")
        
        try:
            # Chunk the document
            chunk_infos = self.chunking_service.chunk_text(content, document_id)
            
            # Create ChunkModel objects
            chunks = []
            for chunk_info in chunk_infos:
                chunk_id = f"{document_id}_chunk_{chunk_info['chunk_index']}"
                
                metadata = MetadataModel(
                    source=source,
                    page_number=page_number,
                    chunk_index=chunk_info['chunk_index'],
                    created_at=datetime.utcnow().isoformat(),
                    tags=tags or []
                )
                
                chunk = ChunkModel(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    user_id=user_id,
                    content=chunk_info['content'],
                    metadata=metadata
                )
                
                chunks.append(chunk)
            
            # Index chunks
            result = self.repository.index_chunks(chunks)
            result["document_id"] = document_id
            result["total_chunks"] = len(chunks)
            
            logger.info(f"Indexed document {document_id} with {len(chunks)} chunks")
            return result
        
        except Exception as e:
            logger.error(f"Error indexing document: {str(e)}")
            raise

    async def smart_search(self, request: SearchRequest):
        start_time = time.time()
        
        # Safely extract attributes using getattr(object, name, default)
        # This prevents the "Attribute unknown" error
        query = getattr(request, 'query', None)
        filters = getattr(request, 'filters', None)
        top_k = getattr(request, 'top_k', 5)
        weight = getattr(request, 'weight_vector', 0.7)

        # 1. Detect Hybrid (Both present)
        if query and filters:
            logger.info("Strategy: HYBRID")
            results = self.repository.hybrid_search(
                query=query, 
                filters=filters, 
                top_k=top_k, 
                weight_vector=weight
            )
                
        # 2. Detect Semantic (Query present, no filters)
        elif query:
            logger.info("Strategy: SEMANTIC")
            results = self.repository.semantic_search(
                query=query, 
                top_k=top_k
            )
                
        # 3. Detect Metadata (Filters present, no query)
        elif filters:
            logger.info("Strategy: METADATA")
            results = self.repository.metadata_search(
                filters=filters, 
                top_k=top_k
            )
                
        else:
            # Fallback for empty requests
            results = []

        formatted_results = []
    
        for chunk, score in results:
            # Map the ChunkModel and the float score to the SearchResult schema
            search_result = SearchResult(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                user_id=chunk.user_id,
                content=chunk.content,
                metadata=chunk.metadata,
                similarity_score=score
            )
            formatted_results.append(search_result)

        execution_time = (time.time() - start_time) * 1000
        return formatted_results, execution_time
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        return self.repository.get_stats()
