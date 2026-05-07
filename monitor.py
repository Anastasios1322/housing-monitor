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
import os
import random
import time
import json
import logging
import schedule
import urllib.request
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
    import urllib.request, json as _json
    property_id = listing.get("id", "")
    try:
        property_id = int(property_id)
    except (ValueError, TypeError):
        log.warning(f"  Roofz interest: invalid property_id '{property_id}' — skipping")
        return

    payload = _json.dumps({
        "candidate": {
            "email": "anastasisgoudras@gmail.com"
        },
        "subscription": {
            "firstname": "Anastasios",
            "lastname": "Goudras",
            "phone": "0645590016",
            "property_id": property_id,
            "comment": "Hi, My name is Anastasios, I'm 24 and originally from Greece, currently living in the Netherlands. I work at Picnic as a Manager, a role I was promoted to within three months. My fiancée is also Greek, has been in Amsterdam for four years, and works as a Project Manager. We're an engaged couple looking for a place we can genuinely settle into long-term. We're quiet, responsible tenants, no smoking, no pets. We can provide a landlord recommendation, employer's statement, payslips, and bank statements on request. I also have a guarantor ready with all supporting documents. As students, we each receive €1000 in student benefits, visible in our bank statements. We're very interested in this apartment and are ready to complete the full application quickly. If needed, we can also provide up to six months' rent in advance. Kind regards, Anastasios",
            "metadata": {
                "_ts": int(time.time() * 1000)
            }
        }
    }).encode()

    req = urllib.request.Request(
        "https://www.roofz.eu/api/ms/subscription/candidate",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Referer": listing.get("url", "https://www.roofz.eu/huur/woningen"),
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            log.info(f"  Roofz interest submitted for property {property_id} — HTTP {status}")
    except urllib.error.HTTPError as e:
        if e.code == 409:
            log.info(f"  Roofz interest already submitted for property {property_id} (409)")
        else:
            log.error(f"  Roofz interest failed for property {property_id}: HTTP {e.code}")
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
        next_interval = random.randint(4, 7)
        log.info(f"Next check in {next_interval} minutes")
        schedule.every(next_interval).minutes.do(lambda: (check_all_sites(), reschedule()))

    reschedule()

    while True:
        schedule.run_pending()
        time.sleep(30)
