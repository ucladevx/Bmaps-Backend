# Scraping

## [happenings.ucla.edu](http://feeds.feedburner.com/uclahappenings-all-alldays)
- View page source
- Get all the event links
  - `<feedburner:origLink>http://happenings.ucla.edu/all/event/241951</feedburner:origLink></item>`
- Go through each link and get the appropriate event information from the site with Beautiful Soup
  - `python happenings.py`

## [https://www.studiousapp.com/ucla](https://www.studiousapp.com/ucla)
- View page source
- See categories/pages of categories
  - Get links for each place in each category
  - Different categories have different information, otherwise could go through each place
  - Some locations are part of other locations (e.g. 53 locations within Ackerman)
  - `python studiousapp.py`
- 29 different categories
  - See more information in `studiousCategoryLinks.txt`
