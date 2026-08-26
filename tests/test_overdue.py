from datetime import date, timedelta


def test_create_task_with_optional_due_date_returns_due_date_and_overdue_state(client):
    due_date = date.today() + timedelta(days=1)

    response = client.post("/tasks", json={"title": "Plan release", "due_date": due_date.isoformat()})

    assert response.status_code == 201
    assert response.json()["due_date"] == due_date.isoformat()
    assert response.json()["is_overdue"] is False


def test_patch_task_can_clear_due_date(client, created_task):
    client.patch(
        f"/tasks/{created_task['id']}",
        json={"due_date": (date.today() + timedelta(days=1)).isoformat()},
    )

    response = client.patch(f"/tasks/{created_task['id']}", json={"due_date": None})

    assert response.status_code == 200
    assert response.json()["due_date"] is None
    assert response.json()["is_overdue"] is False


def test_task_due_today_is_not_overdue(client):
    response = client.post("/tasks", json={"title": "Due today", "due_date": date.today().isoformat()})

    assert response.status_code == 201
    assert response.json()["is_overdue"] is False


def test_completed_past_due_task_is_no_longer_overdue_or_in_overdue_results(client):
    task = client.post(
        "/tasks",
        json={"title": "Finish release notes", "due_date": (date.today() - timedelta(days=1)).isoformat()},
    ).json()

    assert task["is_overdue"] is True

    assert client.patch(f"/tasks/{task['id']}", json={"status": "InProgress"}).status_code == 200
    completed_response = client.patch(f"/tasks/{task['id']}", json={"status": "Done"})
    overdue_response = client.get("/tasks", params={"overdue": "true"})

    assert completed_response.status_code == 200
    assert completed_response.json()["is_overdue"] is False
    assert overdue_response.status_code == 200
    assert overdue_response.json() == []


def test_list_tasks_overdue_filter_returns_only_incomplete_past_due_tasks(client):
    overdue_task = client.post(
        "/tasks", json={"title": "Past due", "due_date": (date.today() - timedelta(days=1)).isoformat()}
    ).json()
    client.post("/tasks", json={"title": "No due date"})
    client.post(
        "/tasks", json={"title": "Future task", "due_date": (date.today() + timedelta(days=1)).isoformat()}
    )
    completed_task = client.post(
        "/tasks",
        json={
            "title": "Completed past task",
            "status": "InProgress",
            "due_date": (date.today() - timedelta(days=1)).isoformat(),
        },
    ).json()
    client.patch(f"/tasks/{completed_task['id']}", json={"status": "Done"})

    response = client.get("/tasks", params={"overdue": "true"})

    assert response.status_code == 200
    assert [task["id"] for task in response.json()] == [overdue_task["id"]]
    assert response.json()[0]["is_overdue"] is True


def test_invalid_due_date_returns_422(client):
    response = client.post("/tasks", json={"title": "Bad date", "due_date": "not-a-date"})

    assert response.status_code == 422
