# """
# Configuration for the housing monitor.
# Edit this file to change sites, email, interval, etc.
# """

# CONFIG = {

#     # ── How often to check (minutes) ─────────────────────────────────────────
#     "interval_minutes": 30,

#     # ── Email settings ────────────────────────────────────────────────────────
#     "email": {
#         "sender":       "anastasisgoudras@gmail.com",   # Gmail used to SEND
#         "recipient":    "anastasisgoudras@gmail.com",   # Where to receive alerts
#         # Generate at: https://myaccount.google.com/apppasswords
#         # (needs 2-Step Verification enabled on your Google account)
#         "app_password": "kfxdjhpmhnngloic",
#     },

#     # ── Sites to monitor ──────────────────────────────────────────────────────
#     # Each entry must have:
#     #   name     – display name
#     #   scraper  – key matching a function in scrapers.py
#     #   url      – the listings page to scrape
#     #   enabled  – set False to pause without deleting
#     #
#     # Roommatch requires ROOM.nl login credentials.
#     # To add more sites: add an entry here + a scraper function in scrapers.py
#     "sites": [
#         {
#             "name":     "Roommatch Amsterdam",
#             "scraper":  "roommatch",
#             "url":      "https://www.roommatch.nl/en/offerings/to-rent",
#             "enabled":  True,
#             # Roommatch login (your ROOM.nl account)
#             "username": "anastasisgoudras@gmail.com",
#             "password": "Panatha13221!",
#             # Only keep listings containing these words (case-insensitive)
#             # Leave empty [] to get everything
#             "filter_city": ["amsterdam"],
#         },

#         # ── Template for adding more sites ────────────────────────────────────
#         # Uncomment and fill in to add a site:
#         #
#         # {
#         #     "name":    "Pararius Amsterdam",
#         #     "scraper": "generic",
#         #     "url":     "https://www.pararius.nl/huurwoningen/amsterdam",
#         #     "enabled": False,
#         #     # CSS selector that matches each listing card on the page
#         #     "listing_selector": "li.search-list__item--listing",
#         #     # Selectors relative to each listing card:
#         #     "title_selector":   "a.listing-search-item__link--title",
#         #     "price_selector":   "div.listing-search-item__price",
#         #     "link_selector":    "a.listing-search-item__link--title",
#         #     "link_prefix":      "https://www.pararius.nl",
#         # },
#     ],
# }


CONFIG = {
    "interval_minutes": 5,
    "email": {
        "sender":       "anastasisgoudras@gmail.com",
        "recipient":    "anastasisgoudras@gmail.com",
        "app_password": "kfxdjhpmhnngloic",
    },
    "sites": [
        {
            "name":        "Roofz Amsterdam",
            "scraper":     "roofz",
            "url":         "https://www.roofz.eu/huur/woningen",
            "enabled":     True,
            "filter_city": ["amsterdam"],
        },
        {
            "name":        "Roommatch Amsterdam",
            "scraper":     "roommatch",
            "url":         "https://www.roommatch.nl/en/offerings/to-rent",
            "enabled":     False,
            "username":    "anastasisgoudras@gmail.com",
            "password":    "Panatha13221!",
            "filter_city": ["amsterdam"],
        },
    ],
}
