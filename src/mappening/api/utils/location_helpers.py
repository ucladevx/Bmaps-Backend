from mappening.utils.database import events_fb_collection, events_ml_collection, locations_collection
from mappening.api.utils import tokenize
from mappening.utils.secrets import GOOGLE_API_KEY

from flask import Flask, jsonify, request, json, Blueprint
from flask_cors import CORS, cross_origin
import requests
import re
import json
import os
from operator import itemgetter

# Latitude and Longitude range from (-90, 90) and (-180, 180)
INVALID_COORDINATE = 420

# Set parameters for Bruin Bear/Center of UCLA
CENTER_LATITUDE = "34.070966"
CENTER_LONGITUDE = "-118.445"

# For comprehension: School of Theater, Film, TV within radius 700
# Hammer Museum within radius 1300, Saffron and Rose within radius 1800
RADIUS = "2000"

# Use location coordinates to process event location
def process_location_coordinates(place, loc):
    if loc['location'].get('latitude', INVALID_COORDINATE) == place['latitude'] and loc['location'].get('longitude', INVALID_COORDINATE) == place['longitude']:
      # Go through all the keys
      for key in place['location']:
        # If new key then add it to location
        if key not in loc['location']:
          loc['location'][key] = place['location'][key]
        # If names do not match, coordinates do so add name as an alternate name
        if key == "name" and 'name' in loc['location'] and loc['location']['name'] != place['location']['name']:
          if place['location']['name'].lower() not in (name.lower() for name in loc['location']['alternative_names']):
            loc['location']['alternative_names'].append(place['location']['name'])

# No location coordinates found, location info may be wrong
# Try to use Google API to get location info, otherwise default to Bruin Bear
def process_location_google(place):
    # No coordinates exist, indicate that coordinates may be incorrect
    place['coordinates'] = "GOOGLE"

    # Try to get coordinates from google places
    if 'name' in place['location']:
      # Use location name to try to find location info
      search_results = google_textSearch(place['location']['name'])
      if search_results:
        # If there are results see if there is a latitude/longitude otherwise default to Bruin Bear
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
        # If there are results see if there is a latitude/longitude otherwise default to Bruin Bear
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

    return place

# Process location info from event
def process_event_location_info(place, places):
    # Check that place is not empty
    if not any(place):
      # Reset place to an empty dict
      return {}

    # Otherwise place has valid info
    # All places should have alternative names field
    place['location']['alternative_names'] = []
    if 'name' in place['location']:
      place['location']['alternative_names'].append(place['location']['name'])

    # Reject exact matches, already seen location info
    if place in places:
      return {}

    # Check whether coordinates exist
    if 'latitude' in place['location'] and 'longitude' in place['location']:
      # Check whether coordinates match another event
      if not any(loc.get('latitude', INVALID_COORDINATE) == place['location']['latitude'] and loc.get('longitude', INVALID_COORDINATE) == place['location']['longitude'] for loc in places):
        # No matching coordinates, append to list
        places.append(place)
      else:
        # There exists a nonidentical location with matching coordinates
        # Merge information of new event into old event
        # TODO does this modify places
        for loc in places:
          process_location_coordinates(place, loc)
    else:
      places.append(process_location_google(place))

# Handle keys between the new and old location info
def handle_keys(old_location, new_location, place_name, is_name=False):
    updated = False

    # Location already in db but missing info
    # Merge new info with db document
    for key in new_location['location']:
      # Key is missing from location so add it
      if key not in old_location['location']:
        old_location['location'][key] = new_location['location'][key]
        updated = True
      # Names do not match, coordinates do so add name as alternate name
      if key == "name" and 'name' in old_location['location'] and old_location['location']['name'] != new_location['location']['name']:
        if new_location['location']['name'].lower() not in (name.lower() for name in old_location['location']['alternative_names']):
          old_location['location']['alternative_names'].append(new_location['location']['name'])
          updated = True

    # Also add stripped down name
    if place_name not in (name.lower() for name in old_location['location']['alternative_names']):
      old_location['location']['alternative_names'].append(place_name)
      updated = True

    # Only replace document if it was updated
    if updated:
      if is_name:
        locations_collection.replace_one({'location.alternative_names': processed_place}, old_location)
      else:
        locations_collection.replace_one({'location.latitude': new_location['location'].get('latitude', INVALID_COORDINATE), 'location.longitude': new_location['location'].get('longitude', INVALID_COORDINATE)}, old_location)

      return old_location
    return None

# Do some additional processing on the place_query
def process_query(place_query):
    if place_query.lower() != "ucla":
      place_regex = re.sub(r'(UCLA-|-UCLA)+\s?', '', place_query, flags=re.IGNORECASE)
      place_regex = re.sub(r'\bUCLA\s?', '', place_regex, flags=re.IGNORECASE)
    place_regex = re.sub(r'\|', ' ', place_regex, flags=re.IGNORECASE)
    place_regex = re.sub(r'[()]', '', place_regex, flags=re.IGNORECASE)
    place_regex = place_regex.strip()

    return place_regex

# Append location information to output
def append_location(place, score=False):
  location_dict = {
    'name': place['location'].get('name', "NO NAME"),
    'street': place['location'].get('street', "NO STREET"),
    'zip': place['location'].get('zip', "NO ZIP"),
    'city': place['location'].get('city', "NO CITY"),
    'state': place['location'].get('state', "NO STATE"),
    'country': place['location'].get('country', "NO COUNTRY"),
    'latitude': place['location'].get('latitude', "NO LATITUDE"),
    'longitude': place['location'].get('longitude', "NO LONGITUDE"),
    'alternative_names': place['location']['alternative_names']
  }

  if score:
    location_dict['score'] = place['score']

  return location_dict

# GOOGLE API

# Use the Google Places API Web Service to get info about places based on a string
# Results ordered by perceived relevance (use UCLA in query?)
# Can bias results by specifying location (latitude/longitude) and radius (meters)
def google_textSearch(place_query):
    # Base URL
    TextSearch_URL = 'https://maps.googleapis.com/maps/api/place/textsearch/json?'

    # Forming the request
    textSearch = TextSearch_URL + "query=" + place_query + "&location=" + CENTER_LATITUDE + "," + CENTER_LONGITUDE + "&radius=" + RADIUS + "&key=" + GOOGLE_API_KEY
    print(textSearch)

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
