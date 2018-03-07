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

# From the inside_pages urls figure out which locations are linked
def getLinkedLocations():
  data = []
  counter = 0

  locations = json.load(open('studiousLocations.json'))
  for location in locations:
    location['inside_locations'] = []
    for page in location['inside_pages']:
      if debugMode: print "URL: " + page.strip() + '\n'

      # Query website to get html of the page
      pageHTML = urllib2.urlopen(page.strip())

      # Parse HTML using BeautifulSoup
      soup = BeautifulSoup(pageHTML, 'html.parser')

      # Read all links for locations inside the location
      location_insides_pages = soup.find('ul', attrs={'class': 'list-group'})
      if location_insides_pages:
        inside_urls = location_insides_pages.find_all('a', attrs={'class': 'list-group-item'}, href=True)
        if inside_urls:
          for url in inside_urls:
            if debugMode: print "href: " + url['href']
            location['inside_locations'].append(url['href'])
      if debugMode: print '\n'
    data.append(location)

    print "~~~~~ " + str(counter) + " ~~~~~"
    counter += 1

  with open('studiousInsideLocations.json', 'w') as outfile:
    print json.dump(data, outfile, indent=4)


# Go through all the location urls we gathered and get all available location information
# TODO: keep track of done places, aka don't have duplicates as we do now
def getLocationInfo():
  data = []
  counter = 0

  locationTypes = json.load(open('studiousPages.json'))
  for type in locationTypes:
    for url in type['locationURLs']:
      if debugMode: print "URL: " + url.strip() + '\n'
      data.append({'url': url.strip()})
      data[counter]['type'] = type['type']

      # Query website to get html of the page
      page = urllib2.urlopen(url.strip())

      # Parse HTML using BeautifulSoup
      soup = BeautifulSoup(page, 'html.parser')

      # Get the location information
      # Location name
      # TODO: strip all types (can have multi-types)
      location_name = soup.find('h1')
      if location_name:
        location_name_re = re.sub(type['type'],'', location_name.text, flags=re.IGNORECASE)
        if debugMode: print "NAME: " + location_name_re.strip() + '\n'
        data[counter]['location_name'] = location_name_re.strip()
      else:
        data[counter]['location_name'] = ""

      # Latitude/Longitude
      location_coordinates = soup.find('div', attrs={'data-map-marker': True})
      if location_coordinates:
        if debugMode: print "LATITUDE: " + str(location_coordinates['data-map-marker-latitude']) + '\n'
        if debugMode: print "LONGITUDE: " + str(location_coordinates['data-map-marker-longitude']) + '\n'
        data[counter]['latitude'] = location_coordinates['data-map-marker-latitude']
        data[counter]['longitude'] = location_coordinates['data-map-marker-longitude']
      else:
        data[counter]['latitude'] = 420
        data[counter]['longitude'] = 420
        data[counter]['description'] = ""

      # Description
      if location_coordinates:
        location_description = location_coordinates.parent.find('div', attrs={'class': 'panel-body'})
        if location_description:
          if debugMode: print "DESCRIPTION: " + location_description.text.strip() + '\n'
          data[counter]['description'] = location_description.text.strip()
        else:
          data[counter]['description'] = ""

      # Links
      location_links = soup.find('h3', text='Links')
      data[counter]['links'] = []
      if location_links:
        if debugMode: print "LINKS: "
        for content in location_links.parent.contents:
          if content.name == 'ul':
            for aTag in content.find_all('a', href=True):
              if debugMode: print aTag['href']
              data[counter]['links'].append(aTag['href'])
        if debugMode: print '\n'


      # Entrances
      location_entrances = soup.find_all('img')
      data[counter]['entrances'] = []
      if location_entrances:
        if debugMode: print "ENTRANCES: "
        for entrance in location_entrances:
          if debugMode: print entrance['alt'].strip()
          data[counter]['entrances'].append(entrance['alt'].strip())
        if debugMode: print '\n'

      # What's Inside
      location_insides_pages = soup.find('ul', attrs={'class': 'pagination'})
      data[counter]['inside_pages'] = []
      if location_insides_pages:
        inside_pages = location_insides_pages.find_all('a', href=True)
        if inside_pages:
          data[counter]['inside_pages'].append(url + '?page=1')
          for page in inside_pages:
            if page['href'] not in data[counter]['inside_pages']:
              if debugMode: print page['href']
              data[counter]['inside_pages'].append(page['href'])

      # NO: Levels

      # NO: Hours

      print "~~~~~ " + str(counter) + " ~~~~~"
      counter += 1

  with open('studiousLocations.json', 'w') as outfile:
    print json.dump(data, outfile, indent=4)

# Go through each category and get all the individual location urls
# getLocationsFromPages()

# Go individual locations and get location information
# getLocationInfo()

# From the inside_pages urls figure out which locations are linked
getLinkedLocations()
