from flask import Flask, jsonify, request, json, Blueprint
from flask_cors import CORS, cross_origin
import requests
import re
import pymongo
import json
import os

data = json.load(open('sampleData.json'))

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
total_events_collection = db.total_events
locations_collection = db.UCLA_locations

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
# TODO: add fields that are missing (coordinates)
def find_locations():
    # Iterate through all events and get list of unique venues
    places = []
    place = {}

    # Latitude and Longitude range from (-90, 90) and (-180, 180)
    INVALID_COORDINATE = 420
    
    # TODO: change this to events_collection and integrate with new events caller
    # Every time there are new events, check location info and update db if necessary
    events_cursor = events_collection.find({"place": {"$exists": True}})
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
                        if place['location']['name'] not in loc['location']['alternative_names']:
                          loc['location']['alternative_names'].append(place['location']['name'])
            else:
              # No coordinates exist, just add place
              places.append(place)
        # Reset place to an empty dict
        place = {}
      return places
    else:
      return 'Cannot find any events with locations!'

# Add locations to mlab db
# Gives some duplicate events in db
# TODO: perhaps manually combine duplicate events and in future will be better
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
      print "~~~~~~~~~~~~~~~~~~~~~"
      print new_loc['location'].get('name', "NO NAME")
      # Remove UCLA from name
      re_name = re.sub(r'\bat UCLA\s?', '', new_loc['location'].get('name', "NO NAME"), flags=re.IGNORECASE)
      re_name = re.sub(r'\b@ UCLA\s?', '', re_name, flags=re.IGNORECASE)
      re_name = re.sub(r'\bof UCLA\s?', '', re_name, flags=re.IGNORECASE)
      re_name = re.sub(r'\bUCLA\s?', '', re_name, flags=re.IGNORECASE)
      # TODO: room, the, commas, multispaces, LA, numbers, westwood
      # Remove Hyphens
      re_name = re.sub(r'-\s?', '', re_name)
      # Remove leading/trailing white space
      re_name = re_name.strip()

      print re_name

      # Find location of same coordinates/name
      coord_loc = locations_collection.find_one({'location.latitude': new_loc['location'].get('latitude', INVALID_COORDINATE), 'location.longitude': new_loc['location'].get('longitude', INVALID_COORDINATE)}, {'_id': False})
      name_loc = locations_collection.find_one({'location.name': re_name}, {'_id': False})
      alt_name_loc = locations_collection.find_one({'location.alternative_names': re_name}, {'_id': False})

      # If there exists a pre-existing location with matching coordinates/name
      if coord_loc or name_loc or alt_name_loc:
        old_loc = coord_loc
        loc_type = 1
        if name_loc and not coord_loc:
          old_loc = name_loc
          loc_type = 2
        elif alt_name_loc and not coord_loc and not name_loc:
          old_loc = alt_name_loc
          loc_type = 3

        # Location already in db but missing info
        # Merge new info with db document
        for key in new_loc['location']:
            # Key is missing from location so add it
            if key not in old_loc['location']:
                old_loc['location'][key] = new_loc['location'][key]
                updated = True
            # Names do not match, coordinates do so add name as alternate name
            if key == "name" and 'name' in old_loc['location'] and old_loc['location']['name'] != new_loc['location']['name']:
                if new_loc['location']['name'] not in old_loc['location']['alternative_names']:
                    old_loc['location']['alternative_names'].append(new_loc['location']['name'])
                    updated = True
        # Only replace document if it was updated
        if updated:
          updated = False
          updated_locations.append({'location': old_loc})
          # Replace document with updated info
          if loc_type == 1:
            locations_collection.replace_one({'location.latitude': new_loc['location'].get('latitude', INVALID_COORDINATE), 'location.longitude': new_loc['location'].get('longitude', INVALID_COORDINATE)}, old_loc)
          elif loc_type == 2:
            locations_collection.replace_one({'location.name': re_name}, old_loc)
          else:
            locations_collection.replace_one({'location.alternative_names': re_name}, old_loc)          
      else:
        # No pre-existing location so insert new location to db
        added_locations.append({'location': new_loc})
        locations_collection.insert_one(new_loc.copy())

    return jsonify({'Added Locations': added_locations, 'Updated Locations': updated_locations})

# Given pymongo cursors to places that match by name or alternate name return
# combined output of places' location info
def get_coordinate_results(places_cursor, alt_places_cursor):
    output = []
    output_places = []

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

    # Places that match the alternate name are appended to output if not already
    # part of output
    if alt_places_cursor.count() > 0:
      for alt_place in alt_places_cursor:
        # Check if already added by maintaining list of places added by name
        if alt_place['location'].get('name', "NO NAME") not in output_places:
          output.append({
            'name': alt_place['location'].get('name', "NO NAME"),
            'street': alt_place['location'].get('street', "NO STREET"),
            'zip': alt_place['location'].get('zip', "NO ZIP"),
            'city': alt_place['location'].get('city', "NO CITY"),
            'state': alt_place['location'].get('state', "NO STATE"),
            'country': alt_place['location'].get('country', "NO COUNTRY"),
            'latitude': alt_place['location'].get('latitude', "NO LATITUDE"),
            'longitude': alt_place['location'].get('longitude', "NO LONGITUDE"),
            'alternative_names': alt_place['location']['alternative_names']
          })
          output_places.append(alt_place['location'].get('name', "NO NAME"))

    # Returns list of relevant locations' info
    return output;

# Given a location string try to return coordinates/relevant location info
# Number is important to some locations, so first tries entire query string,
# and then the query string stripped of numbers
# e.g. BH 3400 => Boelter Hall vs. Engr 4 => Engineering IV vs. Engineering VI
@Locations.route('/api/coordinates/<place_query>', methods=['GET'])
def get_coordinates(place_query):
    output = []

    # Check database for matches (case insensitive) in names or alternative names
    # Concatenate results from name and alternative_names fields
    place_regex = re.compile('.*' + place_query + '.*', re.IGNORECASE)
    places_cursor = locations_collection.find({'location.name': place_regex})
    alt_places_cursor = locations_collection.find({'location.alternative_names': place_regex})

    # If no matches found, try to search database after removing numbers from query
    if places_cursor.count() <= 0 and alt_places_cursor.count() <= 0:
      # Removes Integers/Decimals and the following space
      num_place_query = re.sub(r'\b\d+(?:\.\d+)?\s?', '', place_query)
      # Remove UCLA
      num_place_query = re.sub(r'\bat UCLA\s?', '', num_place_query, flags=re.IGNORECASE)
      num_place_query = re.sub(r'\b@ UCLA\s?', '', num_place_query, flags=re.IGNORECASE)
      num_place_query = re.sub(r'\bof UCLA\s?', '', num_place_query, flags=re.IGNORECASE)
      num_place_query = re.sub(r'\bUCLA\s?', '', num_place_query, flags=re.IGNORECASE)
      # Remove Hyphens
      num_place_query = re.sub(r'-\s?', '', num_place_query)
      # Remove leading/trailing white space
      num_place_query = num_place_query.strip()

      # Get results from db with new regex search string
      num_place_regex = re.compile('.*' + num_place_query + '.*', re.IGNORECASE)
      places_cursor = locations_collection.find({'location.name': num_place_regex})
      alt_places_cursor = locations_collection.find({'location.alternative_names': num_place_regex})

      # No results in db, do google api search and return results
      if places_cursor.count() <= 0 and alt_places_cursor.count() <= 0:
        search_results = google_textSearch(place_query)
        if search_results:
          return jsonify({"Google Text Search Results": search_results})
        else:
          # No results from google api either
          return jsonify({"No Results": output})

    # Otherwise, cursors were nonempty so we can get results (either with or without numbers in query)
    output = get_coordinate_results(places_cursor, alt_places_cursor)

    return jsonify({"Database Results": output})

# Insert locations from a JSON file to the db
# See sample format in ./sampleData.json
@Locations.route('/api/insert_locations', methods=['GET'])
def insert_locations():
  locations_collection.insert_many(data['locations'])
  return "Successfully inserted location documents to db!"

# Fill out json data using google api results
# Supplied json missing street/zip/latitude/longitude
# Tries to fill out those missing fields using name field or street if supplied
# Takes top result to fill out info, MAY BE INCORRECT
# Warning: pretty slow, limit of 1000 requests? 100 requests?
# TODO: improve speed/optimality
@Locations.route('/api/location_data', methods=['GET'])
def get_location_data():
  places = []
  updated_places = []
  updated = False

  # Go through every location in json
  for location in data['locations']:
    place = location
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
