from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
from app.core.qdrant import init_qdrant_collection
from app.api.upload import router as upload_router
from app.api.chat import router as chat_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern FastAPI async lifespan context manager handling boot and shutdown configurations."""
    # 1. Boot up: Create SQL schemas/tables
    print("[STARTUP] Triggering PostgreSQL database table migrations...")
    Base.metadata.create_all(bind=engine)
    print("[STARTUP] Database migrations committed successfully!")
    
    # 2. Boot up: Verify/Initialize Qdrant collection configuration
    print("[STARTUP] Syncing Qdrant vector database collection structures...")
    init_qdrant_collection()
    
    yield
    # Cleanup shutdown resources if needed (e.g. database pool termination)
    print("[SHUTDOWN] Exiting backend application, cleaning connection pools...")

app = FastAPI(
    title="PalmMind Agentic RAG Platform",
    description="Enterprise-ready, privacy-first Agentic RAG backend system powered by local llama.cpp and LangGraph.",
    version="1.0.0",
    lifespan=lifespan
)

# Register CORS middleware for robust integration with frontend orchestrators
# Parses trusted origins from a comma-separated configuration string (defaults to '*' in local environment)
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["System Diagnostics"])
def health_check():
    """Diagnostic endpoint checking service operational status."""
    return {
        "status": "healthy",
        "service": "PalmMind RAG Agent Backend",
        "llm_engine": "llama.cpp (GPU-accelerated host execution)"
    }

# Register Core Ingestion and Chat Endpoints
app.include_router(upload_router)
app.include_router(chat_router)
