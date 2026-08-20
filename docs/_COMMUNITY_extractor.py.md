---
type: community
cohesion: 0.10
members: 38
---

# extractor.py

**Cohesion:** 0.10 - loosely connected
**Members:** 38 nodes

## Members
- [[Constructs the reviews URL using the internal Place ID (CID). DEPRECATED…]] - rationale - gmaps_scraper_server/extractor.py
- [[Extracts and standardizes the primary phone number from HTML.]] - rationale - gmaps_scraper_server/extractor.py
- [[Extracts business hours from HTML.]] - rationale - gmaps_scraper_server/extractor.py
- [[Extracts latitude and longitude.]] - rationale - gmaps_scraper_server/extractor.py
- [[Extracts the Google Place ID.]] - rationale - gmaps_scraper_server/extractor.py
- [[Extracts the JSON string assigned to window.APP_INITIALIZATION_STATE from HTML…]] - rationale - gmaps_scraper_server/extractor.py
- [[Extracts the average star rating from HTML.]] - rationale - gmaps_scraper_server/extractor.py
- [[Extracts the complete address from HTML.]] - rationale - gmaps_scraper_server/extractor.py
- [[Extracts the internal Google Place ID (CID) for reviews URL.]] - rationale - gmaps_scraper_server/extractor.py
- [[Extracts the list of categoriestypes from HTML.]] - rationale - gmaps_scraper_server/extractor.py
- [[Extracts the main name of the place from HTML or metadata.]] - rationale - gmaps_scraper_server/extractor.py
- [[Extracts the main thumbnail image URL from HTML.]] - rationale - gmaps_scraper_server/extractor.py
- [[Extracts the primary website link from HTML.]] - rationale - gmaps_scraper_server/extractor.py
- [[Extracts the total number of reviews from HTML.]] - rationale - gmaps_scraper_server/extractor.py
- [[Google Maps Data Extractor This module extracts place data from Google Maps…]] - rationale - gmaps_scraper_server/extractor.py
- [[Helper function to extract data from HTML using regex.]] - rationale - gmaps_scraper_server/extractor.py
- [[High-level function to orchestrate extraction from HTML content. Updated to…]] - rationale - gmaps_scraper_server/extractor.py
- [[Parses the extracted JSON string to get basic metadata. Returns a dict with…]] - rationale - gmaps_scraper_server/extractor.py
- [[Remove HTML tags and clean up text.]] - rationale - gmaps_scraper_server/extractor.py
- [[clean_html_text()]] - code - gmaps_scraper_server/extractor.py
- [[extract_from_html()]] - code - gmaps_scraper_server/extractor.py
- [[extract_initial_json()]] - code - gmaps_scraper_server/extractor.py
- [[extract_place_data()]] - code - gmaps_scraper_server/extractor.py
- [[extractor.py]] - code - gmaps_scraper_server/extractor.py
- [[get_categories()]] - code - gmaps_scraper_server/extractor.py
- [[get_complete_address()]] - code - gmaps_scraper_server/extractor.py
- [[get_gps_coordinates()]] - code - gmaps_scraper_server/extractor.py
- [[get_hours()]] - code - gmaps_scraper_server/extractor.py
- [[get_main_name()]] - code - gmaps_scraper_server/extractor.py
- [[get_phone_number()]] - code - gmaps_scraper_server/extractor.py
- [[get_place_id()]] - code - gmaps_scraper_server/extractor.py
- [[get_place_id_cid()]] - code - gmaps_scraper_server/extractor.py
- [[get_rating()]] - code - gmaps_scraper_server/extractor.py
- [[get_reviews_count()]] - code - gmaps_scraper_server/extractor.py
- [[get_reviews_url()]] - code - gmaps_scraper_server/extractor.py
- [[get_thumbnail()]] - code - gmaps_scraper_server/extractor.py
- [[get_website()]] - code - gmaps_scraper_server/extractor.py
- [[parse_json_data()]] - code - gmaps_scraper_server/extractor.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/extractorpy
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_scrape_google_maps]]

## Top bridge nodes
- [[extractor.py]] - degree 20, connects to 1 community
- [[extract_place_data()]] - degree 17, connects to 1 community