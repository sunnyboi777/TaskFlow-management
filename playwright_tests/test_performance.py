import time
import uuid
from typing import Generator

import pytest
from playwright.sync_api import APIRequestContext, Page, Playwright, expect


FRONTEND_URL = "http://127.0.0.1:8501"
BACKEND_URL = "http://127.0.0.1:8000"
PASSWORD = "TaskFlow_Performance_2026!"

# Initial performance targets; adjust based on your machine and environment.
HOMEPAGE_LIMIT_SECONDS = 10.0
API_LIMIT_SECONDS = 2.0


@pytest.fixture
def api_request(
    playwright: Playwright,
) -> Generator[APIRequestContext, None, None]:
    setup_request = playwright.request.new_context(
        base_url=BACKEND_URL,
        extra_http_headers={"Content-Type": "application/json"},
    )
    email = f"performance-{uuid.uuid4().hex[:12]}@taskflow.test"
    register_response = setup_request.post(
        "/auth/register",
        data={"email": email, "password": PASSWORD},
    )
    assert register_response.status == 201, register_response.text()

    login_response = setup_request.post(
        "/auth/login",
        data={"email": email, "password": PASSWORD},
    )
    assert login_response.status == 200, login_response.text()

    token = login_response.json()["access_token"]
    request = playwright.request.new_context(
        base_url=BACKEND_URL,
        extra_http_headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )
    try:
        yield request
    finally:
        request.dispose()
        setup_request.dispose()


def test_homepage_load_performance(page: Page):
    """Measure time until the main TaskFlow heading is visible."""

    page.set_viewport_size({"width": 1365, "height": 900})

    start = time.perf_counter()

    response = page.goto(
        FRONTEND_URL,
        wait_until="domcontentloaded",
        timeout=30000,
    )

    assert response is not None, "No response received from TaskFlow."
    assert response.status < 400, (
        f"Homepage returned HTTP {response.status}."
    )

    expect(
        page.get_by_role(
            "heading",
            name="TaskFlow",
        )
    ).to_be_visible(timeout=20000)

    elapsed = time.perf_counter() - start

    print(f"\nHomepage load time: {elapsed:.3f} seconds")

    assert elapsed < HOMEPAGE_LIMIT_SECONDS, (
        f"Homepage took {elapsed:.3f}s; "
        f"limit is {HOMEPAGE_LIMIT_SECONDS:.1f}s."
    )


def test_health_api_response_performance(api_request):
    """Measure backend health endpoint response time."""

    start = time.perf_counter()
    response = api_request.get("/health", timeout=10000)
    elapsed = time.perf_counter() - start

    assert response.status == 200, (
        f"Health endpoint returned HTTP {response.status}."
    )

    print(f"\nHealth API response time: {elapsed:.3f} seconds")

    assert elapsed < API_LIMIT_SECONDS, (
        f"Health API took {elapsed:.3f}s; "
        f"limit is {API_LIMIT_SECONDS:.1f}s."
    )


def test_task_crud_api_performance(api_request):
    """Measure task creation, retrieval, and deletion response times."""

    # CREATE
    start = time.perf_counter()
    create_response = api_request.post(
        "/tasks",
        data={
            "title": "Performance Test Task",
            "description": "Created for API performance testing",
        },
        timeout=10000,
    )
    create_time = time.perf_counter() - start

    assert create_response.status == 201, (
        f"Task creation failed: {create_response.status} "
        f"{create_response.text()}"
    )

    task_id = create_response.json()["id"]

    try:
        # READ
        start = time.perf_counter()
        read_response = api_request.get(
            f"/tasks/{task_id}",
            timeout=10000,
        )
        read_time = time.perf_counter() - start

        assert read_response.status == 200, (
            f"Task retrieval failed: {read_response.status} "
            f"{read_response.text()}"
        )

        assert read_response.json()["id"] == task_id

        print(f"\nTask creation time: {create_time:.3f} seconds")
        print(f"Task retrieval time: {read_time:.3f} seconds")

        assert create_time < API_LIMIT_SECONDS, (
            f"Task creation took {create_time:.3f}s."
        )
        assert read_time < API_LIMIT_SECONDS, (
            f"Task retrieval took {read_time:.3f}s."
        )

    finally:
        # Clean up the test-created task.
        delete_response = api_request.delete(
            f"/tasks/{task_id}",
            timeout=10000,
        )

        assert delete_response.status in (200, 204, 404), (
            f"Task cleanup failed: {delete_response.status} "
            f"{delete_response.text()}"
        )
