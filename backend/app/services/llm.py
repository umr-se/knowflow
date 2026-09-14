import json
from urllib import error, request

from ..config import get_settings


def _ollama_chat(messages: list[dict[str, str]]) -> str:
    settings = get_settings()
    endpoint = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
    payload = json.dumps(
        {
            "model": settings.chat_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": settings.llm_temperature},
        }
    ).encode("utf-8")

    req = request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=settings.llm_timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Ollama returned HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(
            "Cannot connect to Ollama. Start Ollama and pull the configured CHAT_MODEL."
        ) from exc

    text = (body.get("message") or {}).get("content", "").strip()
    return text or "The local model returned an empty response."


def answer_question(
    question: str,
    contexts: list[dict],
    history: list[dict[str, str]] | None = None,
) -> str:
    settings = get_settings()
    history = history or []

    if contexts:
        pieces: list[str] = []
        used_chars = 0
        for index, ctx in enumerate(contexts, start=1):
            page = ctx.get("page_number")
            source = ctx.get("filename", "unknown")
            label = f"[{index}] {source}" + (f" page {page}" if page else "")
            piece = f"{label}\n{ctx.get('content', '').strip()}"
            if used_chars + len(piece) > settings.max_context_chars:
                break
            pieces.append(piece)
            used_chars += len(piece)

        system = (
            "You are KnowFlow, a local RAG assistant. Use the supplied document context "
            "as the primary source of truth. Cite supporting chunks using [1], [2], etc. "
            "If the documents do not contain enough information, clearly say that before "
            "giving any general-knowledge explanation. Do not invent citations."
        )
        user_content = (
            "DOCUMENT CONTEXT:\n\n"
            + "\n\n---\n\n".join(pieces)
            + f"\n\nQUESTION:\n{question}"
        )
    else:
        system = (
            "You are KnowFlow, a helpful local AI assistant. No relevant document context "
            "was retrieved for this turn, so answer as a normal assistant and do not claim "
            "to have found information in uploaded files."
        )
        user_content = question

    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    messages.extend(history[-8:])
    messages.append({"role": "user", "content": user_content})
    return _ollama_chat(messages)


def check_llm() -> dict:
    settings = get_settings()
    endpoint = f"{settings.ollama_base_url.rstrip('/')}/api/tags"
    try:
        with request.urlopen(endpoint, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
        models = [item.get("name") for item in data.get("models", [])]
        return {
            "provider": "ollama",
            "available": True,
            "model": settings.chat_model,
            "model_pulled": any(
                name == settings.chat_model or str(name).startswith(f"{settings.chat_model}:")
                for name in models
            ),
        }
    except Exception:
        return {
            "provider": "ollama",
            "available": False,
            "model": settings.chat_model,
            "model_pulled": False,
        }
