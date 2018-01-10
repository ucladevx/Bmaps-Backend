# Interacting with events collection in mlab
# TODO: hide app id/secret

from flask import Flask, jsonify, request, json, Blueprint
from flask_cors import CORS, cross_origin
import pymongo
import re
import requests, urllib
import time, datetime, dateutil.parser
import event_caller
import json

data = json.load(open('secrets.json'))

Events = Blueprint('Events', __name__)

# Enable Cross Origin Resource Sharing (CORS)
cors = CORS(Events)

# Got APP_ID and APP_SECRET from Mappening app with developers.facebook.com
FACEBOOK_APP_ID = data['FACEBOOK_APP_ID']
FACEBOOK_APP_SECRET = data['FACEBOOK_APP_SECRET']

# Standard URI format: mongodb://[dbuser:dbpassword@]host:port/dbname
MLAB_USERNAME = data['MLAB_USERNAME']
MLAB_PASSWORD = data['MLAB_PASSWORD']

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

# Returns JSON of matching event names
@Events.route('/api/search/<search_term>', methods=['GET'])
def get_events_for_search(search_term):
    output = []
    search_regex = re.compile('.*' + search_term + '.*', re.IGNORECASE)
    events_cursor = events_collection.find({'name': search_regex})
    if events_cursor.count() > 0:
        for event in events_cursor:
          output.append({
            'id': event['id'],
            'type': 'Feature',
            'geometry': {
                # Default to Bruin Bear coordinates
                'coordinates': [
                    event['place']['location'].get('longitude', event_caller.CENTER_LONGITUDE),
                    event['place']['location'].get('latitude', event_caller.CENTER_LATITUDE)
                ],
                'type': 'Point'
            },
            'properties': {
                'event_name': event.get('name', '<NONE>'), 
                'description': event.get('description', '<NONE>'),
                'start_time': processed_time(event.get('start_time', '<NONE>')),
                'end_time': processed_time(event.get('end_time', '<NONE>')),
                'venue': event['place'],
                'cover_picture': event['cover'].get('source', '<NONE>') if 'cover' in event else '<NONE>',
                'category': event.get('category', '<NONE>'),
            }})
    else:
        print "No event(s) matched '{}'".format(search_term)
    return jsonify({'features': output, 'type': 'FeatureCollection'})

# Returns JSON of singular event by event name
# /<> defaults to strings without any slashes
@Events.route('/api/event-name/<event_name>', methods=['GET'])
def get_event_by_name(event_name):
    return find_events_in_database('name', event_name, True)

# Returns JSON of singular event by event id
@Events.route('/api/event-id/<event_id>', methods=['GET'])
def get_event_by_id(event_id):
    return find_events_in_database('id', event_id, True)

# Returns JSON of events by event date
# Returns all events starting on the passed in date
@Events.route('/api/event-date/<date>', methods=['GET'])
def get_events_by_date(date):
    date_regex_obj = construct_date_regex(date)
    if not date_regex_obj:
        return jsonify({'error': 'Invalid date string to be parsed.'})
    return find_events_in_database('start_time', date_regex_obj)

# Returns JSON of events by event category & date
@Events.route('/api/event-categories-by-date/<date>', methods=['GET'])
def get_event_categories_by_date(date):
    # Get cursor to all events on a certain day and get unique categories list
    # Iterate through all events and get unique list of all categories
    uniqueList = []
    output = []

    date_regex_obj = construct_date_regex(date)
    if not date_regex_obj:
        return jsonify({'error': 'Invalid date string to be parsed.'})
    
    events_cursor = events_collection.find({"category": {"$exists": True}, "start_time": date_regex_obj})
    if events_cursor.count() > 0:
        for event in events_cursor:
            if event["category"].title() not in uniqueList:
                uniqueList.append(event["category"].title())
        for category in uniqueList:
            output.append({"category": category})
    else:
        print 'Cannot find any events with categories!'
    return jsonify({'categories': output})

# Returns JSON of events by event category & date
@Events.route('/api/events-by-category-and-date', methods=['GET'])
def get_events_by_category_and_date():
    date = request.args['date']
    event_category = request.args['category']

    # Get cursor to all events on a certain day and of a certain category
    output = []

    date_regex_obj = construct_date_regex(date)
    if not date_regex_obj:
        return jsonify({'error': 'Invalid date string to be parsed.'})

    # Handle event category
    regex_str = '^{0}|{0}$'.format(event_category.upper())
    cat_regex_obj = re.compile(regex_str)
    
    events_cursor = events_collection.find({"category": cat_regex_obj, "start_time": date_regex_obj})
    if events_cursor.count() > 0:
        for event in events_cursor:
            output.append(process_event_info(event))
    else:
        print 'Cannot find any events with matching category and date!'
    return jsonify({'features': output, 'type': 'FeatureCollection'})

