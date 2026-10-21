# Development setup

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)
- Ollama with a model downloaded locally
- Podman with a running Podman machine
- A Compose provider configured for `podman compose`

Install uv on Windows with:

```powershell
winget install --id=astral-sh.uv -e
```

## Install Python dependencies

From the project root, sync the virtual environment from the committed lock file:

```powershell
uv sync --locked
```

This root project contains the API dependencies. The AI service has its own
project and lock file; to sync its dependencies for local development, run:

```powershell
Set-Location ai-service
uv sync --locked
Set-Location ..
```

Run `uv lock` in the corresponding project directory after changing that
service's dependencies, then commit the updated lock file.

## Run the API locally with PostgreSQL in Podman

Start the Podman machine. If you have not created one yet, initialize it once with `podman machine init`, then start it:

```powershell
podman machine start
```

The Compose database password is read from the ignored file
`secrets/postgres_password`. Create it once before starting the containers; do
not commit or share this file:

```powershell
New-Item -ItemType Directory -Force secrets | Out-Null
if (-not (Test-Path secrets\postgres_password)) {
    python -c "import pathlib,secrets; pathlib.Path('secrets/postgres_password').write_text(secrets.token_urlsafe(32), encoding='utf-8')"
}
```

Download the default model and start PostgreSQL plus the AI service:

```powershell
ollama pull llama3.2
podman compose up -d postgres ai-service
```

Set the database URL for the API process running on Windows. `localhost` is correct here because the API is outside the Compose network:

```powershell
$env:DATABASE_URL = "postgresql+asyncpg://appuser:apppassword@localhost:5432/nothing"
```

Launch the API with automatic reload:

```powershell
$env:AI_SERVICE_URL = "http://127.0.0.1:8090"
uv run uvicorn src.app.api.endpoint:app --app-dir backend --reload
```

The API is available at <http://127.0.0.1:8000>. Interactive API documentation is at <http://127.0.0.1:8000/docs>.

PostgreSQL must be running before the API starts because the application connects to the database during startup. If the API reports that it cannot connect to port 5432, check that the Podman machine and PostgreSQL container are running.
The AI service must be running for `/ai/chat`; in the local workflow it is
available at `http://127.0.0.1:8090`. Set `OLLAMA_MODEL` in the environment to
use another model you have pulled with Ollama.

## Run the application in containers

Install Ollama on the host and pull the model you want to use:

```powershell
ollama pull llama3.2
```

Build and start the API, AI service, database, and frontend:

```powershell
podman compose up --build
```

Ensure `secrets/postgres_password` exists first; Compose mounts it read-only
into PostgreSQL and the API. If you already have a database in the
`postgres_data` volume, changing or generating this file does not change the
password stored by PostgreSQL. Update the database role password to match the
secret before restarting the API.

The API connects to PostgreSQL and the AI service using their Compose service
hostnames. The AI service calls Ollama on the host at
`host.containers.internal:11434`. Set `OLLAMA_MODEL` to use a different model.
The API is available at <http://localhost:8080>, with interactive API
documentation at <http://localhost:8080/docs>. The React frontend is available
at <http://localhost:3000>. Use `POST /ai/chat` with a `messages` array
containing `role` and `content` to request a chat completion, for example:

```json
{
  "messages": [
    {"role": "user", "content": "Suggest a short fantasy quest"}
  ]
}
```

Set `OLLAMA_MODEL` if you pulled a different model. `OLLAMA_BASE_URL` can be
overridden if Ollama is running somewhere other than the host default.


To run only the frontend container:

```powershell
podman compose up --build frontend
```

For frontend development with Vite's hot reload, run these commands from `frontend/`:

```powershell
npm install
npm run dev
```

The Vite development server proxies `/api` requests to the local API at
`http://127.0.0.1:8000`. In the container setup, Nginx proxies the same path to
the API service, so the browser does not need a separate API URL or CORS setup.
The backend exposes `POST /guides/` to create a guide and `GET /guides/` or
`GET /guides/{guide_id}` to read guides with their ordered quests. Create quests
with `POST /quests/` using `guide_id`, `position`, `title`, and
`completion_criteria`; `GET /quests/?guide_id=<id>` filters quests by guide.
`description` remains optional for compatibility, and quest status remains
available. A quest can include ordered `steps` when created, each with a
`position`, `title`, and optional `description`; steps can also be managed
through `POST`/`GET /quests/{quest_id}/steps/` and
`PATCH`/`DELETE /quests/{quest_id}/steps/{step_id}`. Quest responses include
their ordered steps.

On a fresh database, SQLAlchemy creates the `guides`, `quests`, and
`quest_steps` tables at startup. For an existing database, apply
`backend/migrations/001_add_guides_and_quest_fields.sql` if it has not already
been applied, then apply `backend/migrations/002_add_quest_steps.sql` once
before restarting the API. Existing quests are placed in a new guide, in ID
order, and their completion criteria are initialized from their descriptions
(or titles when descriptions are empty).

Stop the containers with:

```powershell
podman compose down
```

Database data is stored in the `postgres_data` volume and remains after stopping the containers. Avoid `podman compose down -v` unless you intend to delete that data.

## Development and production

Use Uvicorn's `--reload` option for local development, not production. The Compose configuration is useful for running the application as containers, but the database credentials in it are development defaults. For production, provide credentials through secrets or environment configuration and use production-appropriate database management, storage, and network security.
