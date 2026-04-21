# #!/usr/bin/env python3
# """
# Housing Monitor — checks listing sites every N minutes and emails you new results.
# Supports Roommatch (login required) and easily extensible to other sites.
# """

# import time
# import json
# import smtplib
# import logging
# import schedule
# import importlib
# from pathlib import Path
# from datetime import datetime
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart

# from config import CONFIG
# from scrapers import SCRAPERS

# # ── Logging ──────────────────────────────────────────────────────────────────
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s  %(levelname)-8s %(message)s",
#     datefmt="%H:%M:%S",
#     handlers=[
#         logging.StreamHandler(),
#         logging.FileHandler("monitor.log", encoding="utf-8"),
#     ],
# )
# log = logging.getLogger(__name__)

# # ── State persistence ─────────────────────────────────────────────────────────
# STATE_FILE = Path("seen_listings.json")

# def load_seen() -> set:
#     if STATE_FILE.exists():
#         try:
#             return set(json.loads(STATE_FILE.read_text(encoding="utf-8")))
#         except Exception:
#             return set()
#     return set()

# def save_seen(seen: set):
#     STATE_FILE.write_text(json.dumps(list(seen)), encoding="utf-8")

# # ── Email ─────────────────────────────────────────────────────────────────────
# def send_email(new_listings: list):
#     cfg = CONFIG["email"]
#     msg = MIMEMultipart("alternative")
#     msg["Subject"] = f"🏠 {len(new_listings)} new listing(s) found!"
#     msg["From"]    = cfg["sender"]
#     msg["To"]      = cfg["recipient"]

#     # Plain text fallback
#     plain_lines = [f"New housing listings — {datetime.now().strftime('%d %b %Y %H:%M')}\n"]
#     for l in new_listings:
#         plain_lines.append(f"• {l['title']}")
#         plain_lines.append(f"  {l.get('price', 'Price N/A')}  |  {l.get('location', '')}")
#         plain_lines.append(f"  {l['url']}\n")
#     plain = "\n".join(plain_lines)

#     # HTML version
#     cards = ""
#     for l in new_listings:
#         cards += f"""
#         <tr>
#           <td style="padding:16px 0; border-bottom:1px solid #eee;">
#             <a href="{l['url']}" style="font-size:15px; font-weight:600;
#                color:#111; text-decoration:none;">{l['title']}</a><br>
#             <span style="font-size:13px; color:#555; margin-top:4px; display:block;">
#               {l.get('price','—')}
#               {"&nbsp;&nbsp;·&nbsp;&nbsp;" + l['location'] if l.get('location') else ""}
#               {"&nbsp;&nbsp;·&nbsp;&nbsp;" + l['source'] if l.get('source') else ""}
#             </span>
#             <a href="{l['url']}" style="display:inline-block; margin-top:10px;
#                padding:6px 14px; background:#111; color:#fff; border-radius:6px;
#                font-size:12px; text-decoration:none;">View listing →</a>
#           </td>
#         </tr>"""

#     html = f"""
#     <html><body style="font-family:sans-serif; max-width:600px; margin:auto; padding:20px;">
#       <h2 style="font-size:20px; font-weight:600; margin-bottom:4px;">
#         {len(new_listings)} new listing{"s" if len(new_listings)>1 else ""} found
#       </h2>
#       <p style="color:#888; font-size:13px; margin-top:0;">
#         {datetime.now().strftime("%d %b %Y at %H:%M")}
#       </p>
#       <table style="width:100%; border-collapse:collapse;">{cards}</table>
#       <p style="font-size:11px; color:#aaa; margin-top:24px;">
#         Sent by your housing monitor · runs every {CONFIG['interval_minutes']} minutes
#       </p>
#     </body></html>"""

#     msg.attach(MIMEText(plain, "plain"))
#     msg.attach(MIMEText(html,  "html"))

