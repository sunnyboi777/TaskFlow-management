
"""
TaskFlow End-to-End Automation Tests.

Run:
    python -m pytest playwright_tests/test_taskflow_e2e.py -v -s

Evidence:
    Playwright/runs/run_<timestamp>/
"""

import os
import re
import uuid

import pytest
from playwright.sync_api import Page, expect


BASE_URL = os.getenv(
    "TASKFLOW_BASE_URL",
    "http://localhost:8501",
).rstrip("/")

TEST_EMAIL = "playwright@taskflow.test"
TEST_PASSWORD = "TaskFlow_Playwright_2026!"


# ============================================================
# COMMON HELPERS
# ============================================================

def open_app(page: Page) -> None:
    """Open TaskFlow, log in, and verify the Dashboard."""

    response = page.goto(
        BASE_URL,
        wait_until="domcontentloaded",
        timeout=30000,
    )

    if response is not None and response.status >= 400:
        pytest.fail(
            f"TaskFlow returned HTTP {response.status} "
            f"at {BASE_URL}"
        )

    # Locate the Login form fields.
    email_input = page.get_by_role(
        "textbox",
        name="Email Address",
    ).first

    password_input = page.get_by_label(
        "Password"
    ).first

    expect(email_input).to_be_visible(timeout=15000)
    expect(password_input).to_be_visible(timeout=15000)

    # Log in using the dedicated Playwright account.
    email_input.fill(TEST_EMAIL)
    password_input.fill(TEST_PASSWORD)

    page.get_by_role(
        "button",
        name="Login",
    ).click()

    # Verify that the Dashboard loads.
    expect(
        page.get_by_text(
            "YOUR PRODUCTIVITY SPACE",
            exact=False,
        ).first
    ).to_be_visible(timeout=20000)


def navigate_to(page: Page, route: str) -> None:
    """Navigate through the application's sidebar."""

    route_names = {
        "/": "Dashboard",
        "/create-task": "Create Task",
        "/all-tasks": "All Tasks",
    }

    if route not in route_names:
        raise ValueError(
            f"Unknown TaskFlow route: {route}"
        )

    link = page.get_by_role(
        "link",
        name=re.compile(
            re.escape(route_names[route]),
            re.I,
        ),
    ).first

    expect(link).to_be_visible(timeout=10000)

    link.click()

    expected_url = re.compile(
        re.escape(f"{BASE_URL}{route}") + r"/?$"
    )

    expect(page).to_have_url(
        expected_url,
        timeout=15000,
    )


def search_for_task(
    page: Page,
    title: str,
) -> None:
    """Search for a task and verify its heading appears."""

    search_box = page.get_by_role(
        "textbox",
        name=re.compile("Search tasks", re.I),
    )

    expect(search_box).to_be_visible(timeout=10000)

    search_box.fill(title)
    search_box.press("Enter")

    task_heading = page.get_by_role(
        "heading",
        name=re.compile(
            re.escape(title),
            re.I,
        ),
    ).first

    expect(task_heading).to_be_visible(timeout=15000)


def assert_task_exists(
    page: Page,
    title: str,
    description: str,
) -> None:
    """Verify the task title and description."""

    search_for_task(page, title)

    expect(
        page.get_by_text(
            description,
            exact=True,
        )
    ).to_be_visible(timeout=10000)


def delete_task(
    page: Page,
    title: str,
) -> None:
    """Delete only the uniquely named Playwright test task."""

    navigate_to(page, "/all-tasks")

    search_box = page.get_by_role(
        "textbox",
        name=re.compile("Search tasks", re.I),
    )

    expect(search_box).to_be_visible(timeout=10000)

    search_box.fill(title)
    search_box.press("Enter")

    task_heading = page.get_by_role(
        "heading",
        name=re.compile(
            re.escape(title),
            re.I,
        ),
    ).first

    # If the task is already gone, cleanup is complete.
    try:
        expect(
            task_heading
        ).to_be_visible(timeout=5000)

    except AssertionError:
        expect(
            task_heading
        ).to_have_count(0, timeout=5000)

        print(
            f"\n[DELETE] Task already absent: {title}"
        )

        return

    # Scope the Delete button to the task card containing
    # the matching title, rather than deleting another task.
    task_card = task_heading.locator(
        "xpath=ancestor::*[.//button[contains(., 'Delete')]][1]"
    )

    expect(task_card).to_be_visible(timeout=10000)

    delete_button = task_card.get_by_role(
        "button",
        name=re.compile(r"Delete", re.I),
    ).first

    expect(delete_button).to_be_visible(timeout=10000)
    delete_button.click()

    # Wait for the application's confirmation button.
    confirm_button = page.get_by_role(
        "button",
        name=re.compile(
            r"^\s*Yes,\s*Delete\s*$",
            re.I,
        ),
    )

    expect(
        confirm_button
    ).to_be_visible(timeout=15000)

    expect(confirm_button).to_be_enabled()

    confirm_button.click()

    # Verify that the task no longer appears.
    expect(
        task_heading
    ).to_have_count(0, timeout=20000)

    # Search again to verify absence in the task list.
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
                re.escape(title),
                re.I,
            ),
        )
    ).to_have_count(0, timeout=15000)

    print(
        f"\n[DELETE] Deletion verified: {title}"
    )


# ============================================================
# TEST 1: NAVIGATION
# ============================================================

