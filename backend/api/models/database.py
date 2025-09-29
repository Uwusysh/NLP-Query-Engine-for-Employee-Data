from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Document(Base):
    __tablename__ = "system_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    content = Column(Text)
    file_path = Column(String(500))
    file_size = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Integer, default=0)  # 0: pending, 1: processing, 2: completed, 3: error

class QueryHistory(Base):
    __tablename__ = "query_history"
    
    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50))  # sql, document, hybrid
    results_count = Column(Integer)
    response_time = Column(Float)
    cache_hit = Column(Integer, default=0)
    executed_at = Column(DateTime, default=datetime.utcnow)

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer)
    chunk_index = Column(Integer)
    content = Column(Text)
    embedding = Column(Text)  # Store as JSON string for simplicity
    tokens_count = Column(Integer)

def get_engine(connection_string: str):
    """Create SQLAlchemy engine for dynamic database connection"""
    return create_engine(connection_string)

def get_metadata(connection_string: str):
    """Get database metadata for schema discovery"""
    engine = get_engine(connection_string)
    return MetaData(bind=engine)

def create_system_tables():
    """Create system tables for the application"""
    engine = create_engine("sqlite:///./system.db")
    Base.metadata.create_all(bind=engine)
    return engine