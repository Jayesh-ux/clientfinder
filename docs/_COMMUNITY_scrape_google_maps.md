---
type: community
cohesion: 0.20
members: 16
---

# scrape_google_maps

**Cohesion:** 0.20 - loosely connected
**Members:** 16 nodes

## Members
- [[Creates a Google Maps search URL.]] - rationale - gmaps_scraper_server/scraper.py
- [[Returns random delay for anti-detection]] - rationale - gmaps_scraper_server/scraper.py
- [[Scrapes Google Maps for places based on a query. Args query (str) The search…]] - rationale - gmaps_scraper_server/scraper.py
- [[Scrapes details for a single place using a new page from the browser context.…]] - rationale - gmaps_scraper_server/scraper.py
- [[__init__.py]] - code - gmaps_scraper_server/__init__.py
- [[create_search_url()]] - code - gmaps_scraper_server/scraper.py
- [[main()]] - code - scratch/scrape_leads.py
- [[main()_1]] - code - scratch/search_clients.py
- [[main()_2]] - code - scratch/search_more_clients.py
- [[random_delay()]] - code - gmaps_scraper_server/scraper.py
- [[scrape_google_maps()]] - code - gmaps_scraper_server/scraper.py
- [[scrape_leads.py]] - code - scratch/scrape_leads.py
- [[scrape_place_details()]] - code - gmaps_scraper_server/scraper.py
- [[scraper.py]] - code - gmaps_scraper_server/scraper.py
- [[search_clients.py]] - code - scratch/search_clients.py
- [[search_more_clients.py]] - code - scratch/search_more_clients.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/scrape_google_maps
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_extractor.py]]
- 2 edges to [[_COMMUNITY_main_api.py]]

## Top bridge nodes
- [[scraper.py]] - degree 10, connects to 2 communities
- [[scrape_google_maps()]] - degree 11, connects to 1 community
- [[scrape_place_details()]] - degree 5, connects to 1 community