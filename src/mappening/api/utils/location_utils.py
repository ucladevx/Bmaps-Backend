# TODO FIX THIS GROSSNESS

from mappening.utils.database import events_current_collection, events_ml_collection, locations_collection
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
    if 'name' in event['place']:
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

# Go through all events in given events db and extract unique locations from the events
# Return the array of locations discovered
def get_locations_from_collection():
    # Iterate through all events and get list of unique venues
    places = []
    place = {}
    
    # Every time there are new events, check location info and update db if necessary
    # events_cursor = events_ml_collection.find({"place": {"$exists": True}})
    events_cursor = events_current_collection.find({"place": {"$exists": True}})

    if not events_cursor or events_cursor.count() <= 0:
      return 'Cannot find any events with locations!'

    for event in events_cursor:
      # Add location info to place dict
      if 'location' in event['place']:
        place['location'] = event['place']['location']
      if 'name' in event['place']:
        place['location']['name'] = event['place']['name']

      place = process_event_location_info(place, places)

    return places      

# UPDATE DATABASE

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


# Add locations to database from new events
# TODO: hook up so everytime we get new events we add their location data to db
def add_locations_from_collection():
    # Update locations or insert new locations from events in db
    updated_locations = []
    added_locations = []

    # Can change what collection we get locations from
    new_locations = get_locations_from_collection()

    # For every location from events db
    for new_loc in new_locations:
      # Find location of same coordinates/name
      coord_loc = locations_collection.find_one({'location.latitude': new_loc['location'].get('latitude', INVALID_COORDINATE), 'location.longitude': new_loc['location'].get('longitude', INVALID_COORDINATE)}, {'_id': False})
      alt_name_loc = None

      # Tokenize and remove unnecessary/common words
      place_name = new_loc['location'].get('name')
      if place_name:
        place_name = re.sub(r'(UCLA-|-UCLA)+\s?', '', place_name, flags=re.IGNORECASE)
        place_name = tokenize.tokenize_text(place_name)
        processed_place = re.compile(place_name, re.IGNORECASE)
        alt_name_loc = locations_collection.find_one({'location.alternative_names': processed_place}, {'_id': False})
      
      # If there exists a pre-existing location with matching coordinates/name
      # Location already in db but missing info
      # Merge new info with db document
      if coord_loc or alt_name_loc:
        loc_result = None
        if coord_loc and not alt_name_loc:
          loc_result = handle_keys(coord_loc, new_loc, place_name)
        else:
          loc_result = handle_keys(alt_name_loc, new_loc, place_name, True)
        
        if loc_result:
          updated_locations.append(loc_result)
      else:
        # No pre-existing location so insert new location to db
        # Also add stripped version of name to location info
        if place_name and place_name != new_loc['location']['name'].lower():
          new_loc['location']['alternative_names'].append(place_name)
        added_locations.append(new_loc)
        locations_collection.insert_one(new_loc.copy())

    return jsonify({'Added Locations': added_locations, 'Updated Locations': updated_locations})

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

# Given a location string try to return coordinates/relevant location info
# e.g. BH 3400 => Boelter Hall vs. Engr 4 => Engineering IV vs. Engineering VI
# Given location string get all relevant locations found in our db, return json
def search_locations(place_query):
    output = []
    output_places = []

    # Supplied string such as "Boelter Hall" for a location
    print("Original place query: " + place_query)
    # Remove leading/trailing white space
    place_query = place_query.strip()

    # Search for exact match first
    # Sometimes regency village weighted more than sunset village due to repetition of village
    processed_query = process_query(place_query)
    print("Processed place query: " + processed_query)
    place_regex = re.compile("^" + processed_query + "$", re.IGNORECASE)
    places_cursor = locations_collection.find({'location.alternative_names': place_regex})
    
    # Places that match the name are appended to output
    if places_cursor.count() > 0:
      for place in places_cursor:
        output.append(append_location(place))
        output_places.append(place['location'].get('name', "NO NAME"))
      return output

    print("Doing text search...")

    # Tokenize query
    tokenized_query = tokenize.tokenize_text(processed_query)
    print("Tokenized place query: " + tokenized_query)

    # Locations db has text search index on alternate_locations field
    # Search for locations that match words in processed place query
    # Default stop words for english language, case insensitive
    # Sort by score (based on number of occurances of query words in alternate names)
    # Can limit numer of results as well
    places_cursor = locations_collection.find( 
      { '$text': { '$search': tokenized_query, '$language': 'english', '$caseSensitive': False } },
      { 'score': { '$meta': 'textScore' } }
    ).sort([('score', { '$meta': 'textScore' })]) #.limit(3)

    # Places that match the alternate name are appended to output if not already
    # part of output
    if places_cursor.count() > 0:
      for place in places_cursor:
        # Check if already added by maintaining list of places added by name
        if place['location'].get('name', "NO NAME") not in output_places:
          output.append(append_location(place, True))
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
