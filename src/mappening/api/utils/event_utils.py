# TODO: merge events_fb and events_ml to just events_fb, with all the ML events
from mappening.utils.database import events_fb_collection, events_eventbrite_collection, events_test_collection, fb_pages_saved_collection
from mappening.utils.database import events_current_processed_collection
import event_caller

from flask import jsonify
import time, datetime, dateutil.parser
from tqdm import tqdm   # a progress bar, pretty
import json
import os
import re

# each website source has its own database, where raw event info is stored
all_collections = {
    'eventbrite': events_eventbrite_collection,
    'facebook': events_fb_collection,
    'test': events_test_collection
}

def get_month(month):
    try:
        month = int(month)
    except:
        return None
        
    if 1 <= month <= 12:
        return "{0:0=2d}".format(month)
    else:
        return None

# If needed, clean database of duplicate documents
def remove_db_duplicates(changed_collection):
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

    print('Removed {0} duplicates.'.format(len(dups)))
    return dups

def find_events_in_database(find_dict={}, one_result_expected=False, print_results=False):
    output = get_events_in_database(find_dict, one_result_expected, print_results)
    return jsonify({'features': output, 'type': 'FeatureCollection'})

def get_events_in_database(find_dict={}, one_result_expected=False, print_results=False):
    output = []

    if one_result_expected:
        single_event = events_current_processed_collection.find_one(find_dict)
        if single_event:
            output.append(process_event_info(single_event))
            if print_results:
                print(u'Event: {0}'.format(single_event.get('name', '<NONE>')))
        else:
            # careful: output is still empty here; make sure output list never set ANYWHERE else
            # i.e. no other conditional branch is entered after this one, same with multiple event case below
            print('No single event with attributes:' + str(find_dict))
    else:
        events_cursor = events_current_processed_collection.find(find_dict)
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
            print('No events found with attributes:' + str(find_dict))

    return output

def process_event_info(event):
    """
        :Description: Returns GeoJSON of singular event matching event name

        :param str event_name: case-insensitive name string to search database for exact match
    """

    # Remove certain keys from dictionary
    event.pop('_id', None) # pop is basically get and remove; pop(key, default)
    event.get('place', {}).pop('id', None) # pop is basically used as if it exists, remove it
    eId = event.pop('id')

    # Clean up certain entries
    event['stats'] = {
        'attending': event.pop('attending_count', 0),
        'noreply': event.pop('noreply_count', 0),
        'interested': event.pop('interested_count', 0),
        'maybe': event.pop('maybe_count', 0)
    }
    if 'source' in event.get('cover', {}): #default of get `{}` so `in` works
        cover_picture = event.pop('cover')['source']
        event['cover_picture'] = cover_picture
    if 'name' in event.get('hoster', {}):
        host = event.pop('hoster')['name']
        event['hoster'] = host

    # Create GeoJSON
    formatted_info = {
        # will ALWAYS have an ID
        'id': eId,
        'type': 'Feature',
        'geometry': {
            # no coordinates? default to Bruin Bear
            'coordinates': [
                event['place']['location'].get('longitude', event_caller.CENTER_LONGITUDE),
                event['place']['location'].get('latitude', event_caller.CENTER_LATITUDE)
            ],
            'type': 'Point'
        },
        'properties': event
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
    if not raw_date:
        return None

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

def clean_up_existing_events(days_back_in_time, chosen_db_name=''):
    remaining_events = {}
    # only choose 1 source's DB of raw event data to check / clean up existing events
    if len(chosen_db_name) > 0:
        chosen_db = all_collections.get(chosen_db_name)
        if chosen_db:
            remaining_events.update(
                event_caller.update_current_events(
                    list(chosen_db.find()), days_back_in_time
                )
            )
        else:
            print('Invalid website source db specified, skipping existing events update')
            return {}
    # look at all DBs (except the testing one)
    else:
        for db_name, raw_data_db in all_collections.iteritems():
            if db_name == 'test':
                continue
            remaining_events.update(
                event_caller.update_current_events(
                    list(raw_data_db.find()), days_back_in_time
                )
            )
    return remaining_events

# Get all UCLA-related Facebook events and add to database
def update_ucla_events_database(use_test=False, days_back_in_time=0, clear_old_db=False):
    # TODO: pass this in as command line arg for testing
    specified_db = 'eventbrite'

    # TODO: figure out if clearing old DB is processed pooled events, or raw data
    # OLD
    # changed_collection = events_fb_collection
    # if use_test:
    #     changed_collection = events_test_collection

    # if clear_old_db:
    #     changed_collection.delete_many({})
    print('before the other string')
    processed_db_events = 'todo'
    new_events_data = {'metadata': {'events': 0}}
    new_count = 0

    # take out all current events from DB, put into list, check for updates
    # processed_db_events = event_caller.update_current_events(list(changed_collection.find()), days_back_in_time)

    # # actually update all in database, but without mass deletion (for safety)
    # for old_event in tqdm(changed_collection.find()):
    #     event_id = old_event['id']
    #     updated_event = processed_db_events.get(event_id)
    #     # if event should be kept and updated
    #     if updated_event:
    #         changed_collection.delete_one({'id': event_id})
    #         changed_collection.insert_one(updated_event)
    #     # event's time has passed, according to update_current_events
    #     else:
    #         changed_collection.delete_one({'id': event_id})

    # new_events_data = event_caller.get_facebook_events(days_back_in_time)
    # # debugging events output
    # # with open('events_out.json', 'w') as outfile:
    # #     json.dump(new_events_data, outfile, sort_keys=True, indent=4, separators=(',', ': '))

    # # Also add all new events to total_events

    # # .find() returns a CURSOR, like an iterator (NOT a list or dictionary)
    # # conclusion after running some small timed tests: for our purposes and with our data sizes,
    # # INCREMENTAL DB calls (iterate over .find()) and BATCH DB calls (list(.find())) take about the same time
    # # normally use incremental Cursor, to save memory usage
    # new_count = 0
    # for event in tqdm(new_events_data['events']):
    #     curr_id = event['id']
    #     existing_event = processed_db_events.get(curr_id)

    #     # sidenote: when event inserted into DB,
    #     # the event dict has _id key appended to itself both remotely (onto DB) and LOCALLY!

    #     # don't need to do anything if event found previously, since updated in update_current_events()
    #     if existing_event:
    #         continue
    #     changed_collection.insert_one(event)
    #     new_count += 1

    #     # below = UPDATE: pymongo only allows update of specifically listed attributes in a dictionary...
    #     # so delete old if exists, then insert new

    #     # See if event already existed
    #     update_event = events_fb_collection.find_one({'id': curr_id})

    #     # If it existed then delete it, new event gets inserted either way
    #     if update_event:
    #         events_fb_collection.delete_one({'id': curr_id})
    #     events_fb_collection.insert_one(event)

    # remove_db_duplicates(changed_collection)
    print('here\'s a log testing string...')
    return 'Updated with {0} retrieved events, {1} new ones.'.format(new_events_data['metadata']['events'], new_count)
