from scrapers import scrape_plaza

cfg = {
    "url": "https://plaza.newnewnew.space/aanbod/wonen",
    "filter_city": ["amsterdam"],
}

listings = scrape_plaza(cfg)
print(f"Found {len(listings)} listings")
for l in listings:
    print(l)
