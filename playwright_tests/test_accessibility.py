
import pytest
from pathlib import Path
from datetime import datetime
from playwright.sync_api import Page, expect


BASE_URL = "http://127.0.0.1:8501"

TEST_EMAIL = "playwright@taskflow.test"
TEST_PASSWORD = "TaskFlow_Playwright_2026!"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")

SCREENSHOT_DIR = (
    PROJECT_ROOT
    / "Playwright"
    / "Screenshots"
    / "Accessibility"
    / f"Run_{RUN_ID}"
)


@pytest.fixture
def taskflow_page(page: Page):
    """Open TaskFlow and authenticate before accessibility checks."""

    page.set_viewport_size({"width": 1365, "height": 900})

    response = page.goto(
        BASE_URL,
        wait_until="domcontentloaded",
        timeout=30000,
    )

    assert response is not None, "TaskFlow did not return a response."
    assert response.status < 400, (
        f"TaskFlow returned HTTP {response.status}."
    )

    # Verify that the login screen is displayed.
    login_email = page.get_by_role(
        "textbox",
        name="Email Address",
    ).first

    login_password = page.get_by_label("Password").first

    expect(login_email).to_be_visible(timeout=20000)
    expect(login_password).to_be_visible()

    # Log in using the dedicated Playwright account.
    login_email.fill(TEST_EMAIL)
    login_password.fill(TEST_PASSWORD)

    page.get_by_role("button", name="Login").click()

    # Verify that the authenticated Dashboard is displayed.
    expect(
        page.get_by_text("YOUR PRODUCTIVITY SPACE")
    ).to_be_visible(timeout=20000)

    return page


def save_evidence(page: Page, name: str):
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    path = SCREENSHOT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)

    print(f"Accessibility screenshot saved: {path}")


def test_keyboard_navigation(taskflow_page):
    """Verify that Tab moves focus from one interactive element to another."""

    page = taskflow_page

    # Start from a known, visible keyboard-focusable control. This avoids
    # relying on whatever element happens to receive focus after login and
    # Streamlit's page rerender.
    logout_button = page.get_by_role("button", name="Logout")
    expect(logout_button).to_be_visible()

    logout_button.focus()
    expect(logout_button).to_be_focused()

    page.keyboard.press("Tab")

    focus_moved = page.evaluate(
        """(previousElement) => {
            const active = document.activeElement;
            return Boolean(
                active &&
                active !== document.body &&
                active !== document.documentElement &&
                active !== previousElement
            );
        }""",
        logout_button.element_handle(),
    )

    assert focus_moved, (
        "Pressing Tab did not move focus away from the Logout button."
    )

    save_evidence(page, "keyboard_navigation")


def test_main_content_has_accessible_landmark(taskflow_page):
    """Check that the page exposes a main landmark."""

    page = taskflow_page

    main_landmark = page.get_by_role("main")
    expect(main_landmark).to_be_visible()

    save_evidence(page, "main_landmark")


def test_page_has_title(taskflow_page):
    """Verify that the browser page has a non-empty title."""

    page = taskflow_page

    title = page.title()

    assert title.strip(), "The page title is empty."

    print(f"Page title: {title}")

    save_evidence(page, "page_title")


def test_heading_structure(taskflow_page):
    """Check that the main TaskFlow heading is accessible."""

    page = taskflow_page

    heading = page.get_by_text(
        "YOUR PRODUCTIVITY SPACE"
    )

    expect(heading).to_be_visible()

    save_evidence(page, "heading_structure")


def test_interactive_elements_have_accessible_names(taskflow_page):
    """Check visible buttons and inputs for accessible names."""

    page = taskflow_page

    unnamed_elements = page.evaluate(
        """() => {
            const elements = [
                ...document.querySelectorAll(
                    'button, input, select, textarea, [role="button"]'
                )
            ];

            return elements
                .filter(el => {
                    if (el.getAttribute('aria-hidden') === 'true') {
                        return false;
                    }

                    const style = window.getComputedStyle(el);

                    if (
                        style.display === 'none' ||
                        style.visibility === 'hidden'
                    ) {
                        return false;
                    }

                    const ariaLabel = (
                        el.getAttribute('aria-label') || ''
                    ).trim();

                    const labelledBy = (
                        el.getAttribute('aria-labelledby') || ''
                    ).trim();

                    const title = (
                        el.getAttribute('title') || ''
                    ).trim();

                    const text = (
                        el.innerText ||
                        el.value ||
                        ''
                    ).trim();

                    const placeholder = (
                        el.getAttribute('placeholder') || ''
                    ).trim();

                    const hasLabel = el.labels && el.labels.length > 0;

                    return !(
                        ariaLabel ||
                        labelledBy ||
                        title ||
                        text ||
                        placeholder ||
                        hasLabel
                    );
                })
                .map(el => ({
                    tag: el.tagName,
                    type: el.getAttribute('type'),
                    role: el.getAttribute('role'),
                    id: el.id
                }));
        }"""
    )

    if unnamed_elements:
        print("Elements that may lack accessible names:")

        for element in unnamed_elements:
            print(element)

    assert not unnamed_elements, (
        f"Found {len(unnamed_elements)} visible interactive elements "
        "that may lack accessible names. Review the terminal output."
    )

    save_evidence(page, "accessible_names")
