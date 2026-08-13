import playwright
from playwright.sync_api import Page, expect, sync_playwright

SITE = "https://staging.holdenweb.com"

def register_user(page: Page, suffix: str, site: str) -> None:
    page.goto(f"{site}/register")
    page.get_by_role("textbox", name="Email Address").click()
    page.get_by_role("textbox", name="Email Address").fill(f"steve+{suffix}@holdenweb.com")
    page.get_by_role("textbox", name="Email Address").press("Tab")
    page.get_by_role("textbox", name="Password", exact=True).fill("password")
    page.get_by_role("textbox", name="Password", exact=True).press("Tab")
    page.get_by_role("textbox", name="Retype Password").fill("password")
    page.get_by_role("button", name="Register").click()

import sys

if __name__ == '__main__':
    if not 1 < len(sys.argv) <= 3:
       sys.exit(f"{sys.argv[0]} [site_url] suffix")
    if len(sys.argv) == 3:
       SITE = sys.argv[1]
       del sys.argv[1]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        register_user(page, suffix=sys.argv[1], site=SITE)