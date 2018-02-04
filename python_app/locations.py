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
    locations = find_locations()

    for loc in locations:
        output.append({"location": loc})
    # Output typically contains name, city, country, latitude, longitude, state, 
    # street, and zip for each location
    return jsonify({'locations': output})

def find_locations():
    # Iterate through all events and get list of unique venues
    places = []
    place = {}

    # Latitude and Longitude range from (-90, 90) and (-180, 180)
    INVALID_COORDINATE = 420
    
    # TODO: change this to events_collection and integrate with new events caller
    # Every time there are new events, check location info and update db if necessary
    events_cursor = total_events_collection.find({"place": {"$exists": True}})
    if events_cursor.count() > 0:
        for event in events_cursor:
            if 'location' in event['place']:
                place = event['place']['location']
            if 'name' in event['place']:
                place['name'] = event['place']['name']

            # Check that place is not empty
            if any(place):
                place['alternative_names'] = []
                # Reject exact matches
                if place not in places:
                    # Check whether coordinates exist
                    if 'latitude' in place and 'longitude' in place:
                        # Check whether coordinates match another event
                        if not any(loc.get('latitude', INVALID_COORDINATE) == place['latitude'] and loc.get('longitude', INVALID_COORDINATE) == place['longitude'] for loc in places):
                            # No matching coordinates, append to list
                            places.append(place)
                        else:
                            # There exists a nonidentical location with matching coordinates
                            # Merge information, keeping 
                            for loc in places:
                                if loc.get('latitude', INVALID_COORDINATE) == place['latitude'] and loc.get('longitude', INVALID_COORDINATE) == place['longitude']:
                                    for key in place:
                                        if key not in loc:
                                            loc[key] = place[key]
                                        if key == "name" and 'name' in loc and loc['name'] != place['name']:
                                            if place['name'] not in loc['alternative_names']:
                                                loc['alternative_names'].append(place['name'])
                    else:
                        # No coordinates exist, just add place
                        places.append(place)
            place = {}
        return places
    else:
        print 'Cannot find any events with locations!'
        return []

# Add locations to mlab db
# Gives some duplicate events in db
@Locations.route('/api/db_locations')
def db_locations():
    # Given JSON, update locations or insert new locations
    new_locations = find_locations()
    added_locations = []
    updated = False

    # Latitude and Longitude range from (-90, 90) and (-180, 180)
    INVALID_COORDINATE = 420
    
    # Get all db locations and put in another list
    # Or keep calling find and update

    for new_loc in new_locations:
      # Find location of same coordinates
      coord_loc = locations_collection.find_one({'latitude': new_loc.get('latitude', INVALID_COORDINATE), 'longitude': new_loc.get('longitude', INVALID_COORDINATE)}, {'_id': False})
      name_loc = locations_collection.find_one({'name': new_loc.get('name', "NO NAME")}, {'_id': False})
      alt_name_loc = locations_collection.find_one({'alternative_names': new_loc.get('name', "NO NAME")}, {'_id': False})
      if coord_loc or name_loc or alt_name_loc:
        old_loc = coord_loc
        if name_loc and not coord_loc:
          old_loc = name_loc
        elif alt_name_loc and not coord_loc and not name_loc:
          old_loc = alt_name_loc

        # Location already in db but missing info
        # Merge new info with db document
        for key in new_loc:
            if key not in old_loc:
                old_loc[key] = new_loc[key]
                updated = True
            if key == "name" and 'name' in old_loc and old_loc['name'] != new_loc['name']:
                if new_loc['name'] not in old_loc['alternative_names']:
                    old_loc['alternative_names'].append(new_loc['name'])
                    updated = True
        locations_collection.replace_one({'latitude': new_loc['latitude'], 'longitude': new_loc['longitude']}, old_loc, True)
        if updated:
          added_locations.append(old_loc)
          updated = False
      else:
        # Insert new location to db
        locations_collection.insert_one(new_loc)
        added_locations.append(new_loc)
    return jsonify({"added locations": added_locations})

