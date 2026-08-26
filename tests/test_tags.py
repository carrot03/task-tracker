def create_tag(client, name: str = "Backend"):
    response = client.post("/tags", json={"name": name})
    assert response.status_code == 201
    return response.json()


def test_create_tag_returns_201_with_trimmed_name(client):
    response = client.post("/tags", json={"name": "  Backend  "})

    assert response.status_code == 201
    assert response.json()["name"] == "Backend"
    assert "id" in response.json()


def test_create_duplicate_tag_returns_409(client):
    create_tag(client, "Backend")

    response = client.post("/tags", json={"name": "backend"})

    assert response.status_code == 409


def test_list_tags_returns_available_tags(client):
    backend = create_tag(client, "Backend")
    bug = create_tag(client, "Bug")

    response = client.get("/tags")

    assert response.status_code == 200
    assert response.json() == [backend, bug]


def test_create_task_with_multiple_tags_returns_them_on_task(client):
    backend = create_tag(client, "Backend")
    bug = create_tag(client, "Bug")

    response = client.post("/tasks", json={"title": "Fix API", "tag_ids": [backend["id"], bug["id"]]})

    assert response.status_code == 201
    assert response.json()["tags"] == [backend, bug]


def test_patch_task_replaces_its_tags(client):
    backend = create_tag(client, "Backend")
    bug = create_tag(client, "Bug")
    task = client.post("/tasks", json={"title": "Fix API", "tag_ids": [backend["id"]]}).json()

    response = client.patch(f"/tasks/{task['id']}", json={"tag_ids": [bug["id"]]})

    assert response.status_code == 200
    assert response.json()["tags"] == [bug]


def test_tag_filter_excludes_task_after_its_tag_is_changed(client):
    backend = create_tag(client, "Backend")
    bug = create_tag(client, "Bug")
    task = client.post("/tasks", json={"title": "Fix API", "tag_ids": [backend["id"]]}).json()

    update_response = client.patch(f"/tasks/{task['id']}", json={"tag_ids": [bug["id"]]})
    filtered_response = client.get("/tasks", params={"tag_id": backend["id"]})

    assert update_response.status_code == 200
    assert filtered_response.status_code == 200
    assert filtered_response.json() == []


def test_task_with_unknown_tag_is_rejected(client):
    response = client.post("/tasks", json={"title": "Fix API", "tag_ids": ["missing"]})

    assert response.status_code == 422


def test_list_tasks_filter_by_tag_returns_only_matching_tasks(client):
    backend = create_tag(client, "Backend")
    bug = create_tag(client, "Bug")
    matching = client.post("/tasks", json={"title": "API task", "tag_ids": [backend["id"]]}).json()
    client.post("/tasks", json={"title": "UI task", "tag_ids": [bug["id"]]}).json()

    response = client.get("/tasks", params={"tag_id": backend["id"]})

    assert response.status_code == 200
    assert [task["id"] for task in response.json()] == [matching["id"]]
