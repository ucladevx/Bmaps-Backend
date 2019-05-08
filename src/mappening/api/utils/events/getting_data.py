from flask import jsonify
import time, datetime, dateutil.parser, pytz
from dateutil.tz import tzlocal
from tqdm import tqdm   # a progress bar, pretty
import json
import os
import re

from definitions import CENTER_LATITUDE, CENTER_LONGITUDE, BASE_EVENT_START_BOUND

from mappening.utils.database import events_fb_collection, events_eventbrite_collection, events_test_collection, fb_pages_saved_collection
from mappening.utils.database import events_current_processed_collection

from mappening.api.utils.facebook_scraper import get_data, process_data

from mappening.api.utils.eventbrite_scraper import eventbrite_scraper

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

# Get all UCLA-related events from sources (Eventbrite, FB, etc.) and add to database
def update_ucla_events_database(use_test=False, days_back_in_time=0, clear_old_db=False):
    
    clean_up_existing_events(days_back_in_time)

    eb_count = eventbrite_scraper.entire_eventbrite_retrieval(days_back_in_time)

    # processed_db_events = 'todo'
    new_events_data = {'metadata': {'events': eb_count}}
    new_count = eb_count
   
    return 'Updated with {0} retrieved events, {1} new ones.'.format(new_events_data['metadata']['events'], new_count)
