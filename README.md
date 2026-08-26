# Task Tracker API

A minimal **Module 1** learning project: a Python/FastAPI REST API for managing tasks with in-memory storage (see ADR-001). There is no authentication, no database, and no persistence across server restarts.

## Architecture

- **FastAPI** — HTTP API framework
- **Pydantic** — request/response validation (models added in later modules)
- **In-memory store** — module-level Python dictionary (added in later modules)
- **No auth, no Docker, no frontend** — backend API only

## Project structure

```
task-tracker-api/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application entry point
│   ├── models/          # Pydantic schemas
│   ├── routers/         # Route handlers
│   └── store/           # In-memory task dictionary
├── tests/
│   └── __init__.py 
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

1. **Create and activate a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   Windows PowerShell:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   After installation, verify pinned versions match your environment:

   ```bash
   pip freeze
   ```

   Update `requirements.txt` if needed.

3. **Configure environment**

   ```bash
   cp .env.example .env
   ```

   Windows PowerShell:

   ```powershell
   Copy-Item .env.example .env
   ```

## Run the server

From the project root (with the virtual environment active):

```bash
uvicorn app.main:app --reload --port 8000
```

The server reads `PORT` from `.env` when you pass it explicitly, or use the default above.

## Test the health endpoint

```bash
curl http://127.0.0.1:8000/health
```

Expected response shape (timestamp varies):

```json
{
  "status": "ok",
  "timestamp": "2026-07-06T19:33:00.123456+00:00"
}
```

## API documentation (Swagger)

Open in your browser:

```
http://127.0.0.1:8000/docs
```

Interactive OpenAPI docs are served automatically by FastAPI.
