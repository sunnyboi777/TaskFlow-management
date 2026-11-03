import os
import time
import uuid

import pytest


BASE_URL = os.getenv("TASKFLOW_API_URL", "http://127.0.0.1:8000")
PASSWORD = "TaskFlow_Security_Test_2026!"
RUN_ID = uuid.uuid4().hex[:12]


class AuthenticatedAPI:
    """Small helper that attaches a user's bearer token to API requests."""

    def __init__(self, request, token):
        self.request = request
        self.headers = {"Authorization": f"Bearer {token}"}

    def get(self, path, **kwargs):
        return self.request.get(
            f"{BASE_URL}{path}", headers=self.headers, **kwargs
        )

    def post(self, path, **kwargs):
        return self.request.post(
            f"{BASE_URL}{path}", headers=self.headers, **kwargs
        )

    def put(self, path, **kwargs):
        return self.request.put(
            f"{BASE_URL}{path}", headers=self.headers, **kwargs
        )

    def delete(self, path, **kwargs):
        return self.request.delete(
            f"{BASE_URL}{path}", headers=self.headers, **kwargs
        )


@pytest.fixture(scope="module")
def api_context(playwright):
    request = playwright.request.new_context(
        base_url=BASE_URL,
        extra_http_headers={"Accept": "application/json"},
        timeout=15000,
    )
    try:
        yield request
    finally:
        request.dispose()


def register_and_login(api_context, email):
    register_response = api_context.post(
        "/auth/register",
        data={"email": email, "password": PASSWORD},
    )
    assert register_response.status in (201, 409), (
        f"Registration failed for test account {email}: "
        f"{register_response.status} {register_response.text()}"
    )

    login_response = api_context.post(
        "/auth/login",
        data={"email": email, "password": PASSWORD},
    )
    assert login_response.status == 200, (
        f"Login failed for test account {email}: "
        f"{login_response.status} {login_response.text()}"
    )
    token = login_response.json()["access_token"]
    return AuthenticatedAPI(api_context, token)


@pytest.fixture(scope="module")
def two_test_users(api_context):
    # Unique temporary accounts avoid using either of the user's normal accounts.
    user_a_email = f"security-a-{RUN_ID}@taskflow.test"
    user_b_email = f"security-b-{RUN_ID}@taskflow.test"

    user_a = register_and_login(api_context, user_a_email)
    user_b = register_and_login(api_context, user_b_email)

    yield user_a, user_b

    # The application has no user-delete endpoint. The uniquely named test
    # accounts are therefore left in the database; all test tasks are removed.


def test_tasks_require_authentication(api_context):
    response = api_context.get("/tasks")
    assert response.status == 401


def test_invalid_bearer_token_is_rejected(api_context):
    response = api_context.get(
        "/tasks",
        headers={"Authorization": "Bearer definitely-not-a-valid-token"},
    )
    assert response.status == 401


def test_duplicate_registration_is_rejected(api_context, two_test_users):
    user_email = f"security-a-{RUN_ID}@taskflow.test"
    response = api_context.post(
        "/auth/register",
        data={"email": user_email.upper(), "password": PASSWORD},
    )
    assert response.status == 409


def test_users_cannot_access_each_others_tasks(two_test_users):
    user_a, user_b = two_test_users
    unique_title = f"Security isolation test {RUN_ID}"

    create_response = user_a.post(
        "/tasks",
        data={
            "title": unique_title,
            "description": "Temporary task for authorization testing.",
        },
    )
    assert create_response.status == 201, create_response.text()
    task_id = create_response.json()["id"]

    try:
        # The task must not appear in the second user's task list.
        list_response = user_b.get("/tasks")
        assert list_response.status == 200
        visible_ids = [task["id"] for task in list_response.json()]
        assert task_id not in visible_ids

        # A different user must not be able to read, update, or delete it.
        read_response = user_b.get(f"/tasks/{task_id}")
        assert read_response.status == 404

        update_response = user_b.put(
            f"/tasks/{task_id}",
            data={
                "title": "Unauthorized change attempt",
                "description": "This update must not be applied.",
                "completed": True,
            },
        )
        assert update_response.status == 404

        delete_response = user_b.delete(f"/tasks/{task_id}")
        assert delete_response.status == 404

        # Confirm the original owner still has the unchanged task.
        owner_read_response = user_a.get(f"/tasks/{task_id}")
        assert owner_read_response.status == 200
        owner_task = owner_read_response.json()
        assert owner_task["title"] == unique_title
        assert owner_task["completed"] is False
    finally:
        # Cleanup is performed by the task's owner, never by the other user.
        cleanup_response = user_a.delete(f"/tasks/{task_id}")
        assert cleanup_response.status in (204, 404)


def test_malformed_authorization_header_is_rejected(api_context):
    response = api_context.get(
        "/tasks",
        headers={"Authorization": "NotBearer some-value"},
    )
    assert response.status == 401
