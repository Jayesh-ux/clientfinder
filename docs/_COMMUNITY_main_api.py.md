---
type: community
cohesion: 0.31
members: 9
---

# main_api.py

**Cohesion:** 0.31 - loosely connected
**Members:** 9 nodes

## Members
- [[Triggers the Google Maps scraping process for the given query via GET request.]] - rationale - gmaps_scraper_server/main_api.py
- [[Triggers the Google Maps scraping process for the given query.]] - rationale - gmaps_scraper_server/main_api.py
- [[get]] - code
- [[main_api.py]] - code - gmaps_scraper_server/main_api.py
- [[post]] - code
- [[read_root()]] - code - gmaps_scraper_server/main_api.py
- [[run_scrape()]] - code - gmaps_scraper_server/main_api.py
- [[run_scrape_get()]] - code - gmaps_scraper_server/main_api.py
- [[scrape_google_maps()_1]] - code - gmaps_scraper_server/main_api.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/main_apipy
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_scrape_google_maps]]

## Top bridge nodes
- [[main_api.py]] - degree 6, connects to 1 community