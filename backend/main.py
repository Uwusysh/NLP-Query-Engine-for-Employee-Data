from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from backend.api.routes import ingestion, query, schema
from backend.config import settings

app = FastAPI(
    title="NLP Query Engine for Employee Data",
    description="A natural language query system that dynamically adapts to database schemas",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingestion.router)
app.include_router(query.router)
app.include_router(schema.router)

@app.get("/")
async def root():
    return {"message": "NLP Query Engine API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Serve frontend in production
if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if not full_path.startswith("api"):
            return FileResponse("frontend/dist/index.html")
        raise HTTPException(status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )