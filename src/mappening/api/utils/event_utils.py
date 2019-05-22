from flask import jsonify
import time, datetime, dateutil.parser, pytz
from dateutil.tz import tzlocal
from tqdm import tqdm   # a progress bar, pretty
import json
import os
import re

from definitions import CENTER_LATITUDE, CENTER_LONGITUDE, BASE_EVENT_START_BOUND

from mappening.utils.database import events_fb_collection, events_eventbrite_collection, events_test_collection, fb_pages_saved_collection
from mappening.utils.database import events_current_processed_collection, events_internal_added_collection

from mappening.api.utils import facebook_scraper, eventbrite_scraper

# each website source has its own database, where raw event info is stored
all_raw_collections = {
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
        events_internal_cursor = events_internal_added_collection.find(find_dict)
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
        
        for event in events_internal_cursor:
            output.append(process_event_info(event))

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
                event['place']['location'].get('longitude', float(CENTER_LONGITUDE)),
                event['place']['location'].get('latitude', float(CENTER_LATITUDE))
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

def time_in_past(time_str, days_before=BASE_EVENT_START_BOUND):
    """
    takes in an FB formatted timestamp: Y-m-d'T'H:M:S<tz>
    to account for weird timezone things, construct 2 datetime objects
    one from simply parsing the string, and another from current time
    required by Python (and to standardize), need to convert both times to UTC explicitly, use pytz module
    return boolean, if given time string has passed in real time
    """
    try:
        # Use dateutil parser to get time zone
        time_obj = dateutil.parser.parse(time_str).astimezone(pytz.UTC)
    except ValueError:
        # Got invalid date string
        print('Invalid datetime string from event \'start_time\' key, cannot be parsed!')
        return False
    # need to explicitly set time zone (tzlocal() here), or else astimezone() will not work
    now = datetime.datetime.now(tzlocal()).astimezone(pytz.UTC)

    # if time from string is smaller than now, with offset (to match time range of new events found)
    # offset shifts the boundary back in time, for which events to update rather than delete
    return time_obj <= now - datetime.timedelta(days=days_before)

# ONLY clean up processed events, never raw DB
def clean_up_existing_events(days_before=BASE_EVENT_START_BOUND):
    """
    update events currently in processed events database before new ones put in
    means remove ones too old and re-search the rest
    events = list of all event info dicts
    """
    print('Go through currently stored events to update.')
    kept_events = {}
    for processed_event in tqdm(events_current_processed_collection.find()):
        # for multi-day events that were found a long time ago, have to recall API to check for updates (e.g. cancelled)
        # to tell if multi-day event, check "duplicate_occurrence" tag
        
        if not time_in_past(processed_event['start_time'], days_before):
            # TODO: make a general process_event function for events of each source
            # this line is FB specific
            # updated_event_dict = process_event(event, event.get('hoster', '<NONE>'), event.get('duplicate_occurrence', False))
            kept_events.update(processed_event)
        # return a dict of kept event IDs to their info
    return kept_events

# Get all UCLA-related events from sources (Eventbrite, FB, etc.) and add to database
def update_ucla_events_database(use_test=False, days_back_in_time=0, clear_old_db=False):
    
    clean_up_existing_events(days_back_in_time)

    eb_count = eventbrite_scraper.entire_eventbrite_retrieval(days_back_in_time)

    # processed_db_events = 'todo'
    new_events_data = {'metadata': {'events': eb_count}}
    new_count = eb_count
    # OLD
    # changed_collection = events_fb_collection
    # if use_test:
    #     changed_collection = events_test_collection

    # if clear_old_db:
    #     changed_collection.delete_many({})

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

    # new_events_data = facebook_scraper.get_facebook_events(days_back_in_time)
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
    return 'Updated with {0} retrieved events, {1} new ones.'.format(new_events_data['metadata']['events'], new_count)
