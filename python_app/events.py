"""
Welcome to the Mappening Events API! Through this RESTful interface, we provide you with all the events happening around UCLA. The easiest way to use this is to simply go to the url `api.ucladevx.com/events <http://api.ucladevx.com/events>`_ and take all the events. See the explanation of events below. We offer many ways to search and filter these events through our api though you could do it yourself.

-----------------
Event Object
-----------------
An *event* object is a GeoJSON which means it has the following keys:

* geometry: with a type of "Point" and coordinates for latitude and longitude
* id: a unique id for this event
* properties: this contains all the event information and will be explored below

**Mandatory Event Properties**

These properties must have a valid value for every event.

* category: All the categories can be seen by dynamically calling /api/event-categories. About half of events have a category and the rest have <NONE>
* event_name: String of event's name
* stats: JSON for events from Facebook with attendance stats from at ~6 hour accuracy. Will have 4 keys 'attending', 'noreply', 'interested', and 'maybe' each with a integer value.
* start_time: String start time of event in the format Sat, 17 Feb 2018 23:30:00 GMT-0800
* is_cancelled: Boolean indicating event is cancelled

**Potential Event Properties**

If the actual event has no value, the value will be <NONE>. Make sure to check for none in your code to avoid errors.

* description: String description
* venue: A JSON with a location key with a mandatory country, city, latitude, and longitude. Other potential venue details such as name can be seen in the example event below
* cover_picture: A url to a photo for the event
* ticketing: A JSON with a single ticket_uri element with a url to the ticketing site or <NONE>
* end_time: String end time of event in the format Sat, 17 Feb 2018 23:30:00 GMT-0800
* free_food: If event has free food, currently just a strong NO

**Sample Event**::

    {
      "geometry": {
        "coordinates": [
          -118.451994,
          34.071474
        ],
        "type": "Point"
      },
      "id": "1766863560001661",
      "properties": {
        "category": "<NONE>",
        "cover_picture": "https://scontent.xx.fbcdn.net/v/t31.0-8/s720x720/27356375_1972757046097696_6206118120755555565_o.jpg?oh=2240b43f536e76f9cf00410f602af386&oe=5B136061",
        "description": "Hack on the Hill IV (HOTH) is a 12 hour, beginner-friendly hackathon designed to give beginners a glimpse into what a real hackathon would be and feel like. During HOTH, there are workshops, mentors, and amazing prizes for the best hacks. As a sequel to HOTH III, HOTH IV features double the attendance and hacking tracks hosted by different ACM committees. We are also excited to announce that we'll be providing select hardware for hacking as well! LEARN MORE AND SIGN-UP HERE (applications close 2/10 at midnight): https://hoth.splashthat.com/ Sponsored by IS Associates, a UCLA-sponsored organization that provides an educational forum for the management and understanding of information technology. Learn more at: https://isassociates.ucla.edu",
        "duplicate_occurrence": "NO",
        "end_time": "Sat, 17 Feb 2018 23:30:00 GMT-0800",
        "event_name": "ACM Hack | Hack on the Hill IV",
        "free_food": "NO",
        "hoster": {
          "id": "369769286554402",
          "name": "UCLA Class of 2020"
        },
        "is_cancelled": false,
        "start_time": "Sat, 17 Feb 2018 08:30:00 GMT-0800",
        "stats": {
          "attending": 97,
          "interested": 199,
          "maybe": 199,
          "noreply": 107
        },
        "ticketing": {
          "ticket_uri": "https://hoth.splashthat.com/"
        },
        "venue": {
          "id": "955967887795957",
          "location": {
            "city": "Los Angeles",
            "country": "United States",
            "latitude": 34.071474,
            "longitude": -118.451994,
            "state": "CA",
            "street": "330 De Neve Dr Ste L-16",
            "zip": "90024"
          },
          "name": "Carnesale Commons"
        }
      },
      "type": "Feature"
    }

-----------------
API DOCS
-----------------
"""
# Interacting with events collection in mlab

from flask import Flask, jsonify, request, json, Blueprint
from flask_cors import CORS, cross_origin
import pymongo
import re
import requests, urllib
import time, datetime, dateutil.parser
import event_caller
import json
import os
from tqdm import tqdm

Events = Blueprint('Events', __name__)

