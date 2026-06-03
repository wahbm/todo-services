import sqlite3
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.database import get_db
from app.schemas import (
    TodoBulkDeleteRequest,
    TodoBulkDeleteResponse,
    TodoCreate,
    TodoListResponse,
    TodoResponse,
    TodoStatsResponse,
    TodoUpdate,
)


router = APIRouter(prefix="/todos", tags=["todos"])


def row_to_todo(row: sqlite3.Row) -> TodoResponse:
    return TodoResponse(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        completed=bool(row["completed"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def get_todo_or_404(todo_id: int, db: sqlite3.Connection) -> sqlite3.Row:
    row = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo {todo_id} not found",
        )
    return row


@router.post(
    "",
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a todo",
    description="Create a new todo item with a required title and optional description.",
)
def create_todo(payload: TodoCreate, db: sqlite3.Connection = Depends(get_db)) -> TodoResponse:
    cursor = db.execute(
        "INSERT INTO todos (title, description) VALUES (?, ?)",
        (payload.title, payload.description),
    )
    db.commit()
    return row_to_todo(get_todo_or_404(cursor.lastrowid, db))


@router.get(
    "",
    response_model=TodoListResponse,
    summary="List todos",
    description="Return a paginated list of todos with optional completed-state and keyword filters.",
)
def list_todos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    completed: Optional[bool] = None,
    keyword: Optional[str] = Query(default=None, min_length=1),
    db: sqlite3.Connection = Depends(get_db),
) -> TodoListResponse:
    filters: List[str] = []
    params: List[object] = []

    if completed is not None:
        filters.append("completed = ?")
        params.append(1 if completed else 0)

    if keyword:
        filters.append("(title LIKE ? OR description LIKE ?)")
        pattern = f"%{keyword}%"
        params.extend([pattern, pattern])

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    total = db.execute(
        f"SELECT COUNT(*) AS count FROM todos {where_clause}",
        params,
    ).fetchone()["count"]

    offset = (page - 1) * page_size
    rows = db.execute(
        f"""
        SELECT * FROM todos
        {where_clause}
        ORDER BY id DESC
        LIMIT ? OFFSET ?
        """,
        [*params, page_size, offset],
    ).fetchall()

    return TodoListResponse(
        items=[row_to_todo(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/stats/summary",
    response_model=TodoStatsResponse,
    summary="Get todo statistics",
    description="Return total, completed, and active todo counts.",
)
def get_todo_stats(db: sqlite3.Connection = Depends(get_db)) -> TodoStatsResponse:
    row = db.execute(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) AS completed
        FROM todos
        """
    ).fetchone()
    completed_count = row["completed"] or 0
    return TodoStatsResponse(
        total=row["total"],
        completed=completed_count,
        active=row["total"] - completed_count,
    )


@router.delete(
    "",
    response_model=TodoBulkDeleteResponse,
    summary="Bulk delete todos",
    description="Delete multiple todos by id and return the number of rows removed.",
)
def bulk_delete_todos(
    payload: TodoBulkDeleteRequest,
    db: sqlite3.Connection = Depends(get_db),
) -> TodoBulkDeleteResponse:
    placeholders = ",".join("?" for _ in payload.ids)
    cursor = db.execute(
        f"DELETE FROM todos WHERE id IN ({placeholders})",
        payload.ids,
    )
    db.commit()
    return TodoBulkDeleteResponse(deleted=cursor.rowcount)


@router.get(
    "/{todo_id}",
    response_model=TodoResponse,
    summary="Get a todo",
    description="Return a single todo by id.",
)
def get_todo(todo_id: int, db: sqlite3.Connection = Depends(get_db)) -> TodoResponse:
    return row_to_todo(get_todo_or_404(todo_id, db))


@router.patch(
    "/{todo_id}",
    response_model=TodoResponse,
    summary="Update a todo",
    description="Partially update a todo title, description, or completed state.",
)
def update_todo(
    todo_id: int,
    payload: TodoUpdate,
    db: sqlite3.Connection = Depends(get_db),
) -> TodoResponse:
    get_todo_or_404(todo_id, db)
    changes = payload.model_dump(exclude_unset=True)

    if changes:
        assignments = ", ".join(f"{field} = ?" for field in changes)
        values = [
            1 if field == "completed" and value else 0 if field == "completed" else value
            for field, value in changes.items()
        ]
        db.execute(
            f"UPDATE todos SET {assignments} WHERE id = ?",
            [*values, todo_id],
        )
        db.commit()

    return row_to_todo(get_todo_or_404(todo_id, db))


@router.delete(
    "/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a todo",
    description="Delete a single todo by id.",
)
def delete_todo(todo_id: int, db: sqlite3.Connection = Depends(get_db)) -> Response:
    get_todo_or_404(todo_id, db)
    db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{todo_id}/complete",
    response_model=TodoResponse,
    summary="Complete a todo",
    description="Mark a todo as completed.",
)
def complete_todo(todo_id: int, db: sqlite3.Connection = Depends(get_db)) -> TodoResponse:
    get_todo_or_404(todo_id, db)
    db.execute("UPDATE todos SET completed = 1 WHERE id = ?", (todo_id,))
    db.commit()
    return row_to_todo(get_todo_or_404(todo_id, db))


@router.patch(
    "/{todo_id}/reopen",
    response_model=TodoResponse,
    summary="Reopen a todo",
    description="Mark a completed todo as active again.",
)
def reopen_todo(todo_id: int, db: sqlite3.Connection = Depends(get_db)) -> TodoResponse:
    get_todo_or_404(todo_id, db)
    db.execute("UPDATE todos SET completed = 0 WHERE id = ?", (todo_id,))
    db.commit()
    return row_to_todo(get_todo_or_404(todo_id, db))

