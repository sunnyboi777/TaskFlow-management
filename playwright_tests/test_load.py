"""Bounded concurrent API load test for TaskFlow.

Run explicitly with:
    python -m pytest playwright_tests/test_load.py -v -s

Environment variables:
    LOAD_TEST_REQUESTS: total authenticated GET requests (default: 30)
    LOAD_TEST_CONCURRENCY: concurrent workers (default: 5)
    LOAD_TEST_P95_SECONDS: maximum p95 latency (default: 2.0)
"""

import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from playwright.sync_api import APIRequestContext, Playwright, sync_playwright


BASE_URL = os.getenv("TASKFLOW_API_URL", "http://127.0.0.1:8000").rstrip("/")
PASSWORD = "TaskFlow_Load_2026!"


def _positive_int(name: str, default: int) -> int:
    value = int(os.getenv(name, str(default)))
    if value < 1:
        raise ValueError(f"{name} must be at least 1")
    return value


def _login(request: APIRequestContext, email: str) -> str:
    register_response = request.post(
        "/auth/register",
        data={"email": email, "password": PASSWORD},
    )
    assert register_response.status == 201, (
        f"Load-test registration failed: {register_response.status} "
        f"{register_response.text()}"
    )

    login_response = request.post(
        "/auth/login",
        data={"email": email, "password": PASSWORD},
    )
    assert login_response.status == 200, (
        f"Load-test login failed: {login_response.status} "
        f"{login_response.text()}"
    )
    return login_response.json()["access_token"]


def _worker(token: str, request_count: int) -> list[tuple[int, float]]:
    results = []
    with sync_playwright() as playwright:
        request = playwright.request.new_context(
            base_url=BASE_URL,
            extra_http_headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {token}",
            },
            timeout=15000,
        )
        try:
            for _ in range(request_count):
                start = time.perf_counter()
                response = request.get("/tasks")
                elapsed = time.perf_counter() - start
                results.append((response.status, elapsed))
        finally:
            request.dispose()
    return results


def test_authenticated_task_reads_under_concurrent_load(
    playwright: Playwright,
):
    total_requests = _positive_int("LOAD_TEST_REQUESTS", 30)
    concurrency = _positive_int("LOAD_TEST_CONCURRENCY", 5)
    p95_limit = float(os.getenv("LOAD_TEST_P95_SECONDS", "2.0"))
    if p95_limit <= 0:
        raise ValueError("LOAD_TEST_P95_SECONDS must be greater than 0")

    setup_request = playwright.request.new_context(
        base_url=BASE_URL,
        extra_http_headers={"Accept": "application/json"},
        timeout=15000,
    )
    try:
        token = _login(
            setup_request,
            f"load-{uuid.uuid4().hex[:12]}@taskflow.test",
        )
    finally:
        setup_request.dispose()

    worker_count = min(concurrency, total_requests)
    base_count, remainder = divmod(total_requests, worker_count)
    counts = [
        base_count + (1 if index < remainder else 0)
        for index in range(worker_count)
    ]

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        batches = list(
            executor.map(
                lambda count: _worker(token, count),
                counts,
            )
        )
    wall_time = time.perf_counter() - started

    results = [result for batch in batches for result in batch]
    assert len(results) == total_requests

    failures = [(status, elapsed) for status, elapsed in results if status != 200]
    assert not failures, f"Unexpected response statuses: {failures[:5]}"

    latencies = sorted(elapsed for _, elapsed in results)
    p95_index = min(len(latencies) - 1, int(len(latencies) * 0.95))
    p95 = latencies[p95_index]

    print(
        f"\nLoad test: {total_requests} requests, "
        f"{worker_count} workers, wall time {wall_time:.3f}s, "
        f"p95 {p95:.3f}s"
    )
    assert p95 <= p95_limit, (
        f"p95 latency was {p95:.3f}s; limit is {p95_limit:.3f}s"
    )
