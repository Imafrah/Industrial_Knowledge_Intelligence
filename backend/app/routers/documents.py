"""
Documents router — upload and list ingested documents.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Document, Entity
from app.ingestion import ingest_document

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "xlsx", "txt", "text", "csv", "png", "jpg", "jpeg"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


class DocumentResponse(BaseModel):
    id: int
    filename: str
    doc_type: str | None
    chunk_count: int
    entity_count: int
    created_at: str
    metadata_json: dict | None


class DocumentDetail(BaseModel):
    id: int
    filename: str
    doc_type: str | None
    chunk_count: int
    content_preview: str
    metadata_json: dict | None
    entities: list[dict]
    created_at: str


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a document file (PDF, DOCX, XLSX, TXT) and run the full ingestion pipeline:
    extract text → chunk → embed → extract entities → store.
    """
    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: .{ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 20MB)")

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        doc = await ingest_document(file_bytes, file.filename, db)

        # Get entity count
        result = await db.execute(
            select(func.count()).select_from(Entity).where(Entity.document_id == doc.id)
        )
        entity_count = result.scalar() or 0

        return DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            doc_type=doc.doc_type,
            chunk_count=doc.chunk_count,
            entity_count=entity_count,
            created_at=str(doc.created_at),
            metadata_json=doc.metadata_json,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("", response_model=list[DocumentResponse])
async def list_documents(db: AsyncSession = Depends(get_db)):
    """List all ingested documents with entity counts."""
    result = await db.execute(
        select(
            Document.id,
            Document.filename,
            Document.doc_type,
            Document.chunk_count,
            func.count(Entity.id).label("entity_count"),
            Document.created_at,
            Document.metadata_json,
        )
        .outerjoin(Entity, Entity.document_id == Document.id)
        .group_by(Document.id)
        .order_by(Document.created_at.desc())
    )
    rows = result.all()

    return [
        DocumentResponse(
            id=row[0],
            filename=row[1],
            doc_type=row[2] or "unknown",
            chunk_count=row[3] or 0,
            entity_count=row[4],
            created_at=str(row[5]) if row[5] else "",
            metadata_json=row[6],
        )
        for row in rows
    ]


@router.get("/{doc_id}", response_model=DocumentDetail)
async def get_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    """Get detailed info about a single document including its entities."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get entities
    entity_result = await db.execute(
        select(Entity).where(Entity.document_id == doc_id)
    )
    entities = entity_result.scalars().all()

    return DocumentDetail(
        id=doc.id,
        filename=doc.filename,
        doc_type=doc.doc_type,
        chunk_count=doc.chunk_count,
        content_preview=doc.content_text[:1000] if doc.content_text else "",
        metadata_json=doc.metadata_json,
        entities=[
            {
                "id": e.id,
                "type": e.entity_type,
                "value": e.entity_value,
            }
            for e in entities
        ],
        created_at=str(doc.created_at) if doc.created_at else "",
    )
