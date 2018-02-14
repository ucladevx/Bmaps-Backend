# TODO get locations without coords from jason

from flask import Flask, jsonify, request, json, Blueprint
from flask_cors import CORS, cross_origin
import requests
import re
import pymongo
import json
import os
from operator import itemgetter
import process

data = json.load(open('tokenizeData.json'))

Locations = Blueprint('Locations', __name__)

# Enable Cross Origin Resource Sharing (CORS)
cors = CORS(Locations)

# Google API Key
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Standard URI format: mongodb://[dbuser:dbpassword@]host:port/dbname
MLAB_USERNAME = os.getenv('MLAB_USERNAME')
MLAB_PASSWORD = os.getenv('MLAB_PASSWORD')

uri = 'mongodb://{0}:{1}@ds044709.mlab.com:44709/mappening_data'.format(MLAB_USERNAME, MLAB_PASSWORD)

# Set up database connection
client = pymongo.MongoClient(uri)
db = client['mappening_data'] 

events_collection = db.map_events
ml_events_collection = db.events_ml
locations_collection = db.test_locations

# Returns JSON of all past locations/venues
@Locations.route('/api/locations', methods=['GET'])
def get_all_locations():
    output = []

    locations_cursor = locations_collection.find({}, {'_id': False})
    if locations_cursor.count() > 0:
      for loc in locations_cursor:
        output.append({"location": loc})
    else:
        print 'Cannot find any locations!'

    # Output typically contains name, city, country, latitude, longitude, state, 
    # street, and zip for each location
    return jsonify({'locations': output})

# Go through all events in events db and extract unique locations from the events
def find_locations():
    # Iterate through all events and get list of unique venues
    places = []
    place = {}

    # Latitude and Longitude range from (-90, 90) and (-180, 180)
    INVALID_COORDINATE = 420

    # Set parameters for Bruin Bear/Center of UCLA
    CENTER_LATITUDE = "34.070966"
    CENTER_LONGITUDE = "-118.445"
    
    # TODO: Integrate with new events caller
    # Every time there are new events, check location info and update db if necessary
    events_cursor = ml_events_collection.find({"place": {"$exists": True}})
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

# Add locations to mlab db
# Gives some duplicate events in db
# Duplicate events resolved if the different names used are put under alternate_names
@Locations.route('/api/db_locations')
def db_locations():
    # Update locations or insert new locations from events in db
    new_locations = find_locations()
    updated_locations = []
    added_locations = []
    updated = False

    # Latitude and Longitude range from (-90, 90) and (-180, 180)
    INVALID_COORDINATE = 420
    
    # For every location from events db
    for new_loc in new_locations:
      # Tokenize and remove unnecessary/common words 
      place_name = process.processText(new_loc['location'].get('name', "NO NAME"))
      processed_place = re.compile(place_name, re.IGNORECASE)

      # Find location of same coordinates/name
      coord_loc = locations_collection.find_one({'location.latitude': new_loc['location'].get('latitude', INVALID_COORDINATE), 'location.longitude': new_loc['location'].get('longitude', INVALID_COORDINATE)}, {'_id': False})
      alt_name_loc = locations_collection.find_one({'location.alternative_names': processed_place}, {'_id': False})

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
          # Replace document with updated info
          # if is_coord:
          #   locations_collection.replace_one({'location.latitude': new_loc['location'].get('latitude', INVALID_COORDINATE), 'location.longitude': new_loc['location'].get('longitude', INVALID_COORDINATE)}, old_loc)
          # else:
          #   locations_collection.replace_one({'location.alternative_names': processed_place}, old_loc)          
      else:
        # No pre-existing location so insert new location to db
        # Also add stripped version of name to location info
        if place_name != new_loc['location']['name'].lower():
          new_loc['location']['alternative_names'].append(place_name)
        added_locations.append(new_loc)
        # locations_collection.insert_one(new_loc.copy())

    return jsonify({'Added Locations': added_locations, 'Updated Locations': updated_locations})

