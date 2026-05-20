from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.ingestion import IngestionService
from app.schemas.upload import UploadResponse

router = APIRouter(tags=["Document Ingestion"])

# Max file size limit: 10 MB (10,485,760 bytes) to mitigate memory exhaustion
MAX_FILE_SIZE = 10 * 1024 * 1024

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
    import os
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required and cannot be empty."
        )

    # Extract only the base name to prevent directory traversal exploits
    filename = os.path.basename(file.filename)
    if not filename.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename: name cannot resolve to empty text."
        )

    # 1. Parameter Input Boundaries Validation
    strategy = chunk_strategy.lower().strip()
    if strategy not in ["recursive", "semantic"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid chunk_strategy '{chunk_strategy}'. Options are 'recursive' or 'semantic'."
        )

    if strategy == "recursive":
        if chunk_size <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid chunk_size {chunk_size}. Must be a positive integer greater than zero."
            )
        if chunk_size > 10000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid chunk_size {chunk_size}. Exceeds maximum limit of 10000 characters."
            )
        if chunk_overlap < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid chunk_overlap {chunk_overlap}. Must be a non-negative integer."
            )
        if chunk_overlap >= chunk_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid chunk_overlap {chunk_overlap}. Overlap must be strictly less than chunk_size ({chunk_size})."
            )

    if strategy == "semantic":
        if not (0.0 <= similarity_percentile <= 100.0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid similarity_percentile {similarity_percentile}. Must be a float value between 0.0 and 100.0."
            )

    # 2. Strict File Size Validation (Header/Metadata-level check)
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File exceeds maximum upload limit of {MAX_FILE_SIZE // (1024 * 1024)}MB."
        )

    try:
        # 3. Secure Streaming Read to prevent large memory spikes on huge files
        file_bytes = b""
        chunk_read_bytes = 1024 * 1024  # Read in 1MB chunks
        
        while True:
            chunk = await file.read(chunk_read_bytes)
            if not chunk:
                break
            file_bytes += chunk
            if len(file_bytes) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail=f"File size dynamically exceeded the maximum upload limit of {MAX_FILE_SIZE // (1024 * 1024)}MB."
                )

        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file is empty."
            )
        
        # Instantiate Ingestion Service
        service = IngestionService(db)
        
        # Process and ingest
        response = service.ingest_document(
            filename=filename,
            file_bytes=file_bytes,
            chunk_strategy=strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            similarity_percentile=similarity_percentile
        )
        return response
        
    except HTTPException:
        # Re-raise HTTPExceptions to prevent them from being wrapped into 500
        raise
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
