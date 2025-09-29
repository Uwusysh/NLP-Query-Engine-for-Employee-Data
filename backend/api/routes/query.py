from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel
from backend.api.services.query_engine import QueryEngine
from backend.api.models.database import QueryHistory, create_system_tables
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, desc, func
from datetime import datetime, timedelta
import json

router = APIRouter(prefix="/api/query", tags=["query"])

class QueryRequest(BaseModel):
    query: str
    connection_string: str

class QueryResponse(BaseModel):
    results: List[Dict[str, Any]] = []  # Make optional with default
    query_type: str
    response_time: float
    cache_hit: bool = False
    results_count: int = 0  # Make optional with default
    sql_generated: str = None
    mapping_used: Dict = None
    error: str = None
    # Add hybrid-specific fields
    sql_results: List[Dict[str, Any]] = None
    document_results: List[Dict[str, Any]] = None
    sql_count: int = 0
    document_count: int = 0
    combined_count: int = 0

    class Config:
        extra = 'allow'  # Allow extra fields

# Store query engines by connection string
query_engines = {}

def get_system_session():
    """Get system database session"""
    engine = create_system_tables()
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@router.post("", response_model=QueryResponse)
async def process_query(
    request: QueryRequest, 
    db_session: Session = Depends(get_system_session)
):
    """Process natural language query with better error handling"""
    try:
        # Get or create query engine for this connection
        if request.connection_string not in query_engines:
            query_engine = QueryEngine(request.connection_string)
            await query_engine.initialize()
            query_engines[request.connection_string] = query_engine
        else:
            query_engine = query_engines[request.connection_string]
        
        # Process query
        result = query_engine.process_query(request.query, db_session)
        
        # Ensure required fields are present
        if 'results' not in result:
            result['results'] = []
        if 'results_count' not in result:
            result['results_count'] = len(result.get('results', []))
        if 'cache_hit' not in result:
            result['cache_hit'] = False
            
        return QueryResponse(**result)
        
    except Exception as e:
        print(f"Query processing error: {e}")
        # Return valid response even on error
        return QueryResponse(
            results=[],
            query_type="error",
            response_time=0.0,
            cache_hit=False,
            results_count=0,
            error=f"Query processing failed: {str(e)}"
        )

@router.get("/history")
async def get_query_history(
    limit: int = 10,
    db_session: Session = Depends(get_system_session)
):
    """Get previous queries for caching demo"""
    try:
        history = db_session.query(QueryHistory)\
            .order_by(desc(QueryHistory.executed_at))\
            .limit(limit)\
            .all()
        
        return {
            "queries": [
                {
                    "id": item.id,
                    "query_text": item.query_text,
                    "query_type": item.query_type,
                    "results_count": item.results_count,
                    "response_time": item.response_time,
                    "cache_hit": bool(item.cache_hit),
                    "executed_at": item.executed_at.isoformat()
                }
                for item in history
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get query history: {str(e)}")

@router.get("/metrics")
async def get_performance_metrics(db_session: Session = Depends(get_system_session)):
    """Get performance metrics"""
    try:
        # Calculate average response time
        avg_response_time = db_session.query(
            func.avg(QueryHistory.response_time)
        ).scalar() or 0
        
        # Calculate cache hit rate
        total_queries = db_session.query(QueryHistory).count()
        cache_hits = db_session.query(QueryHistory).filter(QueryHistory.cache_hit == 1).count()
        cache_hit_rate = (cache_hits / total_queries * 100) if total_queries > 0 else 0
        
        # Get recent query count
        last_hour = datetime.utcnow() - timedelta(hours=1)
        recent_queries = db_session.query(QueryHistory)\
            .filter(QueryHistory.executed_at >= last_hour)\
            .count()
        
        return {
            "avg_response_time": round(avg_response_time, 2),
            "cache_hit_rate": round(cache_hit_rate, 2),
            "total_queries": total_queries,
            "recent_queries": recent_queries,
            "active_connections": len(query_engines)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")