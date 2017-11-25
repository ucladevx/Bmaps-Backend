# Interacting with events collection in mlab
# TODO: hide app id/secret

from flask import Flask, jsonify, request, json, Blueprint
from flask_cors import CORS, cross_origin
import pymongo
import re
import requests, urllib
import time, datetime
import event_caller

Events = Blueprint('Events', __name__)

# Enable Cross Origin Resource Sharing (CORS)
cors = CORS(Events)

# Got APP_ID and APP_SECRET from Mappening app with developers.facebook.com
FACEBOOK_APP_ID = '353855031743097'
FACEBOOK_APP_SECRET = '2831879e276d90955f3aafe0627d3673'

MLAB_USERNAME = 'devx_dora'
MLAB_PASSWORD = '3map5me'
# Standard URI format: mongodb://[dbuser:dbpassword@]host:port/dbname
uri = 'mongodb://{0}:{1}@ds044709.mlab.com:44709/mappening_data'.format(MLAB_USERNAME, MLAB_PASSWORD)

# Set up database connection
client = pymongo.MongoClient(uri)
db = client['mappening_data'] 
events_collection = db.map_events

"""
CHANGES
when search for category, just put actual name ('EVENT' not needed)
everything calls find_events_in_database, giving search terms and options if needed
HEADS UP: make sure special Unicode characters handled!

in processing data from database (process_event_info):
'venue' is now 'place' and has less info: name, id, and location
'attendance' --> 'stats' contains attending, noreply, interested, and maybe (removed declined)
'end_time' may not be set
'is_canceled' may return False boolean value
defaults set by using dict.get(key, default value), returns None (null) if no default value given
"""

# Returns JSON of all events in format that Mapbox likes
@Events.route('/api/events', methods=['GET'])
def get_all_events():
    return find_events_in_database(print_results=True)
    """
    output = []
    for event in events_collection.find():
      print ("Event: " + event["name"].encode('ascii', 'ignore'))
      output.append({
        'id': event['id'],
        'type': 'Feature',
        'geometry': {
            'coordinates': [
                event['place']['location']['longitude'],
                event['place']['location']['latitude']
            ],
            'type': 'Point'
        },
        'properties': {
            'event_name': event['name'], 
            'description': event['description'],
            'start_time': event['startTime'],
            'end_time': event['endTime'],
            'venue': event['place'],
            'stats': event['stats'],
            'category': event['category'],
            'cover_picture': event['coverPicture'],
            'is_cancelled': event['isCancelled'],
            'ticketing': event['ticketing'] if 'ticketing' in event else "None",
            'free_food': 'YES' if event['category'] == 'EVENT_FOOD' else 'No'
        }
      })
    return jsonify({'features': output, 'type': 'FeatureCollection'})
    """

# Returns JSON of matching event names
@Events.route('/api/search/<search_term>', methods=['GET'])
def get_events_for_search(search_term):
    output = []
    search_regex = re.compile('.*' + search_term + '.*', re.IGNORECASE)
    events_cursor = events_collection.find({'name': search_regex})
    if events_cursor.count() > 0:
        for event in events_cursor:
          output.append({'event_name': event['name']})
    else:
        output = "No event(s) matched '{}'".format(search_term)
    return jsonify(output)

# Returns JSON of singular event by event name
# /<> defaults to strings without any slashes
@Events.route('/api/event-name/<event_name>', methods=['GET'])
def get_event_by_name(event_name):
    return find_events_in_database('name', event_name, True)
    """
    output = []
    event = events_collection.find_one({'name': event_name})
    if event:
      output.append({
        'id': event['id'],
        'type': 'Feature',
        'geometry': {
            'coordinates': [
                event['place']['location']['longitude'],
                event['place']['location']['latitude']
            ],
            'type': 'Point'
        },
        'properties': {
            'event_name': event['name'], 
            'description': event['description'],
            'start_time': event['startTime'],
            'end_time': event['endTime'],
            'venue': event['place'],
            'stats': event['stats'],
            'category': event['category'],
            'cover_picture': event['coverPicture'],
            'is_cancelled': event['isCancelled'],
            'ticketing': event['ticketing'] if 'ticketing' in event else "None",
            'free_food': 'YES' if event['category'] == 'EVENT_FOOD' else 'No'
        }
      })
    else:
      return "No event of name '{}'".format(event_name)
    return jsonify({'features': output, 'type': 'FeatureCollection'})
    """

