
import uuid
import pytest
from typing import Generator

from playwright.sync_api import APIRequestContext, Playwright


BASE_URL = "http://127.0.0.1:8000"

TEST_EMAIL = "playwright@taskflow.test"
TEST_PASSWORD = "TaskFlow_Playwright_2026!"


# ============================================================
# AUTHENTICATED API REQUEST HELPER
# ============================================================

class AuthenticatedAPIRequest:

    def __init__(self, request, headers):
        self.request = request
        self.headers = headers

    def get(self, url, **kwargs):
        return self.request.get(
            url,
            headers=self.headers,
            **kwargs,
        )

    def post(self, url, **kwargs):
        return self.request.post(
            url,
            headers=self.headers,
            **kwargs,
        )

    def put(self, url, **kwargs):
        return self.request.put(
            url,
            headers=self.headers,
            **kwargs,
        )

    def delete(self, url, **kwargs):
        return self.request.delete(
            url,
            headers=self.headers,
            **kwargs,
        )


# ============================================================
# AUTHENTICATION FIXTURE
# ============================================================

@pytest.fixture
def api_request(
    playwright: Playwright,
) -> Generator[AuthenticatedAPIRequest, None, None]:

    request = playwright.request.new_context(
        base_url=BASE_URL,
        extra_http_headers={
            "Content-Type": "application/json",
        },
    )

    try:
        # Register the dedicated Playwright account if needed.
        register_response = request.post(
            "/auth/register",
            data={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
            },
        )

        if register_response.status == 201:
            print("Dedicated Playwright account created.")

        elif register_response.status == 409:
            print("Dedicated Playwright account already exists.")

        else:
            pytest.fail(
                "Could not prepare the Playwright account: "
                f"{register_response.status} "
                f"{register_response.text}"
            )

        # Log in and obtain the JWT token.
        login_response = request.post(
            "/auth/login",
            data={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
            },
        )

        assert login_response.status == 200, (
            f"Playwright login failed: "
            f"{login_response.status} "
            f"{login_response.text}"
        )

        token = login_response.json()["access_token"]

        # Attach the token to all authenticated API requests.
        request_headers = {
            "Authorization": f"Bearer {token}",
        }

        yield AuthenticatedAPIRequest(
            request,
            request_headers,
        )

    finally:
        request.dispose()


# ============================================================
# HOME ENDPOINT TEST
# ============================================================

def test_home_endpoint(api_request):

    response = api_request.get("/")

    assert response.status == 200

    data = response.json()

    assert data["message"] == "Task Management API is running"
    assert data["database"] == "taskproject"


# ============================================================
# HEALTH ENDPOINT TEST
# ============================================================

def test_health_endpoint(api_request):

    response = api_request.get("/health")

    assert response.status == 200

    assert response.json() == {
        "status": "ok",
    }


# ============================================================
# TASK CRUD API TEST
# ============================================================

def test_create_read_update_delete_task(api_request):

    marker = uuid.uuid4().hex[:8]

    original_title = f"Playwright API Test {marker}"
    updated_title = f"Updated Playwright API Test {marker}"

    task_id = None

    try:
        # ----------------------------------------------------
        # CREATE TASK
        # ----------------------------------------------------

        create_response = api_request.post(
            "/tasks",
            data={
                "title": original_title,
                "description": "Created by automated API testing",
            },
        )

        assert create_response.status == 201, (
            create_response.text
        )

        created_task = create_response.json()

        task_id = created_task["id"]

        assert created_task["title"] == original_title

        assert created_task["description"] == (
            "Created by automated API testing"
        )

        assert created_task["completed"] is False

        # ----------------------------------------------------
        # READ ALL TASKS
        # ----------------------------------------------------

        list_response = api_request.get("/tasks")

        assert list_response.status == 200

        assert any(
            task["id"] == task_id
            for task in list_response.json()
        )

        # ----------------------------------------------------
        # READ ONE TASK
        # ----------------------------------------------------

        read_response = api_request.get(
            f"/tasks/{task_id}"
        )

        assert read_response.status == 200

        assert read_response.json()["id"] == task_id

        # ----------------------------------------------------
        # UPDATE TASK
        # ----------------------------------------------------

        update_response = api_request.put(
            f"/tasks/{task_id}",
            data={
                "title": updated_title,
                "description": "Task updated successfully",
                "completed": True,
            },
        )

        assert update_response.status == 200, (
            update_response.text
        )

        updated_task = update_response.json()

        assert updated_task["title"] == updated_title

        assert updated_task["description"] == (
            "Task updated successfully"
        )

        assert updated_task["completed"] is True

    finally:
        # ----------------------------------------------------
        # CLEANUP — DELETE ONLY THE TEST TASK
        # ----------------------------------------------------

        if task_id is not None:

            delete_response = api_request.delete(
                f"/tasks/{task_id}"
            )

            assert delete_response.status in (204, 404), (
                f"Cleanup failed: "
                f"{delete_response.status} "
                f"{delete_response.text}"
            )

    # --------------------------------------------------------
    # VERIFY TASK DELETION
    # --------------------------------------------------------

    if task_id is not None:

        missing_response = api_request.get(
            f"/tasks/{task_id}"
        )

        assert missing_response.status == 404


# ============================================================
# READ NONEXISTENT TASK TEST
# ============================================================

def test_read_nonexistent_task(api_request):

    response = api_request.get(
        "/tasks/999999999"
    )

    assert response.status == 404

    assert response.json()["detail"] == "Task not found"


# ============================================================
# UPDATE NONEXISTENT TASK TEST
# ============================================================

def test_update_nonexistent_task(api_request):

    response = api_request.put(
        "/tasks/999999999",
        data={
            "title": "Missing Task",
            "description": "This task does not exist",
            "completed": False,
        },
    )

    assert response.status == 404

    assert response.json()["detail"] == "Task not found"


# ============================================================
# DELETE NONEXISTENT TASK TEST
# ============================================================

def test_delete_nonexistent_task(api_request):

    response = api_request.delete(
        "/tasks/999999999"
    )

    assert response.status == 404

    assert response.json()["detail"] == "Task not found"
