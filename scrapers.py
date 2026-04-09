"""
Scrapers for each housing site.
"""

import logging
import requests

log = logging.getLogger(__name__)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://www.roommatch.nl",
    "Referer": "https://www.roommatch.nl/",
})


def scrape_roommatch(site_cfg: dict) -> list:
    api_url = "https://roommatching-aanbodapi.zig365.nl/api/v1/actueel-aanbod"
    params  = {"limit": 30, "locale": "en_GB", "page": 0,
                "sort": "%2BreactionData.aangepasteTotaleHuurprijs"}
    payload = {
        "filters": {"$and": [{"$and": [{"regio.id": {"$eq": "3"}}]}]},
        "hidden-filters": {}
    }

    listings = []
    try:
        log.info("  Calling Roommatch API ...")
        resp = SESSION.post(api_url, params=params, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        # Find the list in response
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            for key in ["items", "data", "results", "aanbod"]:
                if key in data and isinstance(data[key], list):
                    items = data[key]
                    break

        log.info(f"  API returned {len(items)} item(s)")

        for item in items:
            try:
                # Build title from address
                street   = item.get("street", "")
                housenr  = item.get("houseNumber", "")
                city     = ""
                if isinstance(item.get("city"), dict):
                    city = item["city"].get("name", "")
                elif isinstance(item.get("municipality"), dict):
                    city = item["municipality"].get("name", "")

                title = f"{street} {housenr}".strip()
                if city:
                    title += f", {city}"
                if not title:
                    title = "Room listing"

                # Price
                prijs = (item.get("totalePrijs") or item.get("huurprijs") or
                         item.get("prijs") or item.get("price") or "")
                price = f"€{prijs}" if prijs else ""

                # ID and URL
                item_id = str(item.get("Id") or item.get("id") or item.get("advertentieId") or "")
                url = f"https://www.roommatch.nl/en/offerings/to-rent/{item_id}" if item_id else site_cfg["url"]

                listings.append({
                    "id": item_id or url,
                    "title": title,
                    "price": price,
                    "location": city,
                    "url": url,
                })

            except Exception as e:
                log.debug(f"  Item parse error: {e}")

    except Exception as e:
        log.error(f"  Roommatch API call failed: {e}")

    return listings


def scrape_generic(site_cfg: dict) -> list:
    from bs4 import BeautifulSoup

    url         = site_cfg["url"]
    listing_sel = site_cfg.get("listing_selector", "article")
    title_sel   = site_cfg.get("title_selector", "h2")
    price_sel   = site_cfg.get("price_selector", ".price")
    link_sel    = site_cfg.get("link_selector", "a")
    link_prefix = site_cfg.get("link_prefix", "")
    filter_city = [c.lower() for c in site_cfg.get("filter_city", [])]

    try:
        resp = SESSION.get(url, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        log.error(f"  Request failed for {url}: {e}")
        return []

    soup     = BeautifulSoup(resp.text, "html.parser")
    cards    = soup.select(listing_sel)
    listings = []

    for card in cards:
        try:
            title_el = card.select_one(title_sel)
            title    = title_el.get_text(strip=True) if title_el else "Listing"
            link_el  = card.select_one(link_sel)
            href     = link_el["href"] if link_el and link_el.get("href") else url
            full_url = link_prefix + href if href.startswith("/") else href
            price_el = card.select_one(price_sel)
            price    = price_el.get_text(strip=True) if price_el else ""
            text_to_check = (title + " " + full_url).lower()
            if filter_city and not any(c in text_to_check for c in filter_city):
                continue
            listings.append({"id": full_url, "title": title, "price": price, "location": "", "url": full_url})
        except Exception as e:
            log.debug(f"  Card parse error: {e}")

    return listings


SCRAPERS = {
    "roommatch": scrape_roommatch,
    "generic":   scrape_generic,
}
