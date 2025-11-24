import re
# from __future__ import annotations
import argparse
import time
import json
from termcolor import colored
from typing import List, Optional
from requests_html import HTMLSession
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import undetected_chromedriver as uc
import time
from typing import Dict, Optional, Tuple
from selenium.common.exceptions import (
    WebDriverException,
    NoSuchWindowException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Optional selenium imports guarded at runtime
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC    

    _HAS_SELENIUM = True
except Exception:
    _HAS_SELENIUM = False

"""Small web scraping helper with two fetch modes:
- "requests" (fast, headless, use when JS not required)
- "selenium" (falls back to webdriver; use when JS rendering needed)

Provides:
- fetch(url, mode='requests') -> HTML string
- extract_text(html, selector=None) -> list of texts
- extract_links(html, selector=None) -> list of hrefs
- simple CLI for quick testing

Install:
    pip install requests beautifulsoup4 lxml
    # for selenium mode (optional):
    pip install selenium webdriver-manager

Usage examples (zsh):
    python src/tools/scrapper.py --mode requests --url https://example.com
    python src/tools/scrapper.py --mode selenium --url https://example.com
"""


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
}


def fetch_requests(url: str, timeout: int = 45, headers: Optional[dict] = None) -> str:
    print(f"[INFO] Fetching page with requests... {url}")
    headers = {**DEFAULT_HEADERS, **(headers or {})}
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.text


from selenium.webdriver.chrome.service import Service


def fetch_uc_selenium(
    url: str,
    headless: bool = True,
    wait_timeout: int = 30,
    manual_solve: bool = False,
    max_retries: int = 2,
) -> Tuple[str, Dict[str, str]]:
    """
    Fetch rendered HTML using undetected_chromedriver with Cloudflare Turnstile handling.

    Returns:
        (html, cookies) where cookies is a dict suitable for requests (name->value).

    Args:
        url: target URL
        headless: run headless or not. Use headless=False if you plan to manually solve CAPTCHAs.
        wait_timeout: seconds to wait for normal page load or for manual solve completion
        manual_solve: if True and a Turnstile challenge is detected, the function
                      will wait up to wait_timeout seconds for you to solve it in the visible browser.
        max_retries: number of times to restart driver on recoverable errors.
    Raises:
        RuntimeError on unrecoverable errors (or if Turnstile requires solving and manual_solve is False).
    """
    attempt = 0
    last_exc = None

    while attempt <= max_retries:
        attempt += 1
        driver = None
        try:
            opts = uc.ChromeOptions()
            if headless:
                opts.add_argument("--headless=new")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--window-size=1920,1080")
            # Avoid some automation flags
            opts.add_argument("--disable-blink-features=AutomationControlled")

            driver = uc.Chrome(options=opts)
            driver.set_page_load_timeout(max(60, wait_timeout))

            # navigate
            driver.get(url)

            # wait for basic page presence
            try:
                WebDriverWait(driver, min(10, wait_timeout)).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                # If even body isn't present, continue to capture whatever we have
                pass

            # brief settle + scroll to encourage lazy load
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            html = driver.page_source

            # Detect Cloudflare Turnstile / challenge indicators in the DOM
            # Look for common elements / text used by CF challenge pages
            is_turnstile = False
            try:
                # common hidden input used by Turnstile widgets
                if driver.find_elements(By.CSS_SELECTOR, "input[id^='cf-chl-widget']"):
                    is_turnstile = True
                # Turnstile script reference
                elif (
                    "challenges.cloudflare.com/turnstile" in html
                    or "cdn-cgi/challenge-platform" in html
                ):
                    is_turnstile = True
                # visible "Verify you are human" text
                elif driver.find_elements(
                    By.XPATH,
                    "//*[contains(text(), 'Verify you are human') or contains(text(), 'Just a moment') or contains(text(), 'needs to review the security of your connection')]",
                ):
                    is_turnstile = True
            except Exception:
                # Non-fatal detection error, continue with html
                is_turnstile = is_turnstile or False

            if is_turnstile:
                # If headless + manual_solve==False -> we can't proceed
                if not manual_solve:
                    # Clean up and raise guidance
                    cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
                    driver.quit()
                    raise RuntimeError(
                        "Cloudflare Turnstile detected. Set manual_solve=True and headless=False to solve it interactively,"
                        " or use a Turnstile solver service (not implemented here). "
                        f"Current partial HTML length: {len(html)}. Cookies saved: {len(cookies)}"
                    )

                # Manual solve path: ensure browser is visible and wait for cf token or success marker
                if headless:
                    # we require visible browser for manual solve
                    driver.quit()
                    raise RuntimeError(
                        "To manually solve Turnstile, set headless=False and manual_solve=True"
                    )

                print(
                    "[INFO] Cloudflare Turnstile detected. Please solve the challenge in the opened browser window."
                )
                # Wait until the Turnstile hidden input is populated or success text appears
                try:
                    # wait for the input value to become non-empty
                    solved = WebDriverWait(driver, wait_timeout).until(
                        lambda d: any(
                            (elem.get_attribute("value") or "").strip()
                            for elem in d.find_elements(
                                By.CSS_SELECTOR,
                                "input[id^='cf-chl-widget'], input[name='cf-turnstile-response']",
                            )
                        )
                        or bool(
                            d.find_elements(
                                By.XPATH,
                                "//*[contains(text(), 'Verification successful') or contains(text(),'Waiting for') or contains(text(),'challenge succeeded')]",
                            )
                        )
                    )
                except TimeoutException:
                    # timed out waiting for manual solve
                    html_after_wait = driver.page_source
                    cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
                    driver.quit()
                    raise RuntimeError(
                        f"Timed out ({wait_timeout}s) waiting for manual Turnstile solve. Partial HTML length: {len(html_after_wait)}. Cookies saved: {len(cookies)}"
                    )

                # If solved, let the page settle and re-fetch content
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                html = driver.page_source
                cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
                driver.quit()
                return html, cookies

            # No Turnstile detected — return page content and cookies
            cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
            driver.quit()
            return html, cookies

        except NoSuchWindowException as e:
            last_exc = e
            # driver window closed unexpectedly; attempt a retry
            try:
                if driver:
                    driver.quit()
            except Exception:
                pass
            print(
                f"[WARN] NoSuchWindowException on attempt {attempt}: {e}. Retrying..."
            )
            time.sleep(1 + attempt)
            continue

        except WebDriverException as e:
            last_exc = e
            try:
                if driver:
                    driver.quit()
            except Exception:
                pass
            # Some WebDriver errors are transient; retry a few times
            print(f"[WARN] WebDriverException on attempt {attempt}: {e}")
            time.sleep(1 + attempt)
            continue

        except Exception as e:
            # Unrecoverable — clean up and re-raise with helpful message
            try:
                if driver:
                    driver.quit()
            except Exception:
                pass
            raise

    # if we exhausted retries
    raise RuntimeError(
        f"Failed to fetch page after {max_retries} retries. Last error: {last_exc}"
    )


def fetch_requests_html(url: str, timeout: int = 30) -> str:
    """Fetch HTML using Playwright, fully rendered, no selector needed."""
    print("[INFO] Fetching page with Playwright (auto-wait)...")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Load and wait for full network idle (no new requests for 500ms)
        page.goto(url, timeout=timeout * 1000, wait_until="networkidle")

        # Optional: scroll to trigger lazy-load content
        page.evaluate(
            """() => {
            window.scrollBy(0, document.body.scrollHeight);
        }"""
        )
        page.wait_for_timeout(2000)  # wait 2s extra

        html = page.content()
        browser.close()
        return html


def extract_links(soup: BeautifulSoup, selector: Optional[str] = None) -> List[str]:
    if selector:
        elems = soup.select(selector)
    else:
        elems = soup.find_all("a")
    out = []
    for e in elems:
        href = e.get("href")
        if href:
            out.append(href)
    return out


def extract_text(soup: BeautifulSoup, selector: Optional[str] = None) -> List[str]:
    if selector:
        elems = soup.select(selector)
    else:
        elems = [soup.body] if soup.body else [soup]
    out = []
    for e in elems:
        text = e.get_text(separator=" ", strip=True)
        if text:
            out.append(text)
    return out


def extract_site_info(soup: BeautifulSoup, base_url: Optional[str] = None) -> dict:
    """Extract Website URL (href) and Industry/Niche from the known page structure."""
    site_href = None
    dom_span = soup.select_one("span.domain-name")
    if dom_span:
        a = dom_span.find_parent("a")
        if a and a.get("href"):
            site_href = a["href"].strip()
            if base_url:
                site_href = urljoin(base_url, site_href)

    industry = None
    for li in soup.select("ul.insIcons > li"):
        title = li.select_one("span.titleText")
        if title and title.get_text(strip=True).lower().startswith("industry"):
            h2 = li.select_one("h2")
            if h2:
                industry = h2.get_text(strip=True)
            break

    return {"website": site_href, "industry": industry}


def extract_total_percent(soup: BeautifulSoup) -> Optional[str]:
    """Extract the total percent value from .totalRankDiv."""
    percent = None
    div = soup.select_one("div.totalRankDiv p.totalPercent strong")
    if div:
        percent = div.get_text(strip=True)
    return percent