def get_coordinate_results(places_cursor, alt_places_cursor):
    output = []
    output_places = []

    if places_cursor.count() > 0:
      for place in places_cursor:
        output.append({
          'name': place.get('name', "NO NAME"),
          'street': place.get('street', "NO STREET"),
          'zip': place.get('zip', "NO ZIP"),
          'city': place.get('city', "NO CITY"),
          'state': place.get('state', "NO STATE"),
          'country': place.get('country', "NO COUNTRY"),
          'latitude': place.get('latitude', "NO LATITUDE"),
          'longitude': place.get('longitude', "NO LONGITUDE"),
          'alternative_names': place['alternative_names']
        })
        output_places.append(place.get('name', "NO NAME"))

    if alt_places_cursor.count() > 0:
      for alt_place in alt_places_cursor:
        # Check if already added
        if alt_place.get('name', "NO NAME") not in output_places:
          output.append({
            'name': alt_place.get('name', "NO NAME"),
            'street': alt_place.get('street', "NO STREET"),
            'zip': alt_place.get('zip', "NO ZIP"),
            'city': alt_place.get('city', "NO CITY"),
            'state': alt_place.get('state', "NO STATE"),
            'country': alt_place.get('country', "NO COUNTRY"),
            'latitude': alt_place.get('latitude', "NO LATITUDE"),
            'longitude': alt_place.get('longitude', "NO LONGITUDE"),
            'alternative_names': alt_place['alternative_names']
          })
          output_places.append(alt_place.get('name', "NO NAME"))

    return output;

# Given a location string try to return coordinates/relevant location info
# IMPORTANT: Should be given base query, like Boelter or BH, not BH 3400.
# I would have removed the 3400 programmatically, but in cases like Parking Structure 8
# OR Engineering 4, the number is important.
@Locations.route('/api/coordinates/<place_query>', methods=['GET'])
def get_coordinates(place_query):
    output = []

    # Check database for matches (case insensitive) in names or alternative names
    # Concatenate results from name and alternative_names fields
    place_regex = re.compile('.*' + place_query + '.*', re.IGNORECASE)
    places_cursor = locations_collection.find({'name': place_regex})
    alt_places_cursor = locations_collection.find({'alternative_names': place_regex})

    if places_cursor.count() <= 0 and alt_places_cursor.count() <= 0:
      # Removes Integers/Decimals and the following space
      num_place_query = re.sub(r'\b\d+(?:\.\d+)?\s?', '', place_query)
      # Remove leading/trailing white space
      num_place_query = num_place_query.strip()

      num_place_regex = re.compile('.*' + num_place_query + '.*', re.IGNORECASE)
      places_cursor = locations_collection.find({'name': num_place_regex})
      alt_places_cursor = locations_collection.find({'alternative_names': num_place_regex})

      # No results in db, do google api search and return results
      if places_cursor.count() <= 0 and alt_places_cursor.count() <= 0:
        search_results = google_textSearch(place_query)
        if search_results:
          return jsonify({"google text search results": search_results})
        else:
          return jsonify({"no results": output})

    # Otherwise, cursors were nonempty so we can get results
    output = get_coordinate_results(places_cursor, alt_places_cursor)

    return jsonify({"location db results": output})

# Insert locations from a JSON file to the db
@Locations.route('/api/insert_locations', methods=['GET'])
def insert_locations():
  locations_collection.insert_many(data['locations'])
  return "Successfully inserted location documents to db"

# Fill out json data using google api results
# Warning: pretty slow, limit of 1000 requests
@Locations.route('/api/location_data', methods=['GET'])
def get_location_data():
  # return jsonify(data)

  places = []
  updated_places = []
  updated = False

  # Go through every location
  for location in data['locations']:
    place = location
    # No street or zip information, try to find it
    if location['street'] == '' or location['zip'] == '':
      if 'name' in location:
        search_results = google_textSearch(location['name'])
        if search_results:
          # Assume first result is best result
          place['street'] = search_results[0]['address']
          re_result = re.search(r'(\d{5}(\-\d{4})?)', place['street'])
          if re_result:
            place['zip'] = re_result.group(0) # Sometimes get 5 digit address numbers
          else:
            place['zip'] = "NO ZIP"
          updated = True
      else:
        place['street'] = "NO STREET"
        place['zip'] = "NO ZIP"
    # Check if latitude/longitude is filled out
    if location['latitude'] == 420 or location['longitude'] == 420:
      if 'name' in location:
        search_results = google_textSearch(location['name'])
        if search_results:
          if search_results[0]['latitude'] == "NO LATITUDE" or search_results[0]['longitude'] == "NO LONGITUDE":
            place['latitude'] = 404
            place['longitude'] = 404
          else:
            place['latitude'] = search_results[0]['latitude']
            place['longitude'] = search_results[0]['longitude']
            updated = True
      elif place['street'] != "NO STREET" and place['street'] != '':
        search_results = google_textSearch(place['street'])
        if search_results:
          if search_results[0]['latitude'] == "NO LATITUDE" or search_results[0]['longitude'] == "NO LONGITUDE":
            place['latitude'] = 404
            place['longitude'] = 404
          else:
            place['latitude'] = search_results[0]['latitude']
            place['longitude'] = search_results[0]['longitude']
            updated = True
      else:
        place['latitude'] = 666
        place['longitude'] = 666
    # places.append(place)
    if updated:
      updated_places.append(place)
    updated = False

  # return jsonify({"locations": places, "changed locations": updated_places})
  return jsonify({"changed locations": updated_places})

