from mappening.utils.database import unknown_locations_collection, API_unknown_locations_collection, API_TODO_locations_collection, locations_collection # , events_ml_collection
from mappening.api.utils import location_utils, tokenizer

import requests
import re
import json
import os
from operator import itemgetter

# Must be on same level as app.py
data = json.load(open('sampleData.json'))

# TEST

# Use ucla tkinter GUI to process tkinter_UCLA_locations
# Use function to run through locations api and add to tkinter_unknown_locations
# Use unknown tkinter GUI to verify correctness of results
def process_unknown_locations():
  num_assigned = 0
  num_unassigned = 0
  counter = 1

  locs_cursor = unknown_locations_collection.find({})
  if locs_cursor.count() > 0:
    for loc_db in locs_cursor:
      if API_unknown_locations_collection.find_one({'_id': loc_db['_id']}):
        print("Already in db")
      else:
        print("~~~~~~~ " + str(counter) + " ~~~~~~~" + " WR: " + str(num_unassigned))
        counter = counter + 1
        if 'location_name' in loc_db:
          loc_result = get_location_search_result(loc_db['location_name'])
          if loc_result != "There were no results!":
            print("Found a match!")
            num_assigned = num_assigned + 1
            API_unknown_locations_collection.insert_one({
              "unknown_loc": {
                "loc_name": loc_db.get('location_name', "NO LOCATION NAME"),
                "event_name": loc_db.get('event_name', "NO EVENT NAME")
              },
              "db_loc": {
                "loc_name": loc_result['name'],
                "loc_alt_names": loc_result['alternative_names'],
                "loc_latitude": loc_result['latitude'],
                "loc_longitude": loc_result['longitude'],
                "map_url": "https://www.google.com/maps/place/" + str(loc_result['latitude']) + "," + str(loc_result['longitude'])
              }
            }) 
          else:
            print("Didn't find a location!")
            num_unassigned = num_unassigned + 1
            API_TODO_locations_collection.insert_one({
              "unknown_loc": {
                "loc_name": loc_db.get('location_name', "NO LOCATION NAME"),
                "event_name": loc_db.get('event_name', "NO EVENT NAME")
              },
              "db_loc": {}
            }) 
   else:
       print('Cannot find any unknown locations!')
 
  print("num_assigned: " + str(num_assigned))
  print("num_unassigned: " + str(num_unassigned))
  return "Added unknown locations to database\n"

# Go through events_ml_collection and run every location name through locations api
# See if resulting coordinates match the supplied location data from the event
# Manually verify/resolve any conflicting results
def test_location_search():
  num_correct = 0
  num_wrong = 0
  num_invalid = 0
  wrong_locs = []
  counter = 1

  # events_cursor = events_ml_collection.find({}, {'_id': False})
  events_cursor = events_test_collection.find({}, {'_id': False})
  if events_cursor.count() > 0:
    for event in events_cursor:
      print("~~~~~~~ " + str(counter) + " ~~~~~~~" + " WR: " + str(num_wrong))
      counter = counter + 1
      if 'place' in event and 'location' in event['place']:
        loc = get_location_search_result(event['place']['name'])
        if loc != "There were no results!":
          # Latitude and longitude are significant to the 4th digit, but 3rd to be safe
          event_lat = event['place']['location'].get('latitude', 420)
          event_long = event['place']['location'].get('longitude', 420)
          lat_diff = abs(loc['latitude'] - event_lat)
          long_diff = abs(loc['longitude'] - event_long)
          if lat_diff < 0.0015 and long_diff < 0.0015:
            print("Correct")
            num_correct = num_correct + 1
          else:
            print("Wrong")
            num_wrong = num_wrong + 1
            wrong_locs.append({
              "event": {
                "place_name": event['place']['name'], 
                "place_latitude": event['place']['location'].get('latitude', 420),
                "place_longitude": event['place']['location'].get('longitude', 420)
              },
              "loc": {
                "loc_name": loc['name'],
                "loc_alt_names": loc['alternative_names'],
                "loc_latitude": loc['latitude'],
                "loc_longitude": loc['longitude']
              }
            }) 
        else:
          print("Invalid Loc")
          num_invalid = num_invalid + 1
          wrong_locs.append({
              "event": {
                "place_name": event['place']['name'], 
                "place_latitude": event['place']['location'].get('latitude', 420),
                "place_longitude": event['place']['location'].get('longitude', 420)
              },
              "loc": "NONE"
            }) 
  else:
      print('Cannot find any events!')

  # Output typically contains name, city, country, latitude, longitude, state, 
  # street, and zip for each location
  return jsonify({'num_correct': num_correct, 'num_wrong': num_wrong, 'num_invalid': num_invalid, 'wrong_locs': wrong_locs})

# JSON Handling

# Given JSON add tokenized versions of alternate names to alternate names list
# See sample format in ./sampleData.json
def tokenize_names():
  places = []
  updated = False

  # Go through every location in json
  for location in data['locations']:
    place = location
    if 'alternative_names' in place['location']:
      for alt_name in place['location']['alternative_names']:
        processed_name = tokenizer.tokenize_text(alt_name)
        if processed_name not in (name.lower() for name in place['location']['alternative_names']):
          if processed_name:
            place['location']['alternative_names'].append(processed_name)
            updated = True
      if updated:
        places.append(place)
        updated = False

  return jsonify({"locations": places})

# Given JSON add alternate names with "UCLA" stripped to alternate names list
# See sample format in ./sampleData.json
def remove_ucla_from_names():
  places = []
  loc_counter = 1

  # Go through every location in json
  for location in data['locations']:
    loc_counter = loc_counter + 1
    place = location
    if 'alternative_names' in place['location']:
      for alt_name in place['location']['alternative_names']:
        processed_name = re.sub(r'\bUCLA\s?', '', alt_name, flags=re.IGNORECASE)
        processed_name = processed_name.strip()
        if processed_name.lower() not in (name.lower() for name in place['location']['alternative_names']):
          if processed_name:
            place['location']['alternative_names'].append(processed_name)
      places.append(place)

  return jsonify({"locations": places})

# Given JSON insert all locations to the locations database
# See sample format in ./sampleData.json
# TODO: don't add duplicates
def insert_locations_from_json():
  locations_collection.insert_many(data['locations'])
  return "Successfully inserted location documents to db!"

# Given JSON, fill out any missing location data using the Google Places API
# Tries to fill out street/zip/latitude/longitude
# Takes top result to fill out info, MAY BE INCORRECT
# See sample format in ./sampleData.json
def fill_location_data():
  places = []
  updated_places = []
  updated = False

  # Go through every location in json
  for location in data['locations']:
    place = location
    # Add stripped down name to alternative_names
    if 'name' in location['location']:
      processed_place = tokenizer.tokenize_text(location['location']['name'])
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

