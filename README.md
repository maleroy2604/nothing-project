# nothing-prject

A FastAPI application backed by PostgreSQL and SQLAlchemy's async API.

## Quick start

Requirements: Python 3.15+, [uv](https://docs.astral.sh/uv/), and Podman with a running machine and Compose provider.

Install dependencies and start PostgreSQL:

```powershell
Set-Location backend
uv sync --locked
Set-Location ..
podman machine start
ollama pull llama3.2
podman compose up -d postgres ai-service
```

Run the API locally:

```powershell
$env:DATABASE_URL = "postgresql+asyncpg://appuser:apppassword@localhost:5432/nothing"
$env:AI_SERVICE_URL = "http://127.0.0.1:8090"
Set-Location backend
uv run uvicorn src.app.api.endpoint:app --reload
```

The API is available at <http://127.0.0.1:8000>; interactive API documentation is at <http://127.0.0.1:8000/docs>.

For container-based startup, run `podman compose up --build`. See [Development setup](docs/development.md) for prerequisites, both workflows, and shutdown instructions.

The backend exposes `POST /ai/chat` and forwards chat messages to the AI service.
In containers, the AI service calls Ollama on the host at port 11434; set
`OLLAMA_MODEL` to a model you have pulled in Ollama (defaults to `llama3.2`).
