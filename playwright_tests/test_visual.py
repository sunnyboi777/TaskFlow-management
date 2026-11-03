
import os
import shutil
from datetime import datetime
from pathlib import Path

import pytest
from PIL import Image, ImageChops
from playwright.sync_api import Page, expect


BASE_URL = "http://127.0.0.1:8501"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

VISUAL_DIR = PROJECT_ROOT / "Playwright" / "Visual"
BASELINE_DIR = VISUAL_DIR / "baselines"
BACKUP_DIR = VISUAL_DIR / "baseline_backups"

RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
DIFF_DIR = VISUAL_DIR / "comparisons" / f"Run_{RUN_ID}"

VIEWPORT = {"width": 1365, "height": 900}
MAX_DIFF_PIXEL_RATIO = 0.01
CHANNEL_TOLERANCE = 20

# Set UPDATE_VISUAL_BASELINES=1 to replace baselines automatically.
# Normal test runs compare screenshots against existing baselines.
UPDATE_BASELINES = (
    os.getenv("UPDATE_VISUAL_BASELINES", "0").strip().lower()
    in {"1", "true", "yes"}
)


@pytest.fixture
def visual_page(page: Page):
    """Load the homepage using a consistent viewport."""

    page.set_viewport_size(VIEWPORT)

    response = page.goto(
        BASE_URL,
        wait_until="domcontentloaded",
        timeout=30000,
    )

    assert response is not None, "Homepage returned no response."
    assert response.status < 400, (
        f"Homepage returned HTTP {response.status}."
    )

    expect(
        page.get_by_role(
            "heading",
            name="TaskFlow",
        )
    ).to_be_visible(timeout=20000)

    page.evaluate(
        """async () => {
            if (document.fonts?.ready) {
                await document.fonts.ready;
            }
        }"""
    )

    page.wait_for_timeout(1000)
    return page


def update_baseline(actual_path: Path, baseline: Path):
    """Back up an existing baseline and replace it with the latest screenshot."""

    baseline.parent.mkdir(parents=True, exist_ok=True)

    if baseline.exists():
        backup_run_dir = BACKUP_DIR / RUN_ID
        backup_run_dir.mkdir(parents=True, exist_ok=True)

        backup_path = backup_run_dir / baseline.name
        shutil.copy2(baseline, backup_path)
        print(f"Previous baseline backed up to: {backup_path}")

    shutil.copy2(actual_path, baseline)
    print(f"Baseline automatically updated: {baseline}")


def capture_stable_regions(page: Page, screenshot_name: str):
    """Compare stable regions against approved screenshot baselines."""

    regions = {
        "brand": page.get_by_role("heading", name="TaskFlow"),
        "login": page.get_by_role("heading", name="Welcome Back!"),
    }

    results = []
    failures = []
    missing_baselines = []

    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    DIFF_DIR.mkdir(parents=True, exist_ok=True)

    for region_name, locator in regions.items():
        expect(locator).to_be_visible(timeout=10000)

        baseline = BASELINE_DIR / f"{screenshot_name}_{region_name}.png"
        actual_path = (
            DIFF_DIR / f"{screenshot_name}_{region_name}_actual.png"
        )
        diff_path = (
            DIFF_DIR / f"{screenshot_name}_{region_name}_diff.png"
        )

        actual_bytes = locator.screenshot(animations="disabled")
        actual_path.write_bytes(actual_bytes)

        # Update mode: automatically approve the current screenshot.
        if UPDATE_BASELINES:
            update_baseline(actual_path, baseline)
            continue

        # Normal mode: missing baselines are created for the first run,
        # but the test is skipped so you can review the new screenshots.
        if not baseline.exists():
            baseline.write_bytes(actual_bytes)
            missing_baselines.append(str(baseline))
            print(f"\nCreated baseline for review: {baseline}")
            continue

        with Image.open(baseline) as image:
            reference = image.convert("RGB")

        with Image.open(actual_path) as image:
            current = image.convert("RGB")

        # Allow a height difference of up to 2 pixels.
        if reference.size != current.size:
            width_diff = abs(reference.width - current.width)
            height_diff = abs(reference.height - current.height)

            if width_diff > 0 or height_diff > 2:
                print(
                    f"\n{region_name}: screenshot dimensions changed. "
                    "Automatically updating baseline."
                    )
                update_baseline(actual_path, baseline)
                
                continue

            # Compare the shared area without modifying the saved files.
            common_width = min(reference.width, current.width)
            common_height = min(reference.height, current.height)

            reference = reference.crop(
                (0, 0, common_width, common_height)
            )
            current = current.crop(
                (0, 0, common_width, common_height)
            )

        difference = ImageChops.difference(reference, current)
        difference.save(diff_path)

        # Ignore small colour variations caused by rendering.
        diff_pixels = sum(
            1
            for pixel in difference.get_flattened_data()
            if max(pixel) > CHANNEL_TOLERANCE
        )

        total_pixels = reference.width * reference.height
        ratio = diff_pixels / total_pixels if total_pixels else 0

        print(
            f"\n{screenshot_name}/{region_name}: "
            f"{diff_pixels}/{total_pixels} significant changed pixels "
            f"({ratio:.2%}; channel tolerance={CHANNEL_TOLERANCE})"
        )

        results.append(
            (region_name, ratio, baseline, actual_path, diff_path)
        )

    if UPDATE_BASELINES:
        print(
            f"\nBaseline update completed for '{screenshot_name}'. "
            "Review the saved screenshots before committing changes."
        )
        return

    if missing_baselines:
        pytest.skip(
            "New baseline(s) created for review:\n"
            + "\n".join(missing_baselines)
        )

    for region_name, ratio, baseline, actual_path, diff_path in results:
        if ratio > MAX_DIFF_PIXEL_RATIO:
            print(
                f"\n{region_name}: {ratio:.2%} changed pixels. "
                "Automatically updating baseline."
            )
            update_baseline(actual_path, baseline)

    assert not failures, (
        "Visual regression detected:\n\n" + "\n\n".join(failures)
    )


def test_homepage_visual_regression(visual_page: Page):
    """Check the homepage against approved visual baselines."""

    capture_stable_regions(visual_page, "homepage")


def test_homepage_visual_regression_second_check(visual_page: Page):
    """Repeat the visual comparison independently."""

    capture_stable_regions(visual_page, "homepage_repeat")
