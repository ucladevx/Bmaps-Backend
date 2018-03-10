from mappening.utils.database import *
from mappening.utils import tokenize
import location_utils


from flask import Flask, jsonify, request, json, Blueprint
from flask_cors import CORS, cross_origin
import requests
import re
import json
import os
from operator import itemgetter

# Google API Key
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Latitude and Longitude range from (-90, 90) and (-180, 180)
INVALID_COORDINATE = 420

# Set parameters for Bruin Bear/Center of UCLA
CENTER_LATITUDE = "34.070966"
CENTER_LONGITUDE = "-118.445"

# For comprehension: School of Theater, Film, TV within radius 700
# Hammer Museum within radius 1300, Saffron and Rose within radius 1800
RADIUS = "2000"

# Go through all events in given events db and extract unique locations from the events
# Return the array of locations discovered
def get_locations_from_collection(events_collection):
    # Iterate through all events and get list of unique venues
    places = []
    place = {}

    if events_collection == "ucla_events":
      events_cursor = ucla_events_collection.find({"place": {"$exists": True}})
    elif events_collection == "events_ml":
      events_cursor = events_ml_collection.find({"place": {"$exists": True}})
    else: # events_collection == "test":
      events_cursor = test_collection.find({"place": {"$exists": True}})
    
    # Every time there are new events, check location info and update db if necessary
    # events_cursor = events_ml_collection.find({"place": {"$exists": True}})
    # events_cursor = events_collection.find({"place": {"$exists": True}})
    if events_cursor.count() > 0:
      for event in events_cursor:
        # Add location info to place dict
        if 'location' in event['place']:
          place['location'] = event['place']['location']
        if 'name' in event['place']:
          place['location']['name'] = event['place']['name']

        # Check that place is not empty
        if any(place):
          # All places should have alternative names field
          place['location']['alternative_names'] = []
          if 'name' in event['place']:
            place['location']['alternative_names'].append(place['location']['name'])
          # Reject exact matches
          if place not in places:
            # Check whether coordinates exist
            if 'latitude' in place['location'] and 'longitude' in place['location']:
              # Check whether coordinates match another event
              if not any(loc.get('latitude', INVALID_COORDINATE) == place['location']['latitude'] and loc.get('longitude', INVALID_COORDINATE) == place['location']['longitude'] for loc in places):
                # No matching coordinates, append to list
                places.append(place)
              else:
                # There exists a nonidentical location with matching coordinates
                # Merge information of new event into old event
                # Can probably improve this part
                for loc in places:
                  if loc['location'].get('latitude', INVALID_COORDINATE) == place['latitude'] and loc['location'].get('longitude', INVALID_COORDINATE) == place['longitude']:
                    # Go through all the keys
                    for key in place['location']:
                      # If new key then add it to location
                      if key not in loc['location']:
                        loc['location'][key] = place['location'][key]
                      # If names do not match, coordinates do so add name as an alternate name
                      if key == "name" and 'name' in loc['location'] and loc['location']['name'] != place['location']['name']:
                        if place['location']['name'].lower() not in (name.lower() for name in loc['location']['alternative_names']):
                          if place['location']['name']:
                            loc['location']['alternative_names'].append(place['location']['name'])
            else:
              # No coordinates exist, indicate that coordinates may be incorrect
              place['coordinates'] = "GOOGLE"
              # Try to get coordinates from google places
              if 'name' in place['location']:
                # Use location name to try to find location info
                search_results = google_textSearch(place['location']['name'])
                if search_results:
                  # If there are results see if there is a latitude/longitude
                  if search_results[0]['latitude'] == "NO LATITUDE" or search_results[0]['longitude'] == "NO LONGITUDE":
                    place['location']['latitude'] = CENTER_LATITUDE
                    place['location']['longitude'] = CENTER_LONGITUDE
                  else:
                    place['location']['latitude'] = search_results[0]['latitude']
                    place['location']['longitude'] = search_results[0]['longitude']
              # If there is no name, see if there is street info
              elif 'street' in place['location'] and place['location']['street'] != "NO STREET" and place['location']['street'] != '':
                # Use name to try to find location info
                search_results = google_textSearch(place['location']['street'])
                if search_results:
                  if search_results[0]['latitude'] == "NO LATITUDE" or search_results[0]['longitude'] == "NO LONGITUDE":
                    place['location']['latitude'] = CENTER_LATITUDE
                    place['location']['longitude'] = CENTER_LONGITUDE
                  else:
                    place['location']['latitude'] = search_results[0]['latitude']
                    place['location']['longitude'] = search_results[0]['longitude']
                    updated = True
              else:
                # There was no name or street info, set to Bruin Bear location
                place['location']['latitude'] = CENTER_LATITUDE
                place['location']['longitude'] = CENTER_LONGITUDE

              places.append(place)
        # Reset place to an empty dict
        place = {}
      return places
    else:
      return 'Cannot find any events with locations!'

