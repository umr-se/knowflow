# KnowFlow

KnowFlow is a fully local chat + RAG application designed to remain practical on an **low end** machine. Cloud chat providers such as Gemini are not required.

## Stack

- **Frontend:** Next.js
- **API:** FastAPI
- **Vector/database:** PostgreSQL 16 + pgvector
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (CPU, 384 dimensions)
- **Local LLM:** Ollama, default `qwen2.5:1.5b`
- **RAG:** cosine retrieval from pgvector + local generation
- **Files:** PDF, DOCX, XLSX/XLSM, CSV, TSV, PPTX, TXT, Markdown, HTML, XML, JSON and JSONL

The local model and embedding model are separate. MiniLM creates/retrieves vectors efficiently, while Ollama runs the small generative model.

## Why `qwen2.5:1.5b`?

The default is deliberately small. It is much easier to run alongside PostgreSQL, the embedding model, FastAPI, a browser and the frontend than a 7B/8B model. If your machine handles it comfortably, you can later change `CHAT_MODEL` to another Ollama model without changing application code.

## 1. Install Ollama with project-local model storage

Ollama does **not** take a model path in `CHAT_MODEL`. Instead, it stores models in its model directory. To keep those files off `C:`, this project provides PowerShell scripts that set `OLLAMA_MODELS` to `models\ollama` inside the project.

From the project root on Windows PowerShell:

```powershell
.\scripts\start-ollama-local.ps1
```

Leave that terminal running. In a second terminal, run:

```powershell
$env:OLLAMA_MODELS = "$(Resolve-Path .\models\ollama)"
ollama pull qwen2.5:1.5b
```

The model will then be stored under `models\ollama`, not the default Windows Ollama location. If Ollama Desktop is already running, stop it before using these scripts so a different Ollama process does not claim the default model directory.

You can also set `OLLAMA_MODELS` permanently for your Windows user, but a project-local PowerShell session is safer because each project can have its own model directory.

You only need `ollama run` to test it interactively. The KnowFlow backend talks to the Ollama HTTP server directly.

Verify Ollama is available:

```bash
curl http://localhost:11434/api/tags
```

## 2. Local caches

The Sentence Transformers / Hugging Face cache is also redirected to `models\huggingface` for host development. Docker mounts that same project directory at `/root/.cache/huggingface`, so the embedding model is downloaded once and reused. These directories are intentionally git-ignored because model/cache files can be hundreds of MB.

## 3. Environment files

For Docker Compose:

```bash
cp .env.example .env
```

For a backend running directly on the host:

```bash
cp backend/.env.example backend/.env
```

Settings are loaded lazily through `get_settings()`. It reads project `.env` first and `backend/.env` second; actual process environment variables take priority.

Important defaults:

```env
OLLAMA_BASE_URL=http://localhost:11434
CHAT_MODEL=qwen2.5:1.5b
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
RETRIEVAL_TOP_K=5
MIN_RETRIEVAL_SCORE=0.20
MAX_UPLOAD_MB=30
```

Inside Docker Compose the backend defaults to `http://host.docker.internal:11434`, because Ollama is expected to run on the host rather than consume more memory in another container.

## 4. Run with Docker Compose

With Ollama already running on your machine:

```bash
docker compose up -d --build
```

Open:

- Frontend: `http://localhost:3000`
- API: `http://localhost:8000`
- Health/local-model status: `http://localhost:8000/health`

The health endpoint reports whether Ollama is reachable and which model is configured.

## 5. Local development

Start only PostgreSQL if desired:

```bash
docker compose up -d db
```

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate     # Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm ci
npm run dev
```

## How chat + RAG works

When a file is uploaded, KnowFlow extracts text locally, chunks it, creates MiniLM embeddings, and stores both chunks and vectors in PostgreSQL/pgvector. PDF pages and PowerPoint slide numbers are retained where possible.

For every question, KnowFlow embeds the query and retrieves the closest chunks. Chunks below `MIN_RETRIEVAL_SCORE` are discarded. If useful chunks remain, the local LLM receives them and responds in **RAG mode** with `[1]`, `[2]` style citations. If no useful document context is found, the same local model responds in normal **local LLM mode**, so the app is still a general chat assistant.

Conversation history is now sent to the model as well, and the frontend keeps the returned conversation ID for follow-up questions.

## File support notes

- PDF extraction is text-based; scanned/image-only PDFs require OCR, which is intentionally not bundled into this lightweight setup.
- Excel support covers `.xlsx` and `.xlsm`. Legacy binary `.xls` is not enabled by default; converting it to `.xlsx` keeps dependencies smaller and safer.
- Large files are rejected above `MAX_UPLOAD_MB` (30 MB by default).

## Changing the local model

Pull a different Ollama model and change only the environment variable:

```bash
ollama pull <model-name>
```

```env
CHAT_MODEL=<model-name>
```

Then restart the backend. No Gemini API key or other cloud credential is needed.

## Reset database

```bash
docker compose down -v
```

This permanently deletes uploaded-document metadata, chunks, embeddings and conversations stored in PostgreSQL.
