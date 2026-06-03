# Todo API Service

A small FastAPI backend for managing todos. It uses SQLite for local persistence and FastAPI's generated OpenAPI schema for Swagger documentation.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Open:

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json
- Health check: http://127.0.0.1:8000/health

The default database file is `todo.db`. To use a different file:

```bash
TODO_DB_PATH=/path/to/todo.db uvicorn app.main:app --reload
```

## Endpoints

- `GET /health`
- `POST /todos`
- `GET /todos?page=1&page_size=20&completed=false&keyword=buy`
- `GET /todos/{todo_id}`
- `PATCH /todos/{todo_id}`
- `DELETE /todos/{todo_id}`
- `PATCH /todos/{todo_id}/complete`
- `PATCH /todos/{todo_id}/reopen`
- `DELETE /todos`
- `GET /todos/stats/summary`

## Test

```bash
pytest
```

