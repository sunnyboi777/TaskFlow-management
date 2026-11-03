from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import traceback

import pytest
import imageio_ffmpeg
from playwright.sync_api import sync_playwright


# ============================================================
# CONFIGURATION
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLAYWRIGHT_DIR = PROJECT_ROOT / "Playwright"

RECORDINGS_DIR = PLAYWRIGHT_DIR / "Recordings"
SCREENSHOTS_DIR = PLAYWRIGHT_DIR / "Screenshots"

PASSED_DIR = SCREENSHOTS_DIR / "Passed"
FAILED_DIR = SCREENSHOTS_DIR / "Failed"
FAILURES_DIR = SCREENSHOTS_DIR / "failures"

MAX_RUNS_TO_KEEP = 2
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")

CURRENT_RECORDINGS_DIR = RECORDINGS_DIR / f"Run_{RUN_ID}"
CURRENT_PASSED_DIR = PASSED_DIR / f"Run_{RUN_ID}"
CURRENT_FAILED_DIR = FAILED_DIR / f"Run_{RUN_ID}"
CURRENT_FAILURES_DIR = FAILURES_DIR / f"Run_{RUN_ID}"


# ============================================================
# RETENTION
# ============================================================

def cleanup_old_runs(directory, keep=MAX_RUNS_TO_KEEP):
    directory.mkdir(parents=True, exist_ok=True)

    run_folders = sorted(
        [
            folder
            for folder in directory.iterdir()
            if folder.is_dir() and folder.name.startswith("Run_")
        ],
        key=lambda folder: folder.name,
        reverse=True,
    )

    for folder in run_folders[keep:]:
        try:
            shutil.rmtree(folder)
            print(f"Removed old run: {folder}")
        except OSError as exc:
            print(f"Could not remove old run {folder}: {exc}")


def output_directories():
    return (
        RECORDINGS_DIR,
        PASSED_DIR,
        FAILED_DIR,
        FAILURES_DIR,
    )


def pytest_sessionstart(session):
    for directory in output_directories():
        directory.mkdir(parents=True, exist_ok=True)
        cleanup_old_runs(directory, keep=MAX_RUNS_TO_KEEP - 1)

    CURRENT_RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
    CURRENT_PASSED_DIR.mkdir(parents=True, exist_ok=True)
    CURRENT_FAILED_DIR.mkdir(parents=True, exist_ok=True)
    CURRENT_FAILURES_DIR.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("TASKFLOW PLAYWRIGHT TEST RUN")
    print("=" * 60)
    print(f"Project root: {PROJECT_ROOT}")
    print(f"MP4 recordings: {CURRENT_RECORDINGS_DIR}")
    print(f"Passed screenshots: {CURRENT_PASSED_DIR}")
    print(f"Failed screenshots: {CURRENT_FAILED_DIR}")
    print(f"Failure reports: {CURRENT_FAILURES_DIR}")
    print("=" * 60)


def pytest_sessionfinish(session, exitstatus):
    for directory in output_directories():
        cleanup_old_runs(directory, keep=MAX_RUNS_TO_KEEP)

    print("Retention cleanup completed.")


# ============================================================
# VIDEO CONVERSION
# ============================================================

def convert_to_mp4(webm_path, mp4_path):
    """
    Convert a finalized Playwright WebM video to H.264 MP4.
    The MP4 is accepted only if FFmpeg succeeds and produces
    a non-empty output file.
    """

    webm_path = Path(webm_path)
    mp4_path = Path(mp4_path)
    temporary_mp4 = mp4_path.with_name(
        f"{mp4_path.stem}.converting.mp4"
    )

    if not webm_path.exists() or webm_path.stat().st_size == 0:
        raise RuntimeError(f"WebM source is missing or empty: {webm_path}")

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel", "error",
        "-y",
        "-i", str(webm_path),
        "-map", "0:v:0",
        "-an",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-f", "mp4",
        str(temporary_mp4),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                "FFmpeg conversion failed:\n"
                + (result.stderr or "No FFmpeg error output.")
            )

        if (
            not temporary_mp4.exists()
            or temporary_mp4.stat().st_size == 0
        ):
            raise RuntimeError("FFmpeg created an empty MP4.")

        # Replace the final MP4 only after successful conversion.
        temporary_mp4.replace(mp4_path)

        print(f"MP4 saved: {mp4_path}")
        print(f"MP4 size: {mp4_path.stat().st_size:,} bytes")

    finally:
        if temporary_mp4.exists():
            try:
                temporary_mp4.unlink()
            except OSError:
                pass


