# nothing-prject

A FastAPI application backed by PostgreSQL and SQLAlchemy's async API.

## Quick start

Requirements: Python 3.15+, [uv](https://docs.astral.sh/uv/), a Groq API key, and Podman with a running machine and Compose provider.

Install dependencies and start the local development services:

```powershell
Set-Location backend
uv sync --locked
Set-Location ..
podman machine start
```

Create `ai-service\.env` and add your Groq API key:

```text
GROQ_API_KEY=your_groq_api_key
```

The environment file is git-ignored; do not commit or share it. Create local
configuration files and start the database and AI service containers:

```powershell
if (-not (Test-Path backend\.env.local)) {
    Copy-Item backend\.env.local.example backend\.env.local
}
if (-not (Test-Path frontend\.env.local)) {
    Copy-Item frontend\.env.local.example frontend\.env.local
}
New-Item -ItemType Directory -Force secrets | Out-Null
if (-not (Test-Path secrets\postgres_password)) {
    python -c "import pathlib,secrets; pathlib.Path('secrets/postgres_password').write_text(secrets.token_urlsafe(32), encoding='utf-8')"
}
podman compose up -d postgres ai-service
```

Run the API locally from `backend/`:

```powershell
$env:DATABASE_URL = "postgresql+asyncpg://appuser:apppassword@localhost:5432/nothing"
$env:AI_SERVICE_URL = "http://127.0.0.1:8090"
Set-Location backend
uv run uvicorn src.app.api.endpoint:app --reload --env-file .env.local
```

The API is available at <http://127.0.0.1:8000>; interactive API documentation is at <http://127.0.0.1:8000/docs>.

Run the frontend in a second terminal with `Set-Location frontend` and
`npm run dev`. See [Development setup](docs/development.md) for database-secret
setup and the complete local workflow.

For container-based startup, run `podman compose up --build`. See [Development setup](docs/development.md) for prerequisites, both workflows, and shutdown instructions.

The backend exposes `POST /ai/chat` and forwards chat messages to the AI service.
The AI service uses Groq Cloud with `openai/gpt-oss-20b` by default; configure
`GROQ_MODEL` in `.env` to select another model available to your Groq account.