# Returns JSON of events by event category
# Potential event categories: Crafts, Art, Causes, Comedy, Dance, Drinks, Film,
# Fitness, Food, Games, Gardening, Health, Home, Literature, Music, Other, 
# Party, Religion, Shopping, Sports, Theater, Wellness
@Events.route('/api/event-categories', methods=['GET'])
def get_event_categories():
    # Iterate through all events and get unique list of all categories
    # TODO: sort by quantity?
    uniqueList = []
    output = []
    
    events_cursor = events_collection.find({"category": {"$exists": True}})
    if events_cursor.count() > 0:
        for event in events_cursor:
            if event["category"].title() not in uniqueList:
                uniqueList.append(event["category"].title())
        for category in uniqueList:
            output.append({"category": category})
    else:
        print 'Cannot find any events with categories!'
    return jsonify({'categories': output})

# Returns JSON of currently existing event categories
# Event category examples: food, THEATER
# use regexes to search in 'category', since both EVENT_TYPE and TYPE_EVENT string formats exist now
@Events.route('/api/event-category/<event_category>', methods=['GET'])
def get_events_by_category(event_category):
    regex_str = '^{0}|{0}$'.format(event_category.upper())
    cat_regex_obj = re.compile(regex_str)
    return find_events_in_database('category', cat_regex_obj)

# Returns JSON of events with free food
@Events.route('/api/event-food', methods=['GET'])
def get_events_by_food():
    return get_event_by_category('food')

def construct_date_regex(raw_date):
    # Try to parse date
    try:
        # Use dateutil parser to get time zone
        time_obj = dateutil.parser.parse(raw_date)
    except ValueError:
        # Got invalid date string
        print 'Invalid date string, cannot be parsed!'
        return None

    # Get the date string by YYYY-MM-DD format
    time_str = datetime.datetime.strftime(time_obj, '%Y-%m-%d')

    date_regex_str = '^{0}.*'.format(time_str)
    date_regex_obj = re.compile(date_regex_str)
    return date_regex_obj

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
                print(u'Event: {0}'.format(single_event.get('name', '<NONE>')))
        else:
            # careful: output is still empty here; make sure output list never set ANYWHERE else
            # i.e. no other conditional branch is entered after this one, same with multiple event case below
            print 'No single event with attribute {0}: value {1}'.format(find_key, find_value)
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
                    print(u'Event: {0}'.format(event.get('name', '<NONE>')))
        else:
            print 'No events found with search pair {0}: {1}.'.format(find_key, find_value)
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
            'event_name': event.get('name', '<NONE>'), 
            'description': event.get('description', '<NONE>'),
            'start_time': processed_time(event.get('start_time', '<NONE>')),
            'end_time': processed_time(event.get('end_time', '<NONE>')),
            'venue': event['place'],
            'stats': {
                'attending': event['attending_count'],
                'noreply': event['noreply_count'],
                'interested': event['interested_count'],
                'maybe': event['maybe_count']
            },
            'category': event.get('category', '<NONE>'),
            'cover_picture': event['cover'].get('source', '<NONE>') if 'cover' in event else '<NONE>',
            'is_cancelled': event.get('is_canceled', False),
            'ticketing': {
                'ticket_uri': event.get('ticket_uri', '<NONE>')
            },
            'free_food': 'YES' if 'category' in event and 'FOOD' == event['category'] else 'NO'
        }
    }
    return formatted_info

def processed_time(old_time_str):
    # if not valid time string, return default value from dict.get()
    try:
        # use dateutil parser to get time zone
        time_obj = dateutil.parser.parse(old_time_str)
    except ValueError:
        return old_time_str
    # Formatting according to date.parse() requirements
    # time zone offset always off of GMT
    res_time_str = datetime.datetime.strftime(time_obj, '%a, %d %b %Y %H:%M:%S GMT%z')
    return res_time_str

# Get all UCLA-related Facebook events and add to database
@Events.route('/api/populate-ucla-events-database')
def populate_ucla_events_database():
    print('Call to populate database with events.')
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
