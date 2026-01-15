from sentence_transformers import SentenceTransformer
from typing import List, Union
from app.core.config import settings
import logging
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using Sentence Transformers."""
    
    def __init__(self, model_name: str = None):
        """
        Initialize embedding service.
        
        Args:
            model_name: Name of the embedding model
        """
        self.model_name = model_name or settings.embedding_model
        
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded with dimension: {self.embedding_dimension}")
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            raise
    
    def embed(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text(s).
        
        Args:
            texts: Single text or list of texts
            
        Returns:
            Single embedding or list of embeddings
        """
        if isinstance(texts, str):
            if not texts.strip():
                raise ValueError("Text cannot be empty")
            
            embeddings = self.model.encode([texts])
            return embeddings[0].tolist()
        
        elif isinstance(texts, list):
            if not texts:
                raise ValueError("Text list cannot be empty")
            
            # Filter out empty texts
            filtered_texts = [t for t in texts if t and t.strip()]
            if not filtered_texts:
                raise ValueError("All texts are empty")
            
            embeddings = self.model.encode(filtered_texts)
            return embeddings.tolist()
        
        else:
            raise ValueError("texts must be string or list of strings")
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings."""
        return self.embedding_dimension
