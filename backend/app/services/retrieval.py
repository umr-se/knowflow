from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import DocumentChunk
from .embeddings import embed_texts


def retrieve(db: Session, query: str, top_k: int | None = None) -> list[dict]:
    if not query.strip():
        return []

    settings = get_settings()
    top_k = top_k or settings.retrieval_top_k
    query_vector = embed_texts([query])[0]
    distance = DocumentChunk.embedding.cosine_distance(query_vector)

    stmt = (
        select(DocumentChunk, distance.label("distance"))
        .where(DocumentChunk.embedding.is_not(None))
        .order_by(distance)
        .limit(top_k)
    )

    rows = db.execute(stmt).all()
    results = []
    for chunk, distance_value in rows:
        score = max(0.0, 1.0 - float(distance_value))
        if score < settings.min_retrieval_score:
            continue
        results.append(
            {
                "content": chunk.content,
                "filename": chunk.document.filename if chunk.document else "unknown",
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "score": round(score, 4),
            }
        )
    return results
