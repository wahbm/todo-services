import sqlite3
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from app.database import get_db, init_database
from app.main import app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch) -> Iterator[TestClient]:
    # Verify the healthy baseline even while the deployed test faults are active.
    monkeypatch.setattr("app.routes.todos.ACTIVE_BUGS", frozenset())
    db_path = tmp_path / "test.db"
    init_database(str(db_path))

    def override_get_db() -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(str(db_path), check_same_thread=False)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def create_todo(client: TestClient, title: str, description: str = "") -> dict:
    response = client.post(
        "/todos",
        json={"title": title, "description": description},
    )
    assert response.status_code == 201
    return response.json()


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_get_todo(client: TestClient) -> None:
    created = create_todo(client, " Buy groceries ", "Milk and bread")

    assert created["title"] == "Buy groceries"
    assert created["description"] == "Milk and bread"
    assert created["completed"] is False

    response = client.get(f"/todos/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_rejects_blank_title(client: TestClient) -> None:
    response = client.post("/todos", json={"title": "   "})
    assert response.status_code == 422


def test_list_todos_with_pagination_and_filters(client: TestClient) -> None:
    first = create_todo(client, "Buy groceries", "fruit")
    second = create_todo(client, "Write report", "work")
    client.patch(f"/todos/{second['id']}/complete")

    response = client.get("/todos", params={"page": 1, "page_size": 1})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert payload["page"] == 1
    assert payload["page_size"] == 1
    assert len(payload["items"]) == 1

    active_response = client.get("/todos", params={"completed": False})
    assert active_response.status_code == 200
    assert [item["id"] for item in active_response.json()["items"]] == [first["id"]]

    keyword_response = client.get("/todos", params={"keyword": "report"})
    assert keyword_response.status_code == 200
    assert keyword_response.json()["items"][0]["id"] == second["id"]


def test_update_todo(client: TestClient) -> None:
    todo = create_todo(client, "Original")

    response = client.patch(
        f"/todos/{todo['id']}",
        json={"title": "Updated", "description": "new", "completed": True},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Updated"
    assert payload["description"] == "new"
    assert payload["completed"] is True


def test_complete_and_reopen_todo(client: TestClient) -> None:
    todo = create_todo(client, "Workout")

    complete_response = client.patch(f"/todos/{todo['id']}/complete")
    assert complete_response.status_code == 200
    assert complete_response.json()["completed"] is True

    reopen_response = client.patch(f"/todos/{todo['id']}/reopen")
    assert reopen_response.status_code == 200
    assert reopen_response.json()["completed"] is False


def test_delete_todo(client: TestClient) -> None:
    todo = create_todo(client, "Remove me")

    delete_response = client.delete(f"/todos/{todo['id']}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/todos/{todo['id']}")
    assert get_response.status_code == 404


def test_bulk_delete_todos(client: TestClient) -> None:
    first = create_todo(client, "One")
    second = create_todo(client, "Two")
    third = create_todo(client, "Three")

    response = client.request(
        "DELETE",
        "/todos",
        json={"ids": [first["id"], second["id"]]},
    )

    assert response.status_code == 200
    assert response.json() == {"deleted": 2}
    remaining = client.get("/todos").json()["items"]
    assert [item["id"] for item in remaining] == [third["id"]]


def test_stats_summary(client: TestClient) -> None:
    first = create_todo(client, "Done")
    create_todo(client, "Active")
    client.patch(f"/todos/{first['id']}/complete")

    response = client.get("/todos/stats/summary")

    assert response.status_code == 200
    assert response.json() == {"total": 2, "completed": 1, "active": 1}


def test_missing_todo_returns_404(client: TestClient) -> None:
    response = client.get("/todos/999")
    assert response.status_code == 404
