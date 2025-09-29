from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import tempfile
import os
import asyncio
from backend.api.services.schema_discovery import SchemaDiscovery
from backend.api.services.document_processor import DocumentProcessor
from backend.api.models.database import get_engine, create_system_tables, Document, get_metadata
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import uuid

router = APIRouter(prefix="/api/ingest", tags=["ingestion"])

# In-memory storage for ingestion status (in production, use Redis)
ingestion_status = {}
schema_cache = {}

@router.post("/database")
async def connect_database(connection_string: str = Form(...)):
    """Connect to database and discover schema"""
    try:
        # Validate connection string format
        if not connection_string:
            raise HTTPException(status_code=400, detail="Connection string is required")
        
        # Test connection and discover schema
        schema_discovery = SchemaDiscovery()
        schema = schema_discovery.analyze_database(connection_string)
        
        # Cache schema
        schema_cache[connection_string] = schema
        
        return {
            "status": "success",
            "message": "Database connected successfully",
            "schema": {
                "tables_count": len(schema['tables']),
                "relationships_count": len(schema['relationships']),
                "tables": list(schema['tables'].keys()),
                "table_purposes": schema['table_purposes']
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/documents")
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """Upload and process multiple documents"""
    try:
        # Create system tables if they don't exist
        system_engine = create_system_tables()
        
        # Create temporary directory for uploaded files
        temp_dir = tempfile.mkdtemp()
        file_paths = []
        
        # Save uploaded files
        for file in files:
            # Validate file type
            allowed_types = ['.pdf', '.docx', '.txt', '.csv']
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension not in allowed_types:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File type {file_extension} not allowed. Allowed types: {allowed_types}"
                )
            
            # Save file
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            file_paths.append(file_path)
        
        # Create job ID
        job_id = str(uuid.uuid4())
        ingestion_status[job_id] = {
            "status": "processing",
            "total_files": len(file_paths),
            "processed_files": 0,
            "failed_files": 0,
            "documents": []
        }
        
        # Process documents in background
        background_tasks.add_task(
            process_documents_background,
            job_id,
            file_paths,
            system_engine
        )
        
        return {
            "job_id": job_id,
            "status": "processing",
            "total_files": len(file_paths),
            "message": f"Started processing {len(file_paths)} files"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def process_documents_background(job_id: str, file_paths: List[str], system_engine):
    """Background task to process documents"""
    try:
        processor = DocumentProcessor()
        
        # Create database session
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(bind=system_engine)
        db_session = SessionLocal()
        
        # Process documents
        results = await processor.process_documents(file_paths, db_session)
        
        # Update status
        ingestion_status[job_id] = {
            "status": "completed",
            "total_files": len(file_paths),
            "processed_files": results['processed'],
            "failed_files": results['failed'],
            "documents": results['documents']
        }
        
        # Cleanup temporary files
        for file_path in file_paths:
            try:
                os.remove(file_path)
            except:
                pass
        os.rmdir(os.path.dirname(file_paths[0]))
        
        db_session.close()
        
    except Exception as e:
        ingestion_status[job_id] = {
            "status": "error",
            "error": str(e)
        }

@router.get("/status/{job_id}")
async def get_ingestion_status(job_id: str):
    """Get ingestion processing status"""
    status = ingestion_status.get(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return status

@router.get("/schema")
async def get_schema(connection_string: str):
    """Get discovered schema for visualization"""
    schema = schema_cache.get(connection_string)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found. Please connect to database first.")
    
    return {
        "tables": schema['tables'],
        "relationships": schema['relationships'],
        "table_purposes": schema['table_purposes'],
        "sample_data": schema['sample_data']
    }