def google_textSearch(place_query):
    CENTER_LATITUDE = "34.070966"
    CENTER_LONGITUDE = "-118.445"
    RADIUS = "2000"
    # UCLA School of Theater, Film and Television is within radius of 700 
    # Hammer museum within 1300 radius
    # Saffron and rose 1800

    TextSearch_URL = 'https://maps.googleapis.com/maps/api/place/textsearch/json?'

    textSearch = TextSearch_URL + "query=" + place_query + "&location=" + CENTER_LATITUDE + "," + CENTER_LONGITUDE + "&radius=" + RADIUS + "&key=" + GOOGLE_API_KEY

    resultsPage = requests.get(textSearch)
    resultsJSON = json.loads(resultsPage.content)

    output = []
    for result in resultsJSON['results']:
      output.append({
          'name': result.get('name', "NO NAME"),
          'address': result.get('formatted_address', "NO ADDRESS"),
          'latitude': result['geometry']['location'].get('lat', "NO LATITUDE"),
          'longitude': result['geometry']['location'].get('lng', "NO LONGITUDE")
      })

    return output

# Run Google Maps TextSearch on given query
@Locations.route('/api/place_textSearch/<place_query>', methods=['GET'])
def get_textsearch(place_query):
    CENTER_LATITUDE = "34.070966"
    CENTER_LONGITUDE = "-118.445"
    RADIUS = "2000"
    # UCLA School of Theater, Film and Television is within radius of 700 
    # Hammer museum within 1300 radius
    # Saffron and rose 1800

    TextSearch_URL = 'https://maps.googleapis.com/maps/api/place/textsearch/json?'

    textSearch = TextSearch_URL + "query=" + place_query + "&location=" + CENTER_LATITUDE + "," + CENTER_LONGITUDE + "&radius=" + RADIUS + "&key=" + GOOGLE_API_KEY

    resultsPage = requests.get(textSearch)
    resultsJSON = json.loads(resultsPage.content)

    output = []
    for result in resultsJSON['results']:
      output.append({
          'name': result.get('name', "NO NAME"),
          'address': result.get('formatted_address', "NO ADDRESS"),
          'latitude': result['geometry']['location'].get('lat', "NO LATITUDE"),
          'longitude': result['geometry']['location'].get('lng', "NO LONGITUDE")
      })

    return jsonify({'results': output})
    # return jsonify({'results': resultsJSON})

# Run Google Maps NearbySearch on given query
@Locations.route('/api/place_nearbySearch/<place_query>', methods=['GET'])
def get_nearbysearch(place_query):
    CENTER_LATITUDE = "34.070966"
    CENTER_LONGITUDE = "-118.445"
    RADIUS = "2000"
    # UCLA School of Theater, Film and Television is within radius of 700 
    # Hammer museum within 1300 radius
    # Saffron and rose 1800

    NearbySearch_URL = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?'

    nearbySearch = NearbySearch_URL + "location=" + CENTER_LATITUDE + "," + CENTER_LONGITUDE + "&radius=" + RADIUS + "&keyword=" + place_query + "&key=" + GOOGLE_API_KEY

    resultsPage = requests.get(nearbySearch)
    resultsJSON = json.loads(resultsPage.content)

    output = []
    for result in resultsJSON['results']:
      output.append({
          'name': result.get('name', "NO NAME"),
          'address': result.get('vicinity', "NO ADDRESS"),
          'latitude': result['geometry']['location'].get('lat', "NO LATITUDE"),
          'longitude': result['geometry']['location'].get('lng', "NO LONGITUDE")
      })

    return jsonify({'results': output})
    # return jsonify({'results': resultsJSON})
