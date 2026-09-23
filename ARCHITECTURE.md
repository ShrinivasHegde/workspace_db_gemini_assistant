# Project Architecture

This guide explains what each project file does, how the components connect, and what happens from a user question to a Gemini answer.

## Directory map

```text
db-gemini-assistant/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── constants.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── history.py
│   │   └── schema_extractor.py
│   ├── exceptions/
│   │   └── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── gemini.py
│   └── static/
│       ├── app.js
│       ├── index.html
│       └── styles.css
├── data/                         # Created on first run; local chat-history database
├── analyze_db.py                 # Thin terminal compatibility wrapper for schema_extractor
├── main.py                       # Application entrypoint and FastAPI composition root
├── requirements.txt              # Python dependencies
├── .env.example                  # Safe template; copy to .env.local or .env.prod
├── Dockerfile                    # Production container image definition
├── docker-compose.yml            # Local or production-style container runner
├── README.md                     # Clone, configure, and run instructions
└── ARCHITECTURE.md                # This file
```

## What every folder does

### `app/api`

`routes.py` defines the HTTP endpoints used by the browser. It validates requests, calls database and Gemini services, and turns expected failures into safe HTTP error responses. It does not contain database-driver or Gemini-SDK implementation details.

### `app/core`

`config.py` reads `APP_ENV` and loads `.env.local` for `local`/`dev` or `.env.prod` for `prod`. It centralizes the API key, models, application and target database URLs, host, port, CORS origins, debug mode, and logging level. `constants.py` holds the Gemini system instruction. Keeping them here avoids scattered hard-coded settings.

### `app/db`

`schema_extractor.py` connects to the configured target database and returns readable metadata. It chooses the correct driver from `TARGET_DATABASE_URL`: PostgreSQL, MySQL, or SQLite.

`history.py` manages application-owned PostgreSQL persistence. It creates and uses the `assistant` schema in the database specified by `APP_DATABASE_URL`, separately from the database being analyzed.

### `app/exceptions`

Defines expected application errors, such as a missing database URL, an unreachable database, or Gemini being unavailable. Routes convert these into friendly messages instead of exposing stack traces.

### `app/models`

`schemas.py` contains Pydantic request and response models. For example, it validates that a submitted question is non-empty and caps its length before it reaches Gemini.

### `app/services`

`gemini.py` owns communication with the official `google-genai` SDK. It creates the prompt from the schema metadata and session history, calls the configured primary model, and tries configured fallback models after a temporary 503 response.

### `app/static`

The browser client. `index.html` provides the layout, `styles.css` provides the responsive dark UI, and `app.js` calls the REST API, manages session selection, syncs the schema display, and renders messages.

## Overall request flow

```text
Browser UI
  │  1. User enters a question and clicks Send
  ▼
app/static/app.js
  │  POST /api/sessions/{session_id}/messages
  ▼
app/api/routes.py
  ├─ verifies the session and request
  ├─ app/db/schema_extractor.py reads target DB metadata
  ├─ app/db/history.py saves the user message and reads recent chat history
  ▼
app/services/gemini.py
  ├─ combines system instructions + database metadata + recent conversation
  ├─ calls the primary Gemini model
  └─ tries configured fallback models only for temporary 503 errors
  ▼
app/db/history.py saves Gemini's answer
  ▼
app/api/routes.py returns JSON
  ▼
app/static/app.js renders the answer in the chat panel
```

## Application startup flow

1. Run `python main.py` with `APP_ENV` set to `local`, `dev`, or `prod`.
2. `main.py` loads settings from `app/core/config.py` and initializes the application PostgreSQL tables.
3. FastAPI mounts API routes under `/api` and the static UI at `/`.
4. Uvicorn serves both from port `3002` by default. `prod` binds to `0.0.0.0` for container hosting; local/dev bind only to `127.0.0.1` by default.
5. The browser opens the UI; no second frontend server is required.

## Important separation of data

| Data | Location | Purpose |
| --- | --- | --- |
| Target database | `TARGET_DATABASE_URL` | Database being inspected; use a dedicated read-only role. |
| Application database | `APP_DATABASE_URL` | PostgreSQL database containing the `assistant` chat tables. |
| Configuration | `.env.local` / `.env.prod` plus ignored `.env.secrets.*` | Runtime settings and local secrets. |