# Given a location string try to return coordinates/relevant location info
# e.g. BH 3400 => Boelter Hall vs. Engr 4 => Engineering IV vs. Engineering VI
# Given location string get all relevant locations found in our db, return json
def search_locations(place_query):
    output = []
    output_places = []

    # Supplied string such as "Boelter Hall" for a location
    print "Original place query: " + place_query
    # Remove leading/trailing white space
    place_query = place_query.strip()

    # Search for exact match first
    # Sometimes regency village weighted more than sunset village due to repetition of village
    # place_regex = re.compile('.*' + place_query + '.*', re.IGNORECASE)
    place_regex = place_query
    if place_query.lower() != "ucla":
      place_regex = re.sub(r'\bUCLA\s?', '', place_regex, flags=re.IGNORECASE)
    place_regex = re.sub(r'\|', ' ', place_regex, flags=re.IGNORECASE)
    place_regex = re.sub(r'\(', '', place_regex, flags=re.IGNORECASE)
    place_regex = re.sub(r'\)', '', place_regex, flags=re.IGNORECASE)
    place_regex = place_regex.strip()
    print "Regex place query: " + place_regex

    place_regex = re.compile("^" + place_regex + "$", re.IGNORECASE)
    places_cursor = UCLA_locations_collection.find({'location.alternative_names': place_regex})
    
    # Places that match the name are appended to output
    if places_cursor.count() > 0:
      for place in places_cursor:
        output.append({
          'name': place['location'].get('name', "NO NAME"),
          'street': place['location'].get('street', "NO STREET"),
          'zip': place['location'].get('zip', "NO ZIP"),
          'city': place['location'].get('city', "NO CITY"),
          'state': place['location'].get('state', "NO STATE"),
          'country': place['location'].get('country', "NO COUNTRY"),
          'latitude': place['location'].get('latitude', "NO LATITUDE"),
          'longitude': place['location'].get('longitude', "NO LONGITUDE"),
          'alternative_names': place['location']['alternative_names']
        })
        output_places.append(place['location'].get('name', "NO NAME"))

      print "Found exact match!"
      return output

    print "Doing text search..."

    # Tokenize and remove unnecessary/common words 
    place_name = re.sub(r'\bUCLA-\s?', '', place_query, flags=re.IGNORECASE)
    place_name = re.sub(r'-UCLA\s?', '', place_name, flags=re.IGNORECASE)
    place_name = re.sub(r'\b[a-zA-Z]+\d+\s?', '', place_name, flags=re.IGNORECASE)
    processed_place = tokenize.tokenize_text(place_name)
    print "Processed place query: " + processed_place

    # Locations db has text search index on alternate_locations field
    # Search for locations that match words in processed place query
    # Default stop words for english language, case insensitive
    # Sort by score (based on number of occurances of query words in alternate names)
    # Can limit numer of results as well
    places_cursor = UCLA_locations_collection.find( 
      { '$text': { '$search': processed_place, '$language': 'english', '$caseSensitive': False } },
      { 'score': { '$meta': 'textScore' } }
    ).sort([('score', { '$meta': 'textScore' })]) #.limit(3)

    # Places that match the alternate name are appended to output if not already
    # part of output
    if places_cursor.count() > 0:
      for place in places_cursor:
        # Check if already added by maintaining list of places added by name
        if place['location'].get('name', "NO NAME") not in output_places:
          output.append({
            'score': place['score'],
            'name': place['location'].get('name', "NO NAME"),
            'street': place['location'].get('street', "NO STREET"),
            'zip': place['location'].get('zip', "NO ZIP"),
            'city': place['location'].get('city', "NO CITY"),
            'state': place['location'].get('state', "NO STATE"),
            'country': place['location'].get('country', "NO COUNTRY"),
            'latitude': place['location'].get('latitude', "NO LATITUDE"),
            'longitude': place['location'].get('longitude', "NO LONGITUDE"),
            'alternative_names': place['location']['alternative_names']
          })
          output_places.append(place['location'].get('name', "NO NAME"))

    return output

# GOOGLE API

# Use the Google Places API Web Service to get info about places based on a string
# Results ordered by perceived relevance (use UCLA in query?)
# Can bias results by specifying location (latitude/longitude) and radius (meters)
def google_textSearch(place_query):
    # Base URL
    TextSearch_URL = 'https://maps.googleapis.com/maps/api/place/textsearch/json?'

    # Forming the request
    textSearch = TextSearch_URL + "query=" + place_query + "&location=" + CENTER_LATITUDE + "," + CENTER_LONGITUDE + "&radius=" + RADIUS + "&key=" + GOOGLE_API_KEY

    # Getting result from URL and processing
    resultsPage = requests.get(textSearch)
    resultsJSON = json.loads(resultsPage.content)

    output = []
    for result in resultsJSON['results']:
      # Extract most relevant information from JSON results
      output.append({
          'name': result.get('name', "NO NAME"),
          'address': result.get('formatted_address', "NO ADDRESS"),
          'latitude': result['geometry']['location'].get('lat', "NO LATITUDE"),
          'longitude': result['geometry']['location'].get('lng', "NO LONGITUDE")
      })

    return output

# Use the Google Places API Web Service to get info about places based on a string
# Results ordered by perceived relevance (use UCLA in query?)
# Can bias results by specifying location (latitude/longitude) and radius (meters)
def google_nearbySearch(place_query):
    # Base URL
    NearbySearch_URL = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?'

    # Forming the request
    nearbySearch = NearbySearch_URL + "location=" + CENTER_LATITUDE + "," + CENTER_LONGITUDE + "&radius=" + RADIUS + "&keyword=" + place_query + "&key=" + GOOGLE_API_KEY

    # Getting result from URL and processing
    resultsPage = requests.get(nearbySearch)
    resultsJSON = json.loads(resultsPage.content)

    output = []
    for result in resultsJSON['results']:
      # Extract most relevant information from JSON results
      output.append({
          'name': result.get('name', "NO NAME"),
          'address': result.get('vicinity', "NO ADDRESS"),
          'latitude': result['geometry']['location'].get('lat', "NO LATITUDE"),
          'longitude': result['geometry']['location'].get('lng', "NO LONGITUDE")
      })

    return output
