# TODO MAJOR CLEANUP but I'm lazy
from mappening.utils.database import *
from mappening.utils import tokenize
import location_utils

from flask import Flask, jsonify, request, json, Blueprint
from flask_cors import CORS, cross_origin
import re
import os
from operator import itemgetter

# Must be on same level as app.py
# data = json.load(open('sampleData.json'))

locations = Blueprint('locations', __name__)

# Google API Key
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Returns JSON of all past locations/venues
@locations.route('/', methods=['GET'])
def get_all_locations():
    output = []

    locations_cursor = UCLA_locations_collection.find({}, {'_id': False})
    if locations_cursor.count() > 0:
      for loc in locations_cursor:
        output.append({"location": loc})
    else:
        print 'Cannot find any locations!'

    # Output typically contains name, city, country, latitude, longitude, state, 
    # street, and zip for each location
    return jsonify({'locations': output})

# UPDATE DATABASE

# Add locations to database from given collection
# Sample collection(s): events_ml_collection, ucla_events_collection
# TODO: hook up so everytime we get new events we add their location data to db
@locations.route('/add/<events_collection>', methods=['PUT'])
def add_locations_from_collection(events_collection):
    # Update locations or insert new locations from events in db
    updated_locations = []
    added_locations = []
    updated = False

    # TODO  Verify collection is valid
    if events_collection != "ucla_events" and events_collection != "events_ml" and events_collection != "test":
      return jsonify({'Added Locations': added_locations, 'Updated Locations': updated_locations})

    new_locations = location_utils.get_locations_from_collection(events_collection)

    # Latitude and Longitude range from (-90, 90) and (-180, 180)
    INVALID_COORDINATE = 420

    print new_locations
    
    # For every location from events db
    for new_loc in new_locations:
      # Tokenize and remove unnecessary/common words 
      place_name = re.sub(r'\bUCLA-\s?', '', new_loc['location'].get('name', "NO NAME"), flags=re.IGNORECASE)
      place_name = re.sub(r'-UCLA\s?', '', place_name, flags=re.IGNORECASE)
      place_name = re.sub(r'\b[a-zA-Z]+\d+\s?', '', place_name, flags=re.IGNORECASE)
      place_name = tokenize.tokenize_text(place_name)
      processed_place = re.compile(place_name, re.IGNORECASE)

      # Find location of same coordinates/name
      coord_loc = UCLA_locations_collection.find_one({'location.latitude': new_loc['location'].get('latitude', INVALID_COORDINATE), 'location.longitude': new_loc['location'].get('longitude', INVALID_COORDINATE)}, {'_id': False})
      alt_name_loc = UCLA_locations_collection.find_one({'location.alternative_names': processed_place}, {'_id': False})

      # If there exists a pre-existing location with matching coordinates/name
      if coord_loc or alt_name_loc:
        old_loc = alt_name_loc
        is_name = True
        if coord_loc and not alt_name_loc:
          old_loc = coord_loc
          is_name = False

        # Location already in db but missing info
        # Merge new info with db document
        for key in new_loc['location']:
          # Key is missing from location so add it
          if key not in old_loc['location']:
            old_loc['location'][key] = new_loc['location'][key]
            updated = True
          # Names do not match, coordinates do so add name as alternate name
          if key == "name" and 'name' in old_loc['location'] and old_loc['location']['name'] != new_loc['location']['name']:
            if new_loc['location']['name'].lower() not in (name.lower() for name in old_loc['location']['alternative_names']):
              if new_loc['location']['name']:
                old_loc['location']['alternative_names'].append(new_loc['location']['name'])
                updated = True
            # Also add stripped down name
            if place_name not in (name.lower() for name in old_loc['location']['alternative_names']):
              if place_name:
                old_loc['location']['alternative_names'].append(place_name)
                updated = True

        # Only replace document if it was updated
        if updated:
          updated = False
          updated_locations.append(old_loc)
          print "Updated: " + old_loc['location']['name']
          # Replace document with updated info
          if is_name:
            UCLA_locations_collection.replace_one({'location.alternative_names': processed_place}, old_loc)  
          else:
            UCLA_locations_collection.replace_one({'location.latitude': new_loc['location'].get('latitude', INVALID_COORDINATE), 'location.longitude': new_loc['location'].get('longitude', INVALID_COORDINATE)}, old_loc)
                    
      else:
        # No pre-existing location so insert new location to db
        # Also add stripped version of name to location info
        if place_name != new_loc['location']['name'].lower():
          new_loc['location']['alternative_names'].append(place_name)
        added_locations.append(new_loc)
        print "Added: " + new_loc['location']['name']
        UCLA_locations_collection.insert_one(new_loc.copy())

    return jsonify({'Added Locations': added_locations, 'Updated Locations': updated_locations})

# LOCATIONS SEARCH

# Given location name, return location data or some indication that no location
# could be found. Returns <num_results> top results
@locations.route('/search/<place_query>', defaults={'num_results': None}, methods=['GET'])
@locations.route('/search/<place_query>/<int:num_results>', methods=['GET'])
def get_location_results(place_query, num_results):
    search_results = location_utils.search_locations(place_query)

    if not search_results:
      return "There were no results!"
    elif not num_results or num_results <= 0:
      return jsonify({"Locations": search_results}) 
    else:
      output = []
      for i in range(0, num_results):
        output.append(search_results[i])
      return jsonify({'Locations': output})

# GOOGLE WRAPPER 

# Run Google Maps TextSearch on given query and print all results in JSON
# Print all results in JSON, a wrapper for Google's API
@locations.route('/google/search/text/<place_query>', methods=['GET'])
def get_textsearch(place_query):
    output = location_utils.google_textSearch(place_query)

    return jsonify({'results': output})

# Run Google Maps NearbySearch on given query. Uses Google Places API Web Service
# to search for places within specified area. Returns more results than textSearch
# Print all results in JSON, a wrapper for Google's API
@locations.route('/google/search/nearby/<place_query>', methods=['GET'])
def get_nearbysearch(place_query):
    output = location_utils.google_nearbySearch(place_query)

    return jsonify({'results': output})