# Enable Cross Origin Resource Sharing (CORS)
cors = CORS(Events)

# Standard URI format: mongodb://[dbuser:dbpassword@]host:port/dbname
MLAB_USERNAME = os.getenv('MLAB_USERNAME')
MLAB_PASSWORD = os.getenv('MLAB_PASSWORD')

uri = 'mongodb://{0}:{1}@ds044709.mlab.com:44709/mappening_data'.format(MLAB_USERNAME, MLAB_PASSWORD)

# Set up database connection
client = pymongo.MongoClient(uri)
db = client['mappening_data']

events_collection = db.map_events
pages_collection = db.saved_pages
total_events_collection = db.events_ml

@Events.route('/api/events', methods=['GET'])
def get_all_events():
    """ 
    :Route: /api/events

    :Description: Returns a GeoJSON of all events within a a few miles of UCLA 

    """
    return find_events_in_database(print_results=True)

@Events.route('/api/search/<search_term>', methods=['GET'])
def get_events_today_for_search(search_term):
    """ 
    :Route: /api/search/<search_term>

    :Description: Returns JSON of events today that match search term in format that Mapbox likes 

    :param search_term: a string to use to find events that contain that word
    """
    output = []
    search_regex = re.compile('.*' + search_term + '.*', re.IGNORECASE)
    events_cursor = events_collection.find({'name': search_regex}) # put today in the search terms
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



@Events.route('/api/search/<search_term>/<date>', methods=['GET'])
def get_events_for_search(search_term, date):
    """
    :Route: /api/search/<search_term>/<date>

    :Description: Returns JSON of events on date that match search term in format that Mapbox likes 

    :param search_term: a string to use to find events that contain that word
    :param date: search in a certain date with raw date format or the following format -> 22 January 2018
    """
    date_regex_obj = construct_date_regex(date)
    output = []
    search_regex = re.compile('.*' + search_term + '.*', re.IGNORECASE)
    events_cursor = events_collection.find({'name': search_regex, 'start_time': date_regex_obj}) # put today in the search terms
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
        print("No event(s) matched '{0}'".format(search_term))
    return jsonify({'features': output, 'type': 'FeatureCollection'})


@Events.route('/api/event-name/<event_name>', methods=['GET'])
def get_event_by_name(event_name):
    """
    :Route: /api/event-name/<event_name>

    :Description: Returns JSON of singular event by event name

    :param event_name: string to match with event names
    """
    return find_events_in_database('name', event_name, True)

@Events.route('/api/event-id/<event_id>', methods=['GET'])
def get_event_by_id(event_id):
    """
    :Route: /api/event-id/<event_id>

    :Description: Returns JSON of singular event by event id

    :param event_id: value to match with event id's to find specific event

    """
    return find_events_in_database('id', event_id, True)

@Events.route('/api/event-date/<date>', methods=['GET'])
def get_events_by_date(date):
    """
    :Route: /api/event-date/<date>
    
    :Description: Returns JSON of all events starting on passed in date
    
    :param date: can search by date in multiple formats (ex. 22 January 2018)
    """
    date_regex_obj = construct_date_regex(date)
    if not date_regex_obj:
        return jsonify({'error': 'Invalid date string to be parsed.'})
    return find_events_in_database('start_time', date_regex_obj)

@Events.route('/api/event-categories-by-date/<date>', methods=['GET'])
def get_event_categories_by_date(date):
    """
    :Route: /api/event-categories-by-date/<date>
    
    :Description: Get cursor to all events on a certain day and get unique categories list for that day
    
    :param date: can search by date in multiple formats (ex. 22 January 2018)
    """
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
        print('Cannot find any events with categories!')
    return jsonify({'categories': output})

@Events.route('/api/events-by-category-and-date', methods=['GET'])
def get_events_by_category_and_date():
    """
    :Route: /api/events-by-category-and-date
    
    :Description: Returns JSON of events by event category starting on passed in date

    """
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
        print('Cannot find any events with matching category and date!')
    return jsonify({'features': output, 'type': 'FeatureCollection'})


