from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./test.db"
    pool_size: int = 10
    
    # Embeddings
    embeddings_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    batch_size: int = 32
    
    # Cache
    cache_ttl_seconds: int = 300
    cache_max_size: int = 1000
    
    # File upload
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: list = [".pdf", ".docx", ".txt", ".csv"]
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()