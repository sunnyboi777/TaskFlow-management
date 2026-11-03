from datetime import datetime
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect


BASE_URL = "http://127.0.0.1:8501"

VIEWPORTS = [
    pytest.param(
        {"width": 1920, "height": 1080},
        "Desktop",
        id="desktop",
    ),
    pytest.param(
        {"width": 1024, "height": 768},
        "Tablet-Landscape",
        id="tablet-landscape",
    ),
    pytest.param(
        {"width": 768, "height": 1024},
        "Tablet-Portrait",
        id="tablet-portrait",
    ),
    pytest.param(
        {"width": 390, "height": 844},
        "Mobile",
        id="mobile",
    ),
    pytest.param(
        {"width": 320, "height": 700},
        "Small-Mobile",
        id="small-mobile",
    ),
]

# Create one timestamped screenshot folder for this test run.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")

SCREENSHOT_DIR = (
    PROJECT_ROOT
    / "Playwright"
    / "Screenshots"
    / "Responsive"
    / f"Run_{RUN_ID}"
)


def open_taskflow(page: Page, viewport: dict, device_name: str):
    """Open TaskFlow and verify that its actual content is visible."""

    page.set_viewport_size(viewport)
    response = page.goto(
        BASE_URL,
        wait_until="domcontentloaded",
        timeout=30000,
    )

    assert response is not None, (
        f"{device_name}: No HTTP response received."
    )
    assert response.status < 400, (
        f"{device_name}: HTTP error {response.status}."
    )

    # Streamlit can need additional time to render its frontend.
    expect(
        page.get_by_role(
            "heading",
            name="TaskFlow",
        )
    ).to_be_visible(timeout=20000)

    # Verify the main application content, not the body element.
    expect(page.locator("main")).to_be_visible()

    assert "Traceback (most recent call last)" not in page.locator(
        "main"
    ).inner_text(), (
        f"{device_name}: A Python traceback appeared in the main content."
    )


def save_screenshot(page: Page, device_name: str):
    """Save the viewport's screenshot in the project Playwright folder."""

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    screenshot_path = SCREENSHOT_DIR / f"{device_name}.png"

    page.screenshot(
        path=str(screenshot_path),
        full_page=True,
        animations="disabled",
    )

    print(f"Screenshot saved: {screenshot_path}")


@pytest.mark.parametrize("viewport,device_name", VIEWPORTS)
def test_homepage_responsive(page: Page, viewport, device_name):
    """Verify homepage content at desktop, tablet, and mobile sizes."""

    open_taskflow(page, viewport, device_name)

    dimensions = page.evaluate(
        """() => ({
            viewportWidth: document.documentElement.clientWidth,
            pageWidth: document.documentElement.scrollWidth,
            viewportHeight: document.documentElement.clientHeight
        })"""
    )

    print(f"{device_name}: {dimensions}")

    # Save evidence even if horizontal overflow is detected.
    save_screenshot(page, device_name)

    # Horizontal overflow is reported as diagnostic information.
    if dimensions["pageWidth"] > dimensions["viewportWidth"]:
        print(
            f"WARNING: Horizontal overflow detected on {device_name}: "
            f"{dimensions['pageWidth']}px content vs "
            f"{dimensions['viewportWidth']}px viewport."
        )


@pytest.mark.parametrize("viewport,device_name", VIEWPORTS)
def test_taskflow_content_responsive(page: Page, viewport, device_name):
    """Verify important TaskFlow content remains visible at each size."""

    open_taskflow(page, viewport, device_name)

    # Check key content shown on your TaskFlow homepage.
    expect(
        page.get_by_role(
            "heading",
            name="TaskFlow",
        )
    ).to_be_visible()

    expect(page.get_by_role("main")).to_contain_text(
        "Welcome Back!"
    )

    # At narrow widths, Streamlit may collapse the sidebar.
    # Check that the main content remains visible regardless.
    expect(page.locator("main")).to_be_visible()

    print(
        f"Responsive content check passed: {device_name} "
        f"({viewport['width']}x{viewport['height']})"
    )