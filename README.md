# DB Gemini Assistant

A local web application that reads PostgreSQL, MySQL, or SQLite database metadata and answers database questions with Gemini. The UI, API, and chat-session persistence run in one process at `http://localhost:3002`.

Read [ARCHITECTURE.md](ARCHITECTURE.md) for a folder-by-folder guide and the complete request flow.

## Clone and run locally

### 1. Prerequisites

- Python 3.11 or later
- A reachable PostgreSQL, MySQL, or SQLite database
- A Gemini API key from Google AI Studio

### 2. Clone and enter the project

```powershell
git clone <YOUR_REPOSITORY_URL>
cd db-gemini-assistant
```

### 3. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell prevents activation, run this once for the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 4. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 5. Create your local configuration

```powershell
Copy-Item .env.example .env.local
```

Edit `.env.local`. Set a new, private `GEMINI_API_KEY` and two separate database URLs:

```dotenv
GEMINI_API_KEY=your_new_private_key
APP_DATABASE_URL=postgresql://postgres:root@localhost:5432/analyse_db
TARGET_DATABASE_URL=postgresql://readonly_user:password@localhost:5432/database_to_analyze
```

`APP_DATABASE_URL` must be PostgreSQL and stores application chat data. `TARGET_DATABASE_URL` is the inspected database and may be PostgreSQL, MySQL, or SQLite:

```dotenv
# TARGET_DATABASE_URL=mysql://readonly_user:password@localhost:3306/database_name
# TARGET_DATABASE_URL=sqlite:///C:/path/to/database.db
```

### 6. Start the application

```powershell
python main.py
```

Open `http://localhost:3002`. Click **Sync schema**, create a chat, and ask a question such as `What schemas and tables are present?`

## Configuration

| Variable | Purpose | Default |
| --- | --- | --- |
| `GEMINI_API_KEY` | Required Gemini API key | None |
| `GEMINI_MODEL_NAME` | Primary Gemini model | `gemini-3.6-flash` |
| `GEMINI_FALLBACK_MODELS` | Comma-separated fallback models for a temporary 503 | `gemini-3.5-flash-lite` |
| `APP_DATABASE_URL` | Required PostgreSQL connection for application sessions and messages | None |
| `TARGET_DATABASE_URL` | Required read-only database connection to inspect | None |
| `APP_HOST` | Server address | `127.0.0.1` |
| `APP_PORT` | UI and API port | `3002` |

Never commit `.env.local`, `.env.prod`, real API keys, or passwords to Git. The `*.example` files are safe templates.

## Environments

Set `APP_ENV` before starting the app. It selects the configuration file and safe runtime defaults.

| Environment | Loaded file | Default host | Debug | Local history file |
| --- | --- | --- | --- | --- |
| `local` | `.env.local` | `127.0.0.1` | On | `data/chat_history.local.db` |
| `dev` | `.env.local` | `127.0.0.1` | On | `data/chat_history.dev.db` |
| `prod` | `.env.prod` | `0.0.0.0` | Off | `data/chat_history.prod.db` |

For local use, no command is needed because `local` is the default. For production-style testing:

```powershell
Copy-Item .env.example .env.prod
$env:APP_ENV = "prod"
python main.py
```

When using `.env.prod`, change `APP_ENV=prod`, set `APP_HOST=0.0.0.0`, set `APP_DEBUG=false`, and configure production-only credentials and CORS origins.

`CORS_ORIGINS`, `APP_HOST`, `APP_DEBUG`, `LOG_LEVEL`, `APP_DATABASE_URL`, and `TARGET_DATABASE_URL` can be overridden in the selected environment file.

## Docker

Docker is included for future AWS-ready deployment, but no cloud resources are created by this project.

Local container test:

```powershell
Copy-Item .env.example .env.local
# Edit .env.local with your local database URL and private Gemini key.
docker compose up --build
```

For a production-style container configuration:

```powershell
Copy-Item .env.example .env.prod
$env:APP_ENV = "prod"
$env:APP_ENV_FILE = ".env.prod"
docker compose up --build
```

The container binds to `0.0.0.0:3002`, suitable for a later ECS, EC2, or App Runner deployment.

## API quick reference

The UI uses these same endpoints:

- `GET /api/health` — application health check
- `GET /api/schema` — scan the configured database metadata
- `GET/POST /api/sessions` — list or create chat sessions
- `GET /api/sessions/{id}/messages` — retrieve a session's messages
- `DELETE /api/sessions/{id}` — delete a session
- `POST /api/sessions/{id}/messages` — send a database question to Gemini
