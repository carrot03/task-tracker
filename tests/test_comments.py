from app import store


def create_comment(client, task_id, author: str = "Alice", body: str = "First comment"):
    response = client.post(f"/tasks/{task_id}/comments", json={"author": author, "body": body})
    assert response.status_code == 201
    return response.json()


# Happy path

def test_create_comment_returns_201_with_expected_fields(client, created_task):
    response = client.post(
        f"/tasks/{created_task['id']}/comments",
        json={"author": "Alice", "body": "Looks good to me"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["author"] == "Alice"
    assert body["body"] == "Looks good to me"
    assert body["task_id"] == created_task["id"]
    assert "id" in body
    assert "created_at" in body


def test_list_comments_returns_comments_for_task_in_creation_order(client, created_task):
    first = create_comment(client, created_task["id"], author="Alice", body="First")
    second = create_comment(client, created_task["id"], author="Bob", body="Second")

    response = client.get(f"/tasks/{created_task['id']}/comments")

    assert response.status_code == 200
    assert [c["id"] for c in response.json()] == [first["id"], second["id"]]


def test_list_comments_empty_task_returns_200_and_empty_list(client, created_task):
    response = client.get(f"/tasks/{created_task['id']}/comments")

    assert response.status_code == 200
    assert response.json() == []


def test_get_comment_by_id_returns_comment(client, created_task):
    comment = create_comment(client, created_task["id"])

    response = client.get(f"/tasks/{created_task['id']}/comments/{comment['id']}")

    assert response.status_code == 200
    assert response.json() == comment


def test_delete_comment_returns_204_no_body(client, created_task):
    comment = create_comment(client, created_task["id"])

    response = client.delete(f"/tasks/{created_task['id']}/comments/{comment['id']}")

    assert response.status_code == 204
    assert response.content == b""


# Validation

def test_create_comment_missing_author_returns_422(client, created_task):
    response = client.post(f"/tasks/{created_task['id']}/comments", json={"body": "no author here"})

    assert response.status_code == 422


def test_create_comment_blank_author_returns_422(client, created_task):
    response = client.post(f"/tasks/{created_task['id']}/comments", json={"author": "   ", "body": "text"})

    assert response.status_code == 422


def test_create_comment_author_over_100_chars_returns_422(client, created_task):
    response = client.post(
        f"/tasks/{created_task['id']}/comments",
        json={"author": "a" * 101, "body": "text"},
    )

    assert response.status_code == 422


def test_create_comment_missing_body_returns_422(client, created_task):
    response = client.post(f"/tasks/{created_task['id']}/comments", json={"author": "Alice"})

    assert response.status_code == 422


def test_create_comment_blank_body_returns_422(client, created_task):
    response = client.post(f"/tasks/{created_task['id']}/comments", json={"author": "Alice", "body": "   "})

    assert response.status_code == 422


def test_create_comment_body_over_2000_chars_returns_422(client, created_task):
    response = client.post(
        f"/tasks/{created_task['id']}/comments",
        json={"author": "Alice", "body": "a" * 2001},
    )

    assert response.status_code == 422


def test_create_comment_unknown_field_returns_422(client, created_task):
    response = client.post(
        f"/tasks/{created_task['id']}/comments",
        json={"author": "Alice", "body": "text", "unknown_field": "value"},
    )

    assert response.status_code == 422


def test_create_comment_id_and_created_at_are_not_client_settable(client, created_task):
    response = client.post(
        f"/tasks/{created_task['id']}/comments",
        json={"author": "Alice", "body": "text", "id": "spoofed-id", "created_at": "2000-01-01T00:00:00Z"},
    )

    assert response.status_code == 422


# Edge cases

def test_create_comment_on_missing_task_returns_404(client):
    response = client.post("/tasks/does-not-exist/comments", json={"author": "Alice", "body": "text"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Task with id does-not-exist not found"


def test_list_comments_on_missing_task_returns_404(client):
    response = client.get("/tasks/does-not-exist/comments")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task with id does-not-exist not found"


def test_get_comment_not_found_returns_404(client, created_task):
    response = client.get(f"/tasks/{created_task['id']}/comments/does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "Comment with id does-not-exist not found"


def test_get_comment_wrong_task_returns_404(client):
    task_a = client.post("/tasks", json={"title": "Task A"}).json()
    task_b = client.post("/tasks", json={"title": "Task B"}).json()
    comment = create_comment(client, task_a["id"])

    response = client.get(f"/tasks/{task_b['id']}/comments/{comment['id']}")

    assert response.status_code == 404


def test_delete_comment_not_found_returns_404(client, created_task):
    response = client.delete(f"/tasks/{created_task['id']}/comments/does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "Comment with id does-not-exist not found"


def test_comments_isolated_between_tasks(client):
    task_a = client.post("/tasks", json={"title": "Task A"}).json()
    task_b = client.post("/tasks", json={"title": "Task B"}).json()
    create_comment(client, task_a["id"], author="Alice", body="On A")

    response = client.get(f"/tasks/{task_b['id']}/comments")

    assert response.status_code == 200
    assert response.json() == []


def test_deleting_task_removes_its_comments(client, created_task):
    comment = create_comment(client, created_task["id"])

    delete_response = client.delete(f"/tasks/{created_task['id']}")

    assert delete_response.status_code == 204
    # Cascade behavior isn't observable through the API once the parent
    # task is gone (list/get 404 on the missing task either way), so
    # inspect the store directly to confirm the comment wasn't orphaned.
    assert comment["id"] not in store._comments
