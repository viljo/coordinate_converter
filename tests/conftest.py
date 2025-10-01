import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
import pytest_asyncio

APP_PORT = int(os.getenv("FLET_SERVER_PORT", "54873"))
APP_URL = f"http://127.0.0.1:{APP_PORT}"
SCREENSHOT_DIR = Path(__file__).resolve().parent.parent / "artifacts"
SCREENSHOT_DIR.mkdir(exist_ok=True)


def _start_app():
    env = os.environ.copy()
    env.setdefault("FLET_FORCE_WEBVIEW", "0")
    env.setdefault("FLET_FORCE_WEB_SERVER", "1")
    env.setdefault("FLET_SERVER_PORT", str(APP_PORT))
    env.setdefault("FLET_SERVER_IP", "127.0.0.1")
    env.setdefault("FLET_FORCE_WEB_RENDERER", "html")

    cmd = [
        sys.executable,
        "-m",
        "app.web_runner",
        "--host",
        "127.0.0.1",
        "--port",
        str(APP_PORT),
    ]

    return subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


@pytest.fixture(scope="session")
def running_app() -> str:
    proc = _start_app()
    try:
        time.sleep(5)
        yield APP_URL
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest_asyncio.fixture()
async def playwright_page():
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        try:
            yield page
        finally:
            await page.close()
            await context.close()
            await browser.close()
