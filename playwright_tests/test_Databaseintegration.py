
import os
import re
import uuid
from collections.abc import Generator

import pytest
from playwright.sync_api import Page, Playwright, APIRequestContext, expect


FRONTEND_URL = os.getenv(
    "TASKFLOW_BASE_URL",
    "http://localhost:8501",
).rstrip("/")

BACKEND_URL = "http://127.0.0.1:8000"

# Reuse the dedicated Playwright account.
TEST_EMAIL = "playwright@taskflow.test"
TEST_PASSWORD = "TaskFlow_Playwright_2026!"


# ============================================================
# AUTHENTICATED API HELPER
# ============================================================

class AuthenticatedAPIRequest:
    """Send API requests with the authenticated user's JWT."""

    def __init__(
        self,
        request: APIRequestContext,
        headers: dict,
    ):
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
# API FIXTURE WITH AUTHENTICATION
# ============================================================

@pytest.fixture
def api_request(
    playwright: Playwright,
) -> Generator[AuthenticatedAPIRequest, None, None]:

    request = playwright.request.new_context(
        base_url=BACKEND_URL,
        extra_http_headers={
            "Content-Type": "application/json",
        },
    )

    try:
        # Register the dedicated account if it does not exist.
        register_response = request.post(
            "/auth/register",
            data={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
            },
        )

        if register_response.status == 201:
            print("\n[AUTH] Playwright account created.")

        elif register_response.status == 409:
            print("\n[AUTH] Reusing existing Playwright account.")

        else:
            pytest.fail(
                f"Registration failed: "
                f"{register_response.status} "
                f"{register_response.text()}"
            )

        # Log in and obtain a JWT.
        login_response = request.post(
            "/auth/login",
            data={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
            },
        )

        assert login_response.status == 200, (
            f"API login failed: {login_response.status} "
            f"{login_response.text()}"
        )

        token = login_response.json()["access_token"]

        authenticated_headers = {
            "Authorization": f"Bearer {token}",
        }

        yield AuthenticatedAPIRequest(
            request,
            authenticated_headers,
        )

    finally:
        request.dispose()


# ============================================================
# FRONTEND + BACKEND + DATABASE INTEGRATION TEST
# ============================================================

def test_frontend_backend_database_integration(
    page: Page,
    api_request: AuthenticatedAPIRequest,
):
    marker = uuid.uuid4().hex[:8]

    title = f"Integration Test {marker}"
    description = f"Created through UI {marker}"

    print(f"\n[TEST] Task title: {title}")

    try:
        # ----------------------------------------------------
        # 1. Open the frontend
        # ----------------------------------------------------

        page.goto(
            FRONTEND_URL,
            wait_until="domcontentloaded",
            timeout=30000,
        )

        # ----------------------------------------------------
        # 2. Log in through the TaskFlow UI
        # ----------------------------------------------------

        email_input = page.get_by_role(
            "textbox",
            name="Email Address",
        ).first

        password_input = page.get_by_label(
            "Password"
        ).first

        expect(email_input).to_be_visible(timeout=15000)
        expect(password_input).to_be_visible(timeout=15000)

        email_input.fill(TEST_EMAIL)
        password_input.fill(TEST_PASSWORD)

        page.get_by_role(
            "button",
            name=re.compile(r"^Login$", re.I),
        ).click()

        # Verify the authenticated Dashboard.
        expect(
            page.get_by_text(
                "YOUR PRODUCTIVITY SPACE",
                exact=False,
            ).first
        ).to_be_visible(timeout=20000)

        # ----------------------------------------------------
        # 3. Navigate to Create Task
        # ----------------------------------------------------

        page.get_by_role(
            "link",
            name=re.compile("Create Task", re.I),
        ).first.click()

        expect(page).to_have_url(
            re.compile(r"/create-task/?$")
        )

        # ----------------------------------------------------
        # 4. Create a uniquely named task through the UI
        # ----------------------------------------------------

        page.get_by_label("Task Title *").fill(title)

        page.get_by_label("Description").fill(description)

        page.get_by_role(
            "button",
            name=re.compile("Create Task", re.I),
        ).click()

        print("\n[TEST] Task submitted through frontend.")

        # ----------------------------------------------------
        # 5. Verify the task through the authenticated API
        # ----------------------------------------------------

        response = api_request.get("/tasks")

        assert response.status == 200, (
            f"Task listing failed: {response.status} "
            f"{response.text()}"
        )

        matching_tasks = [
            task
            for task in response.json()
            if task["title"] == title
        ]

        assert len(matching_tasks) == 1, (
            "Task created through the UI was not found "
            "exactly once through the authenticated API."
        )

        task = matching_tasks[0]
        task_id = task["id"]

        assert task["description"] == description
        assert task["completed"] is False

        print(
            f"\n[TEST] Backend verified task ID: {task_id}"
        )

        # ----------------------------------------------------
        # 6. Verify that the task can be retrieved by ID
        # ----------------------------------------------------

        detail_response = api_request.get(
            f"/tasks/{task_id}"
        )

        assert detail_response.status == 200

        assert detail_response.json()["title"] == title

        assert (
            detail_response.json()["description"]
            == description
        )

        # ----------------------------------------------------
        # 7. Verify the task through the frontend
        # ----------------------------------------------------

        page.get_by_role(
            "link",
            name=re.compile("All Tasks", re.I),
        ).first.click()

        expect(page).to_have_url(
            re.compile(r"/all-tasks/?$")
        )

        search_box = page.get_by_role(
            "textbox",
            name=re.compile("Search tasks", re.I),
        )

        expect(search_box).to_be_visible(timeout=10000)

        search_box.fill(title)
        search_box.press("Enter")

        expect(
            page.get_by_role(
                "heading",
                name=re.compile(
                    re.escape(title)
                ),
            ).first
        ).to_be_visible(timeout=15000)

        expect(
            page.get_by_text(
                description,
                exact=True,
            )
        ).to_be_visible(timeout=10000)

        print(
            "\n[TEST] Frontend, backend, and database "
            "integration verified successfully."
        )

    finally:
        # ----------------------------------------------------
        # 8. CLEANUP: Delete only this test's unique task
        # ----------------------------------------------------

        print(
            f"\n[CLEANUP] Checking test task: {title}"
        )

        try:
            cleanup_response = api_request.get("/tasks")

            assert cleanup_response.status == 200, (
                "Could not retrieve tasks for cleanup: "
                f"{cleanup_response.status}"
            )

            # Find only the uniquely named task belonging
            # to the dedicated Playwright account.
            tasks_to_delete = [
                task
                for task in cleanup_response.json()
                if task["title"] == title
            ]

            for task in tasks_to_delete:
                delete_response = api_request.delete(
                    f"/tasks/{task['id']}"
                )

                assert delete_response.status in (204, 404), (
                    f"Test-task cleanup failed: "
                    f"{delete_response.status} "
                    f"{delete_response.text()}"
                )

                print(
                    f"\n[CLEANUP] Removed test task ID: "
                    f"{task['id']}"
                )

            # Verify that the uniquely named task is absent.
            verification_response = api_request.get("/tasks")

            assert verification_response.status == 200

            remaining_tasks = [
                task
                for task in verification_response.json()
                if task["title"] == title
            ]

            assert len(remaining_tasks) == 0, (
                "Test task still exists after cleanup."
            )

            print(
                "\n[CLEANUP] Test task deletion verified."
            )

        except Exception as cleanup_error:
            print(
                f"\n[CLEANUP WARNING] "
                f"Could not complete automatic cleanup: "
                f"{cleanup_error}"
            )
