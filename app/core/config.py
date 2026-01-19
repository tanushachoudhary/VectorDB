from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Union


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = "Vector Database Search System"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Vector Database
    chroma_persist_directory: str = "./chroma_db"
    collection_name: str = "document_chunks"
    
    # Embedding Model
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    
    # Chunking Configuration
    chunk_size: Union[int, str] = 1000  # Can be int or "semantic" for semantic chunking
    chunk_overlap: int = 0  # Not used in semantic chunking
    semantic_similarity_threshold: float = 0.5  # Similarity threshold for grouping sentences
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()