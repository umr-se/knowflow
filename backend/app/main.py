from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .api.chat import router as chat_router
from .api.conversations import router as conversations_router
from .api.documents import router as documents_router
from .config import get_settings
from .db import Base, engine
from .models import Conversation, Document, DocumentChunk, Message
from .services.llm import check_llm


@asynccontextmanager
async def lifespan(app: FastAPI):
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(bind=conn)
    yield


settings = get_settings()
app = FastAPI(title="KnowFlow Local API", version="3.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(conversations_router)


@app.get("/health")
def health():
    return {"status": "ok", "llm": check_llm()}
