from typing import List
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class ChunkingService:
    """Service for splitting text into chunks with configurable size and overlap."""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        Initialize chunking service.
        
        Args:
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between consecutive chunks
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
    
    def chunk_text(self, text: str, document_id: str) -> List[dict]:
        """
        Split text into chunks with overlap.
        
        Args:
            text: Text to chunk
            document_id: ID of the document being chunked
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        chunks = []
        step_size = self.chunk_size - self.chunk_overlap
        
        for i in range(0, len(text), step_size):
            chunk_text = text[i : i + self.chunk_size]
            
            if chunk_text.strip():  # Only include non-empty chunks
                chunk_info = {
                    "content": chunk_text,
                    "chunk_index": len(chunks),
                    "start_pos": i,
                    "end_pos": min(i + self.chunk_size, len(text))
                }
                chunks.append(chunk_info)
        
        logger.info(f"Split document {document_id} into {len(chunks)} chunks")
        return chunks
