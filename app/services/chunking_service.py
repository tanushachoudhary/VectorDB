"""
1. first break text into sentences uses regex pattern (?<=[.!?])\s+ to ensure splits on punctuation followed by space

2. each sentence passed through sentence transformer (embedding model) to get vector representation

3. iterate through sentences calculating cosine similarity between consecutive sentence embeddings

4.  i. if similarity lower than threshold (0.5),assumes the topic has changed and  starts a new chunk.
    ii. If the chunk is getting too long (exceeding chunk_size), it forces a break even if the topic is the same, to ensure the data fits within the LLM's context window.

5. it wraps the text in a dictionary containing start_pos, end_pos, and chunk_index.
"""
from typing import List
from app.core.config import settings
import logging
import re
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class ChunkingService:
    """Service for semantic chunking based on sentence embeddings and similarity."""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        Initialize semantic chunking service.
        
        Args:
            chunk_size: Target size of each chunk in characters (soft limit)
            chunk_overlap: Not used in semantic chunking but kept for compatibility
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
       
        """
        Low Threshold (0.3 - 0.4): Chunks will be larger. The system is "forgiving" and will keep sentences together even if the topic shifts slightly. Good for long-form essays or narratives.

        High Threshold (0.7 - 0.8): Chunks will be smaller. The system is "strict" and will start a new chunk at the slightest change in wording. Good for technical manuals or legal FAQs.

        Recommended Starting Point (0.5 - 0.6): Usually the "sweet spot" for most general documents.
        """
        
        self.similarity_threshold = 0.5  # Threshold for semantic similarity
        
        # Initialize embedding model for semantic analysis
        logger.info(f"Loading embedding model for semantic chunking: {settings.embedding_model}")
        self.model = SentenceTransformer(settings.embedding_model)
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using regex patterns.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Split on sentence boundaries (., !, ?) followed by whitespace or newlines
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)
        
        # Filter out empty sentences and strip whitespace
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _calculate_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            emb1: First embedding vector
            emb2: Second embedding vector
            
        Returns:
            Similarity score (0-1)
        """
        return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    
    def chunk_text(self, text: str, document_id: str) -> List[dict]:
        """
        Split text into semantic chunks based on sentence embeddings and similarity.
        
        This method:
        1. Splits text into sentences
        2. Computes embeddings for each sentence
        3. Groups sentences together when similarity is above threshold
        4. Creates chunk boundaries when similarity drops
        5. Respects approximate chunk_size as a soft limit
        
        Args:
            text: Text to chunk
            document_id: ID of the document being chunked
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Split into sentences
        sentences = self._split_into_sentences(text)
        
        if not sentences:
            raise ValueError("No sentences found in text")
        
        logger.info(f"Document {document_id}: Split into {len(sentences)} sentences")
        
        # Generate embeddings for all sentences
        logger.info(f"Generating embeddings for {len(sentences)} sentences")
        embeddings = self.model.encode(sentences, convert_to_numpy=True)
        
        # Create semantic chunks
        chunks = []
        current_chunk = [sentences[0]]
        current_chunk_length = len(sentences[0])
        start_pos = 0
        
        for i in range(1, len(sentences)):
            # Calculate similarity with previous sentence
            similarity = self._calculate_similarity(embeddings[i-1], embeddings[i])
            
            sentence_length = len(sentences[i])
            
            # Decide whether to add to current chunk or start new chunk
            should_create_new_chunk = (
                similarity < self.similarity_threshold or  # Low semantic similarity
                current_chunk_length + sentence_length > self.chunk_size  # Size limit reached
            )
            
            if should_create_new_chunk and current_chunk:
                # Finalize current chunk
                chunk_content = ' '.join(current_chunk)
                chunk_info = {
                    "content": chunk_content,
                    "chunk_index": len(chunks),
                    "start_pos": start_pos,
                    "end_pos": start_pos + len(chunk_content),
                    "sentence_count": len(current_chunk)
                }
                chunks.append(chunk_info)
                
                # Start new chunk
                current_chunk = [sentences[i]]
                current_chunk_length = sentence_length
                start_pos = chunk_info["end_pos"] + 1
            else:
                # Add sentence to current chunk
                current_chunk.append(sentences[i])
                current_chunk_length += sentence_length + 1  # +1 for space
        
        # Add final chunk
        if current_chunk:
            chunk_content = ' '.join(current_chunk)
            chunk_info = {
                "content": chunk_content,
                "chunk_index": len(chunks),
                "start_pos": start_pos,
                "end_pos": start_pos + len(chunk_content),
                "sentence_count": len(current_chunk)
            }
            chunks.append(chunk_info)
        
        logger.info(f"Split document {document_id} into {len(chunks)} semantic chunks")
        return chunks
