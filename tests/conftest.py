import pytest
from fastapi.testclient import TestClient

from app.main import app
from app import store


@pytest.fixture(autouse=True)
def _reset_storage():
    store._reset()
    yield
    store._reset()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def created_task(client):
    response = client.post("/tasks", json={"title": "fixture task"})
    assert response.status_code == 201
    return response.json()
