import urllib2
from bs4 import BeautifulSoup
import re
import json

debugMode = True

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

# Go through all the location urls we gathered and get all available location information
# TODO: recursively go through associated/inside locations?
# TODO: keep track of done places
def getLocationInfo():
  data = []
  counter = 0

  locationTypes = json.load(open('studiousPages.json'))
  for type in locationTypes:
    for url in type['locationURLs']:
      if debugMode: print "URL: " + url.strip() + '\n'
      data.append({'url': url.strip()})

      # Query website to get html of the page
      page = urllib2.urlopen(url.strip())

      # Parse HTML using BeautifulSoup
      soup = BeautifulSoup(page, 'html.parser')

      # Get the location information
      # Location name
      location_name = soup.find('h1')
      location_name_re = re.sub(type['type'],'', location_name.text, flags=re.IGNORECASE)
      if debugMode: print "NAME: " + location_name_re.strip() + '\n'
      data[counter]['location_name'] = location_name_re.strip()

      # Latitude/Longitude
      location_coordinates = soup.find('div', attrs={'data-map-marker': True})
      print "LATITUDE: " + str(location_coordinates['data-map-marker-latitude']) + '\n'
      print "LONGITUDE: " + str(location_coordinates['data-map-marker-longitude']) + '\n'

      # Description
      location_description = location_coordinates.parent.find('div', attrs={'class': 'panel-body'})
      if location_description:
        print "DESCRIPTION: " + location_description.text.strip() + '\n'

      # Links
      location_links = soup.find('h3', text='Links')
      print "LINKS: "
      for content in location_links.parent.contents:
        if content.name == 'ul':
          for aTag in content.find_all('a', href=True):
            print aTag['href']
      print '\n'

      # Entrances
      location_entrances = soup.find_all('img')
      if debugMode: print "ENTRANCES: "
      for entrance in location_entrances:
        if debugMode: print entrance['alt'].strip()
        data[counter]['location_entrances'] = entrance['alt'].strip()
      print '\n'

      # What's Inside
      location_insides_pages = soup.find('ul', attrs={'class': 'pagination'})
      inside_pages = location_insides_pages.find_all('a', href=True)
      for page in inside_pages:
        print page['href']
        # TODO remove duplicate and add page=1

      # NO: Levels

      # NO: Hours

      quit()

# Go through each category and get all the individual location urls
# getLocationsFromPages()

# Go individual locations and get location information
getLocationInfo()
