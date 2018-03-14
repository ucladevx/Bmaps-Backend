from mappening.utils.database import ucla_events_collection, events_ml_collection
import event_caller


from flask import jsonify
import time, datetime, dateutil.parser
from tqdm import tqdm   # a progress bar, pretty
import json
import os
import re

def find_events_in_database(find_key='', find_value='', one_result_expected=False, print_results=False):
    output = []
    # for getting all events, no search query needed (empty dict)
    search_pair = {}
    if find_key and find_value:
        search_pair[find_key] = find_value

    if one_result_expected:
        single_event = ucla_events_collection.find_one(search_pair)
        if single_event:
            output.append(process_event_info(single_event))
            if print_results:
                print(u'Event: {0}'.format(single_event.get('name', '<NONE>')))
        else:
            # careful: output is still empty here; make sure output list never set ANYWHERE else
            # i.e. no other conditional branch is entered after this one, same with multiple event case below
            print('No single event with attribute {0}: value {1}'.format(find_key, find_value))
    else:
        events_cursor = ucla_events_collection.find(search_pair)
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

def call_populate_events_database():
    # boolean doesn't work here: if clear parameter has any value, it is a string
    # all non-empty strings are true, so just take it as a string
    clear_old_db = request.args.get('clear', default='False', type=str)
    print(clear_old_db, type(clear_old_db))
    # could do .lower(), but only works for ASCII in Python 2...
    if clear_old_db == 'True' or clear_old_db == 'true':
        ucla_events_collection.delete_many({})

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
    processed_db_events = event_caller.update_current_events(list(ucla_events_collection.find()), earlier_day_bound)

    # actually update all in database, but without mass deletion (for safety)
    for old_event in tqdm(ucla_events_collection.find()):
        event_id = old_event['id']
        updated_event = processed_db_events.get(event_id)
        # if event should be kept and updated
        if updated_event:
            ucla_events_collection.delete_one({'id': event_id})
            ucla_events_collection.insert_one(updated_event)
        # event's time has passed, according to update_current_events
        else:
            ucla_events_collection.delete_one({'id': event_id})

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
        ucla_events_collection.insert_one(event)
        new_count += 1

        # below = UPDATE: pymongo only allows update of specifically listed attributes in a dictionary...
        # so delete old if exists, then insert new

        # See if event already existed
        update_event = events_ml_collection.find_one({'id': curr_id})

        # If it existed then delete it, new event gets inserted either way
        if update_event:
            events_ml_collection.delete_one({'id': curr_id})
        events_ml_collection.insert_one(event)

    return 'Updated with {0} retrieved events, {1} new ones.'.format(new_events_data['metadata']['events'], new_count)