# Returns JSON of singular event by event id
@Events.route('/api/event-id/<event_id>', methods=['GET'])
def get_event_by_id(event_id):
    return find_events_in_database('id', event_id, True)
    """
    output = []
    event = events_collection.find_one({'id': event_id})
    if event:
      output.append({
        'id': event['id'],
        'type': 'Feature',
        'geometry': {
            'coordinates': [
                event['place']['location']['longitude'],
                event['place']['location']['latitude']
            ],
            'type': 'Point'
        },
        'properties': {
            'event_name': event['name'], 
            'description': event['description'],
            'start_time': event['startTime'],
            'end_time': event['endTime'],
            'venue': event['place'],
            'stats': event['stats'],
            'category': event['category'],
            'cover_picture': event['coverPicture'],
            'is_cancelled': event['isCancelled'],
            'ticketing': event['ticketing'] if 'ticketing' in event else "None",
            'free_food': 'YES' if event['category'] == 'EVENT_FOOD' else 'No'
        }
      })
    else:
      return "No event of id '{}'".format(event_id)
    return jsonify({'features': output, 'type': 'FeatureCollection'})
    """

# Returns JSON of events by event category
# Event category examples: food, THEATER
# use regexes to search in 'category', since both EVENT_TYPE and TYPE_EVENT string formats exist now
@Events.route('/api/event-category/<event_category>', methods=['GET'])
def get_event_by_category(event_category):
    regex_str = '^{0}|{0}$'.format(event_category.upper())
    cat_regex_obj = re.compile(regex_str)
    return find_events_in_database('category', cat_regex_obj)
    """
    output = []
    events_cursor = events_collection.find({'category': event_category})
    if events_cursor.count() > 0:
        for event in events_cursor:
          output.append({
            'id': event['id'],
            'type': 'Feature',
            'geometry': {
                'coordinates': [
                    event['place']['location']['longitude'],
                    event['place']['location']['latitude']
                ],
                'type': 'Point'
            },
            'properties': {
                'event_name': event['name'], 
                'description': event['description'],
                'start_time': event['startTime'],
                'end_time': event['endTime'],
                'venue': event['place'],
                'stats': event['stats'],
                'category': event['category'],
                'cover_picture': event['coverPicture'],
                'is_cancelled': event['isCancelled'],
                'ticketing': event['ticketing'] if 'ticketing' in event else "None",
                'free_food': 'YES' if event['category'] == 'EVENT_FOOD' else 'No'
            }
          })
    else:
        return "No event(s) of category '{}'".format(event_category)
    return jsonify({'features': output, 'type': 'FeatureCollection'})
    """

# Returns JSON of events with free food
@Events.route('/api/event-food', methods=['GET'])
def get_event_by_food():
    return get_event_by_category('food')
    """
    output = []
    events_cursor = events_collection.find({'category': 'EVENT_FOOD'})
    if events_cursor.count() > 0:
        for event in events_cursor:
          output.append({
            'id': event['id'],
            'type': 'Feature',
            'geometry': {
                'coordinates': [
                    event['venue']['location']['longitude'],
                    event['venue']['location']['latitude']
                ],
                'type': 'Point'
            },
            'properties': {
                'event_name': event['name'], 
                'description': event['description'],
                'start_time': event['startTime'],
                'end_time': event['endTime'],
                'venue': event['venue'],
                'stats': event['stats'],
                'category': event['category'],
                'cover_picture': event['coverPicture'],
                'is_cancelled': event['isCancelled'],
                'ticketing': event['ticketing'] if 'ticketing' in event else "None",
                'free_food': 'YES' if event['category'] == 'EVENT_FOOD' else 'No'
            }
          })
    else:
        return "No event(s) with free food"
    return jsonify({'features': output, 'type': 'FeatureCollection'})
    """

# find_key / value = search strings, can pass in REGEX objects for find_value (using re.compile)
def find_events_in_database(find_key='', find_value='', one_result_expected=False, print_results=False):
    output = []
    # for getting all events, no search query needed (empty dict)
    search_pair = {}
    if find_key and find_value:
        search_pair[find_key] = find_value

    if one_result_expected:
        single_event = events_collection.find_one(search_pair)
        if single_event:
            output.append(process_event_info(single_event))
            if print_results:
                print(u'Event: {0}'.format(single_event.get('name', '<No Name>')))
        else:
            return 'Cannot find single event with attribute {0}: value {1}'.format(find_key, find_value)
    else:
        events_cursor = events_collection.find(search_pair)
        if events_cursor.count() > 0:
            for event in events_cursor:
                output.append(process_event_info(event))
                if print_results:
                    # Python 2 sucks
                    # event['name'] returns unicode string
                    # to use with format(), another unicode string must be parent
                    # unicode strings have 'u' in the front, as below
                    # THEN: make sure Docker container locale / environment variable set, so print() itself works!!!!
                    print(u'Event: {0}'.format(event.get('name', '<No Name>')))
        else:
            return 'Cannot find multiple events with attribute {0}: value {1}'.format(find_key, find_value)
    return jsonify({'features': output, 'type': 'FeatureCollection'})

