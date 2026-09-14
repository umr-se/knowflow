from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Conversation, Message

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

@router.get("")
def conversations(db: Session = Depends(get_db)):
    rows = db.scalars(select(Conversation).order_by(Conversation.created_at.desc())).all()
    return [{"id": str(row.id), "title": row.title, "created_at": row.created_at} for row in rows]

@router.get("/{conversation_id}")
def conversation(conversation_id: UUID, db: Session = Depends(get_db)):
    row = db.get(Conversation, conversation_id)
    if not row:
        raise HTTPException(404, "Conversation not found.")
    messages = db.scalars(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
    ).all()
    return {"id": str(row.id), "title": row.title,
            "messages": [{"id": str(m.id), "role": m.role, "content": m.content} for m in messages]}