#     try:
#         with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
#             server.login(cfg["sender"], cfg["app_password"])
#             server.sendmail(cfg["sender"], cfg["recipient"], msg.as_string())
#         log.info(f"Email sent — {len(new_listings)} new listing(s)")
#     except Exception as e:
#         log.error(f"Failed to send email: {e}")


    

# # ── Core check loop ───────────────────────────────────────────────────────────
# def check_all_sites():
#     log.info("── Checking all sites ──────────────────────────")
#     seen = load_seen()
#     new_listings = []

#     for site_cfg in CONFIG["sites"]:
#         if not site_cfg.get("enabled", True):
#             continue

#         scraper_name = site_cfg["scraper"]
#         scraper_fn   = SCRAPERS.get(scraper_name)

#         if not scraper_fn:
#             log.warning(f"No scraper found for '{scraper_name}' — skipping")
#             continue

#         log.info(f"Checking {site_cfg['name']} …")
#         try:
#             listings = scraper_fn(site_cfg)
#             log.info(f"  Found {len(listings)} total listing(s)")

#             for listing in listings:
#                 uid = listing.get("id") or listing["url"]
#                 if uid not in seen:
#                     seen.add(uid)
#                     listing["source"] = site_cfg["name"]
#                     new_listings.append(listing)
#                     log.info(f"  NEW: {listing['title']}")

#         except Exception as e:
#             log.error(f"  Error scraping {site_cfg['name']}: {e}")

#     save_seen(seen)

#     if new_listings:
#         log.info(f"Sending email for {len(new_listings)} new listing(s)")
#         send_email(new_listings)
#     else:
#         log.info("No new listings found.")

#     log.info(f"Next check in {CONFIG['interval_minutes']} minutes\n")

# # ── Entry point ───────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     log.info("Housing monitor started")
#     log.info(f"Sites    : {[s['name'] for s in CONFIG['sites'] if s.get('enabled', True)]}")
#     log.info(f"Interval : every {CONFIG['interval_minutes']} minutes")
#     log.info(f"Notify   : {CONFIG['email']['recipient']}")
#     log.info("")

#     # Run immediately on start, then on schedule
#     check_all_sites()
#     schedule.every(CONFIG["interval_minutes"]).minutes.do(check_all_sites)

#     while True:
#         schedule.run_pending()
#         time.sleep(30)


#!/usr/bin/env python3
"""
Housing Monitor — checks listing sites every N minutes and sends Telegram notifications.
"""

import time
import json
import logging
import schedule
import urllib.request
from pathlib import Path
from datetime import datetime

from config import CONFIG
from scrapers import SCRAPERS

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
    token   = "8614985590:AAH_ilJn8jCSIWy2KStnE9cgCmStWa5Ed_0"
    chat_id = "8032104558"

    for l in new_listings:
        msg  = f"🏠 New listing!\n{l['title']}\n{l.get('price', '')}\n{l['url']}"
        data = json.dumps({"chat_id": chat_id, "text": msg}).encode()
        req  = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        try:
            urllib.request.urlopen(req)
        except Exception as e:
            log.error(f"Telegram failed: {e}")

    log.info(f"Telegram sent — {len(new_listings)} listing(s)")

def check_all_sites():
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

        except Exception as e:
            log.error(f"  Error scraping {site_cfg['name']}: {e}")

    save_seen(seen)

    if new_listings:
        log.info(f"Sending notification for {len(new_listings)} new listing(s)")
        send_notification(new_listings)
    else:
        log.info("No new listings found.")

    log.info(f"Next check in {CONFIG['interval_minutes']} minutes\n")

if __name__ == "__main__":
    log.info("Housing monitor started")
    log.info(f"Sites    : {[s['name'] for s in CONFIG['sites'] if s.get('enabled', True)]}")
    log.info(f"Interval : every {CONFIG['interval_minutes']} minutes")
    log.info("")

    check_all_sites()
    schedule.every(CONFIG["interval_minutes"]).minutes.do(check_all_sites)

    while True:
        schedule.run_pending()
        time.sleep(30)
