import re


def chunk_text(
    text: str,
    chunk_size: int = 900,
    overlap: int = 150,
) -> list[str]:
    """Create readable, overlapping chunks without splitting words unnecessarily."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_overlap must be >= 0 and smaller than chunk_size")

    text = re.sub(r"[ \t]+", " ", text.replace("\x00", "")).strip()
    if not text:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(text):
        target_end = min(start + chunk_size, len(text))
        end = target_end

        if target_end < len(text):
            # Prefer a natural boundary near the target.
            boundary = max(
                text.rfind("\n", start + chunk_size // 2, target_end),
                text.rfind(". ", start + chunk_size // 2, target_end),
                text.rfind(" ", start + chunk_size // 2, target_end),
            )
            if boundary > start:
                end = boundary + (2 if text[boundary:boundary + 2] == ". " else 1)

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        next_start = max(0, end - overlap)
        if next_start <= start:
            next_start = end
        start = next_start

    return chunks
