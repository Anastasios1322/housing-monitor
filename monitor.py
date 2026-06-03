#!/usr/bin/env python3
"""
Housing Monitor — checks listing sites every N minutes and sends Telegram notifications.
"""
import os
import random
import time
import json
import logging
import schedule
import urllib.request
import requests
from pathlib import Path
from datetime import datetime
from config import CONFIG
from scrapers import SCRAPERS

os.environ["TZ"] = "Europe/Amsterdam"
time.tzset()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("monitor.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

STATE_FILE = Path("seen_listings.json")

def load_seen() -> set:
    if STATE_FILE.exists():
        try:
            return set(json.loads(STATE_FILE.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()

def save_seen(seen: set):
    STATE_FILE.write_text(json.dumps(list(seen)), encoding="utf-8")

def send_notification(new_listings: list):
    token    = "8614985590:AAH_ilJn8jCSIWy2KStnE9cgCmStWa5Ed_0"
    chat_ids = ["8032104558", "5177744933"]
    for l in new_listings:
        msg  = f"🏠 New listing!\n{l['title']}\n{l.get('price', '')}\n{l['url']}"
        data_base = {"text": msg}
        for chat_id in chat_ids:
            data = json.dumps({**data_base, "chat_id": chat_id}).encode()
            req  = urllib.request.Request(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data=data,
                headers={"Content-Type": "application/json"}
            )
            try:
                urllib.request.urlopen(req)
            except Exception as e:
                log.error(f"Telegram failed for {chat_id}: {e}")
    log.info(f"Telegram sent — {len(new_listings)} listing(s)")

def submit_roofz_interest(listing: dict):
    property_id = listing.get("id", "")
    try:
        property_id = int(property_id)
    except (ValueError, TypeError):
        log.warning(f"  Roofz interest: invalid property_id '{property_id}' — skipping")
        return

    # Match the browser exactly: roofz.eu (no www) as Referer
    referer = listing.get("url", "https://roofz.eu/huur/woningen").replace("www.roofz.eu", "roofz.eu")

    payload = {
        "candidate": {"email": "anastasisgoudras@gmail.com"},
        "subscription": {
            "firstname": "Anastasios",
            "lastname": "Goudras",
            "phone": "0645590016",
            "property_id": property_id,
            "message": """Hi,
My name is Anastasios, I'm 24 years old, originally from Greece, and currently living in the Netherlands. I work at Picnic as a Manager, a position I was promoted to within three months.
I am looking for a place where I can settle long-term. I am engaged, and my fiancée, who is also Greek, has been living and working in Amsterdam for several years as a Project Manager. Stability and a comfortable home are therefore very important to me.
I am a quiet and responsible tenant, non-smoker, with no pets. I can provide payslips, employer statements, bank statements, a landlord recommendation, and guarantor documents upon request. I also receive student benefits, visible in my bank statements.
I am very interested in the apartment and ready to complete the application quickly. If needed, I can also pay several months of rent in advance.
Kind regards,
Anastasios""",
            "metadata": {"_ts": int(time.time() * 1000)},
        },
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://roofz.eu",
        "Referer": referer,
        "Accept-Language": "en,el;q=0.9,nl;q=0.8",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/148.0.0.0 Safari/537.36"),
    }

    try:
        resp = requests.post(
            "https://roofz.eu/api/ms/subscription/candidate",
            json=payload, headers=headers, timeout=15,
        )
        body = resp.text[:120]
        if resp.status_code == 409:
            log.info(f"  Roofz interest already submitted for property {property_id} (409)")
        elif resp.status_code == 200:
            log.info(f"  Roofz interest submitted for property {property_id} — HTTP 200 | resp: {body}")
        else:
            log.error(f"  Roofz interest FAILED for property {property_id}: HTTP {resp.status_code} | resp: {body}")
    except Exception as e:
        log.error(f"  Roofz interest failed for property {property_id}: {e}")

def check_all_sites():
    hour = datetime.now().hour
    if hour < 7 or hour >= 23:
        log.info("Night time — skipping check")
        return

    log.info("── Checking all sites ──────────────────────────")
    seen         = load_seen()
    new_listings = []

    for site_cfg in CONFIG["sites"]:
        if not site_cfg.get("enabled", True):
            continue
        scraper_name = site_cfg["scraper"]
        scraper_fn   = SCRAPERS.get(scraper_name)
        if not scraper_fn:
            log.warning(f"No scraper found for '{scraper_name}' — skipping")
            continue
        log.info(f"Checking {site_cfg['name']} …")
        try:
            listings = scraper_fn(site_cfg)
            log.info(f"  Found {len(listings)} total listing(s)")
            for listing in listings:
                uid = listing.get("id") or listing["url"]
                if uid not in seen:
                    seen.add(uid)
                    listing["source"] = site_cfg["name"]
                    new_listings.append(listing)
                    log.info(f"  NEW: {listing['title']}")
                    if scraper_name == "roofz":
                        submit_roofz_interest(listing)
        except Exception as e:
            log.error(f"  Error scraping {site_cfg['name']}: {e}")

    save_seen(seen)

    if new_listings:
        log.info(f"Sending notification for {len(new_listings)} new listing(s)")
        send_notification(new_listings)
    else:
        log.info("No new listings found.")

if __name__ == "__main__":
    log.info("Housing monitor started")
    log.info(f"Sites    : {[s['name'] for s in CONFIG['sites'] if s.get('enabled', True)]}")
    log.info("")

    check_all_sites()

    def reschedule():
        schedule.clear()
        next_interval = 1
        log.info(f"Next check in {next_interval} minutes")
        schedule.every(next_interval).minutes.do(lambda: (check_all_sites(), reschedule()))

    reschedule()

    while True:
        schedule.run_pending()
        time.sleep(30)