# ============================================================
# BROWSER FIXTURE — RECORD, CONVERT, REMOVE WEBM
# ============================================================


@pytest.fixture(scope="session")
def playwright():
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser(playwright, pytestconfig):
    try:
        headed = pytestconfig.getoption("--headed")
    except ValueError:
        headed = False

    browser = playwright.chromium.launch(
        headless=not headed
    )
    try:
        yield browser
    finally:
        browser.close()


@pytest.fixture
def page(browser, request):
    # Playwright records to a temporary folder. Only MP4 files
    # are retained in the final Recordings run directory.
    temporary_recordings = CURRENT_RECORDINGS_DIR / "_temporary_webm"
    temporary_recordings.mkdir(parents=True, exist_ok=True)

    context = browser.new_context(
        record_video_dir=str(temporary_recordings),
        record_video_size={"width": 1280, "height": 720},
        viewport={"width": 1280, "height": 720},
    )

    test_page = context.new_page()
    video = test_page.video

    try:
        yield test_page

    finally:
        # Closing the context finalizes the video.
        try:
            context.close()
        except Exception as exc:
            print(f"Browser context closing error: {exc}")

        if video is None:
            print(f"No video object for test: {request.node.name}")
        else:
            try:
                # The video path is accessed only after context.close().
                webm_path = Path(video.path())

                if (
                    not webm_path.exists()
                    or webm_path.stat().st_size == 0
                ):
                    raise RuntimeError(
                        f"Recording is missing or empty: {webm_path}"
                    )

                safe_name = "".join(
                    char if char.isalnum() or char in "-_" else "_"
                    for char in request.node.name
                )

                mp4_path = CURRENT_RECORDINGS_DIR / f"{safe_name}.mp4"

                if mp4_path.exists():
                    mp4_path = (
                        CURRENT_RECORDINGS_DIR
                        / f"{safe_name}_{RUN_ID}.mp4"
                    )

                # Convert the completed recording.
                convert_to_mp4(webm_path, mp4_path)

                # Remove WebM only after successful MP4 conversion.
                if mp4_path.exists() and mp4_path.stat().st_size > 0:
                    webm_path.unlink(missing_ok=True)
                    print(f"Temporary WebM removed: {webm_path}")
                else:
                    raise RuntimeError(
                        f"MP4 verification failed: {mp4_path}"
                    )

            except Exception as exc:
                print(
                    f"VIDEO ERROR for {request.node.name}: {exc}"
                )

        # Remove the temporary folder if it is empty.
        try:
            if temporary_recordings.exists():
                for leftover in temporary_recordings.iterdir():
                    if leftover.is_file():
                        print(
                            "Unconverted temporary recording retained "
                            f"for diagnosis: {leftover}"
                        )

                if not any(temporary_recordings.iterdir()):
                    temporary_recordings.rmdir()

        except OSError as exc:
            print(f"Temporary recording cleanup warning: {exc}")


# ============================================================
# SCREENSHOT HELPER
# ============================================================

