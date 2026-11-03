from fastapi.testclient import TestClient  # pyright: ignore[reportMissingImports]

from backend.main import app

client = TestClient(app)


def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Task Management API is running",
        "database": "taskproject",
    }


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