# Given a location string try to return coordinates/relevant location info
# e.g. BH 3400 => Boelter Hall vs. Engr 4 => Engineering IV vs. Engineering VI
@Locations.route('/api/coordinates/<place_query>', methods=['GET'])
def get_mongo_textSearch(place_query):
    output = []
    output_places = []

    # Supplied string such as "Boelter Hall" for a location
    print "Original place query: " + place_query

    # Tokenize and remove unnecessary/common words 
    processed_place = process.processText(place_query)
    print "Processed place query: " + processed_place

    # Locations db has text search index on alternate_locations field
    # Search for locations that match words in processed place query
    # Default stop words for english language, case insensitive
    # Sort by score (based on number of occurances of query words in alternate names)
    # Can limit numer of results as well
    places_cursor = locations_collection.find( 
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

    return jsonify({"Database Results": output})

# Insert locations from a JSON file to the db
# See sample format in ./sampleData.json
# curl -d -X POST http://localhost:5000/api/insert_locations
# TODO make other things that should be POST post lmao
@Locations.route('/api/insert_locations', methods=['POST'])
def insert_locations():
  locations_collection.insert_many(data['locations'])
  return "Successfully inserted location documents to db!"


# Add tokenized version of all alternate names to alternate names list
@Locations.route('/api/tokenize_names', methods=['GET'])
def get_tokenized_names():
  places = []
  updated = False

  # Go through every location in json
  for location in data['locations']:
    place = location
    if 'alternative_names' in place['location']:
      for alt_name in place['location']['alternative_names']:
        processed_name = process.processText(alt_name)
        if processed_name not in (name.lower() for name in place['location']['alternative_names']):
          if processed_name:
            place['location']['alternative_names'].append(processed_name)
            updated = True
      if updated:
        places.append(place)
        updated = False

  return jsonify({"locations": places})

# Fill out json data using google api results
# Supplied json missing street/zip/latitude/longitude
# Tries to fill out those missing fields using name field or street if supplied
# Takes top result to fill out info, MAY BE INCORRECT
# Warning: pretty slow, limit of 1000 requests? 100 requests?
@Locations.route('/api/location_data', methods=['GET'])
def get_location_data():
  places = []
  updated_places = []
  updated = False

  # Go through every location in json
  for location in data['locations']:
    place = location
    # Add stripped down name to alternative_names
    if 'name' in location['location']:
      processed_place = process.processText(location['location']['name'])
      if 'alternative_names' in location['location']:
        if location['location']['name'].lower() not in (name.lower() for name in location['location']['alternative_names']):
          if location['location']['name']:
            place['location']['alternative_names'].append(location['location']['name'])
            updated = True
        if processed_place not in (name.lower() for name in location['location']['alternative_names']):
          if processed_place:
            place['location']['alternative_names'].append(processed_place)
            updated = True
    # No street or zip information, try to find it
    if 'street' not in location['location'] or 'zip' not in location['location'] or location['location']['street'] == '' or location['location']['zip'] == '':
      if 'name' in location['location']:
        # Use location name to try to find location info
        search_results = google_textSearch(location['location']['name'])
        if search_results:
          # Assume first result is best result/most relevant result
          # Set street to the address
          place['location']['street'] = search_results[0]['address']

          # Extract zip code from address
          re_result = re.search(r'(\d{5}(\-\d{4})?)', place['location']['street'])
          if re_result:
            place['location']['zip'] = re_result.group(0) # Sometimes get 5 digit address numbers
          else:
            place['location']['zip'] = "NO ZIP"
          updated = True
      else:
        # Without a name, street, or zip cannot find out much about location
        # Is it even a location at this point lmao
        place['location']['street'] = "NO STREET"
        place['location']['zip'] = "NO ZIP"
        place['location']['name'] = "NO NAME"
    # Check if latitude/longitude is filled out (420 is default value)
    if 'latitude' not in location['location'] or 'longitude' not in location['location'] or location['location']['latitude'] == 420 or location['location']['longitude'] == 420:
      if 'name' in location['location']:
        # Use location name to try to find location info
        search_results = google_textSearch(location['location']['name'])
        if search_results:
          # If there are results see if there is a latitude/longitude
          if search_results[0]['latitude'] == "NO LATITUDE" or search_results[0]['longitude'] == "NO LONGITUDE":
            place['location']['latitude'] = 404
            place['location']['longitude'] = 404
          else:
            place['location']['latitude'] = search_results[0]['latitude']
            place['location']['longitude'] = search_results[0]['longitude']
            updated = True
      # If there is no name, see if there is street info
      elif 'street' in place['location'] and place['location']['street'] != "NO STREET" and place['location']['street'] != '':
        # Use name to try to find location info
        search_results = google_textSearch(place['location']['street'])
        if search_results:
          if search_results[0]['latitude'] == "NO LATITUDE" or search_results[0]['longitude'] == "NO LONGITUDE":
            place['location']['latitude'] = 404
            place['location']['longitude'] = 404
          else:
            place['location']['latitude'] = search_results[0]['latitude']
            place['location']['longitude'] = search_results[0]['longitude']
            updated = True
      else:
        # There was no name or street info, set to another junk value
        place['location']['latitude'] = 666
        place['location']['longitude'] = 666

    # If we want to keep track of all places from json data uncomment this
    # places.append(place)

    # Keep track of places with info that was actually updated
    if updated:
      updated_places.append(place)
    updated = False

  # Return json info on updated locations and/or all locations from json data
  # return jsonify({"locations": places, "changed locations": updated_places})
  return jsonify({"New/Modified Locations": updated_places})

# Use the Google Places API Web Service to get info about places based on a string
# Results ordered by perceived relevance (use UCLA in query?)
# Can bias results by specifying location (latitude/longitude) and radius (meters)
def google_textSearch(place_query):
    # Set parameters for Bruin Bear/Center of UCLA
    CENTER_LATITUDE = "34.070966"
    CENTER_LONGITUDE = "-118.445"

    # For comprehension: School of Theater, Film, TV within radius 700
    # Hammer Museum within radius 1300, Saffron and Rose within radius 1800
    RADIUS = "2000"

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

# Run Google Maps TextSearch on given query and print all results in JSON
# Uses same function as before but for printing rather than use in event processing
@Locations.route('/api/place_textSearch/<place_query>', methods=['GET'])
def get_textsearch(place_query):
    output = google_textSearch(place_query)

    return jsonify({'results': output})
    # return jsonify({'results': resultsJSON})

# Run Google Maps NearbySearch on given query. Uses Google Places API Web Service
# to search for places within specified area. Takes in location, radius, and a keyword.
# Optional rankby parameter, and also returns more results than textSearch
@Locations.route('/api/place_nearbySearch/<place_query>', methods=['GET'])
def get_nearbysearch(place_query):
    # Set parameters for Bruin Bear/Center of UCLA
    CENTER_LATITUDE = "34.070966"
    CENTER_LONGITUDE = "-118.445"

    # For comprehension: School of Theater, Film, TV within radius 700
    # Hammer Museum within radius 1300, Saffron and Rose within radius 1800
    RADIUS = "2000"

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

    return jsonify({'results': output})
    # return jsonify({'results': resultsJSON})