@pytest.fixture
def proof(page, request):
    screenshot_count = {"value": 0}

    safe_name = "".join(
        char if char.isalnum() or char in "-_" else "_"
        for char in request.node.name
    )

    def capture(message="screenshot", status="passed"):
        screenshot_count["value"] += 1

        safe_message = "".join(
            char if char.isalnum() or char in "-_" else "_"
            for char in str(message)
        )

        target_dir = (
            CURRENT_FAILED_DIR
            if str(status).lower() == "failed"
            else CURRENT_PASSED_DIR
        )

        target_dir.mkdir(parents=True, exist_ok=True)

        screenshot_path = target_dir / (
            f"{safe_name}_{screenshot_count['value']:03d}_"
            f"{safe_message}.png"
        )

        try:
            page.screenshot(
                path=str(screenshot_path),
                full_page=True,
            )
            print(f"Screenshot saved: {screenshot_path}")
        except Exception as exc:
            print(f"Screenshot capture failed: {exc}")

    def start_step(step_name):
        capture(f"{step_name}_started", "passed")

    capture.start_step = start_step
    return capture


# ============================================================
# TEST RESULT SCREENSHOTS AND FAILURE REPORTS
# ============================================================

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call":
        return

    safe_name = "".join(
        char if char.isalnum() or char in "-_" else "_"
        for char in item.name
    )

    page_obj = item.funcargs.get("page")

    # --------------------------------------------------------
    # PASSED TEST
    # --------------------------------------------------------

    if report.passed:
        if page_obj is not None:
            screenshot_path = CURRENT_PASSED_DIR / f"{safe_name}_PASSED.png"

            try:
                page_obj.screenshot(
                    path=str(screenshot_path),
                    full_page=True,
                )
                print(f"Passed screenshot saved: {screenshot_path}")
            except Exception as exc:
                print(f"Could not save passed screenshot: {exc}")

        return

    if not report.failed:
        return

    # --------------------------------------------------------
    # FAILED TEST
    # --------------------------------------------------------

    CURRENT_FAILED_DIR.mkdir(parents=True, exist_ok=True)
    CURRENT_FAILURES_DIR.mkdir(parents=True, exist_ok=True)

    if page_obj is not None:
        failed_screenshot = CURRENT_FAILED_DIR / f"{safe_name}_FAILED.png"
        report_screenshot = CURRENT_FAILURES_DIR / f"{safe_name}_FAILED.png"

        try:
            page_obj.screenshot(
                path=str(failed_screenshot),
                full_page=True,
            )
            shutil.copy2(failed_screenshot, report_screenshot)
            print(f"Failed screenshot saved: {failed_screenshot}")
        except Exception as exc:
            print(f"Could not save failed screenshot: {exc}")

    exception = call.excinfo.value if call.excinfo else None

    if exception is not None:
        error_type = type(exception).__name__
        error_message = str(exception)
        traceback_text = "".join(
            traceback.format_exception(
                type(exception),
                exception,
                exception.__traceback__,
            )
        )
    else:
        error_type = "TestFailure"
        error_message = str(report.longrepr)
        traceback_text = str(report.longrepr)

    failure_text = f"""
TASKFLOW PLAYWRIGHT FAILURE REPORT
==================================

Test:
{item.nodeid}

Failure time:
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Result:
FAILED

Error type:
{error_type}

Error message:
{error_message}

WHAT FAILED?
------------
Review the error message and traceback to identify the failing
operation, locator, assertion, or application behavior.

WHAT NEEDS TO BE CHANGED?
-------------------------
1. Locator error: verify the selector against the current UI.
2. Timeout: check application availability and wait conditions.
3. Assertion error: compare expected and actual results.
4. Navigation error: verify the route and server.
5. Backend/database error: check API responses and backend logs.
6. Other errors: use the traceback to locate the failing code.

These are diagnostic suggestions; confirm the root cause before
changing application code or test expectations.

FULL TRACEBACK
--------------
{traceback_text}

RELATED SCREENSHOT:
{safe_name}_FAILED.png
"""

    report_path = CURRENT_FAILURES_DIR / f"{safe_name}_FAILURE.txt"

    try:
        report_path.write_text(
            failure_text.strip() + "\n",
            encoding="utf-8",
        )
        print(f"Failure report saved: {report_path}")
    except Exception as exc:
        print(f"Could not save failure report: {exc}")