from functools import lru_cache
import os

from sentence_transformers import SentenceTransformer

from ..config import get_settings


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    settings = get_settings()
    os.environ.setdefault("HF_HOME", settings.hf_home)
    os.environ.setdefault("TRANSFORMERS_CACHE", settings.transformers_cache)
    return SentenceTransformer(settings.embedding_model, device="cpu")


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    vectors = get_embedding_model().encode(
        texts,
        batch_size=16,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return vectors.tolist()
