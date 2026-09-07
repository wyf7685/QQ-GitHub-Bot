"""
@Author         : yanyongyu
@Date           : 2022-09-14 14:22:39
@LastEditors    : yanyongyu
@LastEditTime   : 2024-05-26 17:09:44
@Description    : Playwright provider plugin
@GitHub         : https://github.com/yanyongyu
"""

__author__ = "yanyongyu"

from collections.abc import AsyncGenerator
from contextlib import contextmanager, asynccontextmanager

from nonebot import logger, get_driver, get_plugin_config
from playwright.async_api import (
    Page,
    Browser,
    Playwright,
    BrowserType,
    async_playwright,
)

from .config import Config

driver = get_driver()
playwright_config = get_plugin_config(Config)

_playwright: Playwright | None = None
_browser: Browser | None = None
"""Global playwright browser instance used to control multiple pages."""


@contextmanager
def _suppress_and_log():
    try:
        yield
    except Exception as e:
        logger.opt(exception=e).warning("An error occurred during playwright shutdown.")


@driver.on_startup
async def start_browser():
    global _playwright
    global _browser
    _playwright = await async_playwright().start()
    browser_name = playwright_config.playwright_browser_type
    try:
        browser_type: BrowserType = getattr(_playwright, browser_name)
        _browser = await browser_type.connect(
            str(playwright_config.playwright_ws_endpoint),
            timeout=playwright_config.playwright_connect_timeout * 1000,
        )
    except BaseException:
        await _playwright.stop()
        _playwright = None
        raise
    logger.info(f"Connected to remote Playwright {browser_name} browser.")


@driver.on_shutdown
async def shutdown_browser():
    global _playwright
    global _browser
    if _browser:
        with _suppress_and_log():
            await _browser.close()
        _browser = None
    if _playwright:
        with _suppress_and_log():
            await _playwright.stop()
        _playwright = None


def get_browser() -> Browser:
    """Get the global playwright browser instance."""
    if not _browser:
        raise RuntimeError("playwright is not initialized")
    return _browser


@asynccontextmanager
async def get_new_page(**kwargs) -> AsyncGenerator[Page, None]:
    """Context manager to get a new page.

    Args:
        kwargs: Keyword arguments to pass to `browser.new_context`.
    """
    ctx = await get_browser().new_context(**kwargs)
    page = await ctx.new_page()
    try:
        yield page
    finally:
        await page.close()
        await ctx.close()