def extract_wot_details(soup: BeautifulSoup) -> dict:
    """Extract details from the .WOTDetailsList section as key-value pairs."""
    details = {}
    ul = soup.select_one("ul.WOTDetailsList")
    if ul:
        for li in ul.find_all("li", recursive=False):
            ps = li.find_all("p")
            if len(ps) >= 2:
                key = ps[0].get_text(strip=True)
                value = ps[1].get_text(strip=True)
                details[key] = value
    return details


def extract_about_text(soup: BeautifulSoup) -> Optional[str]:
    """Extract the about text from .about-text section."""
    div = soup.select_one("div.about-text p")
    if div:
        return div.get_text(strip=True)
    return None


def extract_panels(soup: BeautifulSoup) -> dict:
    """Extract all panels (active or inactive) as a dict: heading -> {key: value, ...}."""
    panels = {}

    all_panels = soup.select("div.panel, div.panel.active")
    print(
        f"DEBUG: Extracting panels... {len(all_panels)} panels found (active + inactive)."
    )

    for panel in all_panels:
        heading_tag = panel.select_one(".panel-heading h4")
        heading = heading_tag.get_text(strip=True) if heading_tag else None
        body = {}

        # Find all <p> tags in content-wrapper
        for p in panel.select(".panel-body .content-wrapper p"):
            strong = p.find("strong")
            if strong:
                key = strong.get_text(strip=True)
                br = strong.find_next("br")
                if br and br.next_sibling:
                    value = br.next_sibling.strip()
                else:
                    value = (
                        strong.next_sibling.strip()
                        if strong.next_sibling
                        else p.get_text(strip=True).replace(key, "", 1).strip()
                    )
                body[key] = value
            else:
                value = p.get_text(strip=True)
                if value:
                    body.setdefault("values", []).append(value)

        # Handle panels with no <p> tags
        if not body:
            content = panel.select_one(".panel-body .content-wrapper")
            if content:
                text = content.get_text(" ", strip=True)
                if text:
                    body["values"] = [text]

        if heading:
            panels[heading] = body

    return panels

import re


def url_to_review_slug(domain: str) -> str:

    # Replace dots with hyphens
    slug = domain.replace(".", "-")

    # Add "-review"
    return f"https://www.scam-detector.com/validator/{slug}-review"


def scrape_url_info(url: str, mode: str = "requests") -> dict:
    """
    Description: Main scrapper function to fetch and extract data from a domain review page.

    Input: Domain name as provided by the user (e.g slidejewels.com, amazon.com)

    Output: A dictionary containing information about the domain
    """

    print(colored(50 * "=", "green"))

    start_time = time.time()
    print(colored(f"[TIME] starting time for scrape_url_info: {start_time}", "blue"))

    print(f"[INFO] Converted URL to review slug: {url}")

    url = url_to_review_slug(url)

    if mode == "requests":
        html = fetch_requests(url)
    elif mode == "selenium":
        html, _ = fetch_uc_selenium(
            url, headless=False, manual_solve=True, wait_timeout=180
        )
    elif mode == "requests_html":
        html = fetch_requests_html(url)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    print(f"[DEBUG] HTML length: {len(html)}")
    print(f"[DEBUG] Raw 'panel active' count: {html.count('panel')}")

    soup = BeautifulSoup(html, "lxml")

    all_info = {}
    all_info.update(extract_site_info(soup, base_url=url))
    all_info["total_percent"] = extract_total_percent(soup)
    all_info["wot_details"] = extract_wot_details(soup)
    all_info["about_text"] = extract_about_text(soup)
    all_info.update(extract_panels(soup))

    print(colored(f"[TIME] Time taken for scrape_url_info: {time.time() - start_time} seconds", "blue"))


    return all_info


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument(
        "--mode",
        choices=["requests", "selenium", "requests_html"],
        default="requests",
    )
    p.add_argument("--selector", help="CSS selector to extract text or links")
    args = p.parse_args()


    args.url = url_to_review_slug(args.url)

    if args.mode == "requests":
        html = fetch_requests(args.url)
    elif args.mode == "selenium":
        html = fetch_uc_selenium(
            args.url, headless=False, manual_solve=True, wait_timeout=180
        )
    elif args.mode == "requests_html":
        html = fetch_requests_html(args.url)

    print(f"[DEBUG] HTML length: {len(html)}")
    print(f"[DEBUG] Raw 'panel active' count: {html.count('panel')}")
    # print(html[:30000])

    soup = BeautifulSoup(html, "lxml")

    all_info = {}
    all_info.update(extract_site_info(soup, base_url=args.url))
    all_info["total_percent"] = extract_total_percent(soup)
    all_info["wot_details"] = extract_wot_details(soup)
    all_info["about_text"] = extract_about_text(soup)
    all_info.update(extract_panels(soup))

    print(json.dumps(all_info, indent=2))
