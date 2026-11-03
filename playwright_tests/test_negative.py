import uuid

import pytest
from typing import Generator
from playwright.sync_api import APIRequestContext, Playwright


BASE_URL = "http://127.0.0.1:8000"
PASSWORD = "TaskFlow_Negative_2026!"


@pytest.fixture
def api_request(playwright: Playwright) -> Generator[APIRequestContext, None, None]:
    request = playwright.request.new_context(
        base_url=BASE_URL,
        extra_http_headers={"Content-Type": "application/json"},
    )
    email = f"negative-{uuid.uuid4().hex[:12]}@taskflow.test"
    register_response = request.post(
        "/auth/register",
        data={"email": email, "password": PASSWORD},
    )
    assert register_response.status == 201, register_response.text()

    login_response = request.post(
        "/auth/login",
        data={"email": email, "password": PASSWORD},
    )
    assert login_response.status == 200, login_response.text()

    token = login_response.json()["access_token"]
    authenticated_request = playwright.request.new_context(
        base_url=BASE_URL,
        extra_http_headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )
    try:
        yield authenticated_request
    finally:
        authenticated_request.dispose()
        request.dispose()


def test_create_task_with_missing_title(api_request):
    """A task without a required title should be rejected."""

    response = api_request.post(
        "/tasks",
        data={
            "description": "Task without a title",
        },
    )

    assert response.status == 422, (
        f"Expected 422 for missing title, got "
        f"{response.status}: {response.text()}"
    )


def test_create_task_with_empty_title(api_request):
    """An empty title should not create a task."""

    response = api_request.post(
        "/tasks",
        data={
            "title": "",
            "description": "Task with an empty title",
        },
    )

    assert response.status in (400, 422), (
        f"Expected validation rejection, got "
        f"{response.status}: {response.text()}"
    )


def test_read_nonexistent_task(api_request):
    """Reading a nonexistent task should return 404."""

    response = api_request.get("/tasks/999999999")

    assert response.status == 404, (
        f"Expected 404, got {response.status}: {response.text()}"
    )


def test_update_nonexistent_task(api_request):
    """Updating a nonexistent task should return 404."""

    response = api_request.put(
        "/tasks/999999999",
        data={
            "title": "Updated missing task",
            "description": "This task does not exist",
            "completed": False,
        },
    )

    assert response.status == 404, (
        f"Expected 404, got {response.status}: {response.text()}"
    )


def test_delete_nonexistent_task(api_request):
    """Deleting a nonexistent task should return 404."""

    response = api_request.delete("/tasks/999999999")

    assert response.status == 404, (
        f"Expected 404, got {response.status}: {response.text()}"
    )


def test_create_task_with_wrong_data_types(api_request):
    """Invalid field types should be rejected."""

    response = api_request.post(
        "/tasks",
        data={
            "title": 12345,
            "description": ["invalid", "description"],
        },
    )

    assert response.status in (400, 422), (
        f"Expected validation rejection, got "
        f"{response.status}: {response.text()}"
    )


def test_unknown_api_endpoint(api_request):
    """An unknown endpoint should return 404."""

    response = api_request.get("/this-endpoint-does-not-exist")

    assert response.status == 404, (
        f"Expected 404, got {response.status}: {response.text()}"
    )
