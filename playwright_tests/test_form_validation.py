
import re
import uuid
from datetime import datetime
from pathlib import Path

import pytest
from playwright.sync_api import Page, Playwright, expect


BASE_URL = "http://127.0.0.1:8501"
API_URL = "http://127.0.0.1:8000"

TEST_EMAIL = "playwright@taskflow.test"
TEST_PASSWORD = "TaskFlow_Playwright_2026!"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")

SCREENSHOT_DIR = (
    PROJECT_ROOT
    / "Playwright"
    / "Screenshots"
    / "FormValidation"
    / f"Run_{RUN_ID}"
)


@pytest.fixture
def taskflow_page(page: Page):
    """Open TaskFlow and log in before testing protected forms."""

    page.set_viewport_size({"width": 1365, "height": 900})

    response = page.goto(
        BASE_URL,
        wait_until="domcontentloaded",
        timeout=30000,
    )

    assert response is not None
    assert response.status < 400

    email_input = page.get_by_role(
        "textbox",
        name="Email Address",
    ).first

    password_input = page.get_by_label("Password").first

    expect(email_input).to_be_visible(timeout=20000)
    expect(password_input).to_be_visible()

    email_input.fill(TEST_EMAIL)
    password_input.fill(TEST_PASSWORD)

    page.get_by_role("button", name="Login").click()

    expect(
        page.get_by_text("YOUR PRODUCTIVITY SPACE")
    ).to_be_visible(timeout=20000)

    return page


@pytest.fixture
def authenticated_api(playwright: Playwright):
    """Create an authenticated API context for the Playwright account."""

    context = playwright.request.new_context(
        base_url=API_URL,
    )

    try:
        login_response = context.post(
            "/auth/login",
            data={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
            },
        )

        assert login_response.status == 200, (
            f"Playwright API login failed: "
            f"{login_response.status} "
            f"{login_response.text()}"
        )

        token = login_response.json()["access_token"]

        headers = {
            "Authorization": f"Bearer {token}"
        }

        yield context, headers

    finally:
        context.dispose()


def save_screenshot(page: Page, name: str):
    """Save evidence for the current form validation test."""

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    screenshot_path = SCREENSHOT_DIR / f"{name}.png"

    page.screenshot(
        path=str(screenshot_path),
        full_page=True,
        animations="disabled",
    )

    print(f"Form validation screenshot saved: {screenshot_path}")


def open_create_task_form(page: Page):
    """Open Create Task using authenticated application navigation."""

    create_task_link = page.get_by_text(
        "➕ Create Task",
        exact=True,
    )

    expect(create_task_link).to_be_visible(timeout=15000)
    create_task_link.click()

    expect(
        page.get_by_text("✨ Create a New Task")
    ).to_be_visible(timeout=15000)

    print("Create Task page opened successfully.")


def get_title_input(page: Page):
    """Find the Task Title input."""

    title_input = page.locator(
        'input[data-testid="stTextInputField"]'
    ).first

    expect(title_input).to_be_visible(timeout=15000)
    expect(title_input).to_be_editable()

    return title_input


def get_description_input(page: Page):
    """Find the Description text area."""

    description = page.locator(
        '[data-testid="stTextArea"] textarea'
    ).first

    expect(description).to_be_visible(timeout=15000)
    expect(description).to_be_editable()

    return description


def click_create_button(page: Page):
    """Submit the Create Task form."""

    create_button = page.get_by_role(
        "button",
        name=re.compile(r"Create Task"),
    )

    expect(create_button).to_be_visible(timeout=10000)
    create_button.click()


def test_empty_task_title(taskflow_page: Page):
    """Verify that an empty title is rejected."""

    page = taskflow_page

    open_create_task_form(page)

    title_input = get_title_input(page)
    title_input.fill("")

    save_screenshot(page, "empty_title_before_submit")

    click_create_button(page)

    warning = page.get_by_text(
        "Please enter a task title.",
        exact=True,
    )

    expect(warning).to_be_visible(timeout=10000)

    save_screenshot(page, "empty_title_validation")

    print("Empty task title correctly rejected.")


