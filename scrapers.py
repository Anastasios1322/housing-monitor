"""
Scrapers for each housing site.
"""

import logging
import requests
import random
import time

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
                street  = item.get("street", "")
                housenr = item.get("houseNumber", "")
                city    = ""
                if isinstance(item.get("city"), dict):
                    city = item["city"].get("name", "")
                elif isinstance(item.get("municipality"), dict):
                    city = item["municipality"].get("name", "")

                title = f"{street} {housenr}".strip()
                if city:
                    title += f", {city}"
                if not title:
                    title = "Room listing"

                prijs = (item.get("totalePrijs") or item.get("huurprijs") or
                         item.get("prijs") or item.get("price") or "")
                price = f"€{prijs}" if prijs else ""

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


def scrape_roofz(site_cfg: dict) -> list:
    time.sleep(random.uniform(1, 2))
    api_url     = "https://www.roofz.eu/api/ms/listing/properties"
    filter_city = [c.lower() for c in site_cfg.get("filter_city", [])]
    listings    = []

    try:
        log.info("  Calling Roofz API ...")
        params = {
            "perPage": 50,
            "page": 1,
            "sort": "stage",
            "filter[stage]": "available",
            "filter[import_type]": "RentResident",
        }
        resp = SESSION.get(api_url, params=params, timeout=20)
        resp.raise_for_status()
        data  = resp.json()
        items = data.get("data", [])
        log.info(f"  API returned {len(items)} item(s)")

        for item in items:
            try:
                title    = item.get("title", "")
                slug     = item.get("slug", "")
                url      = f"https://www.roofz.eu/huur/woningen/{slug}" if slug else site_cfg["url"]
                address  = item.get("address", {})
                city     = address.get("location", "")
                street   = address.get("street", "")
                housenr  = address.get("house_number", "")
                handover = item.get("handover", {})
                price    = handover.get("price_formatted", "")
                text_to_check = (title + " " + city).lower()
                if filter_city and not any(c in text_to_check for c in filter_city):
                    continue
                listings.append({
                    "id": str(item.get("id", url)),
                    "title": title or f"{street} {housenr}".strip(),
                    "price": price,
                    "location": city,
                    "url": url,
                })
            except Exception as e:
                log.debug(f"  Item parse error: {e}")

    except Exception as e:
        log.error(f"  Roofz API call failed: {e}")

    return listings

def scrape_plaza(site_cfg: dict) -> list:
    time.sleep(random.uniform(1, 2))
    api_url     = "https://plaza.newnewnew.space/portal/object/frontend/getreagerendata/format/json"
    filter_city = [c.lower() for c in site_cfg.get("filter_city", [])]
    listings    = []
 
    try:
        log.info("  Calling Plaza API ...")
        headers = {
            "Accept":  "application/json",
            "Referer": "https://plaza.newnewnew.space/aanbod/wonen",
            "Origin":  "https://plaza.newnewnew.space",
        }
        resp = SESSION.get(api_url, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()
 
        # Log top-level keys on first run so we can verify the shape
        if isinstance(data, dict):
            log.info(f"  Plaza response keys: {list(data.keys())}")
 
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            for key in ["data", "items", "results", "objects", "woningen", "aanbod"]:
                if key in data and isinstance(data[key], list):
                    items = data[key]
                    log.info(f"  Found listings under key '{key}'")
                    break
            if not items:
                candidates = [v for v in data.values() if isinstance(v, list)]
                if candidates:
                    items = candidates[0]
 
        log.info(f"  API returned {len(items)} item(s)")
 
        for item in items:
            try:
                if not isinstance(item, dict):
                    continue
 
                item_id = str(
                    item.get("id") or item.get("Id") or
                    item.get("objectId") or item.get("object_id") or ""
                )
 
                street  = (
                    item.get("street") or item.get("straat") or
                    item.get("adres") or item.get("address") or
                    item.get("title") or item.get("naam") or ""
                )
                housenr = str(item.get("houseNumber") or item.get("huisnummer") or "")
                title   = f"{street} {housenr}".strip() if housenr else street
                if not title:
                    title = "Plaza listing"
 
                city_raw = (
                    item.get("city") or item.get("stad") or
                    item.get("plaats") or item.get("gemeente") or ""
                )
                city = (
                    city_raw.get("name") or city_raw.get("naam") or ""
                    if isinstance(city_raw, dict) else str(city_raw)
                )
 
                # Filter by city the same way Roofz does
                text_to_check = (title + " " + city).lower()
                if filter_city and not any(c in text_to_check for c in filter_city):
                    continue
 
                price_raw = (
                    item.get("price") or item.get("prijs") or
                    item.get("huurprijs") or item.get("rent") or
                    item.get("totalRent") or ""
                )
                price = (
                    f"€{price_raw}"
                    if price_raw and not str(price_raw).startswith("€")
                    else str(price_raw)
                )
 
                slug = item.get("slug") or item.get("url") or item.get("path") or ""
                if slug and slug.startswith("http"):
                    url = slug
                elif slug:
                    url = f"https://plaza.newnewnew.space/aanbod/wonen/{slug.lstrip('/')}"
                elif item_id:
                    url = f"https://plaza.newnewnew.space/aanbod/wonen/{item_id}"
                else:
                    url = site_cfg["url"]
 
                listings.append({
                    "id":       item_id or url,
                    "title":    title,
                    "price":    price,
                    "location": city,
                    "url":      url,
                })
 
            except Exception as e:
                log.debug(f"  Item parse error: {e}")
 
    except Exception as e:
        log.error(f"  Plaza API call failed: {e}")
 
    return listings


SCRAPERS = {
    "roommatch": scrape_roommatch,
    "generic":   scrape_generic,
    "roofz":     scrape_roofz,
    "plaza":     scrape_plaza,   # ← add this
}