@Events.route('/api/event-categories', methods=['GET'])
def get_event_categories():
    """
    :Route: /api/event-categories
    
    :Description: Returns JSON of all event categories used in all events. Potential Categories: Crafts, Art, Causes, Comedy, Dance, Drinks, Film, Fitness, Food, Games, Gardening, Health, Home, Literature, Music, Other, Party, Religion, Shopping, Sports, Theater, Wellness Conference, Lecture, Neighborhood, Networking

    """
    # Iterate through all events and get unique list of all categories
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
        print('Cannot find any events with categories!')
    return jsonify({'categories': output})


@Events.route('/api/event-category/<event_category>', methods=['GET'])
def get_events_by_category(event_category):
    """
    :Route: /api/event-category/<event_category>
        
    :Description: Returns JSON of currently existing event categories
    
    :param event_category: string to match with event categories
    """
    """

     Event category examples: food, THEATER
     use regexes to search in 'category', since both EVENT_TYPE and TYPE_EVENT string formats exist now
    """
    regex_str = '^{0}|{0}$'.format(event_category.upper())
    cat_regex_obj = re.compile(regex_str)
    return find_events_in_database('category', cat_regex_obj)


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
        print('Invalid date string, cannot be parsed!')
        return None

    # Get the date string by YYYY-MM-DD format
    time_str = datetime.datetime.strftime(time_obj, '%Y-%m-%d')

    date_regex_str = '^{0}.*'.format(time_str)
    date_regex_obj = re.compile(date_regex_str)
    return date_regex_obj

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
            print('No single event with attribute {0}: value {1}'.format(find_key, find_value))
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
            print('No events found with search pair {0}: {1}.'.format(find_key, find_value))
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
            'hoster': event.get('hoster', '<MISSING HOST>'),
            'start_time': processed_time(event.get('start_time', '<NONE>')),
            'end_time': processed_time(event.get('end_time', '<NONE>')),
            'venue': event['place'],
            'stats': {
                'attending': event['attending_count'],
                'noreply': event['noreply_count'],
                'interested': event['interested_count'],
                'maybe': event['maybe_count']
            },
            # TODO: whenever category is checked, run Jorge's online ML algorithm
            'category': event.get('category', '<NONE>'),
            'cover_picture': event['cover'].get('source', '<NONE>') if 'cover' in event else '<NONE>',
            'is_cancelled': event.get('is_canceled', False),
            'ticketing': {
                'ticket_uri': event.get('ticket_uri', '<NONE>')
            },
            'free_food': 'YES' if 'category' in event and 'FOOD' == event['category'] else 'NO',
            'duplicate_occurrence': 'YES' if 'duplicate_occurrence' in event else 'NO',
            'time_updated': event.get('time_updated', '<UNKNOWN TIME>')
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

# TODO: new endpoint to manually add Facebook page to DB
@Events.route('/api/add-page')
def add_page_to_database(type):
    """
    Call event_caller's add_facebook_page() to find the official info from Graph API,
    returns array of 1 or multiple results (if search), and add into existing data on DB IF not already there
    use URL parameters, either id= or name=, and optional type=page, group, or place if needed (default = group)
    """
    page_type = request.args.get('type', default='group', type=str)
    page_id = request.args.get('id', default='', type=str)
    page_exact_name = request.args.get('name', default='', type=str)
    if not page_id and not page_exact_name:
        return 'Add a page using URL parameters id or exact name, with optional type specified: group (default), page, place.'
    
    page_result = event_caller.add_facebook_page(page_type, page_id, page_exact_name)
    if 'error' in page_result:
        return page_result['error']

    found_same_page = pages_collection.find_one({'id': page_result['id']})

    # TODO
    return page_result

#     Now refresh pages we search separately, can be done way less frequently than event search

@Events.route('/api/refresh-page-database')
def refresh_page_database():
    # separately run from refreshing events, also check for new pages under set of search terms

    # update just like accumulated events list
    # remember: find() just returns a cursor, not whole data structure
    saved_pages = pages_collection.find()
    # returns a dict of IDs to names
    raw_page_data = event_caller.find_ucla_entities()

    # raw_page_data = {"test_id": "test_name"}

    # in contrast to raw_page_data, pages_collection is list of {"id": <id>, "name": <name>}
    for page_id, page_name in raw_page_data.iteritems():
        # See if event already existed
        update_page = pages_collection.find_one({'id': page_id})

        # If it existed then delete it, new event gets inserted in both cases
        if update_page:
            pages_collection.delete_one({'id': page_id})
        pages_collection.insert_one({'id': page_id, 'name': page_name})

    return 'Refreshed page database!'

