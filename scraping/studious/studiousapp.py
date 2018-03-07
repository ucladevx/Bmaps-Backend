import urllib2
from bs4 import BeautifulSoup
import re
import json

debugMode = False

# Go through all pages of locations and get the url to each individual location
# Separated by category
def getLocationsFromPages():
  locations = []
  counter = 0

  data = json.load(open('studiousCategoryLinks.json'))
  for category in data['locationCategories']:
    if debugMode: print category['type']
    if debugMode: print category['pages']
    if debugMode: print category['count']
    locations.append({'type': category['type']})
    locations[counter]['locationURLs'] = []

    for pageURL in category['pages']:
      if debugMode: print "PAGE URL: " + pageURL.strip()

      # Query website to get html of the page
      page = urllib2.urlopen(pageURL.strip())

      # Parse HTML using BeautifulSoup
      soup = BeautifulSoup(page, 'html.parser')

      # Get the location urls
      location_urls = []
      urls = soup.find_all('a', attrs={'class': 'thumbnail'}, href=True)
      for url in urls:
        if debugMode: print "href: " + url['href']
        locations[counter]['locationURLs'].append(url['href'])

    counter += 1
  with open('studiousPages.json', 'w') as outfile:
    print json.dump(locations, outfile, indent=4)

# Go through each place and get information for the location
getLocationsFromPages()