def test_navigation_routes(
    page: Page,
    proof,
) -> None:
    """Test navigation across the TaskFlow pages."""

    open_app(page)

    proof.start_step("navigation")

    for name in (
        "Dashboard",
        "Create Task",
        "All Tasks",
    ):
        expect(
            page.get_by_role(
                "link",
                name=re.compile(name, re.I),
            ).first
        ).to_be_visible()

    navigate_to(page, "/create-task")

    expect(
        page.get_by_text(
            "Create a New Task",
            exact=False,
        ).first
    ).to_be_visible()

    navigate_to(page, "/all-tasks")

    expect(
        page.get_by_text(
            "Manage All Tasks",
            exact=False,
        ).first
    ).to_be_visible()

    navigate_to(page, "/")

    expect(
        page.get_by_text(
            "YOUR PRODUCTIVITY SPACE",
            exact=False,
        ).first
    ).to_be_visible()

    proof("navigation_passed")


# ============================================================
# TEST 2: COMPLETE CRUD LIFECYCLE
# ============================================================

def test_task_crud_lifecycle(
    page: Page,
    proof,
) -> None:
    """
    Test task creation, reading, updating, completion,
    and automatic deletion.
    """

    open_app(page)

    marker = uuid.uuid4().hex[:8]

    original_title = f"PW Test Task {marker}"
    edited_title = f"PW Edited Task {marker}"

    original_description = (
        f"Created automatically by Playwright ({marker})"
    )

    edited_description = (
        f"Edited automatically by Playwright ({marker})"
    )

    created = False
    title_to_clean = original_title

    try:
        # ----------------------------------------------------
        # CREATE
        # ----------------------------------------------------

        proof.start_step("create_task")

        navigate_to(page, "/create-task")

        title_input = page.get_by_label("Task Title *")
        description_input = page.get_by_label("Description")

        title_input.fill(original_title)
        description_input.fill(original_description)

        page.get_by_role(
            "button",
            name=re.compile("Create Task", re.I),
        ).click()

        # Mark for cleanup immediately after submission.
        created = True

        navigate_to(page, "/all-tasks")

        assert_task_exists(
            page,
            original_title,
            original_description,
        )

        proof("create_task_passed")

        # ----------------------------------------------------
        # READ
        # ----------------------------------------------------

        proof.start_step("read_task")

        assert_task_exists(
            page,
            original_title,
            original_description,
        )

        proof("read_task_passed")

        # ----------------------------------------------------
        # UPDATE
        # ----------------------------------------------------

        proof.start_step("update_task")

        page.get_by_role(
            "button",
            name=re.compile("Edit Task", re.I),
        ).first.click()

        expect(
            page.get_by_text(
                "Edit Task Details",
                exact=False,
            ).first
        ).to_be_visible(timeout=10000)

        page.get_by_label("Title").fill(edited_title)

        page.get_by_label(
            "Description"
        ).last.fill(edited_description)

        page.get_by_role(
            "button",
            name=re.compile("Save Changes", re.I),
        ).click()

        # Track the updated name for cleanup.
        title_to_clean = edited_title

        assert_task_exists(
            page,
            edited_title,
            edited_description,
        )

        proof("update_task_passed")

        # ----------------------------------------------------
        # COMPLETE
        # ----------------------------------------------------

        proof.start_step("complete_task")

        complete_button = page.get_by_role(
            "button",
            name=re.compile("Complete Task", re.I),
        ).first

        expect(
            complete_button
        ).to_be_visible(timeout=10000)

        complete_button.click()

        expect(
            page.get_by_text(
                "Completed",
                exact=False,
            ).first
        ).to_be_visible(timeout=15000)

        proof("complete_task_passed")

        # ----------------------------------------------------
        # DELETE
        # ----------------------------------------------------

        proof.start_step("delete_task")

        delete_task(
            page,
            title_to_clean,
        )

        created = False

        proof("delete_task_passed")

    finally:
        # ----------------------------------------------------
        # CLEANUP
        # ----------------------------------------------------

        # If the test fails after creation, attempt to remove
        # the uniquely named test task. Do not intentionally
        # delete unrelated tasks.

        if created:
            print(
                f"\n[CLEANUP] Removing test task: "
                f"{title_to_clean}"
            )

            try:
                proof.start_step("cleanup_delete")

                delete_task(
                    page,
                    title_to_clean,
                )

                print(
                    "[CLEANUP] Test task removed successfully."
                )

            except Exception as exc:
                print(
                    f"\n[CLEANUP] Automatic deletion failed: {exc}"
                )

                # Do not hide the original test failure.
                # The pytest failure hook saves diagnostics.


# ============================================================
# TEST 3: ALL ROUTES LOAD
# ============================================================

@pytest.mark.parametrize(
    ("route", "expected_text"),
    [
        ("/", "YOUR PRODUCTIVITY SPACE"),
        ("/create-task", "Create a New Task"),
        ("/all-tasks", "Manage All Tasks"),
    ],
)
def test_each_route_loads(
    page: Page,
    proof,
    route: str,
    expected_text: str,
) -> None:
    """Verify that each authenticated application route loads."""

    # Log in before accessing any application route.
    open_app(page)

    proof.start_step(
        f"route_{route.strip('/') or 'root'}"
    )

    # Navigate using the authenticated sidebar.
    navigate_to(page, route)

    expect(
        page.get_by_text(
            expected_text,
            exact=False,
        ).first
    ).to_be_visible(timeout=20000)

    route_name = (
        route.strip("/").replace("/", "_") or "root"
    )

    proof(f"route_{route_name}_passed")