@Events.route('/api/update-ucla-events')
def call_populate_events_database():
    # boolean doesn't work here: if clear parameter has any value, it is a string
    # all non-empty strings are true, so just take it as a string
    clear_old_db = request.args.get('clear', default='False', type=str)
    print(clear_old_db, type(clear_old_db))
    # could do .lower(), but only works for ASCII in Python 2...
    if clear_old_db == 'True' or clear_old_db == 'true':
        events_collection.delete_many({})

    earlier_day_bound = request.args.get('days', default=0, type=int)
    print(earlier_day_bound)
    return update_ucla_events_database(earlier_day_bound)

    
# Get all UCLA-related Facebook events and add to database
def update_ucla_events_database(earlier_day_bound=0):
    print('\n\n\n\n\n\n\n\n######\n\n######\n\n######\n\n')
    print('BEGIN POPULATING EVENTS DATABASE')
    print('\n\n######\n\n######\n\n######\n\n\n\n\n\n\n')
    # Location of Bruin Bear
    # current_events = get_facebook_events(34.070964, -118.444757)
    # take out all current events from DB, put into list, check for updates
    processed_db_events = event_caller.update_current_events(list(events_collection.find()), earlier_day_bound)

    # actually update all in database, but without mass deletion (for safety)
    for old_event in tqdm(events_collection.find()):
        event_id = old_event['id']
        updated_event = processed_db_events.get(event_id)
        # if event should be kept and updated
        if updated_event:
            events_collection.delete_one({'id': event_id})
            events_collection.insert_one(updated_event)
        # event's time has passed, according to update_current_events
        else:
            events_collection.delete_one({'id': event_id})

    new_events_data = event_caller.get_facebook_events(earlier_day_bound)
    # debugging events output
    # with open('events_out.json', 'w') as outfile:
    #     json.dump(new_events_data, outfile, sort_keys=True, indent=4, separators=(',', ': '))

    # Also add all new events to total_events

    # .find() returns a CURSOR, like an iterator (NOT a list or dictionary)
    # conclusion after running some small timed tests: for our purposes and with our data sizes,
    # INCREMENTAL DB calls (iterate over .find()) and BATCH DB calls (list(.find())) take about the same time
    # normally use incremental Cursor, to save memory usage
    new_count = 0
    for event in tqdm(new_events_data['events']):
        curr_id = event['id']
        existing_event = processed_db_events.get(curr_id)

        # sidenote: when event inserted into DB,
        # the event dict has _id key appended to itself both remotely (onto DB) and LOCALLY!

        # don't need to do anything if event found previously, since updated in update_current_events()
        if existing_event:
            continue
        events_collection.insert_one(event)
        new_count += 1

        # below = UPDATE: pymongo only allows update of specifically listed attributes in a dictionary...
        # so delete old if exists, then insert new

        # See if event already existed
        update_event = total_events_collection.find_one({'id': curr_id})

        # If it existed then delete it, new event gets inserted either way
        if update_event:
            total_events_collection.delete_one({'id': curr_id})
        total_events_collection.insert_one(event)

    return 'Updated with {0} retrieved events, {1} new ones.'.format(new_events_data['metadata']['events'], new_count)

@Events.route('/api/test-code-update')
def test_code_update():
    return 'LNY'

def clean_collection(collection):
    """
    simply save each unique document and delete any that have been found already
    """
  
    # a set, not a dict
    unique_ids = set()
    dups = []
    # IMPORTANT: do not take down _id, jsonify can't handle type
    for item in collection.find({}, {'_id': False}):
        # assume all items must have a unique id key-value pair
        curr_id = item['id']
        if curr_id in unique_ids:
            dups.append(item)
            collection.delete_many({'id': curr_id})
        else:
            unique_ids.add(curr_id)
    return dups

#    if needed, clean database of duplicate documents
@Events.route('/api/remove-duplicates', methods=['GET'])
def remove_db_duplicates():
    total_dups = []
    # difference between append and extend: extend flattens out lists to add elements, append adds 1 element
    total_dups.extend(clean_collection(events_collection))
    total_dups.extend(clean_collection(pages_collection))
    total_dups.extend(clean_collection(total_events_collection))
    return jsonify(total_dups)
