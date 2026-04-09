"""
Single-run version of the monitor for GitHub Actions.
Checks all sites once, sends email if new listings found.
State is stored in seen_listings.json which is committed back to the repo.
"""

import json
import smtplib
import logging
import os
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from scrapers import SCRAPERS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

STATE_FILE = Path("seen_listings.json")

def load_seen():
    if STATE_FILE.exists():
        try:
            return set(json.loads(STATE_FILE.read_text()))
        except Exception:
            return set()
    return set()

def save_seen(seen):
    STATE_FILE.write_text(json.dumps(list(seen)))

def send_email(new_listings, cfg):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🏠 {len(new_listings)} new Amsterdam listing(s)!"
    msg["From"]    = cfg["sender"]
    msg["To"]      = cfg["recipient"]

    plain = f"New listings — {datetime.now().strftime('%d %b %Y %H:%M')}\n\n"
    for l in new_listings:
        plain += f"• {l['title']}\n  {l.get('price','')}  {l.get('location','')}\n  {l['url']}\n\n"

    cards = ""
    for l in new_listings:
        cards += f"""
        <tr>
          <td style="padding:16px 0; border-bottom:1px solid #eee;">
            <a href="{l['url']}" style="font-size:15px; font-weight:600; color:#111; text-decoration:none;">{l['title']}</a><br>
            <span style="font-size:13px; color:#555; margin-top:4px; display:block;">
              {l.get('price','—')}
              {"&nbsp;·&nbsp;" + l['location'] if l.get('location') else ""}
              {"&nbsp;·&nbsp;" + l['source'] if l.get('source') else ""}
            </span>
            <a href="{l['url']}" style="display:inline-block; margin-top:10px; padding:6px 14px;
               background:#111; color:#fff; border-radius:6px; font-size:12px; text-decoration:none;">
               View listing →
            </a>
          </td>
        </tr>"""

    html = f"""
    <html><body style="font-family:sans-serif; max-width:600px; margin:auto; padding:20px;">
      <h2 style="font-size:20px;">{len(new_listings)} new listing{"s" if len(new_listings)>1 else ""}</h2>
      <p style="color:#888; font-size:13px;">{datetime.now().strftime("%d %b %Y at %H:%M")}</p>
      <table style="width:100%; border-collapse:collapse;">{cards}</table>
    </body></html>"""

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(cfg["sender"], cfg["app_password"])
        server.sendmail(cfg["sender"], cfg["recipient"], msg.as_string())
    log.info(f"Email sent — {len(new_listings)} listing(s)")

def main():
    # Read config from environment variables (set as GitHub Secrets)
    cfg = {
        "sender":       os.environ["EMAIL_SENDER"],
        "recipient":    os.environ["EMAIL_RECIPIENT"],
        "app_password": os.environ["EMAIL_APP_PASSWORD"],
    }

    sites = [
        {
            "name":        "Roommatch Amsterdam",
            "scraper":     "roommatch",
            "url":         "https://www.roommatch.nl/en/offerings/to-rent",
            "filter_city": ["amsterdam"],
        }
    ]

    seen = load_seen()
    new_listings = []

    for site_cfg in sites:
        scraper_fn = SCRAPERS.get(site_cfg["scraper"])
        if not scraper_fn:
            continue
        log.info(f"Checking {site_cfg['name']} ...")
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
            log.error(f"  Error: {e}")

    save_seen(seen)

    if new_listings:
        log.info(f"Sending email for {len(new_listings)} new listing(s)")
        try:
            send_email(new_listings, cfg)
        except Exception as e:
            log.error(f"Email failed: {e}")
    else:
        log.info("No new listings.")

if __name__ == "__main__":
    main()