def process_event_info(event):
    formatted_info = {
        # will ALWAYS have an ID
        'id': event['id'],
        'type': 'Feature',
        'geometry': {
            # no coordinates? default to Bruin Bear
            'coordinates': [
                event['place']['location'].get('longitude', event_caller.CENTER_LONGITUDE),
                event['place']['location'].get('latitude', event_caller.CENTER_LATITUDE)
            ],
            'type': 'Point'
        },
        'properties': {
            'event_name': event.get('name', '<No Name>'), 
            'description': event.get('description', '<No Description>'),
            'start_time': event.get('start_time', '<Unknown Start Time>'),
            'end_time': event.get('end_time', '<No End Time>'),
            'venue': event['place'],
            'stats': {
                'attending': event['attending_count'],
                'noreply': event['noreply_count'],
                'interested': event['interested_count'],
                'maybe': event['maybe_count']
            },    
            'category': event.get('category', '<No Category Chosen>'),
            'cover_picture': event['cover'].get('source', '<No Cover Image>') if 'cover' in event else '<No Cover Info>',
            'is_cancelled': event.get('is_canceled', False),
            'ticketing': {
                'ticket_uri': event.get('ticket_uri', '<No Ticketing Link>')
            },
            'free_food': 'YES' if 'category' in event and 'FOOD' in event['category'] else 'NO'
        }
    }
    return formatted_info

# Get all UCLA-related Facebook events and add to database
@Events.route('/api/populate-ucla-events-database')
def populate_ucla_events_database():
    # Location of Bruin Bear
    # current_events = get_facebook_events(34.070964, -118.444757)

    # DUMB WAY to refresh database: delete all data, then insert all new
    # TODO: update data already there, insert new, delete leftover data (not in new events)
    delete_result = events_collection.delete_many({})

    raw_events_data = event_caller.get_facebook_events()
    # debugging events output
    # with open('new_out.json', 'w') as outfile:
    #     json.dump(current_events, outfile, sort_keys=True, indent=4, separators=(',', ': '))

    # metadata block has total event count
    # insert_many takes in array of dictionaries
    # process and format events before inserting database
    if raw_events_data['metadata']['events'] > 0:
        events_collection.insert_many(raw_events_data['events'])
    else:
        return 'No new events to save!'
    return 'Populated events database!'

"""
# DEPRECATED
# Can also access fb events this way
# http://localhost:3000/events?
# lat=40.710803
# &lng=-73.964040
# &distance=100
# &sort=venue
# &accessToken=353855031743097|2831879e276d90955f3aafe0627d3673

# Gets Facebook App access token using App ID and Secret
def get_facebook_events(latitude, longitude):
    token_args = {'client_id': FACEBOOK_APP_ID, 'client_secret': FACEBOOK_APP_SECRET, 'grant_type': 'client_credentials'}
    resp = requests.get('https://graph.facebook.com/oauth/access_token', token_args)
    if resp.status_code != 200:
        print('Error in getting access code! Status code {}'.format(resp.status_code))
        return []
    app_access_token = resp.json()['access_token']
    print('APP ACCESS TOKEN {}'.format(app_access_token))

    # URL call to endpoint set up by server from 
    # https://github.com/tobilg/facebook-events-by-location
    baseurl = 'http://fb_events:3000/events?'

    # Location
    fb_latitude = latitude
    fb_longitude = longitude

    # Going back and forward in days using seconds
    seconds_in_day = 86400
    now_time = time.mktime(datetime.datetime.now().timetuple())
    start_t = now_time
    end_t = now_time + seconds_in_day

    # Sort by some number, options: time, distance, venue, popularity
    sort_type = 'time'

    event_args = dict(  accessToken = app_access_token,
                        lat         = latitude,
                        lng         = longitude,
                        since       = start_t,
                        until       = end_t,
                        sort        = sort_type,
                        distance    = 1 )

    fb_url = baseurl + urllib.urlencode(event_args)
    print(fb_url)

    response = urllib.urlopen(fb_url)
    print(type(response))
    data = json.loads(response.read())
    print(data)

    return data['events']
"""