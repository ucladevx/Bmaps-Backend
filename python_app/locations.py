from flask import Flask, jsonify, request, json, Blueprint
from flask_cors import CORS, cross_origin
import pymongo
import json
import os

Locations = Blueprint('Locations', __name__)

# Enable Cross Origin Resource Sharing (CORS)
cors = CORS(Locations)

# Standard URI format: mongodb://[dbuser:dbpassword@]host:port/dbname
MLAB_USERNAME = os.getenv('MLAB_USERNAME')
MLAB_PASSWORD = os.getenv('MLAB_PASSWORD')

uri = 'mongodb://{0}:{1}@ds044709.mlab.com:44709/mappening_data'.format(MLAB_USERNAME, MLAB_PASSWORD)

# Set up database connection
client = pymongo.MongoClient(uri)
db = client['mappening_data'] 
# TODO CHANGE BACK
events_collection = db.map_events
total_events_collection = db.test_events
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
@Locations.route('/api/db_locations')
def db_locations():
    # Given JSON, update locations or insert new locations
    new_locations = find_locations()

    # Latitude and Longitude range from (-90, 90) and (-180, 180)
    INVALID_COORDINATE = 420
    
    # Get all db locations and put in another list
    # Or keep calling find and update

    for new_loc in new_locations:
        # Check if loc is in db
        single_loc = locations_collection.find_one(new_loc)
        if not single_loc:
            # Exact document not in db
            coord_loc = locations_collection.find_one({'latitude': new_loc.get('latitude', INVALID_COORDINATE), 'longitude': new_loc.get('longitude', INVALID_COORDINATE)})
            if coord_loc:
                # Location already in db but missing info
                # Merge new info with db document
                for key in new_loc:
                    if key not in coord_loc:
                        coord_loc[key] = new_loc[key]
                    if key == "name" and 'name' in coord_loc and coord_loc['name'] != new_loc['name']:
                        if new_loc['name'] not in coord_loc['alternative_names']:
                            coord_loc['alternative_names'].append(new_loc['name'])
                locations_collection.replace_one({'latitude': new_loc['latitude'], 'longitude': new_loc['longitude']}, coord_loc, True)
            else:
                # Insert new location to db
                locations_collection.insert_one(new_loc)
    return "Finished updating db!"

# Given address/name, return all possible matching places
@Locations.route('/api/map_locations')
def get_map_locations():
    # https://maps.googleapis.com/maps/api/place/textsearch/json?query=Bruin+Bear+UCLA&location=34.070966,-118.445&radius=500&key=AIzaSyCCyTRUan4gwknFSc70tN5xCT_HnFPadIc
    # https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=34.070966,-118.445&radius=500&keyword=Bruin+Bear+UCLA&key=AIzaSyCCyTRUan4gwknFSc70tN5xCT_HnFPadIc
    return "NO"
