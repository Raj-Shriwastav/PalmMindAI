from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.ingestion import IngestionService
from app.schemas.upload import UploadResponse

router = APIRouter(tags=["Document Ingestion"])

@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    chunk_strategy: str = Form("recursive", description="Options: 'recursive' or 'semantic'"),
    chunk_size: int = Form(500, description="Used in recursive chunking character count limit"),
    chunk_overlap: int = Form(50, description="Used in recursive chunking overlap size"),
    similarity_percentile: float = Form(90.0, description="Used in semantic chunking transition thresholds"),
    db: Session = Depends(get_db)
):
    """Accepts `.pdf` or `.txt` uploads, chunks the plain text, generates Snowflake Arctic vector embeddings, and stores them in Qdrant and Postgres databases."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required and cannot be empty."
        )
        
    try:
        # Read inbound file payload
        file_bytes = await file.read()
        
        # Instantiate Ingestion Service
        service = IngestionService(db)
        
        # Process and ingest
        response = service.ingest_document(
            filename=file.filename,
            file_bytes=file_bytes,
            chunk_strategy=chunk_strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            similarity_percentile=similarity_percentile
        )
        return response
        
    except ValueError as e:
        # Handle client errors (e.g. invalid file extension or empty file text)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Handle server-side/service exceptions gracefully
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An ingestion pipeline failure occurred: {str(e)}"
        )
