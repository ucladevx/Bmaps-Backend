# TODO some more testing before integration

from mappening.utils.database import events_fb_collection, locations_collection
from mappening.api.utils.locations import location_helpers
from mappening.api.utils import tokenizer
from mappening.api.utils.locations import fuzzy_locations

from flask import Flask, jsonify, request, json, Blueprint
from flask_cors import CORS, cross_origin
import requests
import re
import json
import os
from operator import itemgetter

# Latitude and Longitude range from (-90, 90) and (-180, 180)
INVALID_COORDINATE = 420

# For comprehension: School of Theater, Film, TV within radius 700
# Hammer Museum within radius 1300, Saffron and Rose within radius 1800
RADIUS = "2000"

# Go through all events in given events db and extract unique locations from the events
# Return the array of locations discovered
def get_locations_from_collection():
    # Iterate through all events and get list of unique venues
    places = []
    
    # Every time there are new events, check location info and update db if necessary
    events_cursor = events_fb_collection.find({"place": {"$exists": True}})

    if not events_cursor or events_cursor.count() <= 0:
      return 'Cannot find any events with locations!'

    for event in events_cursor:
      place = {}
      
      # Add location info to place dict
      if 'location' in event['place']:
        place['location'] = event['place']['location']
      if 'name' in event['place']:
        place['location']['name'] = event['place']['name']

      place = location_helpers.process_event_location_info(place, places)

    return places      

# UPDATE DATABASE

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
        place_name = tokenizer.tokenize_text(place_name)
        processed_place = re.compile(place_name, re.IGNORECASE)
        alt_name_loc = locations_collection.find_one({'location.alternative_names': processed_place}, {'_id': False})
      
      # If there exists a pre-existing location with matching coordinates/name
      # Location already in db but missing info
      # Merge new info with db document
      if coord_loc or alt_name_loc:
        loc_result = None
        if coord_loc and not alt_name_loc:
          loc_result = location_helpers.handle_keys(coord_loc, new_loc, place_name)
        else:
          loc_result = location_helpers.handle_keys(alt_name_loc, new_loc, place_name, True)
        
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
    processed_query = location_helpers.process_query(place_query)
    print("Processed place query: " + processed_query)
    place_regex = re.compile("^" + processed_query + "$", re.IGNORECASE)
    places_cursor = locations_collection.find({'location.alternative_names': place_regex})
    
    # Places that match the name are appended to output
    if places_cursor.count() > 0:
      for place in places_cursor:
        output.append(location_helpers.append_location(place))
        output_places.append(place['location'].get('name', "NO NAME"))
      return output

    print("Doing text search...")

    # Tokenize query
    tokenized_query = tokenizer.tokenize_text(processed_query)
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
          output.append(location_helpers.append_location(place, True))
          output_places.append(place['location'].get('name', "NO NAME"))

    another_location = fuzzy_locations.match_location(tokenized_query)
    if another_location is not None:
      output.append(another_location['location'])

    return output
