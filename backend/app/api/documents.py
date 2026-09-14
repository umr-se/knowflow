from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..models import Document, DocumentChunk
from ..services.embeddings import embed_texts
from ..services.ingestion import SUPPORTED_EXTENSIONS, build_chunks

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("")
def list_documents(db: Session = Depends(get_db)):
    docs = db.scalars(select(Document).order_by(Document.created_at.desc())).all()
    return [
        {
            "id": str(doc.id),
            "filename": doc.filename,
            "file_type": doc.file_type,
            "status": doc.status,
            "created_at": doc.created_at,
        }
        for doc in docs
    ]


@router.get("/supported-types")
def supported_types():
    return {"extensions": sorted(SUPPORTED_EXTENSIONS)}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    settings = get_settings()
    data = await file.read()
    if not data:
        raise HTTPException(400, "Uploaded file is empty.")
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File is larger than {settings.max_upload_mb} MB.")

    document = Document(
        filename=file.filename or "unnamed",
        file_type=file.content_type or "application/octet-stream",
        status="processing",
    )
    db.add(document)
    db.flush()

    try:
        chunks = build_chunks(document.filename, document.file_type, data)
        if not chunks:
            raise ValueError("No text could be extracted from the document.")

        vectors = embed_texts([item["content"] for item in chunks])
        db.add_all(
            DocumentChunk(
                document_id=document.id,
                content=item["content"],
                chunk_index=index,
                page_number=item.get("page_number"),
                embedding=vector,
            )
            for index, (item, vector) in enumerate(zip(chunks, vectors))
        )
        document.status = "ready"
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(500, f"Document ingestion failed: {exc}") from exc

    return {
        "id": str(document.id),
        "filename": document.filename,
        "chunks": len(chunks),
        "status": document.status,
    }


@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(404, "Document not found.")
    db.delete(document)
    db.commit()
    return {"deleted": True}
