from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Conversation, Message
from ..services.llm import answer_question
from ..services.retrieval import retrieve

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    conversation_id: UUID | None = None


@router.post("")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    conversation = db.get(Conversation, request.conversation_id) if request.conversation_id else None
    if conversation is None:
        conversation = Conversation(title=request.question[:60])
        db.add(conversation)
        db.flush()

    previous = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(8)
    ).all()
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in reversed(previous)
        if msg.role in {"user", "assistant"}
    ]

    db.add(Message(conversation_id=conversation.id, role="user", content=request.question))
    sources = retrieve(db, request.question)

    try:
        answer = answer_question(request.question, sources, history)
    except RuntimeError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    db.add(Message(conversation_id=conversation.id, role="assistant", content=answer))
    db.commit()
    return {
        "conversation_id": str(conversation.id),
        "answer": answer,
        "mode": "rag" if sources else "local_llm",
        "sources": sources,
    }
