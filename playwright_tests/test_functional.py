"""Functional API workflows for TaskFlow."""

import os
import uuid

import pytest
from playwright.sync_api import APIRequestContext


BASE_URL = os.getenv("TASKFLOW_API_URL", "http://127.0.0.1:8000").rstrip("/")
PASSWORD = "TaskFlow_Functional_2026!"


class AuthenticatedAPI:
    def __init__(self, request: APIRequestContext, token: str):
        self.request = request
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        }

    def get(self, path: str):
        return self.request.get(path, headers=self.headers)

    def post(self, path: str, **kwargs):
        return self.request.post(path, headers=self.headers, **kwargs)

    def put(self, path: str, **kwargs):
        return self.request.put(path, headers=self.headers, **kwargs)

    def delete(self, path: str):
        return self.request.delete(path, headers=self.headers)


@pytest.fixture
def api_request(playwright):
    request = playwright.request.new_context(
        base_url=BASE_URL,
        extra_http_headers={"Accept": "application/json"},
        timeout=15000,
    )
    try:
        yield request
    finally:
        request.dispose()


def register_and_login(
    request: APIRequestContext,
    email: str,
) -> tuple[AuthenticatedAPI, str]:
    register_response = request.post(
        "/auth/register",
        data={"email": email, "password": PASSWORD},
    )
    assert register_response.status == 201, (
        f"Registration failed: {register_response.status} "
        f"{register_response.text()}"
    )

    login_response = request.post(
        "/auth/login",
        data={"email": email, "password": PASSWORD},
    )
    assert login_response.status == 200, (
        f"Login failed: {login_response.status} {login_response.text()}"
    )

    token = login_response.json()["access_token"]
    return AuthenticatedAPI(request, token), token


def test_health_and_authentication_workflow(api_request):
    marker = uuid.uuid4().hex[:12]
    email = f"functional-{marker}@taskflow.test"
    health_response = api_request.get("/health")
    assert health_response.status == 200
    assert health_response.json() == {"status": "ok"}

    authenticated, token = register_and_login(api_request, email)
    assert token

    tasks_response = authenticated.get("/tasks")
    assert tasks_response.status == 200
    assert isinstance(tasks_response.json(), list)


def test_task_crud_and_validation_workflow(api_request):
    marker = uuid.uuid4().hex[:12]
    authenticated, _ = register_and_login(
        api_request,
        f"functional-crud-{marker}@taskflow.test",
    )
    task_id = None

    try:
        invalid_response = authenticated.post(
            "/tasks",
            data={"title": "", "description": "Invalid task"},
        )
        assert invalid_response.status == 422

        create_response = authenticated.post(
            "/tasks",
            data={
                "title": f"Functional task {marker}",
                "description": "Created by the functional Playwright suite.",
            },
        )
        assert create_response.status == 201, create_response.text()
        created_task = create_response.json()
        task_id = created_task["id"]
        assert created_task["completed"] is False

        read_response = authenticated.get(f"/tasks/{task_id}")
        assert read_response.status == 200
        assert read_response.json() == created_task

        update_response = authenticated.put(
            f"/tasks/{task_id}",
            data={
                "title": f"Updated functional task {marker}",
                "description": "Updated by the functional Playwright suite.",
                "completed": True,
            },
        )
        assert update_response.status == 200
        updated_task = update_response.json()
        assert updated_task["title"].startswith("Updated functional task")
        assert updated_task["completed"] is True

        list_response = authenticated.get("/tasks")
        assert list_response.status == 200
        assert any(task["id"] == task_id for task in list_response.json())
    finally:
        if task_id is not None:
            delete_response = authenticated.delete(f"/tasks/{task_id}")
            assert delete_response.status in (204, 404), delete_response.text()


def test_authentication_rejects_invalid_credentials(api_request):
    response = api_request.post(
        "/auth/login",
        data={
            "email": f"missing-{uuid.uuid4().hex[:12]}@taskflow.test",
            "password": PASSWORD,
        },
    )
    assert response.status == 401