def test_long_task_title(taskflow_page: Page):
    """Verify that a long title within the 200-character limit is accepted."""

    page = taskflow_page

    open_create_task_form(page)

    title_input = get_title_input(page)

    long_title = ("TaskFlow " * 20).strip()

    assert len(long_title) <= 200

    title_input.fill(long_title)

    expect(title_input).to_have_value(long_title)

    print(f"Long title accepted: {len(long_title)} characters.")

    save_screenshot(page, "long_task_title")


def test_special_characters_in_title(taskflow_page: Page):
    """Verify that special characters can be entered."""

    page = taskflow_page

    open_create_task_form(page)

    special_title = "Task !@#$%^&*()_+-=[]{}"

    title_input = get_title_input(page)
    title_input.fill(special_title)

    expect(title_input).to_have_value(special_title)

    save_screenshot(page, "special_characters_title")

    print("Special characters entered successfully.")


def test_description_input(taskflow_page: Page):
    """Verify that multiline descriptions can be entered."""

    page = taskflow_page

    open_create_task_form(page)

    description = get_description_input(page)

    multiline_text = (
        "First line of description\n"
        "Second line of description\n"
        "Third line of description"
    )

    description.fill(multiline_text)

    expect(description).to_have_value(multiline_text)

    save_screenshot(page, "multiline_description")

    print("Multiline description entered successfully.")


def test_valid_task_form_submission(
    taskflow_page: Page,
    authenticated_api,
):
    """Create a task through the UI and verify it through the authenticated API."""

    page = taskflow_page
    api_context, headers = authenticated_api

    unique_id = uuid.uuid4().hex[:10]

    title = f"Form Validation Test {unique_id}"
    description = "Testing valid task submission."

    created_task_id = None

    try:
        open_create_task_form(page)

        title_input = get_title_input(page)
        description_input = get_description_input(page)

        title_input.fill(title)
        description_input.fill(description)

        expect(title_input).to_have_value(title)
        expect(description_input).to_have_value(description)

        save_screenshot(page, "valid_task_before_submit")

        click_create_button(page)

        # Streamlit reruns immediately after a successful submission, so the
        # transient success message is not present in the final DOM.
        expect(
            page.get_by_text("✨ Create a New Task")
        ).to_be_visible(timeout=15000)

        # Retrieve tasks using the authenticated API.
        response = api_context.get(
            "/tasks",
            headers=headers,
        )

        assert response.status == 200, (
            f"Could not retrieve tasks: "
            f"{response.status} {response.text()}"
        )

        tasks = response.json()

        matching_tasks = [
            task for task in tasks
            if task.get("title") == title
        ]

        assert matching_tasks, (
            f"Created task was not found through the API: {title}"
        )

        created_task = matching_tasks[0]
        created_task_id = created_task["id"]

        assert created_task.get("description") == description

        print(f"Task created successfully. ID: {created_task_id}")

        save_screenshot(page, "valid_task_created")

    finally:
        # Delete only the uniquely named task owned by the test account.
        if created_task_id is not None:
            delete_response = api_context.delete(
                f"/tasks/{created_task_id}",
                headers=headers,
            )

            assert delete_response.status in (200, 204), (
                f"Test task cleanup failed: "
                f"{delete_response.status} "
                f"{delete_response.text()}"
            )

            verify_response = api_context.get(
                "/tasks",
                headers=headers,
            )

            assert verify_response.status == 200

            remaining_tasks = verify_response.json()

            assert not any(
                task.get("id") == created_task_id
                for task in remaining_tasks
            ), "Test task still exists after cleanup."

            print(
                f"Test task {created_task_id} "
                "deleted and cleanup verified."
            )
