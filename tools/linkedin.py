import csv
import io
from typing import List
from playwright.async_api import async_playwright

def parse_csv(file_obj: io.StringIO) -> List[dict]:
    reader = csv.DictReader(file_obj)
    leads = []
    for row in reader:
        email = (row.get("email") or "").strip()
        if not email:
            continue
        leads.append({
            "email": email,
            "first_name": row.get("first_name", "").strip(),
            "last_name": row.get("last_name", "").strip(),
            "title": row.get("title", "").strip(),
            "company": row.get("company", "").strip(),
            "company_size": None,
            "linkedin_url": row.get("linkedin_url", "").strip() or None,
            "source": "csv",
        })
    return leads

async def linkedin_scrape(search_url: str, cookies: List[dict], max_results: int = 50) -> List[dict]:
    """
    Scrapes LinkedIn Sales Navigator search results.
    Requires valid LinkedIn session cookies (li_at, JSESSIONID).
    """
    leads = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context()
            await context.add_cookies(cookies)
            page = await context.new_page()
            await page.goto(search_url, wait_until="networkidle")

            cards = await page.query_selector_all("[data-view-name='search-results-lead-result']")
            for card in cards[:max_results]:
                try:
                    name_el = await card.query_selector(".artdeco-entity-lockup__title")
                    title_el = await card.query_selector(".artdeco-entity-lockup__subtitle")
                    company_el = await card.query_selector(".artdeco-entity-lockup__caption")
                    name = (await name_el.inner_text()).strip() if name_el else ""
                    parts = name.split(" ", 1) if name else []
                    leads.append({
                        "email": None,
                        "first_name": parts[0] if parts else "",
                        "last_name": parts[1] if len(parts) > 1 else "",
                        "title": (await title_el.inner_text()).strip() if title_el else "",
                        "company": (await company_el.inner_text()).strip() if company_el else "",
                        "company_size": None,
                        "linkedin_url": None,
                        "source": "linkedin",
                    })
                except Exception:
                    continue
        finally:
            await browser.close()
    return leads
