
from playwright.sync_api import Page, expect


BASE_URL = "http://127.0.0.1:8501"

TEST_EMAIL = "playwright@taskflow.test"
TEST_PASSWORD = "TaskFlow_Playwright_2026!"


def test_taskflow_homepage(page: Page):
    # Step 1: Open the TaskFlow application
    page.goto(BASE_URL)

    # Step 2: Verify that the login page appears
    login_email = page.get_by_role(
        "textbox", name="Email Address"
    ).first

    login_password = page.get_by_label("Password").first

    expect(login_email).to_be_visible()
    expect(login_password).to_be_visible()

    # Step 3: Log in using the dedicated Playwright test account
    login_email.fill(TEST_EMAIL)
    login_password.fill(TEST_PASSWORD)

    page.get_by_role("button", name="Login").click()

    # Step 4: Verify that the Dashboard loads after login
    expect(
        page.get_by_text("YOUR PRODUCTIVITY SPACE")
    ).to_be_visible(timeout=15000)

    # Step 5: Verify Dashboard navigation
    expect(page.get_by_text("📊 Dashboard")).to_be_visible()

    # Step 6: Verify Create Task navigation
    expect(
        page.get_by_text("➕ Create Task", exact=True)
    ).to_be_visible()

    # Step 7: Verify All Tasks navigation
    expect(
        page.get_by_text("📋 All Tasks", exact=True)
    ).to_be_visible()
